from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.models import Company, InternshipPost, JobPosition, PostStatus
from app.schemas import InternshipPostRead


def serialize_post(post: InternshipPost) -> InternshipPostRead:
    data = InternshipPostRead.model_validate(post)
    data.company_name = post.company.company_name if post.company else None
    data.position_name = post.position.name if post.position else None
    data.position_category = post.position.category if post.position else None
    return data


def apply_internship_filters(
    query: Query,
    q: str | None = None,
    company: str | None = None,
    location: str | None = None,
    skill: str | None = None,
    work_type: str | None = None,
    job_type: str | None = None,
    experience_level: str | None = None,
    position_id: int | None = None,
    post_status: PostStatus | None = None,
) -> Query:
    if post_status:
        query = query.filter(InternshipPost.status == post_status)
    if q:
        query = query.outerjoin(JobPosition, InternshipPost.position_id == JobPosition.id)
        like = f"%{q}%"
        query = query.filter(
            or_(
                InternshipPost.title.ilike(like),
                InternshipPost.description.ilike(like),
                InternshipPost.requirements.ilike(like),
                InternshipPost.required_skills.ilike(like),
                JobPosition.name.ilike(like),
            )
        )
    if company:
        query = query.join(Company).filter(Company.company_name.ilike(f"%{company}%"))
    if skill:
        like = f"%{skill}%"
        query = query.filter(or_(InternshipPost.requirements.ilike(like), InternshipPost.required_skills.ilike(like)))
    if location:
        query = query.filter(InternshipPost.location.ilike(f"%{location}%"))
    if work_type:
        query = query.filter(InternshipPost.work_type == work_type)
    if job_type:
        query = query.filter(InternshipPost.job_type == job_type)
    if experience_level:
        query = query.filter(InternshipPost.experience_level == experience_level)
    if position_id:
        query = query.filter(InternshipPost.position_id == position_id)
    return query


def list_internship_posts(
    db: Session,
    q: str | None = None,
    company: str | None = None,
    location: str | None = None,
    skill: str | None = None,
    work_type: str | None = None,
    job_type: str | None = None,
    experience_level: str | None = None,
    position_id: int | None = None,
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
        job_type=job_type,
        experience_level=experience_level,
        position_id=position_id,
        post_status=post_status,
    )
    return query.order_by(InternshipPost.created_at.desc()).offset(offset).limit(limit).all()
