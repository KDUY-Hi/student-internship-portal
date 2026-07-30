import { useEffect, useState } from 'react';

export function roleBasePath(role) {
  if (role === 'company') return '/company';
  if (role === 'admin') return '/admin';
  return '/student';
}

export function defaultPathForRole(role) {
  if (role === 'company') return '/company/applicants';
  if (role === 'admin') return '/admin/posts';
  return '/student/jobs';
}

export function normalizePathForRole(role, pathname) {
  const base = roleBasePath(role);
  if (pathname === base) return defaultPathForRole(role);
  if (!pathname.startsWith(base)) return defaultPathForRole(role);
  return pathname;
}

export function useRoute() {
  const [pathname, setPathname] = useState(window.location.pathname);

  useEffect(() => {
    function handlePopState() {
      setPathname(window.location.pathname);
    }
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  function navigate(path) {
    if (window.location.pathname === path) return;
    window.history.pushState({}, '', path);
    setPathname(path);
  }

  return { pathname, navigate };
}
