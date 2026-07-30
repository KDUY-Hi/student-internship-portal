import React, { useEffect, useState } from 'react';
import { BarChart3, Bookmark, Briefcase, Building2, ClipboardList, Clock3, GraduationCap, Heart, MapPin, MessageCircle, Search, Share2, Upload } from 'lucide-react';
import { api, friendlyError } from '../api/client';
import { forumPostTypeLabel, profileFormFromApi } from '../utils/forms';
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
    positions: [],
    market: null,
    forumCategories: [],
    forumPosts: [],
  });
  const [forumForm, setForumForm] = useState({ category_id: '', title: '', content: '', post_type: 'Question' });
  const [forumFilters, setForumFilters] = useState({ category_id: '', post_type: '', q: '', saved_only: false });
  const [forumComments, setForumComments] = useState([]);
  const [commentText, setCommentText] = useState('');
  const [selectedPosition, setSelectedPosition] = useState('');
  const [positionSkills, setPositionSkills] = useState([]);
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
      const forumParams = new URLSearchParams(Object.entries(forumFilters).filter(([, value]) => value));
      const [jobs, companies, applications, notifications, stats, skills, loadedProfile, positions, market, forumCategories, forumPosts] = await Promise.all([
        api(`/internships${params.toString() ? `?${params}` : ''}`),
        api(`/companies${companyParams.toString() ? `?${companyParams}` : ''}`),
        api('/applications/me', { token }),
        api('/notifications', { token }),
        api('/students/dashboard', { token }),
        api('/skills'),
        api('/students/profile', { token }),
        api('/job-positions'),
        api('/analytics/job-market-summary'),
        api('/forum/categories'),
        api(`/forum/posts${forumParams.toString() ? `?${forumParams}` : ''}`, { token }),
      ]);
      setData({ jobs, companies, applications, notifications, stats, skills, positions, market, forumCategories, forumPosts });
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

  async function openOwnCv() {
    try {
      const result = await api('/students/cv', { token });
      if (!result.cv_url) {
        setMessage('Bạn chưa có CV.');
        return;
      }
      window.open(result.cv_url, '_blank', 'noopener,noreferrer');
    } catch (cvError) {
      setMessage(friendlyError(cvError));
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

  async function loadPositionSkills(positionId) {
    setSelectedPosition(positionId);
    if (!positionId) {
      setPositionSkills([]);
      return;
    }
    try {
      const result = await api(`/analytics/skill-by-position/${positionId}`);
      setPositionSkills(result.skills || []);
    } catch (skillsError) {
      setMessage(friendlyError(skillsError));
    }
  }

  async function createForumPost(event) {
    event.preventDefault();
    try {
      const created = await api('/forum/posts', {
        method: 'POST',
        token,
        body: { ...forumForm, category_id: Number(forumForm.category_id) },
      });
      setForumForm({ category_id: '', title: '', content: '', post_type: 'Question' });
      setMessage(created.status === 'Pending' ? 'Bài viết đã gửi, đang chờ admin duyệt.' : 'Đã đăng bài viết cộng đồng.');
      load();
    } catch (forumError) {
      setMessage(friendlyError(forumError));
    }
  }

  async function toggleForumPost(postId, action) {
    try {
      const updated = await api(`/forum/posts/${postId}/${action}`, { method: 'POST', token });
      setData((current) => ({
        ...current,
        forumPosts: current.forumPosts.map((post) => (post.id === updated.id ? updated : post)),
      }));
    } catch (forumError) {
      setMessage(friendlyError(forumError));
    }
  }

  function shareForumPost(postId) {
    const url = `${window.location.origin}/student/forum/${postId}`;
    navigator.clipboard?.writeText(url);
    setMessage('Đã sao chép liên kết bài viết.');
  }

  async function loadForumComments(postId) {
    try {
      const comments = await api(`/forum/posts/${postId}/comments`, { token });
      setForumComments(comments);
    } catch (forumError) {
      setMessage(friendlyError(forumError));
    }
  }

  async function createForumComment(postId, event) {
    event.preventDefault();
    try {
      await api(`/forum/posts/${postId}/comments`, { method: 'POST', token, body: { content: commentText } });
      setCommentText('');
      await loadForumComments(postId);
      await load();
    } catch (forumError) {
      setMessage(friendlyError(forumError));
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const page = route.replace('/student/', '') || 'jobs';
  const [, detailType, detailId] = page.match(/^(jobs|companies|applications|forum)\/(.+)$/) || [];

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
    return <ApplicationDetail application={application} onOpenCv={openOwnCv} onBack={() => navigate('/student/applications')} />;
  }
  if (detailType === 'forum') {
    const post = data.forumPosts.find((item) => String(item.id) === detailId);
    return <ForumPostDetail post={post} comments={forumComments} commentText={commentText} setCommentText={setCommentText} loadComments={loadForumComments} createComment={createForumComment} onBack={() => navigate('/student/forum')} />;
  }

  return (
    <div className="dashboard">
      {page === 'home' && <StudentHome data={data} filters={filters} setFilters={setFilters} load={load} navigate={navigate} />}
      {(page === 'home' || page === 'companies') && <CompaniesPage companies={data.companies} companyFilters={companyFilters} setCompanyFilters={setCompanyFilters} load={load} navigate={navigate} />}
      {(page === 'home' || page === 'jobs') && <JobsPage jobs={data.jobs} filters={filters} setFilters={setFilters} skills={data.skills} load={load} navigate={navigate} apply={apply} />}
      {page === 'insights' && <InsightsPage market={data.market} positions={data.positions} selectedPosition={selectedPosition} positionSkills={positionSkills} onSelectPosition={loadPositionSkills} />}
      {page === 'forum' && <ForumPage posts={data.forumPosts} categories={data.forumCategories} form={forumForm} setForm={setForumForm} filters={forumFilters} setFilters={setForumFilters} load={load} createPost={createForumPost} togglePost={toggleForumPost} sharePost={shareForumPost} navigate={navigate} />}
      {page === 'applications' && <ApplicationsPage applications={data.applications} navigate={navigate} />}
      {page === 'profile' && <ProfilePage session={session} profile={profile} setProfile={setProfile} saveProfile={saveProfile} savingProfile={savingProfile} uploadCv={uploadCv} uploading={uploading} cvFileName={cvFileName} onOpenCv={openOwnCv} />}
      {page === 'notifications' && <NotificationsPanel notifications={data.notifications} token={token} onChange={load} setMessage={setMessage} />}
    </div>
  );
}

function StudentHome({ data, filters, setFilters, load, navigate }) {
  return (
    <section className="candidate-hero">
      <div>
        <p className="eyebrow">Trang chủ của ứng viên</p>
        <h1>Khám phá cơ hội thực tập phù hợp với bạn</h1>
        <div className="hero-search">
          <Search size={18} />
          <input placeholder="Tìm kiếm cơ hội thực tập, vị trí, công ty..." value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} />
          <button className="primary" onClick={() => { load(); navigate('/student/jobs'); }}>Tìm kiếm</button>
        </div>
      </div>
      <div className="hero-metrics">
        <MetricCard icon={Briefcase} label="Cơ hội thực tập phù hợp" value={data.jobs.length} />
        <MetricCard icon={Building2} label="Công ty đang tuyển" value={data.companies.length} tone="blue" />
        <MetricCard icon={ClipboardList} label="Ứng tuyển của bạn" value={data.stats.applications || data.applications.length} tone="purple" />
      </div>
    </section>
  );
}

function ForumPage({ posts, categories, form, setForm, filters, setFilters, load, createPost, togglePost, sharePost, navigate }) {
  return (
    <section className="panel forum-page">
      <PanelHeader icon={MessageCircle} title="Cộng đồng chuyên môn" />
      <form className="forum-compose" onSubmit={createPost}>
        <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} required>
          <option value="">Chọn cộng đồng</option>
          {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select>
        <select value={form.post_type} onChange={(e) => setForm({ ...form, post_type: e.target.value })}>
          <option value="Question">Câu hỏi</option>
          <option value="Academic Post">Bài học thuật</option>
          <option value="Experience Sharing">Chia sẻ kinh nghiệm</option>
          <option value="Resource">Tài liệu</option>
          <option value="Discussion">Thảo luận</option>
        </select>
        <input placeholder="Tiêu đề bài viết hoặc câu hỏi" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <textarea placeholder="Chia sẻ nội dung, câu hỏi hoặc tài liệu học tập..." value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} required />
        <button className="primary">Đăng bài</button>
      </form>

      <div className="filter-row">
        <input placeholder="Tìm bài viết..." value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} />
        <select value={filters.category_id} onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}>
          <option value="">Tất cả cộng đồng</option>
          {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select>
        <select value={filters.post_type} onChange={(e) => setFilters({ ...filters, post_type: e.target.value })}>
          <option value="">Mọi loại bài</option>
          <option value="Question">Câu hỏi</option>
          <option value="Academic Post">Bài học thuật</option>
          <option value="Experience Sharing">Chia sẻ kinh nghiệm</option>
          <option value="Resource">Tài liệu</option>
          <option value="Discussion">Thảo luận</option>
        </select>
        <label className="inline-check"><input type="checkbox" checked={filters.saved_only} onChange={(e) => setFilters({ ...filters, saved_only: e.target.checked })} /> Đã lưu</label>
        <button className="primary" type="button" onClick={load}>Lọc</button>
      </div>

      <div className="forum-list">
        {posts.map((post) => (
          <article className="forum-card" key={post.id}>
            <div>
              <span className="eyebrow">{post.category_name} - {forumPostTypeLabel(post.post_type)}</span>
              <h3>{post.title}</h3>
              <p>{post.content}</p>
              <small>{post.author_name} - {new Date(post.created_at).toLocaleDateString()}</small>
            </div>
            <div className="forum-actions">
              <button className={post.is_liked ? 'active' : ''} type="button" onClick={() => togglePost(post.id, 'like')}><Heart size={16} /> {post.like_count}</button>
              <button type="button" onClick={() => navigate(`/student/forum/${post.id}`)}><MessageCircle size={16} /> {post.comment_count}</button>
              <button className={post.is_saved ? 'active' : ''} type="button" onClick={() => togglePost(post.id, 'save')}><Bookmark size={16} /> {post.save_count}</button>
              <button type="button" onClick={() => sharePost(post.id)}><Share2 size={16} /> Chia sẻ</button>
            </div>
          </article>
        ))}
        {posts.length === 0 && <EmptyState message="Chưa có bài viết phù hợp." />}
      </div>
    </section>
  );
}

function ForumPostDetail({ post, comments, commentText, setCommentText, loadComments, createComment, onBack }) {
  useEffect(() => {
    if (post) loadComments(post.id);
  }, [post?.id]);

  if (!post) return <ErrorState message="Không tìm thấy bài viết." onRetry={onBack} />;
  return (
    <section className="panel detail-page forum-detail">
      <PanelHeader icon={MessageCircle} title={post.title} action={<button className="soft-button" onClick={onBack}>Quay lại</button>} />
      <p className="eyebrow">{post.category_name} - {forumPostTypeLabel(post.post_type)}</p>
      <p>{post.content}</p>
      <form className="comment-form" onSubmit={(event) => createComment(post.id, event)}>
        <input placeholder="Viết bình luận..." value={commentText} onChange={(e) => setCommentText(e.target.value)} required />
        <button className="primary">Gửi</button>
      </form>
      <div className="comment-list">
        {comments.map((comment) => (
          <article key={comment.id}>
            <strong>{comment.author_name}</strong>
            <span>{comment.content}</span>
          </article>
        ))}
        {comments.length === 0 && <EmptyState message="Chưa có bình luận." />}
      </div>
    </section>
  );
}

function InsightsPage({ market, positions, selectedPosition, positionSkills, onSelectPosition }) {
  if (!market) return <EmptyState message="Chưa có dữ liệu thị trường tuyển dụng." />;
  return (
    <section className="panel insights-page">
      <PanelHeader icon={BarChart3} title="Xu hướng thị trường tuyển dụng" />
      <section className="stats-grid">
        <MetricCard icon={Briefcase} label="Tin đang phân tích" value={market.total_posts} />
        <MetricCard icon={GraduationCap} label="Kỹ năng nổi bật" value={market.top_skills?.[0]?.label || '-'} tone="blue" />
        <MetricCard icon={MapPin} label="Địa điểm nổi bật" value={market.top_locations?.[0]?.label || '-'} tone="purple" />
      </section>

      <div className="insights-grid">
        <InsightList title="Kỹ năng được yêu cầu nhiều" items={market.top_skills} />
        <InsightList title="Vị trí đang tuyển nhiều" items={market.top_positions} />
        <InsightList title="Yêu cầu kinh nghiệm" items={market.top_experience_levels} />
        <InsightList title="Xu hướng địa điểm" items={market.top_locations} />
      </div>

      <div className="insight-card">
        <h3>Kỹ năng theo vị trí tuyển dụng</h3>
        <select value={selectedPosition} onChange={(e) => onSelectPosition(e.target.value)}>
          <option value="">Chọn vị trí để xem kỹ năng</option>
          {positions.map((position) => <option key={position.id} value={position.id}>{position.name} - {position.category}</option>)}
        </select>
        <InsightList title="Kỹ năng yêu cầu" items={positionSkills} compact />
      </div>

      <div className="insight-card">
        <h3>Xu hướng lương</h3>
        <div className="salary-summary">
          <span>Tối thiểu: <strong>{formatSalary(market.salary?.minimum)}</strong></span>
          <span>Tối đa: <strong>{formatSalary(market.salary?.maximum)}</strong></span>
          <span>Trung bình tối thiểu: <strong>{formatSalary(market.salary?.average_min)}</strong></span>
          <span>Trung bình tối đa: <strong>{formatSalary(market.salary?.average_max)}</strong></span>
        </div>
        <InsightList title="Khoảng lương phổ biến" items={market.salary?.popular_ranges || []} compact />
      </div>
    </section>
  );
}

function InsightList({ title, items = [], compact = false }) {
  return (
    <div className={`insight-card ${compact ? 'compact' : ''}`}>
      <h3>{title}</h3>
      {items.map((item) => (
        <div className="insight-row" key={item.label}>
          <span>{item.label}</span>
          <strong>{item.percentage != null ? `${item.percentage}%` : item.count}</strong>
        </div>
      ))}
      {items.length === 0 && <EmptyState message="Chưa đủ dữ liệu." />}
    </div>
  );
}

function formatSalary(value) {
  if (value == null) return '-';
  return `${Number(value).toLocaleString('vi-VN')} VND`;
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
            <span>{company.approved_internships} vị trí thực tập</span>
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
      <PanelHeader icon={Briefcase} title="Cơ hội thực tập gợi ý cho bạn" />
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
        {jobs.length === 0 && <EmptyState message="Chưa có cơ hội thực tập nào đã được duyệt." />}
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

function ProfilePage({ session, profile, setProfile, saveProfile, savingProfile, uploadCv, uploading, cvFileName, onOpenCv }) {
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
          {profile.cv_url ? <button className="soft-button" type="button" onClick={onOpenCv}>Xem CV hiện tại</button> : <strong>Chưa có CV</strong>}
        </div>
      </div>
    </section>
  );
}

function InternshipDetail({ job, onApply, onBack }) {
  if (!job) return <ErrorState message="Không tìm thấy cơ hội thực tập trong dữ liệu hiện tại." onRetry={onBack} />;
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
        <p><strong>Vị trí thực tập đã duyệt:</strong> {company.approved_internships}</p>
        <p><strong>Tổng bài đăng:</strong> {company.total_internships}</p>
      </div>
      {company.website && <a href={company.website} target="_blank" rel="noreferrer">Website công ty</a>}
    </section>
  );
}

function ApplicationDetail({ application, onOpenCv, onBack }) {
  if (!application) return <ErrorState message="Không tìm thấy hồ sơ ứng tuyển." onRetry={onBack} />;
  return (
    <section className="panel detail-page">
      <PanelHeader icon={ClipboardList} title={application.internship_title} action={<button className="soft-button" onClick={onBack}>Quay lại</button>} />
      <div className="detail-grid">
        <p><strong>Công ty:</strong> {application.company_name}</p>
        <p><strong>Trạng thái:</strong> <StatusBadge status={application.status} /></p>
        <p><strong>Ngày ứng tuyển:</strong> {new Date(application.applied_at).toLocaleDateString()}</p>
      </div>
      {application.cv_url && <button className="soft-button" type="button" onClick={onOpenCv}>Mở CV đã nộp</button>}
    </section>
  );
}
