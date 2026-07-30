import React, { useEffect, useState } from 'react';
import { Bookmark, Briefcase, Building2, CheckCircle, ClipboardList, Eye, Heart, MessageCircle, Share2, Users } from 'lucide-react';
import { api, friendlyError } from '../api/client';
import { companyFormFromApi, forumPostTypeLabel } from '../utils/forms';
import { EmptyState, ErrorState, LoadingState, MetricCard, PanelHeader, StatusBadge, StatusTable } from '../components/ui';
import { NotificationsPanel } from '../components/NotificationsPanel';

export function CompanyPages({ session, route, navigate, setMessage }) {
  const token = session.token;
  const [profile, setProfile] = useState(companyFormFromApi());
  const emptyPost = {
    position_id: '',
    title: '',
    description: '',
    requirements: '',
    required_skills: '',
    experience_level: 'Fresher',
    job_type: 'Internship',
    salary_min: '',
    salary_max: '',
    education_requirement: '',
    location: '',
    work_type: 'remote',
    allowance: '',
    duration: '',
    quantity: 1,
    deadline: '',
  };
  const [post, setPost] = useState(emptyPost);
  const [posts, setPosts] = useState([]);
  const [positions, setPositions] = useState([]);
  const [applications, setApplications] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({});
  const [forumCategories, setForumCategories] = useState([]);
  const [forumPosts, setForumPosts] = useState([]);
  const [forumForm, setForumForm] = useState({ category_id: '', title: '', content: '', post_type: 'Question' });
  const [forumFilters, setForumFilters] = useState({ category_id: '', post_type: '', q: '', saved_only: false });
  const [forumComments, setForumComments] = useState([]);
  const [commentText, setCommentText] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const forumParams = new URLSearchParams(Object.entries(forumFilters).filter(([, value]) => value));
      const [loadedPosts, loadedApps, loadedNotifications, loadedStats, loadedProfile, loadedPositions, loadedForumCategories, loadedForumPosts] = await Promise.all([
        api('/company/internships', { token }),
        api('/company/applications', { token }),
        api('/notifications', { token }),
        api('/company/dashboard', { token }),
        api('/company/profile', { token }),
        api('/job-positions'),
        api('/forum/categories'),
        api(`/forum/posts${forumParams.toString() ? `?${forumParams}` : ''}`, { token }),
      ]);
      setPosts(loadedPosts);
      setApplications(loadedApps);
      setNotifications(loadedNotifications);
      setStats(loadedStats);
      setProfile(companyFormFromApi(loadedProfile));
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
      const body = {
        ...post,
        position_id: post.position_id ? Number(post.position_id) : null,
        quantity: Number(post.quantity),
        salary_min: post.salary_min ? Number(post.salary_min) : null,
        salary_max: post.salary_max ? Number(post.salary_max) : null,
      };
      await api('/company/internships', { method: 'POST', token, body });
      setPost(emptyPost);
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

  async function openApplicationCv(applicationId) {
    try {
      const result = await api(`/company/applications/${applicationId}/cv`, { token });
      if (!result.cv_url) {
        setMessage('Ứng viên chưa có CV.');
        return;
      }
      window.open(result.cv_url, '_blank', 'noopener,noreferrer');
    } catch (cvError) {
      setMessage(friendlyError(cvError));
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
      setForumPosts((current) => current.map((post) => (post.id === updated.id ? updated : post)));
    } catch (forumError) {
      setMessage(friendlyError(forumError));
    }
  }

  function shareForumPost(postId) {
    const url = `${window.location.origin}/company/forum/${postId}`;
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

  const page = route.replace('/company/', '') || 'home';
  const [, detailId] = page.match(/^applicants\/(.+)$/) || [];
  const [, forumDetailId] = page.match(/^forum\/(.+)$/) || [];
  if (detailId) {
    const application = applications.find((item) => String(item.id) === detailId);
    return <CompanyApplicationDetail application={application} onOpenCv={openApplicationCv} onBack={() => navigate('/company/applicants')} />;
  }
  if (forumDetailId) {
    const forumPost = forumPosts.find((item) => String(item.id) === forumDetailId);
    return <CompanyForumPostDetail post={forumPost} comments={forumComments} commentText={commentText} setCommentText={setCommentText} loadComments={loadForumComments} createComment={createForumComment} onBack={() => navigate('/company/forum')} />;
  }

  return (
    <div className="dashboard">
      {page === 'home' && <CompanyHome profile={profile} stats={stats} posts={posts} applications={applications} navigate={navigate} />}
      {(page === 'home' || page === 'jobs') && <CompanyJobs post={post} setPost={setPost} createPost={createPost} posts={posts} applications={applications} positions={positions} />}
      {page === 'profile' && <CompanyProfile profile={profile} setProfile={setProfile} saveProfile={saveProfile} />}
      {page === 'applicants' && <section className="panel"><PanelHeader icon={Users} title="Danh sách ứng viên" /><StatusTable rows={applications} onStatus={updateStatus} onOpen={(id) => navigate(`/company/applicants/${id}`)} /></section>}
      {page === 'forum' && <CompanyForumPage posts={forumPosts} categories={forumCategories} form={forumForm} setForm={setForumForm} filters={forumFilters} setFilters={setForumFilters} load={load} createPost={createForumPost} togglePost={toggleForumPost} sharePost={shareForumPost} navigate={navigate} />}
      {page === 'stats' && <CompanyStats stats={stats} posts={posts} applications={applications} />}
      {page === 'notifications' && <NotificationsPanel notifications={notifications} token={token} onChange={load} setMessage={setMessage} />}
    </div>
  );
}

function CompanyForumPage({ posts, categories, form, setForm, filters, setFilters, load, createPost, togglePost, sharePost, navigate }) {
  return (
    <section className="panel forum-page">
      <PanelHeader icon={MessageCircle} title="Diễn đàn IT" />
      <form className="forum-compose" onSubmit={createPost}>
        <select value={form.category_id} onChange={(event) => setForm({ ...form, category_id: event.target.value })} required>
          <option value="">Chọn chuyên môn IT</option>
          {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select>
        <select value={form.post_type} onChange={(event) => setForm({ ...form, post_type: event.target.value })}>
          <option value="Question">Câu hỏi</option>
          <option value="Academic Post">Bài học thuật</option>
          <option value="Experience Sharing">Chia sẻ kinh nghiệm</option>
          <option value="Resource">Tài liệu</option>
          <option value="Discussion">Thảo luận</option>
        </select>
        <input placeholder="Tiêu đề bài viết hoặc câu hỏi" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required />
        <textarea placeholder="Chia sẻ nội dung, câu hỏi hoặc kinh nghiệm IT..." value={form.content} onChange={(event) => setForm({ ...form, content: event.target.value })} required />
        <button className="primary">Đăng bài</button>
      </form>

      <div className="filter-row">
        <input placeholder="Tìm bài viết..." value={filters.q} onChange={(event) => setFilters({ ...filters, q: event.target.value })} />
        <select value={filters.category_id} onChange={(event) => setFilters({ ...filters, category_id: event.target.value })}>
          <option value="">Tất cả chuyên môn IT</option>
          {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select>
        <select value={filters.post_type} onChange={(event) => setFilters({ ...filters, post_type: event.target.value })}>
          <option value="">Mọi loại bài</option>
          <option value="Question">Câu hỏi</option>
          <option value="Academic Post">Bài học thuật</option>
          <option value="Experience Sharing">Chia sẻ kinh nghiệm</option>
          <option value="Resource">Tài liệu</option>
          <option value="Discussion">Thảo luận</option>
        </select>
        <label className="inline-check"><input type="checkbox" checked={filters.saved_only} onChange={(event) => setFilters({ ...filters, saved_only: event.target.checked })} /> Đã lưu</label>
        <button className="primary" type="button" onClick={load}>Lọc</button>
      </div>

      <div className="forum-list">
        {posts.map((post) => (
          <article className="forum-card" key={post.id}>
            <div>
              <span className="eyebrow">{post.category_name} - {forumPostTypeLabel(post.post_type)}</span>
              <h3>{post.title}</h3>
              <p>{post.content}</p>
              <small>{post.author_name} - {new Date(post.created_at).toLocaleDateString('vi-VN')}</small>
            </div>
            <div className="forum-actions">
              <button className={post.is_liked ? 'active' : ''} type="button" onClick={() => togglePost(post.id, 'like')}><Heart size={16} /> {post.like_count}</button>
              <button type="button" onClick={() => navigate(`/company/forum/${post.id}`)}><MessageCircle size={16} /> {post.comment_count}</button>
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

function CompanyForumPostDetail({ post, comments, commentText, setCommentText, loadComments, createComment, onBack }) {
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
        <input placeholder="Viết bình luận..." value={commentText} onChange={(event) => setCommentText(event.target.value)} required />
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

function CompanyStats({ stats, posts, applications }) {
  const accepted = applications.filter((item) => item.status === 'Accepted').length;
  const rejected = applications.filter((item) => item.status === 'Rejected').length;
  return (
    <section className="screen-section">
      <div className="screen-title">
        <h1>Thống kê tuyển dụng</h1>
        <p>Dữ liệu tổng hợp từ bài đăng và ứng viên của doanh nghiệp</p>
      </div>
      <section className="stats-grid">
        <MetricCard icon={Briefcase} label="Bài đăng" value={stats.internships || posts.length} />
        <MetricCard icon={Users} label="Ứng viên" value={stats.applications || applications.length} tone="blue" />
        <MetricCard icon={CheckCircle} label="Chấp nhận" value={accepted} tone="green" />
        <MetricCard icon={ClipboardList} label="Từ chối" value={rejected} tone="orange" />
      </section>
      <section className="panel">
        <PanelHeader icon={Briefcase} title="Hiệu suất bài đăng" />
        <div className="table">
          <div className="table-head posts"><span>Bài đăng</span><span>Ứng viên</span><span>Trạng thái</span></div>
          {posts.map((post) => (
            <div className="table-row posts" key={post.id}>
              <span>{post.title}</span>
              <span>{applications.filter((item) => item.internship_id === post.id).length}</span>
              <StatusBadge status={post.status} />
            </div>
          ))}
          {posts.length === 0 && <EmptyState />}
        </div>
      </section>
    </section>
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

function CompanyJobs({ post, setPost, createPost, posts, applications, positions }) {
  const selectedPosition = positions.find((item) => String(item.id) === String(post.position_id));
  const suggestedSkills = splitSkills(selectedPosition?.suggested_skills);
  const selectedSkills = splitSkills(post.required_skills);

  function toggleSkill(skill) {
    const exists = selectedSkills.includes(skill);
    const nextSkills = exists ? selectedSkills.filter((item) => item !== skill) : [...selectedSkills, skill];
    setPost({ ...post, required_skills: nextSkills.join(', ') });
  }

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
          <label>
            Vị trí tuyển dụng
            <select value={post.position_id} onChange={(e) => setPost({ ...post, position_id: e.target.value, title: positions.find((item) => String(item.id) === e.target.value)?.name || post.title })}>
              <option value="">Chọn vị trí</option>
              {positions.map((position) => <option key={position.id} value={position.id}>{position.name} - {position.category}</option>)}
            </select>
          </label>
          <label>Kỹ năng yêu cầu<input placeholder="React, Node.js, MySQL, AWS" value={post.required_skills} onChange={(e) => setPost({ ...post, required_skills: e.target.value })} /></label>
          {suggestedSkills.length > 0 && (
            <div className="skill-suggestions">
              <strong>Kỹ năng gợi ý</strong>
              <div>
                {suggestedSkills.map((skill) => (
                  <button className={selectedSkills.includes(skill) ? 'active' : ''} key={skill} type="button" onClick={() => toggleSkill(skill)}>
                    {skill}
                  </button>
                ))}
              </div>
            </div>
          )}
          <label>
            Mức kinh nghiệm
            <select value={post.experience_level} onChange={(e) => setPost({ ...post, experience_level: e.target.value })}>
              <option>Fresher</option>
              <option>Intern</option>
              <option>Junior</option>
              <option>Middle</option>
              <option>Senior</option>
            </select>
          </label>
          <label>
            Loại hình công việc
            <select value={post.job_type} onChange={(e) => setPost({ ...post, job_type: e.target.value })}>
              <option value="Internship">Thực tập</option>
              <option value="Full-time">Toàn thời gian</option>
              <option value="Part-time">Bán thời gian</option>
              <option value="Contract">Hợp đồng</option>
              <option value="Freelance">Làm tự do</option>
            </select>
          </label>
          <label>Lương tối thiểu<input type="number" min="0" value={post.salary_min} onChange={(e) => setPost({ ...post, salary_min: e.target.value })} /></label>
          <label>Lương tối đa<input type="number" min="0" value={post.salary_max} onChange={(e) => setPost({ ...post, salary_max: e.target.value })} /></label>
          <label>Yêu cầu học vấn<input value={post.education_requirement} onChange={(e) => setPost({ ...post, education_requirement: e.target.value })} /></label>
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

function CompanyApplicationDetail({ application, onOpenCv, onBack }) {
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
      {application.cv_url && <button className="soft-button" type="button" onClick={() => onOpenCv(application.id)}>Mở CV ứng viên</button>}
    </section>
  );
}

function splitSkills(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}
