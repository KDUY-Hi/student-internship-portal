from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.internship_service import list_internship_posts, serialize_post
from app.models import InternshipPost, PostStatus, User
from app.schemas import InternshipPostRead

router = APIRouter(prefix="/internships", tags=["internships"])


@router.get("", response_model=list[InternshipPostRead])
def list_internships(
    q: str | None = None,
    company: str | None = None,
    location: str | None = None,
    skill: str | None = None,
    work_type: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    posts = list_internship_posts(
        db,
        q=q,
        company=company,
        location=location,
        skill=skill,
        work_type=work_type,
        post_status=PostStatus.approved,
        limit=limit,
        offset=offset,
    )
    return [serialize_post(post) for post in posts]


@router.get("/{internship_id}", response_model=InternshipPostRead)
def get_internship(internship_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.get(InternshipPost, internship_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")
    if current_user.role.value == "student" and post.status != PostStatus.approved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")
    return serialize_post(post)
