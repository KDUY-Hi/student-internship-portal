from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Application, ApplicationStatus, InternshipPost, PostStatus, StudentProfile, User
from app.notifications import create_notification
from app.schemas import ApplicationRead


def serialize_application(application: Application) -> ApplicationRead:
    data = ApplicationRead.model_validate(application)
    data.internship_title = application.internship.title
    data.company_name = application.internship.company.company_name
    data.student_name = application.student.user.name
    data.student_email = application.student.user.email
    return data


def apply_to_internship(db: Session, current_user: User, profile: StudentProfile, internship_id: int) -> Application:
    if not profile.cv_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a CV before applying")

    internship = db.get(InternshipPost, internship_id)
    if not internship or internship.status != PostStatus.approved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approved internship not found")
    if internship.deadline and date.fromisoformat(internship.deadline) < date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Internship deadline has passed")

    application = Application(student_id=profile.id, internship_id=internship.id, cv_url=profile.cv_url)
    db.add(application)
    create_notification(
        db,
        current_user.id,
        "Application submitted",
        f"Your application for {internship.title} was submitted successfully.",
    )
    create_notification(
        db,
        internship.company.user_id,
        "New application",
        f"{current_user.name} applied to {internship.title}.",
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already applied to this internship") from exc
    db.refresh(application)
    return application


def list_student_applications(db: Session, student_id: int, limit: int = 50, offset: int = 0) -> list[Application]:
    return (
        db.query(Application)
        .filter(Application.student_id == student_id)
        .order_by(Application.applied_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def list_company_applications(
    db: Session,
    company_id: int,
    status_filter: ApplicationStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Application]:
    query = db.query(Application).join(InternshipPost).filter(InternshipPost.company_id == company_id)
    if status_filter:
        query = query.filter(Application.status == status_filter)
    return query.order_by(Application.applied_at.desc()).offset(offset).limit(limit).all()


def update_company_application_status(
    db: Session,
    company_id: int,
    application_id: int,
    status_update: ApplicationStatus,
) -> Application:
    application = db.get(Application, application_id)
    if not application or application.internship.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    application.status = status_update
    create_notification(
        db,
        application.student.user_id,
        "Application status updated",
        f"Your application for {application.internship.title} is now {status_update.value}.",
    )
    db.commit()
    db.refresh(application)
    return application
