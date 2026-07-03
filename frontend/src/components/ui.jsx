import React from 'react';
import { Bell, Briefcase, Building2, ClipboardList, Search, Star, Users } from 'lucide-react';
import { roleBasePath } from '../hooks/useRoute';
import { roleLabel } from '../utils/forms';

export function Logo({ light = false }) {
  return (
    <div className={`brand ${light ? 'brand-light' : ''}`}>
      <strong>topcv</strong>
      <span />
    </div>
  );
}

export function Sidebar({ role, currentPath, navigate }) {
  const common = [
    [`${roleBasePath(role)}/home`, 'Trang chủ', Briefcase],
    [`${roleBasePath(role)}/notifications`, 'Thông báo', Bell],
  ];
  const student = [
    ['/student/jobs', 'Việc làm phù hợp', Search],
    ['/student/companies', 'Công ty', Building2],
    ['/student/applications', 'Ứng tuyển của tôi', ClipboardList],
  ];
  const company = [
    ['/company/jobs', 'Tin tuyển dụng', Briefcase],
    ['/company/applicants', 'Ứng viên', Users],
    ['/company/profile', 'Hồ sơ công ty', Building2],
  ];
  const admin = [
    ['/admin/users', 'Quản lý người dùng', Users],
    ['/admin/posts', 'Quản lý tin tuyển dụng', ClipboardList],
    ['/admin/skills', 'Quản lý kỹ năng', Star],
  ];
  const items = [...common, ...(role === 'company' ? company : role === 'admin' ? admin : student)];

  return (
    <aside className="sidebar">
      <Logo light={role === 'admin'} />
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
    </aside>
  );
}

export function Topbar({ user, navigate, logout }) {
  return (
    <header className="topbar">
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
            <strong>{user.name}</strong>
            <small>{roleLabel(user.role)}</small>
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
    pending: 'Mới',
    reviewed: 'Đã xem',
    interview: 'Đã phỏng vấn',
    accepted: 'Đã nhận',
    rejected: 'Đã từ chối',
    approved: 'Đang hiển thị',
    closed: 'Đã đóng',
    active: 'Đang hoạt động',
    locked: 'Đã khóa',
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
        <span>Ứng viên/Công ty</span>
        <span>Trạng thái</span>
        <span>Chi tiết</span>
      </div>
      {rows.map((row) => (
        <div className="table-row" key={row.id}>
          <span>{row.internship_title || '-'}</span>
          <span>{row.student_name || row.company_name || '-'}</span>
          <span>
            {onStatus ? (
              <select value={row.status} onChange={(e) => onStatus(row.id, e.target.value)}>
                <option>Pending</option>
                <option>Reviewed</option>
                <option>Interview</option>
                <option>Accepted</option>
                <option>Rejected</option>
              </select>
            ) : (
              <StatusBadge status={row.status} />
            )}
          </span>
          <span>
            {onOpen ? <button className="soft-button" type="button" onClick={() => onOpen(row.id)}>Mở</button> : row.cv_url ? <a href={row.cv_url} target="_blank" rel="noreferrer">Mở CV</a> : '-'}
          </span>
        </div>
      ))}
      {rows.length === 0 && <EmptyState />}
    </div>
  );
}
