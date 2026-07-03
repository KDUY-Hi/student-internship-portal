import React from 'react';
import { Bell } from 'lucide-react';
import { api } from '../api/client';
import { EmptyState, PanelHeader } from './ui';

export function NotificationsPanel({ notifications = [], token, onChange, setMessage }) {
  async function markRead(id) {
    await api(`/notifications/${id}/read`, { method: 'PATCH', token });
    setMessage?.('Đã đánh dấu thông báo là đã đọc');
    onChange?.();
  }

  return (
    <section className="panel" id="notifications">
      <PanelHeader icon={Bell} title="Hoạt động gần đây" />
      <div className="activity-list">
        {notifications.map((item) => (
          <article className={item.is_read ? 'notification-read' : 'notification-unread'} key={item.id}>
            <span className={item.is_read ? 'dot muted' : 'dot'} />
            <div>
              <strong>{item.title}</strong>
              <p>{item.message}</p>
              {!item.is_read && <button className="soft-button tiny-button" type="button" onClick={() => markRead(item.id)}>Đánh dấu đã đọc</button>}
            </div>
          </article>
        ))}
        {notifications.length === 0 && <EmptyState message="Chưa có thông báo mới." />}
      </div>
    </section>
  );
}
