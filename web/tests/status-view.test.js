import { test } from 'node:test';
import assert from 'node:assert/strict';

import { renderStatus, stateFromHealth } from '../js/status-view.js';

test('renderStatus loading shows the checking text', () => {
  assert.deepEqual(renderStatus('loading'), {
    text: 'Sistem durumu kontrol ediliyor…',
    className: 'status status--loading',
  });
});

test('renderStatus ok shows that the system works', () => {
  assert.deepEqual(renderStatus('ok'), {
    text: 'Sistem çalışıyor',
    className: 'status status--ok',
  });
});

test('renderStatus error shows the unreachable text', () => {
  assert.deepEqual(renderStatus('error'), {
    text: 'Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.',
    className: 'status status--error',
  });
});

test('renderStatus unknown state falls back to error', () => {
  assert.equal(renderStatus('whatever').text, renderStatus('error').text);
});

test('stateFromHealth is ok only for an ok response with status ok', () => {
  assert.equal(stateFromHealth(true, { status: 'ok', database: 'ok' }), 'ok');
  assert.equal(stateFromHealth(false, { error: { code: 'SERVICE_UNAVAILABLE' } }), 'error');
  // A non-ok HTTP status is an error even if the body claims ok (VERIFY round 1, F-V2).
  assert.equal(stateFromHealth(false, { status: 'ok' }), 'error');
  assert.equal(stateFromHealth(true, null), 'error');
  assert.equal(stateFromHealth(true, { status: 'degraded' }), 'error');
});
