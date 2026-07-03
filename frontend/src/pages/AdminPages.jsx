import React, { useEffect, useState } from 'react';
import { Briefcase, Building2, ClipboardList, Star, Users } from 'lucide-react';
import { api, friendlyError } from '../api/client';
import { roleLabel } from '../utils/forms';
import { ErrorState, LoadingState, MetricCard, PanelHeader, StatusBadge } from '../components/ui';
import { NotificationsPanel } from '../components/NotificationsPanel';

export function AdminPages({ session, route, setMessage }) {
  const token = session.token;
  const [users, setUsers] = useState([]);
  const [posts, setPosts] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({});
  const [skillName, setSkillName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [loadedUsers, loadedPosts, loadedNotifications, loadedStats] = await Promise.all([
        api('/admin/users', { token }),
        api('/admin/internships', { token }),
        api('/notifications', { token }),
        api('/admin/dashboard', { token }),
      ]);
      setUsers(loadedUsers);
      setPosts(loadedPosts);
      setNotifications(loadedNotifications);
      setStats(loadedStats);
    } catch (loadError) {
      setError(friendlyError(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function setPostStatus(id, status) {
    await api(`/admin/internships/${id}/status`, { method: 'PATCH', token, body: { status } });
    setMessage(`Đã chuyển trạng thái tin sang ${status}`);
    load();
  }

  async function toggleUser(user) {
    await api(`/admin/users/${user.id}/status`, { method: 'PATCH', token, body: { is_active: !user.is_active } });
    load();
  }

  async function addSkill(event) {
    event.preventDefault();
    await api('/admin/skills', { method: 'POST', token, body: { name: skillName } });
    setSkillName('');
    setMessage('Đã thêm kỹ năng');
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const page = route.replace('/admin/', '') || 'home';
  return (
    <div className="dashboard admin-dashboard">
      {page === 'home' && (
        <>
          <section><p className="eyebrow">Admin Panel</p><h1>Tổng quan hệ thống</h1></section>
          <section className="stats-grid">
            <MetricCard icon={Users} label="Ứng viên" value={stats.students} />
            <MetricCard icon={Building2} label="Nhà tuyển dụng" value={stats.companies} tone="purple" />
            <MetricCard icon={Briefcase} label="Tin tuyển dụng" value={stats.internships} tone="blue" />
            <MetricCard icon={ClipboardList} label="Lượt ứng tuyển" value={stats.applications} tone="orange" />
          </section>
        </>
      )}
      {page === 'posts' && <AdminPosts posts={posts} setPostStatus={setPostStatus} />}
      {page === 'users' && <AdminUsers users={users} toggleUser={toggleUser} />}
      {page === 'skills' && <AdminSkills skillName={skillName} setSkillName={setSkillName} addSkill={addSkill} />}
      {page === 'notifications' && <NotificationsPanel notifications={notifications} token={token} onChange={load} setMessage={setMessage} />}
    </div>
  );
}

function AdminPosts({ posts, setPostStatus }) {
  return (
    <section className="panel">
      <PanelHeader icon={ClipboardList} title="Quản lý tin tuyển dụng" />
      <div className="admin-list">
        {posts.map((post) => (
          <article key={post.id}>
            <div><strong>{post.title}</strong><span>{post.company_name}</span></div>
            <StatusBadge status={post.status} />
            <div className="row-actions">
              <button onClick={() => setPostStatus(post.id, 'Approved')}>Duyệt</button>
              <button onClick={() => setPostStatus(post.id, 'Rejected')}>Từ chối</button>
              <button onClick={() => setPostStatus(post.id, 'Closed')}>Đóng</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function AdminUsers({ users, toggleUser }) {
  return (
    <section className="panel">
      <PanelHeader icon={Users} title="Quản lý người dùng" />
      <div className="admin-list compact-admin">
        {users.map((user) => (
          <article key={user.id}>
            <div><strong>{user.name}</strong><span>{user.email} - {roleLabel(user.role)}</span></div>
            <StatusBadge status={user.is_active ? 'Active' : 'Locked'} />
            <button className="soft-button" onClick={() => toggleUser(user)}>{user.is_active ? 'Khóa' : 'Mở khóa'}</button>
          </article>
        ))}
      </div>
    </section>
  );
}

function AdminSkills({ skillName, setSkillName, addSkill }) {
  return (
    <section className="panel">
      <PanelHeader icon={Star} title="Quản lý kỹ năng" />
      <form className="filter-row" onSubmit={addSkill}>
        <input placeholder="Nhập kỹ năng mới" value={skillName} onChange={(e) => setSkillName(e.target.value)} />
        <button className="primary">Thêm kỹ năng</button>
      </form>
    </section>
  );
}
