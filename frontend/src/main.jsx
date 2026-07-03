import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { AuthPanel } from './components/AuthPanel';
import { Sidebar, Topbar } from './components/ui';
import { AdminPages } from './pages/AdminPages';
import { CompanyPages } from './pages/CompanyPages';
import { StudentPages } from './pages/StudentPages';
import { defaultPathForRole, normalizePathForRole, useRoute } from './hooks/useRoute';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'));
  const [mode, setMode] = useState('login');
  const [message, setMessage] = useState('');
  const session = useMemo(() => ({ token, user }), [token, user]);
  const { pathname, navigate } = useRoute();
  const currentPath = user ? normalizePathForRole(user.role, pathname) : pathname;

  useEffect(() => {
    if (user && currentPath !== pathname) navigate(currentPath);
  }, [user, currentPath, pathname]);

  useEffect(() => {
    if (!message) return undefined;
    const timeoutId = window.setTimeout(() => setMessage(''), 3000);
    return () => window.clearTimeout(timeoutId);
  }, [message]);

  useEffect(() => {
    function handleAuthExpired() {
      setToken('');
      setUser(null);
      setMessage('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
    }
    window.addEventListener('auth-expired', handleAuthExpired);
    return () => window.removeEventListener('auth-expired', handleAuthExpired);
  }, []);

  function saveSession(data) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    navigate(defaultPathForRole(data.user.role));
    setMessage('');
  }

  function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken('');
    setUser(null);
    setMessage('');
  }

  if (!user) {
    return (
      <main className="public-shell">
        {message && <div className="notice floating">{message}</div>}
        <AuthPanel mode={mode} setMode={setMode} onAuth={saveSession} setMessage={setMessage} />
      </main>
    );
  }

  return (
    <main className={`app-shell ${user.role === 'admin' ? 'admin-shell' : ''}`}>
      <Sidebar role={user.role} currentPath={currentPath} navigate={navigate} />
      <section className="workspace">
        <Topbar user={user} navigate={navigate} logout={logout} />
        {message && <div className="notice toast-notice">{message}</div>}
        {user.role === 'student' && <StudentPages session={session} route={currentPath} navigate={navigate} setMessage={setMessage} />}
        {user.role === 'company' && <CompanyPages session={session} route={currentPath} navigate={navigate} setMessage={setMessage} />}
        {user.role === 'admin' && <AdminPages session={session} route={currentPath} setMessage={setMessage} />}
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
