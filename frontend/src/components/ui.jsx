import React from 'react';
import { BarChart3, Bell, Briefcase, ClipboardList, FileText, MessageCircle, Search, Shield, Users } from 'lucide-react';
import { roleBasePath } from '../hooks/useRoute';
import { roleLabel } from '../utils/forms';

export function Logo({ light = false }) {
  return (
    <div className={`brand ${light ? 'brand-light' : ''}`}>
      <strong>&lt;Hiring IT /&gt;</strong>
    </div>
  );
}

export function Sidebar({ role, currentPath, navigate }) {
  const student = [
    ['/student/jobs', 'Tìm cơ hội thực tập', Briefcase],
    ['/student/forum', 'Diễn đàn', MessageCircle],
    ['/student/applications', 'Đơn đã nộp', FileText],
  ];
  const company = [
    ['/company/applicants', 'Quản lý ứng viên', Users],
    ['/company/jobs', 'Bài đăng', Briefcase],
    ['/company/forum', 'Diễn đàn', MessageCircle],
    ['/company/stats', 'Thống kê', BarChart3],
  ];
  const admin = [
    ['/admin/posts', 'Kiểm duyệt', Shield],
    ['/admin/users', 'Người dùng', Users],
    ['/admin/forum', 'Diễn đàn', MessageCircle],
    ['/admin/reports', 'Báo cáo', BarChart3],
  ];
  const items = role === 'company' ? company : role === 'admin' ? admin : student;

  return (
    <aside className="sidebar">
      <Logo light />
      <nav className="nav">
        {items.map(([href, label, Icon]) => (
          <a
            className={currentPath === href || currentPath.startsWith(`${href}/`) ? 'active' : ''}
            href={href}
            key={href}
            onClick={(event) => {
              event.preventDefault();
              navigate(href);
            }}
          >
            <Icon size={17} />
            {label}
          </a>
        ))}
      </nav>
      <div className="sidebar-version">&gt;_ v2.4.1 - prod</div>
    </aside>
  );
}

export function Topbar({ user, navigate, logout }) {
  return (
    <header className="topbar">
      <label className="top-search" aria-label="Tìm kiếm">
        <Search size={18} />
        <input placeholder="Tìm kiếm cơ hội thực tập, công ty, kỹ năng..." />
      </label>
      <div className="top-actions">
        <button className="icon-button" type="button" onClick={() => navigate(`/${user.role}/notifications`)} title="Thông báo">
          <Bell size={18} />
        </button>
        <button
          className="account-chip"
          type="button"
          onClick={() => user.role === 'student' && navigate('/student/profile')}
          title={user.role === 'student' ? 'Mở hồ sơ ứng viên' : roleLabel(user.role)}
        >
          <span>{user.name?.slice(0, 1).toUpperCase()}</span>
          <div>
            <strong>{roleLabel(user.role)}</strong>
            <small>{user.name}</small>
          </div>
        </button>
        <button className="icon-button" onClick={logout} title="Đăng xuất">
          <span aria-hidden>↪</span>
        </button>
      </div>
    </header>
  );
}

export function PanelHeader({ icon: Icon, title, action }) {
  return (
    <div className="panel-header">
      <h2>
        <Icon size={19} />
        {title}
      </h2>
      {action}
    </div>
  );
}

export function MetricCard({ icon: Icon, label, value, tone = 'green' }) {
  return (
    <article className={`metric metric-${tone}`}>
      <div>
        <span>{label}</span>
        <strong>{value ?? 0}</strong>
      </div>
      <Icon size={22} />
    </article>
  );
}

export function StatusBadge({ status }) {
  const key = String(status || '').toLowerCase();
  const labelMap = {
    pending: 'Đang chờ',
    reviewed: 'Đã xem',
    interview: 'Phỏng vấn',
    accepted: 'Chấp nhận',
    rejected: 'Từ chối',
    approved: 'Đã duyệt',
    closed: 'Đã đóng',
    active: 'Đang hoạt động',
    locked: 'Đã khóa',
    hidden: 'Đã ẩn',
  };
  return <span className={`status status-${key}`}>{labelMap[key] || status || 'N/A'}</span>;
}

export function LoadingState({ label = 'Đang tải dữ liệu...' }) {
  return <div className="state-box loading-state">{label}</div>;
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state-box error-state">
      <strong>Không tải được dữ liệu</strong>
      <span>{message}</span>
      {onRetry && <button className="soft-button" type="button" onClick={onRetry}>Thử lại</button>}
    </div>
  );
}

export function EmptyState({ message = 'Chưa có dữ liệu.' }) {
  return <p className="empty">{message}</p>;
}

export function StatusTable({ rows, onStatus, onOpen }) {
  return (
    <div className="table">
      <div className="table-head">
        <span>Vị trí</span>
        <span>Ứng viên / Công ty</span>
        <span>Trạng thái</span>
        <span>Chi tiết</span>
      </div>
      {rows.map((row) => (
        <div className="table-row" key={row.id}>
          <span>{row.internship_title || row.title || '-'}</span>
          <span>{row.student_name || row.company_name || '-'}</span>
          <span>
            {onStatus ? (
              <select value={row.status} onChange={(e) => onStatus(row.id, e.target.value)}>
                <option value="Pending">Đang chờ</option>
                <option value="Reviewed">Đã xem</option>
                <option value="Interview">Phỏng vấn</option>
                <option value="Accepted">Chấp nhận</option>
                <option value="Rejected">Từ chối</option>
              </select>
            ) : (
              <StatusBadge status={row.status} />
            )}
          </span>
          <span>
            {onOpen ? <button className="soft-button" type="button" onClick={() => onOpen(row.id)}>Mở</button> : row.cv_url ? <a href={row.cv_url} target="_blank" rel="noreferrer">CV</a> : '-'}
          </span>
        </div>
      ))}
      {rows.length === 0 && <EmptyState />}
    </div>
  );
}
