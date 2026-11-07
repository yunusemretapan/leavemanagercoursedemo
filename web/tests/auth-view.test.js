import { test } from 'node:test';
import assert from 'node:assert/strict';

import { errorCodeOf, loginFormView, messageForError, welcomeText } from '../js/auth-view.js';

test('loginFormView states', () => {
  assert.deepEqual(loginFormView(), { buttonText: 'Giriş yap', buttonDisabled: false, message: '' });
  assert.deepEqual(loginFormView({ submitting: true }), {
    buttonText: 'Giriş yapılıyor…',
    buttonDisabled: true,
    message: '',
  });
  assert.deepEqual(loginFormView({ errorCode: 'INVALID_CREDENTIALS' }), {
    buttonText: 'Giriş yap',
    buttonDisabled: false,
    message: 'Kullanıcı adı veya parola hatalı.',
  });
  assert.equal(
    loginFormView({ errorCode: 'SESSION_EXPIRED' }).message,
    'Oturumunuzun süresi doldu. Lütfen tekrar giriş yapın.',
  );
  assert.equal(
    loginFormView({ errorCode: 'NETWORK' }).message,
    'Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.',
  );
});

test('messageForError codes', () => {
  assert.equal(messageForError(null), '');
  assert.equal(messageForError('UNAUTHENTICATED'), '');
  assert.equal(messageForError('INVALID_CREDENTIALS'), 'Kullanıcı adı veya parola hatalı.');
  assert.equal(messageForError('VALIDATION_ERROR'), 'Kullanıcı adı veya parola hatalı.');
  assert.equal(
    messageForError('SESSION_EXPIRED'),
    'Oturumunuzun süresi doldu. Lütfen tekrar giriş yapın.',
  );
  assert.equal(
    messageForError('INTERNAL_ERROR'),
    'Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.',
  );
});

test('welcomeText shows name and role', () => {
  assert.equal(
    welcomeText({ full_name: 'Ali Demir', role_label: 'Çalışan' }),
    'Hoş geldin, Ali Demir (Çalışan)',
  );
});

test('errorCodeOf reads the standard error body', () => {
  assert.equal(errorCodeOf({ error: { code: 'SESSION_EXPIRED', message: '…' } }), 'SESSION_EXPIRED');
  assert.equal(errorCodeOf(null), null);
  assert.equal(errorCodeOf({ status: 'ok' }), null);
});
