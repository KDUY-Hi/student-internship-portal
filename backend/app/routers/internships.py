from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Company, InternshipPost, PostStatus, User
from app.schemas import InternshipPostRead

router = APIRouter(prefix="/internships", tags=["internships"])


def serialize_post(post: InternshipPost) -> InternshipPostRead:
    data = InternshipPostRead.model_validate(post)
    data.company_name = post.company.company_name if post.company else None
    return data


@router.get("", response_model=list[InternshipPostRead])
def list_internships(
    q: str | None = None,
    company: str | None = None,
    location: str | None = None,
    skill: str | None = None,
    work_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(InternshipPost).filter(InternshipPost.status == PostStatus.approved)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                InternshipPost.title.ilike(like),
                InternshipPost.description.ilike(like),
                InternshipPost.requirements.ilike(like),
            )
        )
    if company:
        query = query.join(Company).filter(Company.company_name.ilike(f"%{company}%"))
    if skill:
        query = query.filter(InternshipPost.requirements.ilike(f"%{skill}%"))
    if location:
        query = query.filter(InternshipPost.location.ilike(f"%{location}%"))
    if work_type:
        query = query.filter(InternshipPost.work_type == work_type)
    return [serialize_post(post) for post in query.order_by(InternshipPost.created_at.desc()).all()]


@router.get("/{internship_id}", response_model=InternshipPostRead)
def get_internship(internship_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.get(InternshipPost, internship_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")
    if current_user.role.value == "student" and post.status != PostStatus.approved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")
    return serialize_post(post)
