from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.forum_service import serialize_forum_comment, serialize_forum_post
from app.models import (
    ForumCategory,
    ForumComment,
    ForumLike,
    ForumPost,
    ForumPostStatus,
    ForumPostType,
    ForumSave,
    User,
    UserRole,
)
from app.schemas import ForumCategoryRead, ForumCommentCreate, ForumCommentRead, ForumPostCreate, ForumPostRead

router = APIRouter(prefix="/forum", tags=["forum"])


MODERATED_TYPES = {ForumPostType.academic, ForumPostType.resource}
IT_FORUM_CATEGORY_NAMES = (
    "Frontend",
    "Backend",
    "Tester / QA",
    "DevOps / Cloud",
    "Mobile",
    "Data / AI",
    "Cybersecurity",
)


@router.get("/categories", response_model=list[ForumCategoryRead])
def list_forum_categories(db: Session = Depends(get_db)):
    return (
        db.query(ForumCategory)
        .filter(ForumCategory.is_active.is_(True), ForumCategory.name.in_(IT_FORUM_CATEGORY_NAMES))
        .order_by(ForumCategory.name.asc())
        .all()
    )


@router.get("/posts", response_model=list[ForumPostRead])
def list_forum_posts(
    category_id: int | None = None,
    post_type: ForumPostType | None = None,
    q: str | None = None,
    saved_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student, UserRole.company)),
):
    query = (
        db.query(ForumPost)
        .join(ForumCategory)
        .filter(ForumPost.status == ForumPostStatus.approved, ForumCategory.name.in_(IT_FORUM_CATEGORY_NAMES))
    )
    if category_id:
        query = query.filter(ForumPost.category_id == category_id)
    if post_type:
        query = query.filter(ForumPost.post_type == post_type)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(ForumPost.title.ilike(like), ForumPost.content.ilike(like)))
    if saved_only:
        query = query.join(ForumSave).filter(ForumSave.user_id == current_user.id)
    posts = query.order_by(ForumPost.created_at.desc()).offset(offset).limit(limit).all()
    return [serialize_forum_post(db, post, current_user.id) for post in posts]


@router.post("/posts", response_model=ForumPostRead, status_code=status.HTTP_201_CREATED)
def create_forum_post(
    payload: ForumPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student, UserRole.company)),
):
    category = db.get(ForumCategory, payload.category_id)
    if not category or not category.is_active or category.name not in IT_FORUM_CATEGORY_NAMES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Forum category not found")
    post = ForumPost(
        user_id=current_user.id,
        category_id=payload.category_id,
        title=payload.title,
        content=payload.content,
        post_type=payload.post_type,
        status=ForumPostStatus.pending if payload.post_type in MODERATED_TYPES else ForumPostStatus.approved,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return serialize_forum_post(db, post, current_user.id)


@router.get("/posts/{post_id}", response_model=ForumPostRead)
def get_forum_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student, UserRole.company)),
):
    post = db.get(ForumPost, post_id)
    if not post or (post.status != ForumPostStatus.approved and post.user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum post not found")
    return serialize_forum_post(db, post, current_user.id)


@router.get("/posts/{post_id}/comments", response_model=list[ForumCommentRead])
def list_forum_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student, UserRole.company)),
):
    post = db.get(ForumPost, post_id)
    if not post or (post.status != ForumPostStatus.approved and post.user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum post not found")
    comments = (
        db.query(ForumComment)
        .filter(ForumComment.post_id == post_id)
        .order_by(ForumComment.created_at.asc())
        .all()
    )
    return [serialize_forum_comment(comment) for comment in comments]


@router.post("/posts/{post_id}/comments", response_model=ForumCommentRead, status_code=status.HTTP_201_CREATED)
def create_forum_comment(
    post_id: int,
    payload: ForumCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student, UserRole.company)),
):
    post = db.get(ForumPost, post_id)
    if not post or post.status != ForumPostStatus.approved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum post not found")
    comment = ForumComment(post_id=post_id, user_id=current_user.id, content=payload.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return serialize_forum_comment(comment)


@router.post("/posts/{post_id}/like", response_model=ForumPostRead)
def toggle_forum_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student, UserRole.company)),
):
    post = db.get(ForumPost, post_id)
    if not post or post.status != ForumPostStatus.approved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum post not found")
    like = db.query(ForumLike).filter(ForumLike.post_id == post_id, ForumLike.user_id == current_user.id).first()
    if like:
        db.delete(like)
    else:
        db.add(ForumLike(post_id=post_id, user_id=current_user.id))
    db.commit()
    db.refresh(post)
    return serialize_forum_post(db, post, current_user.id)


@router.post("/posts/{post_id}/save", response_model=ForumPostRead)
def toggle_forum_save(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student, UserRole.company)),
):
    post = db.get(ForumPost, post_id)
    if not post or post.status != ForumPostStatus.approved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum post not found")
    saved = db.query(ForumSave).filter(ForumSave.post_id == post_id, ForumSave.user_id == current_user.id).first()
    if saved:
        db.delete(saved)
    else:
        db.add(ForumSave(post_id=post_id, user_id=current_user.id))
    db.commit()
    db.refresh(post)
    return serialize_forum_post(db, post, current_user.id)
