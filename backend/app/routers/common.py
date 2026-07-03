from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from sqlalchemy import or_

from app.models import Application, ApplicationStatus, Company, InternshipPost, PostStatus, Skill, User, UserRole
from app.notifications import list_user_notifications, mark_user_notification_read
from app.schemas import CompanySearchRead, DashboardStats, NotificationRead, SkillRead

router = APIRouter(tags=["common"])


@router.get("/skills", response_model=list[SkillRead])
def list_skills(db: Session = Depends(get_db)):
    return db.query(Skill).order_by(Skill.name.asc()).all()


@router.get("/companies", response_model=list[CompanySearchRead])
def search_companies(
    q: str | None = None,
    location: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Company).join(User).filter(User.is_active.is_(True))
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Company.company_name.ilike(like),
                Company.description.ilike(like),
                Company.address.ilike(like),
            )
        )
    if location:
        query = query.filter(Company.address.ilike(f"%{location}%"))

    companies = query.order_by(Company.company_name.asc()).offset(offset).limit(limit).all()
    result = []
    for company in companies:
        result.append(
            CompanySearchRead(
                id=company.id,
                company_name=company.company_name,
                description=company.description,
                website=company.website,
                address=company.address,
                logo_url=company.logo_url,
                approved_internships=sum(1 for post in company.internship_posts if post.status == PostStatus.approved),
                total_internships=len(company.internship_posts),
            )
        )
    return result


@router.get("/notifications", response_model=list[NotificationRead])
def list_notifications(
    is_read: bool | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_user_notifications(db, current_user.id, limit=limit, offset=offset, is_read=is_read)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = mark_user_notification_read(db, current_user.id, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
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
