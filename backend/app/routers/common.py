from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import Application, ApplicationStatus, InternshipPost, Notification, Skill, User, UserRole
from app.schemas import DashboardStats, NotificationRead, SkillRead

router = APIRouter(tags=["common"])


@router.get("/skills", response_model=list[SkillRead])
def list_skills(db: Session = Depends(get_db)):
    return db.query(Skill).order_by(Skill.name.asc()).all()


@router.get("/notifications", response_model=list[NotificationRead])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.patch("/notifications/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notification:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.get("/students/dashboard", response_model=DashboardStats)
def student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student)),
):
    profile = current_user.student_profile
    if not profile:
        return DashboardStats(applications=0, accepted_applications=0, rejected_applications=0)
    applications = db.query(Application).filter(Application.student_id == profile.id)
    return DashboardStats(
        applications=applications.count(),
        accepted_applications=applications.filter(Application.status == ApplicationStatus.accepted).count(),
        rejected_applications=applications.filter(Application.status == ApplicationStatus.rejected).count(),
    )


@router.get("/company/dashboard", response_model=DashboardStats)
def company_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.company)),
):
    company = current_user.company
    if not company:
        return DashboardStats(internships=0, applications=0)
    posts = db.query(InternshipPost).filter(InternshipPost.company_id == company.id)
    applications = db.query(Application).join(InternshipPost).filter(InternshipPost.company_id == company.id)
    return DashboardStats(internships=posts.count(), applications=applications.count())
