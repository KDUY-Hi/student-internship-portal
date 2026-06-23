from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.models import Application, InternshipPost, PostStatus, Skill, StudentProfile, User, UserRole
from app.notifications import create_notification
from app.routers.internships import serialize_post
from app.schemas import (
    DashboardStats,
    InternshipPostRead,
    InternshipStatusUpdate,
    SkillCreate,
    SkillRead,
    UserRead,
    UserStatusUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.admin))):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/status", response_model=UserRead)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id and not payload.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot disable own account")
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/internships/pending", response_model=list[InternshipPostRead])
def pending_internships(db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.admin))):
    posts = db.query(InternshipPost).filter(InternshipPost.status == PostStatus.pending).order_by(InternshipPost.created_at.desc()).all()
    return [serialize_post(post) for post in posts]


@router.get("/internships", response_model=list[InternshipPostRead])
def all_internships(db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.admin))):
    posts = db.query(InternshipPost).order_by(InternshipPost.created_at.desc()).all()
    return [serialize_post(post) for post in posts]


@router.patch("/internships/{internship_id}/approve", response_model=InternshipPostRead)
def approve_internship(
    internship_id: int,
    approved: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    post = db.get(InternshipPost, internship_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")
    post.status = PostStatus.approved if approved else PostStatus.rejected
    create_notification(
        db,
        post.company.user_id,
        "Internship reviewed",
        f"Your internship post '{post.title}' was {post.status.value}.",
    )
    db.commit()
    db.refresh(post)
    return serialize_post(post)


@router.patch("/internships/{internship_id}/status", response_model=InternshipPostRead)
def update_internship_status(
    internship_id: int,
    payload: InternshipStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    post = db.get(InternshipPost, internship_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")
    post.status = payload.status
    create_notification(
        db,
        post.company.user_id,
        "Internship status changed",
        f"Your internship post '{post.title}' is now {post.status.value}.",
    )
    db.commit()
    db.refresh(post)
    return serialize_post(post)


@router.delete("/internships/{internship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    post = db.get(InternshipPost, internship_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")
    db.delete(post)
    db.commit()


@router.post("/skills", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skill name is required")
    existing = db.query(Skill).filter(Skill.name == name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill already exists")
    skill = Skill(name=name)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.get("/dashboard", response_model=DashboardStats)
def admin_dashboard(db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.admin))):
    return DashboardStats(
        users=db.query(User).count(),
        students=db.query(User).filter(User.role == UserRole.student).count(),
        companies=db.query(User).filter(User.role == UserRole.company).count(),
        internships=db.query(InternshipPost).count(),
        applications=db.query(Application).count(),
        pending_internships=db.query(InternshipPost).filter(InternshipPost.status == PostStatus.pending).count(),
        approved_internships=db.query(InternshipPost).filter(InternshipPost.status == PostStatus.approved).count(),
    )
