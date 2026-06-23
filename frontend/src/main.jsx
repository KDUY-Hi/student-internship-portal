import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Bell,
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
import heroImage from './assets/hero-internship.png';

function defaultApiUrl() {
  if (typeof window === 'undefined') return 'http://localhost:8000';
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

const API_URL = (import.meta.env.VITE_API_URL || defaultApiUrl()).replace(/\/$/, '');

function friendlyError(error) {
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return `Cannot connect to backend API at ${API_URL}. Run: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`;
  }
  return error.message || 'API request failed';
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
        <PublicNav mode={mode} setMode={setMode} />
        {message && <div className="notice floating">{message}</div>}
        <AuthPanel mode={mode} setMode={setMode} onAuth={saveSession} setMessage={setMessage} />
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <Logo />
        <nav className="nav">
          <span className="active"><Briefcase size={18} /> Dashboard</span>
          <span><FileText size={18} /> Applications</span>
          <span><Bell size={18} /> Notifications</span>
          <span><ShieldCheck size={18} /> Settings</span>
        </nav>
      </aside>
      <section className="workspace">
        <header className="topbar">
          <Logo compact />
          <div className="top-actions">
            <Bell size={18} />
            <span className={`role ${user.role}`}>{user.role}</span>
            <button className="ghost dark" onClick={logout}><LogOut size={18} /> Sign out</button>
          </div>
        </header>
        <div className="page-title">
          <p className="eyebrow">Cloud-based Student Internship Portal</p>
          <h1>Welcome, {user.name}</h1>
        </div>
        {message && <div className="notice">{message}</div>}
        <Dashboard session={session} setMessage={setMessage} />
      </section>
    </main>
  );
}

function Logo({ compact = false }) {
  return (
    <div className={`brand ${compact ? 'compact-brand' : ''}`}>
      <div className="brand-mark"><Briefcase size={20} /></div>
      {!compact && <strong>InternPortal</strong>}
    </div>
  );
}

function PublicNav({ mode, setMode }) {
  return (
    <header className="public-nav">
      <Logo />
      <nav>
        <a className="active">Trang chủ</a>
        <a>Việc làm</a>
        <a>Công ty</a>
        <a>Về chúng tôi</a>
      </nav>
      <div className="nav-actions">
        <button className="outline" onClick={() => setMode('login')}>Đăng nhập</button>
        <button className="primary" onClick={() => setMode('register')}>Đăng ký</button>
      </div>
    </header>
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
      <div className="hero-copy">
        <p className="eyebrow">Nền tảng thực tập sinh viên</p>
        <h1>Tìm kiếm thực tập <span>phù hợp với bạn</span></h1>
        <p className="hero-text">Khám phá cơ hội thực tập từ các công ty, xây dựng hồ sơ và theo dõi trạng thái ứng tuyển trong một cổng duy nhất.</p>
        <div className="hero-search">
          <Search size={18} />
          <span>Tìm kiếm vị trí, kỹ năng, công ty...</span>
          <button>Tìm kiếm</button>
        </div>
        <div className="chips"><span>IT</span><span>Marketing</span><span>Design</span><span>Business</span><span>Data</span></div>
        <img className="hero-image" src={heroImage} alt="Student searching internships on a laptop" />
        <div className="hero-stats">
          <article><Briefcase /><strong>1,200+</strong><span>Vị trí thực tập</span></article>
          <article><Building2 /><strong>350+</strong><span>Công ty đối tác</span></article>
          <article><GraduationCap /><strong>5,000+</strong><span>Sinh viên ứng tuyển</span></article>
        </div>
      </div>
      <form className="auth-card" onSubmit={submit}>
        <Logo />
        <div className="panel-title"><UserPlus size={20} /><h2>{mode === 'login' ? 'Login' : 'Create account'}</h2></div>
        <p className="form-subtitle">{mode === 'login' ? 'Chào mừng bạn quay trở lại!' : 'Tạo tài khoản để bắt đầu quản lý thực tập.'}</p>
        {mode === 'register' && (
          <>
            <label>Name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
            <label>Role<select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option value="student">Student</option><option value="company">Company</option><option value="admin">Admin</option></select></label>
          </>
        )}
        <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></label>
        <label>Password<input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></label>
        <button className="primary" type="submit">{mode === 'login' ? 'Login' : 'Register'}</button>
        <button className="link" type="button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'Need an account?' : 'Already have an account?'}</button>
      </form>
    </section>
  );
}

function Dashboard({ session, setMessage }) {
  if (session.user.role === 'company') return <CompanyView session={session} setMessage={setMessage} />;
  if (session.user.role === 'admin') return <AdminView session={session} setMessage={setMessage} />;
  return <StudentView session={session} setMessage={setMessage} />;
}

function SharedTop({ session, stats, notifications }) {
  return (
    <>
      <section className="stats">
        {Object.entries(stats || {}).filter(([, value]) => value !== null && value !== undefined).map(([key, value]) => (
          <article className="stat" key={key}><strong>{value}</strong><span>{key.replaceAll('_', ' ')}</span></article>
        ))}
      </section>
      <section className="panel">
        <div className="panel-title"><Bell size={20} /><h2>Notifications</h2></div>
        <div className="list compact">
          {(notifications || []).slice(0, 5).map((item) => <article className="item" key={item.id}><div><strong>{item.title}</strong><span>{item.message}</span></div></article>)}
          {notifications?.length === 0 && <p className="empty">No notifications yet for {session.user.email}.</p>}
        </div>
      </section>
    </>
  );
}

function StudentView({ session, setMessage }) {
  const [jobs, setJobs] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [applications, setApplications] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({});
  const [skills, setSkills] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [filters, setFilters] = useState({ q: '', company: '', location: '', skill: '', work_type: '' });
  const [companyFilters, setCompanyFilters] = useState({ q: '', location: '' });
  const [profile, setProfile] = useState({ university: '', major: '', skills: '', gpa: '', experience: '', github: '', linkedin: '' });

  async function load() {
    const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value));
    const companyParams = new URLSearchParams(Object.entries(companyFilters).filter(([, value]) => value));
    setJobs(await api(`/internships${params.toString() ? `?${params}` : ''}`));
    setCompanies(await api(`/companies${companyParams.toString() ? `?${companyParams}` : ''}`));
    setApplications(await api('/applications/me', { token: session.token }));
    setNotifications(await api('/notifications', { token: session.token }));
    setStats(await api('/students/dashboard', { token: session.token }));
    setSkills(await api('/skills'));
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
      <section className="wide"><SharedTop session={session} stats={stats} notifications={notifications} /></section>
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
        <div className="filter-grid">
          {['q', 'company', 'location', 'work_type'].map((field) => <input key={field} placeholder={field} value={filters[field]} onChange={(e) => setFilters({ ...filters, [field]: e.target.value })} />)}
          <select value={filters.skill} onChange={(e) => setFilters({ ...filters, skill: e.target.value })}><option value="">Skill</option>{skills.map((skill) => <option key={skill.id}>{skill.name}</option>)}</select>
          <button className="primary" onClick={load}>Search</button>
        </div>
        <div className="list">
          {jobs.map((job) => (
            <article className="item" key={job.id}>
              <div><strong>{job.title}</strong><span>{job.company_name} - {job.location || 'Flexible'} - {job.work_type || 'N/A'} - deadline {job.deadline || 'N/A'}</span></div>
              <button onClick={() => setSelectedJob(job)}>Detail</button>
              <button onClick={() => apply(job.id)}>Apply</button>
            </article>
          ))}
        </div>
        {selectedJob && <div className="detail"><strong>{selectedJob.title}</strong><p>{selectedJob.description}</p><p>{selectedJob.requirements}</p></div>}
      </section>
      <section className="panel wide">
        <div className="panel-title"><Building2 size={20} /><h2>Search companies</h2></div>
        <div className="filter-grid">
          <input placeholder="Company name, field, keyword" value={companyFilters.q} onChange={(e) => setCompanyFilters({ ...companyFilters, q: e.target.value })} />
          <input placeholder="Location" value={companyFilters.location} onChange={(e) => setCompanyFilters({ ...companyFilters, location: e.target.value })} />
          <button className="primary" onClick={load}>Search companies</button>
        </div>
        <div className="company-grid">
          {companies.map((company) => (
            <article className="company-card" key={company.id}>
              <div className="company-logo">{company.logo_url ? <img src={company.logo_url} alt={company.company_name} /> : <Building2 size={22} />}</div>
              <div>
                <strong>{company.company_name}</strong>
                <p>{company.description || 'No company description yet.'}</p>
                <span>{company.address || 'Flexible location'} - {company.approved_internships} approved internships</span>
                {company.website && <a href={company.website} target="_blank" rel="noreferrer">Visit website</a>}
              </div>
            </article>
          ))}
          {companies.length === 0 && <p className="empty">No companies match the current filters.</p>}
        </div>
      </section>
      <section className="panel wide"><div className="panel-title"><ClipboardList size={20} /><h2>My applications</h2></div><StatusTable rows={applications} /></section>
    </div>
  );
}

function CompanyView({ session, setMessage }) {
  const [profile, setProfile] = useState({ company_name: '', description: '', website: '', address: '', logo_url: '' });
  const [post, setPost] = useState({ title: '', description: '', requirements: '', location: '', work_type: 'remote', allowance: '', duration: '', quantity: 1, deadline: '' });
  const [posts, setPosts] = useState([]);
  const [applications, setApplications] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({});

  async function load() {
    setPosts(await api('/company/internships', { token: session.token }));
    setApplications(await api('/company/applications', { token: session.token }));
    setNotifications(await api('/notifications', { token: session.token }));
    setStats(await api('/company/dashboard', { token: session.token }));
  }

  useEffect(() => { load().catch((error) => setMessage(friendlyError(error))); }, []);

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
      <section className="wide"><SharedTop session={session} stats={stats} notifications={notifications} /></section>
      <section className="panel"><div className="panel-title"><Building2 size={20} /><h2>Company profile</h2></div><form className="form-grid" onSubmit={saveProfile}>{Object.keys(profile).map((field) => <label key={field}>{field}<input value={profile[field]} onChange={(e) => setProfile({ ...profile, [field]: e.target.value })} required={field === 'company_name'} /></label>)}<button className="primary">Save company</button></form></section>
      <section className="panel"><div className="panel-title"><Briefcase size={20} /><h2>Post internship</h2></div><form className="form-grid" onSubmit={createPost}>{Object.keys(post).map((field) => <label key={field}>{field}<input type={field === 'deadline' ? 'date' : 'text'} value={post[field]} onChange={(e) => setPost({ ...post, [field]: e.target.value })} required={['title', 'description'].includes(field)} /></label>)}<button className="primary">Create post</button></form></section>
      <section className="panel wide"><div className="panel-title"><ClipboardList size={20} /><h2>Posts and applicants</h2></div><div className="list">{posts.map((item) => <article className="item" key={item.id}><div><strong>{item.title}</strong><span>{item.location} - {item.status}</span></div></article>)}</div><StatusTable rows={applications} onStatus={updateStatus} /></section>
    </div>
  );
}

function AdminView({ session, setMessage }) {
  const [users, setUsers] = useState([]);
  const [posts, setPosts] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({});
  const [skillName, setSkillName] = useState('');

  async function load() {
    setUsers(await api('/admin/users', { token: session.token }));
    setPosts(await api('/admin/internships', { token: session.token }));
    setNotifications(await api('/notifications', { token: session.token }));
    setStats(await api('/admin/dashboard', { token: session.token }));
  }

  useEffect(() => { load().catch((error) => setMessage(friendlyError(error))); }, []);

  async function setPostStatus(id, status) {
    await api(`/admin/internships/${id}/status`, { method: 'PATCH', token: session.token, body: { status } });
    setMessage(`Post status changed to ${status}`);
    load();
  }

  async function toggleUser(user) {
    await api(`/admin/users/${user.id}/status`, { method: 'PATCH', token: session.token, body: { is_active: !user.is_active } });
    load();
  }

  async function addSkill(event) {
    event.preventDefault();
    await api('/admin/skills', { method: 'POST', token: session.token, body: { name: skillName } });
    setSkillName('');
    setMessage('Skill added');
  }

  return (
    <div className="grid two">
      <section className="wide"><SharedTop session={session} stats={stats} notifications={notifications} /></section>
      <section className="panel">
        <div className="panel-title"><ShieldCheck size={20} /><h2>Internship posts</h2></div>
        <div className="list">{posts.map((post) => <article className="item" key={post.id}><div><strong>{post.title}</strong><span>{post.company_name} - {post.status}</span></div><button onClick={() => setPostStatus(post.id, 'Approved')}>Approve</button><button onClick={() => setPostStatus(post.id, 'Rejected')}>Reject</button><button onClick={() => setPostStatus(post.id, 'Closed')}>Close</button></article>)}</div>
      </section>
      <section className="panel">
        <div className="panel-title"><UserPlus size={20} /><h2>Users and skills</h2></div>
        <form className="search-row" onSubmit={addSkill}><input placeholder="New skill" value={skillName} onChange={(e) => setSkillName(e.target.value)} /><button className="primary">Add</button></form>
        <div className="list">{users.map((user) => <article className="item" key={user.id}><div><strong>{user.name}</strong><span>{user.email} - {user.role} - {user.is_active ? 'active' : 'locked'}</span></div><button onClick={() => toggleUser(user)}>{user.is_active ? 'Lock' : 'Unlock'}</button></article>)}</div>
      </section>
    </div>
  );
}

function StatusTable({ rows, onStatus }) {
  return (
    <div className="table">
      <div className="table-head"><span>Internship</span><span>Student/Company</span><span>Status</span><span>CV</span></div>
      {rows.map((row) => <div className="table-row" key={row.id}><span>{row.internship_title}</span><span>{row.student_name || row.company_name || '-'}</span><span>{onStatus ? <select value={row.status} onChange={(e) => onStatus(row.id, e.target.value)}><option>Pending</option><option>Reviewed</option><option>Interview</option><option>Accepted</option><option>Rejected</option></select> : row.status}</span><span>{row.cv_url ? <a href={row.cv_url} target="_blank" rel="noreferrer">Open</a> : '-'}</span></div>)}
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
