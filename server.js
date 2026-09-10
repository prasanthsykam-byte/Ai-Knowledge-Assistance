import 'dotenv/config';
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import express from 'express';
import multer from 'multer';
import mammoth from 'mammoth';
import { GoogleGenAI } from '@google/genai';
import pdf from 'pdf-parse';
import ExcelJS from 'exceljs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const port = process.env.PORT || 3000;
const dataDir = process.env.VERCEL ? path.join('/tmp', 'atlas-data') : path.join(__dirname, 'data');
const usersFile = path.join(dataDir, 'users.json');
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 25 * 1024 * 1024 } });
const knowledge = new Map();
const users = new Map();
const sessions = new Map();
const supportedExtensions = new Set(['.txt', '.md', '.csv', '.json', '.pdf', '.docx', '.xlsx']);
const geminiApiKey = process.env.GEMINI_API_KEY || process.env.OPENAI_API_KEY;
const sessionLifetimeMs = 7 * 24 * 60 * 60 * 1000;

await fs.mkdir(dataDir, { recursive: true });
try {
  const storedUsers = JSON.parse(await fs.readFile(usersFile, 'utf8'));
  for (const user of storedUsers) if (user?.id && user?.email && user?.passwordHash) users.set(user.id, user);
} catch (error) {
  if (error.code !== 'ENOENT') console.warn('Could not load local users.');
}
for (const entry of await fs.readdir(dataDir)) {
  if (!entry.endsWith('.json')) continue;
  try {
    const document = JSON.parse(await fs.readFile(path.join(dataDir, entry), 'utf8'));
    if (document?.id && document?.name && Array.isArray(document?.chunks)) knowledge.set(document.id, document);
  } catch {
    // Ignore malformed local cache files instead of preventing the app from starting.
  }
}
app.use(express.json({ limit: '1mb' }));
app.use(express.static(path.join(__dirname, 'public')));

function compact(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function publicUser(user) {
  return { id: user.id, email: user.email, createdAt: user.createdAt };
}

function parseCookies(request) {
  return Object.fromEntries((request.headers.cookie || '').split(';').map((item) => {
    const index = item.indexOf('=');
    return index === -1 ? [] : [item.slice(0, index).trim(), decodeURIComponent(item.slice(index + 1).trim())];
  }).filter((item) => item.length));
}

function setSessionCookie(response, sessionId) {
  response.setHeader('Set-Cookie', `atlas_session=${encodeURIComponent(sessionId)}; HttpOnly; SameSite=Lax; Path=/; Max-Age=${sessionLifetimeMs / 1000}`);
}

function clearSessionCookie(response) {
  response.setHeader('Set-Cookie', 'atlas_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0');
}

async function saveUsers() {
  await fs.writeFile(usersFile, JSON.stringify([...users.values()]), 'utf8');
}

async function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const derived = await new Promise((resolve, reject) => crypto.scrypt(password, salt, 64, (error, key) => error ? reject(error) : resolve(key)));
  return `${salt}:${derived.toString('hex')}`;
}

async function passwordMatches(password, stored) {
  const [salt, hash] = String(stored).split(':');
  if (!salt || !hash) return false;
  const derived = await new Promise((resolve, reject) => crypto.scrypt(password, salt, 64, (error, key) => error ? reject(error) : resolve(key)));
  return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), derived);
}

function createSession(response, user) {
  const id = crypto.randomBytes(32).toString('base64url');
  sessions.set(id, { userId: user.id, expiresAt: Date.now() + sessionLifetimeMs });
  setSessionCookie(response, id);
}

function requireAuth(request, response, next) {
  const sessionId = parseCookies(request).atlas_session;
  const session = sessionId && sessions.get(sessionId);
  if (!session || session.expiresAt < Date.now() || !users.has(session.userId)) {
    if (sessionId) sessions.delete(sessionId);
    return response.status(401).json({ error: 'Please log in to continue.' });
  }
  request.user = users.get(session.userId);
  next();
}

function splitIntoChunks(text, size = 1200, overlap = 180) {
  const clean = compact(text);
  const chunks = [];
  for (let start = 0; start < clean.length; start += size - overlap) {
    const part = clean.slice(start, start + size);
    if (part) chunks.push(part);
  }
  return chunks;
}

function scoreChunk(chunk, question) {
  const terms = question.toLowerCase().match(/[a-z0-9]{3,}/g) || [];
  const lower = chunk.toLowerCase();
  return terms.reduce((score, term) => score + (lower.match(new RegExp(term, 'g')) || []).length, 0);
}

async function extractText(file) {
  const ext = path.extname(file.originalname).toLowerCase();
  if (!supportedExtensions.has(ext)) throw new Error(`Unsupported file type: ${ext || 'unknown'}`);
  if (['.txt', '.md', '.csv', '.json'].includes(ext)) return file.buffer.toString('utf8');
  if (ext === '.pdf') return (await pdf(file.buffer)).text;
  if (ext === '.docx') return (await mammoth.extractRawText({ buffer: file.buffer })).value;
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(file.buffer);
  return workbook.worksheets.map((sheet) => {
    const rows = [];
    sheet.eachRow({ includeEmpty: false }, (row) => rows.push(row.values.slice(1).join(', ')));
    return `Sheet: ${sheet.name}\n${rows.join('\n')}`;
  }).join('\n\n');
}

app.post('/api/auth/signup', async (req, res) => {
  const email = compact(req.body?.email).toLowerCase();
  const password = String(req.body?.password || '');
  if (!/^\S+@\S+\.\S+$/.test(email)) return res.status(400).json({ error: 'Enter a valid email address.' });
  if (password.length < 8) return res.status(400).json({ error: 'Use a password with at least 8 characters.' });
  if ([...users.values()].some((user) => user.email === email)) return res.status(409).json({ error: 'An account with this email already exists.' });
  const user = { id: crypto.randomUUID(), email, passwordHash: await hashPassword(password), createdAt: new Date().toISOString() };
  users.set(user.id, user);
  await saveUsers();
  createSession(res, user);
  res.status(201).json({ user: publicUser(user) });
});

app.post('/api/auth/login', async (req, res) => {
  const email = compact(req.body?.email).toLowerCase();
  const password = String(req.body?.password || '');
  const user = [...users.values()].find((account) => account.email === email);
  if (!user || !(await passwordMatches(password, user.passwordHash))) return res.status(401).json({ error: 'Email or password is incorrect.' });
  createSession(res, user);
  res.json({ user: publicUser(user) });
});

app.post('/api/auth/logout', (req, res) => {
  const sessionId = parseCookies(req).atlas_session;
  if (sessionId) sessions.delete(sessionId);
  clearSessionCookie(res);
  res.status(204).end();
});

app.get('/api/auth/me', (req, res) => {
  const sessionId = parseCookies(req).atlas_session;
  const session = sessionId && sessions.get(sessionId);
  const user = session && session.expiresAt >= Date.now() ? users.get(session.userId) : null;
  if (!user) return res.status(401).json({ error: 'Not logged in.' });
  res.json({ user: publicUser(user) });
});

app.get('/api/documents', requireAuth, (req, res) => {
  res.json([...knowledge.values()].filter((document) => document.ownerId === req.user.id).map(({ chunks, text, ...document }) => document));
});

app.post('/api/upload', requireAuth, upload.array('files', 10), async (req, res) => {
  try {
    const files = req.files || [];
    if (!files.length) return res.status(400).json({ error: 'Choose at least one file.' });
    const added = [];
    for (const file of files) {
      const text = compact(await extractText(file));
      if (!text) throw new Error(`${file.originalname} did not contain readable text.`);
      const id = crypto.randomUUID();
      const document = { id, ownerId: req.user.id, name: file.originalname, size: file.size, addedAt: new Date().toISOString(), text, chunks: splitIntoChunks(text) };
      knowledge.set(id, document);
      await fs.writeFile(path.join(dataDir, `${id}.json`), JSON.stringify(document), 'utf8');
      added.push({ id, name: document.name, chunks: document.chunks.length });
    }
    res.status(201).json({ documents: added });
  } catch (error) {
    res.status(400).json({ error: error.message || 'Could not read that file.' });
  }
});

app.delete('/api/documents/:id', requireAuth, async (req, res) => {
  const document = knowledge.get(req.params.id);
  if (!document || document.ownerId !== req.user.id) return res.status(404).json({ error: 'Document not found.' });
  knowledge.delete(req.params.id);
  await fs.rm(path.join(dataDir, `${req.params.id}.json`), { force: true });
  res.status(204).end();
});

app.post('/api/ask', requireAuth, async (req, res) => {
  const question = compact(req.body?.question);
  if (!question) return res.status(400).json({ error: 'Enter a question.' });
  const userDocuments = [...knowledge.values()].filter((document) => document.ownerId === req.user.id);
  if (!userDocuments.length) return res.status(400).json({ error: 'Upload knowledge first.' });

  const matches = userDocuments.flatMap((document) => document.chunks.map((content, index) => ({
    source: document.name, content, score: scoreChunk(content, question), index
  }))).sort((a, b) => b.score - a.score).slice(0, 6);
  const context = matches.map((match, i) => `[${i + 1}] ${match.source}\n${match.content}`).join('\n\n');

  if (!geminiApiKey) {
    return res.json({
      answer: 'AI answering is not configured yet. Add GEMINI_API_KEY to a .env file, restart the app, and ask again. Here are the most relevant passages from your uploads:',
      sources: matches.map(({ source, content }) => ({ source, excerpt: content }))
    });
  }

  try {
    const client = new GoogleGenAI({ apiKey: geminiApiKey });
    const response = await client.models.generateContent({
      model: process.env.GEMINI_MODEL || 'gemini-3.6-flash',
      contents: `Knowledge:\n${context}\n\nQuestion: ${question}`,
      config: {
        systemInstruction: `You are a patient knowledge assistant for beginner students. Answer only using the supplied knowledge. If it does not contain the answer, say so plainly.

Make each answer easy to understand:
- Start with a one- or two-sentence direct answer.
- Explain ideas in a logical order, using short numbered steps when there is a process or more than one key point.
- Use simple everyday language. Define an unfamiliar technical word the first time you use it.
- Keep sentences and paragraphs short. Give one small example only when it makes the idea clearer.
- End with a brief "Remember:" line containing the main takeaway.
- Use plain text only: do not use Markdown tables, code blocks, or decorative symbols.
- Cite supporting passages as [1], [2], and so on when useful.`
      }
    });
    res.json({ answer: response.text || 'I could not generate an answer from the supplied knowledge.', sources: matches.map(({ source, content }) => ({ source, excerpt: content })) });
  } catch (error) {
    res.status(502).json({ error: `Gemini could not answer: ${error.message}` });
  }
});

export default app;

if (!process.env.VERCEL) {
  app.listen(port, () => console.log(`Knowledge Assistant is running at http://localhost:${port}`));
}
