from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.auth import hash_password
from app.database import get_db
from app.models import Application, Company, InternshipPost, PostStatus, Skill, StudentProfile, User, UserRole
from app.notifications import create_notification
from app.routers.internships import serialize_post
from app.schemas import (
    DashboardStats,
    InternshipPostRead,
    InternshipStatusUpdate,
    SkillCreate,
    SkillRead,
    UserCreate,
    UserRead,
    UserStatusUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users(
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))
    return query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()
    if payload.role == UserRole.student:
        db.add(StudentProfile(user_id=user.id))
    elif payload.role == UserRole.company:
        db.add(Company(user_id=user.id, company_name=payload.name))
    db.commit()
    db.refresh(user)
    return user


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
def pending_internships(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    posts = (
        db.query(InternshipPost)
        .filter(InternshipPost.status == PostStatus.pending)
        .order_by(InternshipPost.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [serialize_post(post) for post in posts]


@router.get("/internships", response_model=list[InternshipPostRead])
def all_internships(
    post_status: PostStatus | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    query = db.query(InternshipPost)
    if post_status:
        query = query.filter(InternshipPost.status == post_status)
    posts = query.order_by(InternshipPost.created_at.desc()).offset(offset).limit(limit).all()
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
