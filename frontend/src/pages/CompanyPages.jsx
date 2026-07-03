import React, { useEffect, useState } from 'react';
import { Briefcase, Building2, CheckCircle, ClipboardList, Eye, Users } from 'lucide-react';
import { api, friendlyError } from '../api/client';
import { companyFormFromApi } from '../utils/forms';
import { EmptyState, ErrorState, LoadingState, MetricCard, PanelHeader, StatusBadge, StatusTable } from '../components/ui';
import { NotificationsPanel } from '../components/NotificationsPanel';

export function CompanyPages({ session, route, navigate, setMessage }) {
  const token = session.token;
  const [profile, setProfile] = useState(companyFormFromApi());
  const [post, setPost] = useState({ title: '', description: '', requirements: '', location: '', work_type: 'remote', allowance: '', duration: '', quantity: 1, deadline: '' });
  const [posts, setPosts] = useState([]);
  const [applications, setApplications] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [loadedPosts, loadedApps, loadedNotifications, loadedStats, loadedProfile] = await Promise.all([
        api('/company/internships', { token }),
        api('/company/applications', { token }),
        api('/notifications', { token }),
        api('/company/dashboard', { token }),
        api('/company/profile', { token }),
      ]);
      setPosts(loadedPosts);
      setApplications(loadedApps);
      setNotifications(loadedNotifications);
      setStats(loadedStats);
      setProfile(companyFormFromApi(loadedProfile));
    } catch (loadError) {
      setError(friendlyError(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function saveProfile(event) {
    event.preventDefault();
    try {
      const savedProfile = await api('/company/profile', { method: 'POST', token, body: profile });
      setProfile(companyFormFromApi(savedProfile));
      setMessage('Đã lưu hồ sơ công ty');
    } catch (saveError) {
      setMessage(friendlyError(saveError));
    }
  }

  async function createPost(event) {
    event.preventDefault();
    try {
      await api('/company/internships', { method: 'POST', token, body: { ...post, quantity: Number(post.quantity) } });
      setPost({ title: '', description: '', requirements: '', location: '', work_type: 'remote', allowance: '', duration: '', quantity: 1, deadline: '' });
      setMessage('Tin tuyển dụng đã được gửi chờ duyệt');
      load();
    } catch (createError) {
      setMessage(friendlyError(createError));
    }
  }

  async function updateStatus(id, status) {
    await api(`/company/applications/${id}/status`, { method: 'PATCH', token, body: { status } });
    setMessage('Đã cập nhật trạng thái ứng viên');
    load();
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const page = route.replace('/company/', '') || 'home';
  const [, detailId] = page.match(/^applicants\/(.+)$/) || [];
  if (detailId) {
    const application = applications.find((item) => String(item.id) === detailId);
    return <CompanyApplicationDetail application={application} onBack={() => navigate('/company/applicants')} />;
  }

  return (
    <div className="dashboard">
      {page === 'home' && <CompanyHome profile={profile} stats={stats} posts={posts} applications={applications} navigate={navigate} />}
      {(page === 'home' || page === 'jobs') && <CompanyJobs post={post} setPost={setPost} createPost={createPost} posts={posts} applications={applications} />}
      {page === 'profile' && <CompanyProfile profile={profile} setProfile={setProfile} saveProfile={saveProfile} />}
      {page === 'applicants' && <section className="panel"><PanelHeader icon={Users} title="Danh sách ứng viên" /><StatusTable rows={applications} onStatus={updateStatus} onOpen={(id) => navigate(`/company/applicants/${id}`)} /></section>}
      {page === 'notifications' && <NotificationsPanel notifications={notifications} token={token} onChange={load} setMessage={setMessage} />}
    </div>
  );
}

function CompanyHome({ profile, stats, posts, applications, navigate }) {
  return (
    <>
      <section className="company-hero">
        <div>
          <p className="eyebrow">Trang chủ của công ty</p>
          <h1>Chào mừng {profile.company_name || 'nhà tuyển dụng'}</h1>
          <p>Quản lý tuyển dụng hiệu quả và tìm kiếm ứng viên phù hợp.</p>
        </div>
        <button className="primary" onClick={() => navigate('/company/jobs')}>Đăng tin tuyển dụng</button>
      </section>
      <section className="stats-grid">
        <MetricCard icon={Briefcase} label="Tin đăng tuyển" value={stats.internships || posts.length} />
        <MetricCard icon={Users} label="Ứng viên mới" value={stats.applications || applications.length} tone="blue" />
        <MetricCard icon={Eye} label="Tin chờ duyệt" value={posts.filter((item) => item.status === 'Pending').length} tone="purple" />
        <MetricCard icon={CheckCircle} label="Tin đang hiển thị" value={posts.filter((item) => item.status === 'Approved').length} tone="orange" />
      </section>
    </>
  );
}

function CompanyJobs({ post, setPost, createPost, posts, applications }) {
  return (
    <>
      <section className="panel">
        <PanelHeader icon={Briefcase} title="Đăng tin tuyển dụng" />
        <form className="form-grid two-cols" onSubmit={createPost}>
          {[
            ['title', 'Vị trí tuyển dụng'],
            ['description', 'Mô tả công việc'],
            ['requirements', 'Yêu cầu'],
            ['location', 'Địa điểm'],
            ['work_type', 'Hình thức làm việc'],
            ['allowance', 'Trợ cấp'],
            ['duration', 'Thời lượng'],
            ['quantity', 'Số lượng'],
            ['deadline', 'Hạn nộp'],
          ].map(([field, label]) => (
            <label key={field}>{label}<input type={field === 'deadline' ? 'date' : field === 'quantity' ? 'number' : 'text'} value={post[field]} onChange={(e) => setPost({ ...post, [field]: e.target.value })} required={['title', 'description'].includes(field)} /></label>
          ))}
          <button className="primary full">Tạo tin tuyển dụng</button>
        </form>
      </section>
      <section className="panel">
        <PanelHeader icon={ClipboardList} title="Tin tuyển dụng mới nhất" />
        <div className="table">
          <div className="table-head posts"><span>Vị trí tuyển dụng</span><span>Lượt ứng tuyển</span><span>Trạng thái</span></div>
          {posts.map((item) => (
            <div className="table-row posts" key={item.id}>
              <span>{item.title}</span>
              <span>{applications.filter((application) => application.internship_id === item.id).length}</span>
              <StatusBadge status={item.status} />
            </div>
          ))}
          {posts.length === 0 && <EmptyState />}
        </div>
      </section>
    </>
  );
}

function CompanyProfile({ profile, setProfile, saveProfile }) {
  return (
    <section className="panel">
      <PanelHeader icon={Building2} title="Hồ sơ công ty" />
      <form className="form-grid" onSubmit={saveProfile}>
        {[
          ['company_name', 'Tên công ty'],
          ['description', 'Mô tả'],
          ['website', 'Website'],
          ['address', 'Địa chỉ'],
          ['logo_url', 'Logo URL'],
        ].map(([field, label]) => (
          <label key={field}>{label}<input value={profile[field]} onChange={(e) => setProfile({ ...profile, [field]: e.target.value })} required={field === 'company_name'} /></label>
        ))}
        <button className="primary full">Lưu công ty</button>
      </form>
    </section>
  );
}

function CompanyApplicationDetail({ application, onBack }) {
  if (!application) return <ErrorState message="Không tìm thấy ứng viên." onRetry={onBack} />;
  return (
    <section className="panel detail-page">
      <PanelHeader icon={Users} title={application.student_name || 'Ứng viên'} action={<button className="soft-button" onClick={onBack}>Quay lại</button>} />
      <div className="detail-grid">
        <p><strong>Email:</strong> {application.student_email}</p>
        <p><strong>Vị trí:</strong> {application.internship_title}</p>
        <p><strong>Trạng thái:</strong> <StatusBadge status={application.status} /></p>
        <p><strong>Ngày ứng tuyển:</strong> {new Date(application.applied_at).toLocaleDateString()}</p>
      </div>
      {application.cv_url && <a href={application.cv_url} target="_blank" rel="noreferrer">Mở CV ứng viên</a>}
    </section>
  );
}
