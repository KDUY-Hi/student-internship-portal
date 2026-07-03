from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.application_service import apply_to_internship as apply_to_internship_service
from app.application_service import list_student_applications, serialize_application
from app.database import get_db
from app.models import StudentProfile, User, UserRole
from app.schemas import ApplicationCreate, ApplicationRead, StudentProfileBase, StudentProfileRead
from app.services import upload_cv_to_s3, validate_cv_file

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


@router.get("/students/profile", response_model=StudentProfileRead)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student)),
):
    return get_or_create_profile(db, current_user)


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
    validate_cv_file(file)
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
    application = apply_to_internship_service(db, current_user, profile, payload.internship_id)
    return serialize_application(application)


@router.get("/applications/me", response_model=list[ApplicationRead])
def my_applications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.student)),
):
    profile = get_or_create_profile(db, current_user)
    applications = list_student_applications(db, profile.id, limit=limit, offset=offset)
    return [serialize_application(application) for application in applications]
