// Pure view functions for login and welcome (spec 0002, User experience).
// No DOM here: main.js binds the results; texts reach the page via textContent only.

export const MESSAGES = {
  INVALID_CREDENTIALS: 'Kullanıcı adı veya parola hatalı.',
  SESSION_EXPIRED: 'Oturumunuzun süresi doldu. Lütfen tekrar giriş yapın.',
  NETWORK: 'Sunucuya ulaşılamıyor. Lütfen daha sonra tekrar deneyin.',
};

/**
 * Message for an API error code. Not signed in yet is no error (empty message); a rejected
 * login form (validation) reads like wrong credentials; anything unknown is a server problem.
 */
export function messageForError(code) {
  switch (code) {
    case null:
    case undefined:
    case 'UNAUTHENTICATED':
      return '';
    case 'INVALID_CREDENTIALS':
    case 'VALIDATION_ERROR':
      return MESSAGES.INVALID_CREDENTIALS;
    case 'SESSION_EXPIRED':
      return MESSAGES.SESSION_EXPIRED;
    default:
      return MESSAGES.NETWORK;
  }
}

/** Login form view: { buttonText, buttonDisabled, message }. */
export function loginFormView({ submitting = false, errorCode = null } = {}) {
  return {
    buttonText: submitting ? 'Giriş yapılıyor…' : 'Giriş yap',
    buttonDisabled: submitting,
    message: submitting ? '' : messageForError(errorCode),
  };
}

/** Greeting for the signed-in user, e.g. "Hoş geldin, Ali Demir (Çalışan)". */
export function welcomeText(user) {
  return `Hoş geldin, ${user.full_name} (${user.role_label})`;
}

/** Error code from an API error body; null when the body has none. */
export function errorCodeOf(body) {
  return body && typeof body === 'object' && body.error ? body.error.code ?? null : null;
}
