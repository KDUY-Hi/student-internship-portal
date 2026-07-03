from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.models import Company, InternshipPost, PostStatus
from app.schemas import InternshipPostRead


def serialize_post(post: InternshipPost) -> InternshipPostRead:
    data = InternshipPostRead.model_validate(post)
    data.company_name = post.company.company_name if post.company else None
    return data


def apply_internship_filters(
    query: Query,
    q: str | None = None,
    company: str | None = None,
    location: str | None = None,
    skill: str | None = None,
    work_type: str | None = None,
    post_status: PostStatus | None = None,
) -> Query:
    if post_status:
        query = query.filter(InternshipPost.status == post_status)
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
    return query


def list_internship_posts(
    db: Session,
    q: str | None = None,
    company: str | None = None,
    location: str | None = None,
    skill: str | None = None,
    work_type: str | None = None,
    post_status: PostStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[InternshipPost]:
    query = apply_internship_filters(
        db.query(InternshipPost),
        q=q,
        company=company,
        location=location,
        skill=skill,
        work_type=work_type,
        post_status=post_status,
    )
    return query.order_by(InternshipPost.created_at.desc()).offset(offset).limit(limit).all()
