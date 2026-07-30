from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.auth import hash_password
from app.database import get_db
from app.models import (
    Application,
    Company,
    ForumCategory,
    ForumComment,
    ForumLike,
    ForumPost,
    ForumPostStatus,
    ForumSave,
    InternshipPost,
    JobPosition,
    PostStatus,
    Skill,
    StudentProfile,
    User,
    UserRole,
)
from app.notifications import create_notification
from app.routers.internships import serialize_post
from app.schemas import (
    DashboardStats,
    InternshipPostRead,
    InternshipStatusUpdate,
    JobPositionCreate,
    JobPositionRead,
    JobPositionUpdate,
    ForumCategoryCreate,
    ForumCategoryRead,
    ForumCategoryUpdate,
    ForumPostRead,
    ForumPostStatusUpdate,
    SkillCreate,
    SkillRead,
    UserCreate,
    UserRead,
    UserStatusUpdate,
)
from app.forum_service import serialize_forum_post

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


@router.get("/job-positions", response_model=list[JobPositionRead])
def list_admin_job_positions(
    include_inactive: bool = True,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    query = db.query(JobPosition)
    if not include_inactive:
        query = query.filter(JobPosition.is_active.is_(True))
    return query.order_by(JobPosition.category.asc(), JobPosition.name.asc()).offset(offset).limit(limit).all()


@router.post("/job-positions", response_model=JobPositionRead, status_code=status.HTTP_201_CREATED)
def create_job_position(
    payload: JobPositionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    existing = db.query(JobPosition).filter(JobPosition.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job position already exists")
    position = JobPosition(**payload.model_dump())
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


@router.patch("/job-positions/{position_id}", response_model=JobPositionRead)
def update_job_position(
    position_id: int,
    payload: JobPositionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    position = db.get(JobPosition, position_id)
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job position not found")
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates:
        existing = db.query(JobPosition).filter(JobPosition.name == updates["name"], JobPosition.id != position_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job position already exists")
    for key, value in updates.items():
        setattr(position, key, value)
    db.commit()
    db.refresh(position)
    return position


@router.delete("/job-positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    position = db.get(JobPosition, position_id)
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job position not found")
    used = db.query(InternshipPost).filter(InternshipPost.position_id == position_id).first()
    if used:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job position is used by internship posts")
    db.delete(position)
    db.commit()


@router.get("/forum/categories", response_model=list[ForumCategoryRead])
def list_admin_forum_categories(
    include_inactive: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    query = db.query(ForumCategory)
    if not include_inactive:
        query = query.filter(ForumCategory.is_active.is_(True))
    return query.order_by(ForumCategory.name.asc()).all()


@router.post("/forum/categories", response_model=ForumCategoryRead, status_code=status.HTTP_201_CREATED)
def create_forum_category(
    payload: ForumCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    existing = db.query(ForumCategory).filter(ForumCategory.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Forum category already exists")
    category = ForumCategory(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/forum/categories/{category_id}", response_model=ForumCategoryRead)
def update_forum_category(
    category_id: int,
    payload: ForumCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    category = db.get(ForumCategory, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum category not found")
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates:
        existing = db.query(ForumCategory).filter(ForumCategory.name == updates["name"], ForumCategory.id != category_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Forum category already exists")
    for key, value in updates.items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/forum/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forum_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    category = db.get(ForumCategory, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum category not found")
    used = db.query(ForumPost).filter(ForumPost.category_id == category_id).first()
    if used:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Forum category is used by posts")
    db.delete(category)
    db.commit()


@router.get("/forum/posts", response_model=list[ForumPostRead])
def list_admin_forum_posts(
    post_status: ForumPostStatus | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    query = db.query(ForumPost)
    if post_status:
        query = query.filter(ForumPost.status == post_status)
    posts = query.order_by(ForumPost.created_at.desc()).offset(offset).limit(limit).all()
    return [serialize_forum_post(db, post) for post in posts]


@router.patch("/forum/posts/{post_id}/status", response_model=ForumPostRead)
def update_forum_post_status(
    post_id: int,
    payload: ForumPostStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    post = db.get(ForumPost, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum post not found")
    post.status = payload.status
    db.commit()
    db.refresh(post)
    return serialize_forum_post(db, post)


@router.delete("/forum/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forum_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    post = db.get(ForumPost, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum post not found")
    db.query(ForumLike).filter(ForumLike.post_id == post_id).delete()
    db.query(ForumSave).filter(ForumSave.post_id == post_id).delete()
    db.query(ForumComment).filter(ForumComment.post_id == post_id).delete()
    db.delete(post)
    db.commit()


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
