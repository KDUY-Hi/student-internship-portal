function defaultApiUrl() {
  if (typeof window === 'undefined') return 'http://localhost:8000';
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

export const API_URL = (import.meta.env.VITE_API_URL || defaultApiUrl()).replace(/\/$/, '');

export function friendlyError(error) {
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return `Không thể kết nối backend tại ${API_URL}. Hãy chạy: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`;
  }
  return error.message || 'API request failed';
}

export async function api(path, { token, method = 'GET', body, isForm = false } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body && !isForm) headers['Content-Type'] = 'application/json';

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: isForm ? body : body ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    throw new Error(friendlyError(error));
  }

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.dispatchEvent(new Event('auth-expired'));
      if (!window.location.pathname.startsWith('/login')) {
        window.history.replaceState({}, '', '/');
        window.dispatchEvent(new PopStateEvent('popstate'));
      }
    }
    throw new Error(data.detail || `API error ${response.status}`);
  }

  if (response.status === 204) return null;
  return response.json();
}
