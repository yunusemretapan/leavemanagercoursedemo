// Pure view functions for the start page's system status (docs/testing.md, Test layers).
// No DOM here: main.js binds the result to the page.

const VIEWS = {
  loading: { text: 'Sistem durumu kontrol ediliyor…', className: 'status status--loading' },
  ok: { text: 'Sistem çalışıyor', className: 'status status--ok' },
  error: {
    text: 'Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.',
    className: 'status status--error',
  },
};

/** Text and CSS class for a status state; an unknown state renders as an error. */
export function renderStatus(state) {
  return VIEWS[state] ?? VIEWS.error;
}

/** Status state from a health check response: ok only for HTTP ok and body.status === 'ok'. */
export function stateFromHealth(httpOk, body) {
  return httpOk && body !== null && typeof body === 'object' && body.status === 'ok'
    ? 'ok'
    : 'error';
}
