// DOM binding only — no logic (the logic lives in status-view.js and is tested there).
import { renderStatus, stateFromHealth } from './status-view.js';

const statusElement = document.getElementById('status');

function show(state) {
  const view = renderStatus(state);
  statusElement.textContent = view.text;
  statusElement.className = view.className;
}

async function checkHealth() {
  show('loading');
  try {
    const response = await fetch('/api/health');
    const body = await response.json().catch(() => null);
    show(stateFromHealth(response.ok, body));
  } catch {
    show('error');
  }
}

checkHealth();
