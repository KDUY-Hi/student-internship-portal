from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.models import Application, InternshipPost, PostStatus, StudentProfile, User, UserRole
from app.schemas import ApplicationCreate, ApplicationRead, StudentProfileBase, StudentProfileRead
from app.services import upload_cv_to_s3

router = APIRouter(tags=["student"])


def get_or_create_profile(db: Session, user: User) -> StudentProfile:
    profile = user.student_profile
    if profile:
        return profile
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def serialize_application(application: Application) -> ApplicationRead:
    data = ApplicationRead.model_validate(application)
    data.internship_title = application.internship.title
    data.company_name = application.internship.company.company_name
    data.student_name = application.student.user.name
    data.student_email = application.student.user.email
    return data


@router.post("/students/profile", response_model=StudentProfileRead)
@router.patch("/students/profile", response_model=StudentProfileRead)
def upsert_profile(
    payload: StudentProfileBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student)),
):
    profile = get_or_create_profile(db, current_user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/students/upload-cv", response_model=StudentProfileRead)
def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student)),
):
    if file.content_type not in {"application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CV must be a PDF or Word document")

    profile = get_or_create_profile(db, current_user)
    profile.cv_url = upload_cv_to_s3(file, current_user.id)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def apply_to_internship(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student)),
):
    profile = get_or_create_profile(db, current_user)
    if not profile.cv_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a CV before applying")

    internship = db.get(InternshipPost, payload.internship_id)
    if not internship or internship.status != PostStatus.approved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approved internship not found")

    application = Application(student_id=profile.id, internship_id=internship.id, cv_url=profile.cv_url)
    db.add(application)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already applied to this internship") from exc
    db.refresh(application)
    return serialize_application(application)


@router.get("/applications/me", response_model=list[ApplicationRead])
def my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student)),
):
    profile = get_or_create_profile(db, current_user)
    applications = (
        db.query(Application)
        .filter(Application.student_id == profile.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return [serialize_application(application) for application in applications]
