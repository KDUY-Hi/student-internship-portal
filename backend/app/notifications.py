from sqlalchemy.orm import Session

from app.models import Notification


def create_notification(db: Session, user_id: int, title: str, message: str) -> Notification:
    notification = Notification(user_id=user_id, title=title, message=message)
    db.add(notification)
    return notification


def list_user_notifications(db: Session, user_id: int, limit: int = 50, offset: int = 0, is_read: bool | None = None):
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if is_read is not None:
        query = query.filter(Notification.is_read.is_(is_read))
    return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()


def mark_user_notification_read(db: Session, user_id: int, notification_id: int) -> Notification | None:
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notification:
        return None
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
