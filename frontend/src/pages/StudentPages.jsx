import React, { useEffect, useState } from 'react';
import { Briefcase, Building2, ClipboardList, Clock3, GraduationCap, MapPin, Search, Upload } from 'lucide-react';
import { api, friendlyError } from '../api/client';
import { profileFormFromApi } from '../utils/forms';
import { EmptyState, ErrorState, LoadingState, MetricCard, PanelHeader, StatusBadge, StatusTable } from '../components/ui';
import { NotificationsPanel } from '../components/NotificationsPanel';

export function StudentPages({ session, route, navigate, setMessage }) {
  const token = session.token;
  const [data, setData] = useState({
    jobs: [],
    companies: [],
    applications: [],
    notifications: [],
    stats: {},
    skills: [],
  });
  const [profile, setProfile] = useState(profileFormFromApi());
  const [filters, setFilters] = useState({ q: '', company: '', location: '', skill: '', work_type: '' });
  const [companyFilters, setCompanyFilters] = useState({ q: '', location: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [cvFileName, setCvFileName] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value));
      const companyParams = new URLSearchParams(Object.entries(companyFilters).filter(([, value]) => value));
      const [jobs, companies, applications, notifications, stats, skills, loadedProfile] = await Promise.all([
        api(`/internships${params.toString() ? `?${params}` : ''}`),
        api(`/companies${companyParams.toString() ? `?${companyParams}` : ''}`),
        api('/applications/me', { token }),
        api('/notifications', { token }),
        api('/students/dashboard', { token }),
        api('/skills'),
        api('/students/profile', { token }),
      ]);
      setData({ jobs, companies, applications, notifications, stats, skills });
      setProfile(profileFormFromApi(loadedProfile));
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
    setSavingProfile(true);
    try {
      const savedProfile = await api('/students/profile', {
        method: 'POST',
        token,
        body: { ...profile, cv_url: undefined, gpa: profile.gpa ? Number(profile.gpa) : null },
      });
      setProfile(profileFormFromApi(savedProfile));
      setMessage('Đã lưu hồ sơ ứng viên');
    } catch (saveError) {
      setMessage(friendlyError(saveError));
    } finally {
      setSavingProfile(false);
    }
  }

  async function uploadCv(event) {
    const file = event.target.files[0];
    if (!file) return;
    setUploading(true);
    setCvFileName(file.name);
    try {
      const body = new FormData();
      body.append('file', file);
      const savedProfile = await api('/students/upload-cv', { method: 'POST', token, body, isForm: true });
      setProfile(profileFormFromApi(savedProfile));
      setMessage('Đã tải CV lên hệ thống');
    } catch (uploadError) {
      setMessage(friendlyError(uploadError));
    } finally {
      setUploading(false);
    }
  }

  async function apply(internshipId) {
    try {
      await api('/applications', { method: 'POST', token, body: { internship_id: internshipId } });
      setMessage('Ứng tuyển thành công');
      await load();
      navigate('/student/applications');
    } catch (applyError) {
      const message = friendlyError(applyError);
      if (message.includes('Upload a CV before applying')) {
        setMessage('Vui lòng tải CV lên trước khi ứng tuyển.');
        navigate('/student/profile');
        return;
      }
      if (message.includes('Already applied')) {
        setMessage('Bạn đã ứng tuyển vị trí này rồi.');
        navigate('/student/applications');
        return;
      }
      setMessage(message);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const page = route.replace('/student/', '') || 'home';
  const [, detailType, detailId] = page.match(/^(jobs|companies|applications)\/(.+)$/) || [];

  if (detailType === 'jobs') {
    const job = data.jobs.find((item) => String(item.id) === detailId);
    return <InternshipDetail job={job} onApply={apply} onBack={() => navigate('/student/jobs')} />;
  }
  if (detailType === 'companies') {
    const company = data.companies.find((item) => String(item.id) === detailId);
    return <CompanyDetail company={company} onBack={() => navigate('/student/companies')} />;
  }
  if (detailType === 'applications') {
    const application = data.applications.find((item) => String(item.id) === detailId);
    return <ApplicationDetail application={application} onBack={() => navigate('/student/applications')} />;
  }

  return (
    <div className="dashboard">
      {page === 'home' && <StudentHome data={data} filters={filters} setFilters={setFilters} load={load} navigate={navigate} />}
      {(page === 'home' || page === 'companies') && <CompaniesPage companies={data.companies} companyFilters={companyFilters} setCompanyFilters={setCompanyFilters} load={load} navigate={navigate} />}
      {(page === 'home' || page === 'jobs') && <JobsPage jobs={data.jobs} filters={filters} setFilters={setFilters} skills={data.skills} load={load} navigate={navigate} apply={apply} />}
      {page === 'applications' && <ApplicationsPage applications={data.applications} navigate={navigate} />}
      {page === 'profile' && <ProfilePage session={session} profile={profile} setProfile={setProfile} saveProfile={saveProfile} savingProfile={savingProfile} uploadCv={uploadCv} uploading={uploading} cvFileName={cvFileName} />}
      {page === 'notifications' && <NotificationsPanel notifications={data.notifications} token={token} onChange={load} setMessage={setMessage} />}
    </div>
  );
}

function StudentHome({ data, filters, setFilters, load, navigate }) {
  return (
    <section className="candidate-hero">
      <div>
        <p className="eyebrow">Trang chủ của ứng viên</p>
        <h1>Khám phá cơ hội việc làm phù hợp với bạn</h1>
        <div className="hero-search">
          <Search size={18} />
          <input placeholder="Tìm kiếm việc làm, vị trí, công ty..." value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} />
          <button className="primary" onClick={() => { load(); navigate('/student/jobs'); }}>Tìm kiếm</button>
        </div>
      </div>
      <div className="hero-metrics">
        <MetricCard icon={Briefcase} label="Việc làm phù hợp" value={data.jobs.length} />
        <MetricCard icon={Building2} label="Công ty đang tuyển" value={data.companies.length} tone="blue" />
        <MetricCard icon={ClipboardList} label="Ứng tuyển của bạn" value={data.stats.applications || data.applications.length} tone="purple" />
      </div>
    </section>
  );
}

function CompaniesPage({ companies, companyFilters, setCompanyFilters, load, navigate }) {
  return (
    <section className="panel">
      <PanelHeader icon={Building2} title="Công ty nổi bật" />
      <div className="filter-row">
        <input placeholder="Tên công ty, lĩnh vực..." value={companyFilters.q} onChange={(e) => setCompanyFilters({ ...companyFilters, q: e.target.value })} />
        <input placeholder="Địa điểm" value={companyFilters.location} onChange={(e) => setCompanyFilters({ ...companyFilters, location: e.target.value })} />
        <button className="soft-button" onClick={load}>Lọc công ty</button>
      </div>
      <div className="company-strip">
        {companies.map((company) => (
          <article key={company.id}>
            <div className="logo-box">{company.logo_url ? <img src={company.logo_url} alt={company.company_name} /> : <Building2 size={22} />}</div>
            <strong>{company.company_name}</strong>
            <span>{company.approved_internships} việc làm</span>
            <button className="soft-button" type="button" onClick={() => navigate(`/student/companies/${company.id}`)}>Chi tiết</button>
          </article>
        ))}
        {companies.length === 0 && <EmptyState message="Chưa có công ty phù hợp bộ lọc." />}
      </div>
    </section>
  );
}

function JobsPage({ jobs, filters, setFilters, skills, load, navigate, apply }) {
  return (
    <section className="panel">
      <PanelHeader icon={Briefcase} title="Việc làm gợi ý cho bạn" />
      <div className="filter-row">
        <input placeholder="Công ty" value={filters.company} onChange={(e) => setFilters({ ...filters, company: e.target.value })} />
        <input placeholder="Địa điểm" value={filters.location} onChange={(e) => setFilters({ ...filters, location: e.target.value })} />
        <select value={filters.skill} onChange={(e) => setFilters({ ...filters, skill: e.target.value })}>
          <option value="">Kỹ năng</option>
          {skills.map((skill) => <option key={skill.id}>{skill.name}</option>)}
        </select>
        <button className="soft-button" onClick={load}>Áp dụng</button>
      </div>
      <div className="job-grid">
        {jobs.map((job) => (
          <article className="job-card" key={job.id}>
            <div className="job-top"><div className="logo-box small"><Briefcase size={18} /></div><StatusBadge status={job.status} /></div>
            <h3>{job.title}</h3>
            <p>{job.company_name}</p>
            <div className="job-meta">
              <span><MapPin size={14} /> {job.location || 'Linh hoạt'}</span>
              <span><Clock3 size={14} /> {job.deadline || 'Chưa đặt hạn'}</span>
            </div>
            <div className="card-actions">
              <button className="soft-button" type="button" onClick={() => navigate(`/student/jobs/${job.id}`)}>Chi tiết</button>
              <button className="primary" type="button" onClick={() => apply(job.id)}>Ứng tuyển</button>
            </div>
          </article>
        ))}
        {jobs.length === 0 && <EmptyState message="Chưa có việc làm đã được duyệt." />}
      </div>
    </section>
  );
}

function ApplicationsPage({ applications, navigate }) {
  return (
    <section className="panel">
      <PanelHeader icon={ClipboardList} title="Ứng tuyển của tôi" />
      <StatusTable rows={applications} onOpen={(id) => navigate(`/student/applications/${id}`)} />
    </section>
  );
}

function ProfilePage({ session, profile, setProfile, saveProfile, savingProfile, uploadCv, uploading, cvFileName }) {
  return (
    <section className="panel profile-panel">
      <PanelHeader icon={GraduationCap} title="Thông tin ứng viên" />
      <div className="profile-head">
        <div className="avatar">{session.user.name?.slice(0, 1).toUpperCase()}</div>
        <div>
          <strong>{session.user.name}</strong>
          <span>{session.user.email}</span>
        </div>
      </div>
      <form className="form-grid" onSubmit={saveProfile}>
        {[
          ['university', 'Trường học'],
          ['major', 'Chuyên ngành'],
          ['skills', 'Kỹ năng'],
          ['gpa', 'GPA'],
          ['experience', 'Kinh nghiệm'],
          ['github', 'Github URL'],
          ['linkedin', 'LinkedIn URL'],
        ].map(([field, label]) => (
          <label key={field}>{label}<input value={profile[field]} onChange={(e) => setProfile({ ...profile, [field]: e.target.value })} /></label>
        ))}
        <button className="primary full" disabled={savingProfile}>{savingProfile ? 'Đang lưu...' : 'Cập nhật thông tin'}</button>
      </form>
      <div className="cv-upload-box">
        <label className="upload">
          <Upload size={17} />
          {uploading ? 'Đang tải CV...' : 'Chọn file CV'}
          <input type="file" accept=".pdf,.doc,.docx" onChange={uploadCv} disabled={uploading} />
        </label>
        <div className="cv-meta">
          <span>{cvFileName || 'Chấp nhận PDF, DOC, DOCX tối đa 5MB.'}</span>
          {profile.cv_url ? <a href={profile.cv_url} target="_blank" rel="noreferrer">Xem CV hiện tại</a> : <strong>Chưa có CV</strong>}
        </div>
      </div>
    </section>
  );
}

function InternshipDetail({ job, onApply, onBack }) {
  if (!job) return <ErrorState message="Không tìm thấy việc làm trong dữ liệu hiện tại." onRetry={onBack} />;
  return (
    <section className="panel detail-page">
      <PanelHeader icon={Briefcase} title={job.title} action={<button className="soft-button" onClick={onBack}>Quay lại</button>} />
      <div className="detail-grid">
        <p><strong>Công ty:</strong> {job.company_name}</p>
        <p><strong>Địa điểm:</strong> {job.location || 'Linh hoạt'}</p>
        <p><strong>Hình thức:</strong> {job.work_type || 'Chưa cập nhật'}</p>
        <p><strong>Hạn nộp:</strong> {job.deadline || 'Chưa đặt hạn'}</p>
        <p><strong>Số lượng:</strong> {job.quantity || 'Chưa cập nhật'}</p>
      </div>
      <div className="detail-box"><strong>Mô tả</strong><p>{job.description}</p><strong>Yêu cầu</strong><p>{job.requirements || 'Chưa cập nhật'}</p></div>
      <button className="primary" onClick={() => onApply(job.id)}>Ứng tuyển</button>
    </section>
  );
}

function CompanyDetail({ company, onBack }) {
  if (!company) return <ErrorState message="Không tìm thấy công ty trong dữ liệu hiện tại." onRetry={onBack} />;
  return (
    <section className="panel detail-page">
      <PanelHeader icon={Building2} title={company.company_name} action={<button className="soft-button" onClick={onBack}>Quay lại</button>} />
      <p>{company.description || 'Chưa có mô tả công ty.'}</p>
      <div className="detail-grid">
        <p><strong>Địa chỉ:</strong> {company.address || 'Chưa cập nhật'}</p>
        <p><strong>Việc làm đã duyệt:</strong> {company.approved_internships}</p>
        <p><strong>Tổng bài đăng:</strong> {company.total_internships}</p>
      </div>
      {company.website && <a href={company.website} target="_blank" rel="noreferrer">Website công ty</a>}
    </section>
  );
}

function ApplicationDetail({ application, onBack }) {
  if (!application) return <ErrorState message="Không tìm thấy hồ sơ ứng tuyển." onRetry={onBack} />;
  return (
    <section className="panel detail-page">
      <PanelHeader icon={ClipboardList} title={application.internship_title} action={<button className="soft-button" onClick={onBack}>Quay lại</button>} />
      <div className="detail-grid">
        <p><strong>Công ty:</strong> {application.company_name}</p>
        <p><strong>Trạng thái:</strong> <StatusBadge status={application.status} /></p>
        <p><strong>Ngày ứng tuyển:</strong> {new Date(application.applied_at).toLocaleDateString()}</p>
      </div>
      {application.cv_url && <a href={application.cv_url} target="_blank" rel="noreferrer">Mở CV đã nộp</a>}
    </section>
  );
}
