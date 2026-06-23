from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.models import InternshipPost, PostStatus, User, UserRole
from app.routers.internships import serialize_post
from app.schemas import InternshipPostRead, UserRead

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.admin))):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/internships/pending", response_model=list[InternshipPostRead])
def pending_internships(db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.admin))):
    posts = db.query(InternshipPost).filter(InternshipPost.status == PostStatus.pending).order_by(InternshipPost.created_at.desc()).all()
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
