import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Briefcase,
  Building2,
  ClipboardList,
  FileText,
  GraduationCap,
  LogOut,
  Search,
  ShieldCheck,
  Upload,
  UserPlus,
} from 'lucide-react';
import './styles.css';

function defaultApiUrl() {
  if (typeof window === 'undefined') return 'http://localhost:8000';
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

const API_URL = (import.meta.env.VITE_API_URL || defaultApiUrl()).replace(/\/$/, '');

function friendlyError(error) {
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return `Không kết nối được backend API tại ${API_URL}. Hãy chạy backend bằng: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`;
  }
  return error.message || 'Có lỗi xảy ra khi gọi API';
}

async function api(path, { token, method = 'GET', body, isForm = false } = {}) {
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
    throw new Error(data.detail || `API error ${response.status}`);
  }

  if (response.status === 204) return null;
  return response.json();
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'));
  const [mode, setMode] = useState('login');
  const [message, setMessage] = useState('');

  const session = useMemo(() => ({ token, user }), [token, user]);

  function saveSession(data) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  }

  function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken('');
    setUser(null);
    setMessage('');
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><GraduationCap size={24} /></div>
          <div>
            <strong>Internship Portal</strong>
            <span>AWS Cloud MVP</span>
          </div>
        </div>

        <nav className="nav">
          <span><Briefcase size={18} /> Internships</span>
          <span><FileText size={18} /> CV Storage</span>
          <span><ShieldCheck size={18} /> Role Access</span>
          <span><ClipboardList size={18} /> Applications</span>
        </nav>

        {user && (
          <button className="ghost" onClick={logout}>
            <LogOut size={18} /> Sign out
          </button>
        )}
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Cloud-based Student Internship Portal</p>
            <h1>{user ? `Welcome, ${user.name}` : 'Find and manage internships'}</h1>
          </div>
          {user && <span className={`role ${user.role}`}>{user.role}</span>}
        </header>

        {message && <div className="notice">{message}</div>}

        {!user ? (
          <AuthPanel mode={mode} setMode={setMode} onAuth={saveSession} setMessage={setMessage} />
        ) : (
          <Dashboard session={session} setMessage={setMessage} />
        )}
      </section>
    </main>
  );
}

function AuthPanel({ mode, setMode, onAuth, setMessage }) {
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'student' });

  async function submit(event) {
    event.preventDefault();
    try {
      const data = await api(mode === 'login' ? '/auth/login' : '/auth/register', {
        method: 'POST',
        body: mode === 'login' ? { email: form.email, password: form.password } : form,
      });
      onAuth(data);
    } catch (error) {
      setMessage(friendlyError(error));
    }
  }

  return (
    <section className="auth-grid">
      <form className="panel" onSubmit={submit}>
        <div className="panel-title">
          <UserPlus size={20} />
          <h2>{mode === 'login' ? 'Login' : 'Create account'}</h2>
        </div>

        {mode === 'register' && (
          <>
            <label>Name</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            <label>Role</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="student">Student</option>
              <option value="company">Company</option>
              <option value="admin">Admin</option>
            </select>
          </>
        )}

        <label>Email</label>
        <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <label>Password</label>
        <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />

        <button className="primary" type="submit">{mode === 'login' ? 'Login' : 'Register'}</button>
        <button className="link" type="button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login' ? 'Need an account?' : 'Already have an account?'}
        </button>
      </form>

      <div className="cloud-panel">
        <div className="cloud-row"><Building2 /> React on S3</div>
        <div className="cloud-row"><Briefcase /> FastAPI on EC2</div>
        <div className="cloud-row"><FileText /> CV files in S3</div>
        <div className="cloud-row"><ShieldCheck /> RDS + CloudWatch</div>
      </div>
    </section>
  );
}

function Dashboard({ session, setMessage }) {
  if (session.user.role === 'company') return <CompanyView session={session} setMessage={setMessage} />;
  if (session.user.role === 'admin') return <AdminView session={session} setMessage={setMessage} />;
  return <StudentView session={session} setMessage={setMessage} />;
}

function StudentView({ session, setMessage }) {
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [query, setQuery] = useState('');
  const [profile, setProfile] = useState({ university: '', major: '', skills: '', gpa: '', experience: '', github: '', linkedin: '' });

  async function load() {
    setJobs(await api(`/internships${query ? `?q=${encodeURIComponent(query)}` : ''}`));
    setApplications(await api('/applications/me', { token: session.token }));
  }

  useEffect(() => { load().catch((error) => setMessage(friendlyError(error))); }, []);

  async function saveProfile(event) {
    event.preventDefault();
    await api('/students/profile', { method: 'POST', token: session.token, body: { ...profile, gpa: profile.gpa ? Number(profile.gpa) : null } });
    setMessage('Profile saved');
  }

  async function uploadCv(event) {
    const file = event.target.files[0];
    if (!file) return;
    const body = new FormData();
    body.append('file', file);
    await api('/students/upload-cv', { method: 'POST', token: session.token, body, isForm: true });
    setMessage('CV uploaded');
  }

  async function apply(internshipId) {
    await api('/applications', { method: 'POST', token: session.token, body: { internship_id: internshipId } });
    setMessage('Application submitted');
    load();
  }

  return (
    <div className="grid two">
      <section className="panel">
        <div className="panel-title"><GraduationCap size={20} /><h2>Student profile</h2></div>
        <form className="form-grid" onSubmit={saveProfile}>
          {['university', 'major', 'skills', 'gpa', 'experience', 'github', 'linkedin'].map((field) => (
            <label key={field}>{field}<input value={profile[field]} onChange={(e) => setProfile({ ...profile, [field]: e.target.value })} /></label>
          ))}
          <button className="primary">Save profile</button>
        </form>
        <label className="upload"><Upload size={18} /> Upload CV<input type="file" accept=".pdf,.doc,.docx" onChange={uploadCv} /></label>
      </section>

      <section className="panel">
        <div className="panel-title"><Search size={20} /><h2>Find internships</h2></div>
        <div className="search-row">
          <input placeholder="Search title, skills, company" value={query} onChange={(e) => setQuery(e.target.value)} />
          <button className="icon-button" onClick={load} title="Search"><Search size={18} /></button>
        </div>
        <div className="list">
          {jobs.map((job) => (
            <article className="item" key={job.id}>
              <div><strong>{job.title}</strong><span>{job.company_name} - {job.location || 'Flexible'} - {job.work_type || 'N/A'}</span></div>
              <button onClick={() => apply(job.id)}>Apply</button>
            </article>
          ))}
        </div>
      </section>

      <section className="panel wide">
        <div className="panel-title"><ClipboardList size={20} /><h2>My applications</h2></div>
        <StatusTable rows={applications} />
      </section>
    </div>
  );
}

function CompanyView({ session, setMessage }) {
  const [profile, setProfile] = useState({ company_name: '', description: '', website: '', address: '' });
  const [post, setPost] = useState({ title: '', description: '', requirements: '', location: '', work_type: 'remote', allowance: '', duration: '', quantity: 1, deadline: '' });
  const [posts, setPosts] = useState([]);
  const [applications, setApplications] = useState([]);

  async function load() {
    setPosts(await api('/company/internships', { token: session.token }));
    setApplications(await api('/company/applications', { token: session.token }));
  }

  useEffect(() => { load().catch(() => {}); }, []);

  async function saveProfile(event) {
    event.preventDefault();
    await api('/company/profile', { method: 'POST', token: session.token, body: profile });
    setMessage('Company profile saved');
    load();
  }

  async function createPost(event) {
    event.preventDefault();
    await api('/company/internships', { method: 'POST', token: session.token, body: { ...post, quantity: Number(post.quantity) } });
    setMessage('Internship sent for admin approval');
    load();
  }

  async function updateStatus(id, status) {
    await api(`/company/applications/${id}/status`, { method: 'PATCH', token: session.token, body: { status } });
    load();
  }

  return (
    <div className="grid two">
      <section className="panel">
        <div className="panel-title"><Building2 size={20} /><h2>Company profile</h2></div>
        <form className="form-grid" onSubmit={saveProfile}>
          {Object.keys(profile).map((field) => <label key={field}>{field}<input value={profile[field]} onChange={(e) => setProfile({ ...profile, [field]: e.target.value })} required={field === 'company_name'} /></label>)}
          <button className="primary">Save company</button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-title"><Briefcase size={20} /><h2>Post internship</h2></div>
        <form className="form-grid" onSubmit={createPost}>
          {Object.keys(post).map((field) => <label key={field}>{field}<input value={post[field]} onChange={(e) => setPost({ ...post, [field]: e.target.value })} required={['title', 'description'].includes(field)} /></label>)}
          <button className="primary">Create post</button>
        </form>
      </section>

      <section className="panel wide">
        <div className="panel-title"><ClipboardList size={20} /><h2>Posts and applicants</h2></div>
        <div className="list">{posts.map((item) => <article className="item" key={item.id}><div><strong>{item.title}</strong><span>{item.location} - {item.status}</span></div></article>)}</div>
        <StatusTable rows={applications} onStatus={updateStatus} />
      </section>
    </div>
  );
}

function AdminView({ session, setMessage }) {
  const [users, setUsers] = useState([]);
  const [pending, setPending] = useState([]);

  async function load() {
    setUsers(await api('/admin/users', { token: session.token }));
    setPending(await api('/admin/internships/pending', { token: session.token }));
  }

  useEffect(() => { load().catch((error) => setMessage(friendlyError(error))); }, []);

  async function approve(id, approved = true) {
    await api(`/admin/internships/${id}/approve?approved=${approved}`, { method: 'PATCH', token: session.token });
    setMessage(approved ? 'Internship approved' : 'Internship rejected');
    load();
  }

  return (
    <div className="grid two">
      <section className="panel">
        <div className="panel-title"><ShieldCheck size={20} /><h2>Pending posts</h2></div>
        <div className="list">
          {pending.map((post) => (
            <article className="item" key={post.id}>
              <div><strong>{post.title}</strong><span>{post.company_name} - {post.location}</span></div>
              <button onClick={() => approve(post.id, true)}>Approve</button>
              <button className="danger" onClick={() => approve(post.id, false)}>Reject</button>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panel-title"><UserPlus size={20} /><h2>Users</h2></div>
        <div className="list">
          {users.map((user) => <article className="item" key={user.id}><div><strong>{user.name}</strong><span>{user.email} - {user.role}</span></div></article>)}
        </div>
      </section>
    </div>
  );
}

function StatusTable({ rows, onStatus }) {
  return (
    <div className="table">
      <div className="table-head"><span>Internship</span><span>Student</span><span>Status</span><span>CV</span></div>
      {rows.map((row) => (
        <div className="table-row" key={row.id}>
          <span>{row.internship_title}</span>
          <span>{row.student_name || row.company_name || '-'}</span>
          <span>{onStatus ? <select value={row.status} onChange={(e) => onStatus(row.id, e.target.value)}><option>Pending</option><option>Reviewed</option><option>Interview</option><option>Accepted</option><option>Rejected</option></select> : row.status}</span>
          <span>{row.cv_url ? <a href={row.cv_url} target="_blank" rel="noreferrer">Open</a> : '-'}</span>
        </div>
      ))}
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
