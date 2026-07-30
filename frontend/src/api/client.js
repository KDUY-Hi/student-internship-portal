function defaultApiUrl() {
  if (typeof window === 'undefined') return 'http://localhost:8000';
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

export const API_URL = (import.meta.env.VITE_API_URL || defaultApiUrl()).replace(/\/$/, '');

let inMemoryAccessToken = '';
let onSessionRefresh = null;
let onAuthExpired = null;
let refreshPromise = null;

export function setAccessToken(token) {
  inMemoryAccessToken = token || '';
}

export function configureAuthHandlers({ onRefresh, onExpired } = {}) {
  onSessionRefresh = onRefresh || null;
  onAuthExpired = onExpired || null;
}

export function friendlyError(error) {
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return `Không thể kết nối backend tại ${API_URL}. Hãy chạy: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`;
  }
  return error.message || 'API request failed';
}

async function parseError(response) {
  const data = await response.json().catch(() => ({}));
  return data.detail || `API error ${response.status}`;
}

async function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(await parseError(response));
        return response.json();
      })
      .then((data) => {
        setAccessToken(data.access_token);
        onSessionRefresh?.(data);
        return data.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

export async function logoutSession() {
  await fetch(`${API_URL}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  }).catch(() => {});
  setAccessToken('');
}

export async function api(path, { token, method = 'GET', body, isForm = false, skipRefresh = false } = {}) {
  const headers = {};
  const requestToken = token || inMemoryAccessToken;
  if (requestToken) headers.Authorization = `Bearer ${requestToken}`;
  if (body && !isForm) headers['Content-Type'] = 'application/json';

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      credentials: 'include',
      body: isForm ? body : body ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    throw new Error(friendlyError(error));
  }

  if (response.status === 401 && !skipRefresh && !path.startsWith('/auth/')) {
    try {
      const refreshedToken = await refreshSession();
      return api(path, { token: refreshedToken, method, body, isForm, skipRefresh: true });
    } catch {
      setAccessToken('');
      onAuthExpired?.();
      throw new Error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      setAccessToken('');
      onAuthExpired?.();
    }
    throw new Error(await parseError(response));
  }

  if (response.status === 204) return null;
  return response.json();
}
