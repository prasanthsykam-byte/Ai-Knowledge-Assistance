const authScreen = document.querySelector('#auth-screen');
const appShell = document.querySelector('#app-shell');
const authForm = document.querySelector('#auth-form');
const authTitle = document.querySelector('#auth-title');
const authSubtitle = document.querySelector('#auth-subtitle');
const authSubmit = document.querySelector('#auth-submit');
const authError = document.querySelector('#auth-error');
const switchAuth = document.querySelector('#switch-auth');
const switchPrompt = document.querySelector('#switch-prompt');
const confirmField = document.querySelector('#confirm-field');
const emailInput = document.querySelector('#email');
const passwordInput = document.querySelector('#password');
const confirmPasswordInput = document.querySelector('#confirm-password');
const filesInput = document.querySelector('#files');
const list = document.querySelector('#document-list');
const fileCount = document.querySelector('#file-count');
const emptyState = document.querySelector('#empty-state');
const conversation = document.querySelector('#conversation');
const form = document.querySelector('#question-form');
const questionInput = document.querySelector('#question');
const status = document.querySelector('#status');
const userEmail = document.querySelector('#user-email');
const userInitial = document.querySelector('#user-initial');
const logout = document.querySelector('#logout');
let isSignup = false;

const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' })[char]);
const setStatus = (text, busy = false) => { status.textContent = text; status.classList.toggle('busy', busy); };

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const body = response.status === 204 ? '' : await response.text();
  let data = null;
  try { data = body ? JSON.parse(body) : null; } catch { data = { error: body || 'The server returned an invalid response.' }; }
  if (!response.ok) {
    if (response.status === 401 && !url.startsWith('/api/auth/')) showAuth();
    throw new Error(data.error || `Request failed (${response.status}).`);
  }
  return data;
}

function setAuthMode(signup) {
  isSignup = signup;
  authTitle.textContent = signup ? 'Create your space' : 'Welcome back';
  authSubtitle.textContent = signup ? 'Create a secure local account for your files.' : 'Log in to access your knowledge dashboard.';
  authSubmit.innerHTML = signup ? 'Create account <span>→</span>' : 'Log in <span>→</span>';
  confirmField.hidden = !signup;
  confirmPasswordInput.required = signup;
  passwordInput.autocomplete = signup ? 'new-password' : 'current-password';
  switchPrompt.textContent = signup ? 'Already have an account?' : 'New to Atlas?';
  switchAuth.textContent = signup ? 'Log in' : 'Create an account';
  authError.textContent = '';
}

function showAuth() {
  appShell.hidden = true;
  authScreen.hidden = false;
  conversation.innerHTML = '';
  setAuthMode(false);
}

function showApp(user) {
  authScreen.hidden = true;
  appShell.hidden = false;
  userEmail.textContent = user.email;
  userInitial.textContent = user.email.slice(0, 1).toUpperCase();
  loadDocuments();
}

async function loadDocuments() {
  const docs = await request('/api/documents');
  list.innerHTML = '';
  fileCount.textContent = docs.length;
  emptyState.hidden = docs.length > 0;
  if (!docs.length) { list.innerHTML = '<p class="empty-docs">No files uploaded yet</p>'; return; }
  const template = document.querySelector('#doc-template');
  docs.forEach((doc) => {
    const node = template.content.cloneNode(true);
    node.querySelector('strong').textContent = doc.name;
    node.querySelector('small').textContent = `${Math.max(1, Math.round(doc.size / 1024))} KB · ${new Date(doc.addedAt).toLocaleDateString()}`;
    node.querySelector('button').onclick = async () => {
      if (!window.confirm(`Delete “${doc.name}”? This cannot be undone.`)) return;
      await request(`/api/documents/${doc.id}`, { method: 'DELETE' });
      setStatus('File deleted');
      loadDocuments();
    };
    list.append(node);
  });
}

function addMessage(kind, content, sources = []) {
  const card = document.createElement('article');
  card.className = `message ${kind}`;
  const sourceMarkup = sources.length ? `<details><summary>Sources (${sources.length})</summary>${sources.map((source) => `<div class="source"><b>${escapeHtml(source.source)}</b><p>${escapeHtml(source.excerpt)}</p></div>`).join('')}</details>` : '';
  card.innerHTML = `<div class="message-label">${kind === 'user' ? 'You' : 'Atlas'}</div><div class="message-content ${kind === 'assistant' ? 'beginner-answer' : ''}">${escapeHtml(content).replace(/\n/g, '<br>')}</div>${sourceMarkup}`;
  conversation.append(card);
  card.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

authForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  authError.textContent = '';
  if (isSignup && passwordInput.value !== confirmPasswordInput.value) { authError.textContent = 'Passwords do not match.'; return; }
  authSubmit.disabled = true;
  try {
    const result = await request(isSignup ? '/api/auth/signup' : '/api/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: emailInput.value, password: passwordInput.value })
    });
    passwordInput.value = ''; confirmPasswordInput.value = '';
    showApp(result.user);
  } catch (error) { authError.textContent = error.message; }
  finally { authSubmit.disabled = false; }
});

switchAuth.addEventListener('click', () => setAuthMode(!isSignup));

filesInput.addEventListener('change', async () => {
  if (!filesInput.files.length) return;
  setStatus('Reading files…', true);
  const data = new FormData();
  [...filesInput.files].forEach((file) => data.append('files', file));
  try { const result = await request('/api/upload', { method: 'POST', body: data }); setStatus(`${result.documents.length} file${result.documents.length > 1 ? 's' : ''} added`); await loadDocuments(); }
  catch (error) { setStatus(error.message); }
  finally { filesInput.value = ''; }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;
  addMessage('user', question); questionInput.value = ''; setStatus('Thinking…', true);
  try { const result = await request('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) }); addMessage('assistant', result.answer, result.sources); setStatus('Ready'); }
  catch (error) { addMessage('assistant', error.message); setStatus('Ready'); }
});

logout.addEventListener('click', async () => { await request('/api/auth/logout', { method: 'POST' }); showAuth(); });

async function initialise() {
  try { const result = await request('/api/auth/me'); showApp(result.user); }
  catch { showAuth(); }
}

initialise();
