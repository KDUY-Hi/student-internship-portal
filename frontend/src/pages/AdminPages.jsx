import React, { useEffect, useState } from 'react';
import { Briefcase, Building2, ClipboardList, MessageCircle, Star, Users } from 'lucide-react';
import { api, friendlyError } from '../api/client';
import { forumPostTypeLabel, roleLabel } from '../utils/forms';
import { ErrorState, LoadingState, MetricCard, PanelHeader, StatusBadge } from '../components/ui';
import { NotificationsPanel } from '../components/NotificationsPanel';

export function AdminPages({ session, route, setMessage }) {
  const token = session.token;
  const [users, setUsers] = useState([]);
  const [posts, setPosts] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({});
  const [skillName, setSkillName] = useState('');
  const [positions, setPositions] = useState([]);
  const [positionForm, setPositionForm] = useState({ name: '', category: '', description: '', suggested_skills: '' });
  const [editingPositionId, setEditingPositionId] = useState(null);
  const [forumCategories, setForumCategories] = useState([]);
  const [forumPosts, setForumPosts] = useState([]);
  const [forumCategoryForm, setForumCategoryForm] = useState({ name: '', description: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [loadedUsers, loadedPosts, loadedNotifications, loadedStats, loadedPositions, loadedForumCategories, loadedForumPosts] = await Promise.all([
        api('/admin/users', { token }),
        api('/admin/internships', { token }),
        api('/notifications', { token }),
        api('/admin/dashboard', { token }),
        api('/admin/job-positions', { token }),
        api('/admin/forum/categories', { token }),
        api('/admin/forum/posts', { token }),
      ]);
      setUsers(loadedUsers);
      setPosts(loadedPosts);
      setNotifications(loadedNotifications);
      setStats(loadedStats);
      setPositions(loadedPositions);
      setForumCategories(loadedForumCategories);
      setForumPosts(loadedForumPosts);
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

  async function savePosition(event) {
    event.preventDefault();
    const path = editingPositionId ? `/admin/job-positions/${editingPositionId}` : '/admin/job-positions';
    const method = editingPositionId ? 'PATCH' : 'POST';
    await api(path, { method, token, body: positionForm });
    setPositionForm({ name: '', category: '', description: '', suggested_skills: '' });
    setEditingPositionId(null);
    setMessage(editingPositionId ? 'Đã cập nhật vị trí' : 'Đã thêm vị trí');
    load();
  }

  function editPosition(position) {
    setEditingPositionId(position.id);
    setPositionForm({
      name: position.name || '',
      category: position.category || '',
      description: position.description || '',
      suggested_skills: position.suggested_skills || '',
    });
  }

  async function togglePosition(position) {
    await api(`/admin/job-positions/${position.id}`, { method: 'PATCH', token, body: { is_active: !position.is_active } });
    load();
  }

  async function deletePosition(position) {
    try {
      await api(`/admin/job-positions/${position.id}`, { method: 'DELETE', token });
      setMessage('Đã xóa vị trí');
      load();
    } catch (deleteError) {
      setMessage(friendlyError(deleteError));
    }
  }

  async function createForumCategory(event) {
    event.preventDefault();
    await api('/admin/forum/categories', { method: 'POST', token, body: forumCategoryForm });
    setForumCategoryForm({ name: '', description: '' });
    setMessage('Đã thêm cộng đồng');
    load();
  }

  async function toggleForumCategory(category) {
    await api(`/admin/forum/categories/${category.id}`, { method: 'PATCH', token, body: { is_active: !category.is_active } });
    load();
  }

  async function setForumPostStatus(post, status) {
    await api(`/admin/forum/posts/${post.id}/status`, { method: 'PATCH', token, body: { status } });
    setMessage(`Đã chuyển bài viết sang ${status}`);
    load();
  }

  async function deleteForumPost(post) {
    await api(`/admin/forum/posts/${post.id}`, { method: 'DELETE', token });
    setMessage('Đã xóa bài viết');
    load();
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const page = route.replace('/admin/', '') || 'home';
  return (
    <div className="dashboard admin-dashboard">
      {page === 'home' && (
        <>
          <section><p className="eyebrow">Bảng quản trị</p><h1>Tổng quan hệ thống</h1></section>
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
      {page === 'job-positions' && <AdminJobPositions positions={positions} form={positionForm} setForm={setPositionForm} editingId={editingPositionId} cancelEdit={() => { setEditingPositionId(null); setPositionForm({ name: '', category: '', description: '', suggested_skills: '' }); }} savePosition={savePosition} editPosition={editPosition} togglePosition={togglePosition} deletePosition={deletePosition} />}
      {page === 'forum' && <AdminForum categories={forumCategories} posts={forumPosts} categoryForm={forumCategoryForm} setCategoryForm={setForumCategoryForm} createCategory={createForumCategory} toggleCategory={toggleForumCategory} setPostStatus={setForumPostStatus} deletePost={deleteForumPost} />}
      {page === 'skills' && <AdminSkills skillName={skillName} setSkillName={setSkillName} addSkill={addSkill} />}
      {page === 'reports' && <AdminReports stats={stats} users={users} posts={posts} forumPosts={forumPosts} />}
      {page === 'notifications' && <NotificationsPanel notifications={notifications} token={token} onChange={load} setMessage={setMessage} />}
    </div>
  );
}

function AdminReports({ stats, users, posts, forumPosts }) {
  const activeUsers = users.filter((user) => user.is_active).length;
  const pendingPosts = posts.filter((post) => post.status === 'Pending').length;
  const approvedPosts = posts.filter((post) => post.status === 'Approved').length;
  return (
    <section className="screen-section">
      <div className="screen-title">
        <h1>Báo cáo hệ thống</h1>
        <p>Tổng hợp nhanh hoạt động tuyển dụng, người dùng và diễn đàn</p>
      </div>
      <section className="stats-grid">
        <MetricCard icon={Users} label="Người dùng" value={stats.users || users.length} />
        <MetricCard icon={Briefcase} label="Tin tuyển dụng" value={stats.internships || posts.length} tone="blue" />
        <MetricCard icon={ClipboardList} label="Đơn ứng tuyển" value={stats.applications || 0} tone="purple" />
        <MetricCard icon={MessageCircle} label="Bài diễn đàn" value={forumPosts.length} tone="orange" />
      </section>
      <section className="report-grid">
        <article className="panel">
          <PanelHeader icon={Users} title="Người dùng" />
          <div className="insight-row"><span>Đang hoạt động</span><strong>{activeUsers}</strong></div>
          <div className="insight-row"><span>Sinh viên</span><strong>{stats.students || 0}</strong></div>
          <div className="insight-row"><span>Doanh nghiệp</span><strong>{stats.companies || 0}</strong></div>
        </article>
        <article className="panel">
          <PanelHeader icon={Briefcase} title="Kiểm duyệt" />
          <div className="insight-row"><span>Đang chờ</span><strong>{pendingPosts}</strong></div>
          <div className="insight-row"><span>Đã duyệt</span><strong>{approvedPosts}</strong></div>
          <div className="insight-row"><span>Bị từ chối</span><strong>{posts.filter((post) => post.status === 'Rejected').length}</strong></div>
        </article>
      </section>
    </section>
  );
}

function AdminJobPositions({ positions, form, setForm, editingId, cancelEdit, savePosition, editPosition, togglePosition, deletePosition }) {
  return (
    <section className="panel">
      <PanelHeader icon={Briefcase} title="Quản lý vị trí tuyển dụng" />
      <form className="form-grid two-cols" onSubmit={savePosition}>
        <label>Tên vị trí<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
        <label>Ngành nghề<input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></label>
        <label>Mô tả<input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
        <label>Kỹ năng gợi ý<input placeholder="React, Node.js, MySQL, Git, AWS" value={form.suggested_skills} onChange={(e) => setForm({ ...form, suggested_skills: e.target.value })} /></label>
        <button className="primary full">{editingId ? 'Lưu thay đổi' : 'Thêm vị trí'}</button>
        {editingId && <button className="soft-button full" type="button" onClick={cancelEdit}>Hủy sửa</button>}
      </form>
      <div className="admin-list compact-admin">
        {positions.map((position) => (
          <article key={position.id}>
            <div>
              <strong>{position.name}</strong>
              <span>{position.category || 'Chưa gán ngành'} - {position.suggested_skills || 'Chưa có kỹ năng gợi ý'}</span>
            </div>
            <StatusBadge status={position.is_active ? 'Active' : 'Locked'} />
            <div className="row-actions">
              <button onClick={() => editPosition(position)}>Sửa</button>
              <button onClick={() => togglePosition(position)}>{position.is_active ? 'Ẩn' : 'Hiện'}</button>
              <button onClick={() => deletePosition(position)}>Xóa</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function AdminForum({ categories, posts, categoryForm, setCategoryForm, createCategory, toggleCategory, setPostStatus, deletePost }) {
  return (
    <>
      <section className="panel">
        <PanelHeader icon={MessageCircle} title="Quản lý cộng đồng chuyên môn" />
        <form className="filter-row" onSubmit={createCategory}>
          <input placeholder="Tên cộng đồng" value={categoryForm.name} onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })} required />
          <input placeholder="Mô tả" value={categoryForm.description} onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })} />
          <button className="primary">Thêm cộng đồng</button>
        </form>
        <div className="admin-list compact-admin">
          {categories.map((category) => (
            <article key={category.id}>
              <div><strong>{category.name}</strong><span>{category.description || '-'}</span></div>
              <StatusBadge status={category.is_active ? 'Active' : 'Locked'} />
              <button className="soft-button" onClick={() => toggleCategory(category)}>{category.is_active ? 'Ẩn' : 'Hiện'}</button>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <PanelHeader icon={ClipboardList} title="Kiểm duyệt bài viết" />
        <div className="admin-list">
          {posts.map((post) => (
            <article key={post.id}>
              <div>
                <strong>{post.title}</strong>
                <span>{post.category_name} - {forumPostTypeLabel(post.post_type)} - {post.author_name}</span>
              </div>
              <StatusBadge status={post.status} />
              <div className="row-actions">
                <button onClick={() => setPostStatus(post, 'Approved')}>Duyệt</button>
                <button onClick={() => setPostStatus(post, 'Hidden')}>Ẩn</button>
                <button onClick={() => setPostStatus(post, 'Rejected')}>Từ chối</button>
                <button onClick={() => deletePost(post)}>Xóa</button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
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
