// DOM binding only — no logic (the logic lives in status-view.js / auth-view.js and is tested there).
import { renderStatus, stateFromHealth } from './status-view.js';
import { errorCodeOf, loginFormView, welcomeText } from './auth-view.js';

const statusElement = document.getElementById('status');
const loginSection = document.getElementById('login');
const loginForm = document.getElementById('login-form');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const loginButton = document.getElementById('login-button');
const loginMessage = document.getElementById('login-message');
const welcomeSection = document.getElementById('welcome');
const welcomeElement = document.getElementById('welcome-text');
const logoutButton = document.getElementById('logout-button');

const NETWORK = 'NETWORK';

function showStatus(state) {
  const view = renderStatus(state);
  statusElement.textContent = view.text;
  statusElement.className = view.className;
}

function showLogin(formState) {
  const view = loginFormView(formState);
  loginButton.textContent = view.buttonText;
  loginButton.disabled = view.buttonDisabled;
  loginMessage.textContent = view.message;
  welcomeSection.hidden = true;
  loginSection.hidden = false;
}

function showWelcome(user) {
  welcomeElement.textContent = welcomeText(user);
  loginSection.hidden = true;
  welcomeSection.hidden = false;
  logoutButton.focus();
}

async function readJson(response) {
  return response.json().catch(() => null);
}

async function checkHealth() {
  showStatus('loading');
  try {
    const response = await fetch('/api/health');
    showStatus(stateFromHealth(response.ok, await readJson(response)));
  } catch {
    showStatus('error');
  }
}

async function loadCurrentUser() {
  try {
    const response = await fetch('/api/me');
    const body = await readJson(response);
    if (response.ok) {
      showWelcome(body);
    } else {
      showLogin({ errorCode: response.status === 401 ? errorCodeOf(body) : NETWORK });
    }
  } catch {
    showLogin({ errorCode: NETWORK });
  }
}

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  showLogin({ submitting: true });
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: usernameInput.value, password: passwordInput.value }),
    });
    const body = await readJson(response);
    passwordInput.value = '';
    if (response.ok) {
      showWelcome(body);
    } else {
      showLogin({ errorCode: errorCodeOf(body) ?? NETWORK });
      passwordInput.focus();
    }
  } catch {
    passwordInput.value = '';
    showLogin({ errorCode: NETWORK });
  }
});

logoutButton.addEventListener('click', async () => {
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    });
  } finally {
    showLogin({});
    usernameInput.focus();
  }
});

checkHealth();
loadCurrentUser();
