from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.models import Application, Company, InternshipPost, User, UserRole
from app.routers.internships import serialize_post
from app.routers.student import serialize_application
from app.schemas import ApplicationRead, ApplicationStatusUpdate, CompanyBase, CompanyRead, InternshipPostCreate, InternshipPostRead

router = APIRouter(prefix="/company", tags=["company"])


def get_or_create_company(db: Session, user: User, payload: CompanyBase | None = None) -> Company:
    company = user.company
    if company:
        return company
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Create a company profile first")
    company = Company(user_id=user.id, **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/profile", response_model=CompanyRead)
@router.patch("/profile", response_model=CompanyRead)
def upsert_company_profile(
    payload: CompanyBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.company)),
):
    company = get_or_create_company(db, current_user, payload)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


@router.post("/internships", response_model=InternshipPostRead, status_code=status.HTTP_201_CREATED)
def create_internship(
    payload: InternshipPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.company)),
):
    company = get_or_create_company(db, current_user)
    post = InternshipPost(company_id=company.id, **payload.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return serialize_post(post)


@router.get("/internships", response_model=list[InternshipPostRead])
def own_internships(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.company)),
):
    company = get_or_create_company(db, current_user)
    posts = db.query(InternshipPost).filter(InternshipPost.company_id == company.id).order_by(InternshipPost.created_at.desc()).all()
    return [serialize_post(post) for post in posts]


@router.get("/applications", response_model=list[ApplicationRead])
def company_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.company)),
):
    company = get_or_create_company(db, current_user)
    applications = (
        db.query(Application)
        .join(InternshipPost)
        .filter(InternshipPost.company_id == company.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return [serialize_application(application) for application in applications]


@router.patch("/applications/{application_id}/status", response_model=ApplicationRead)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.company)),
):
    company = get_or_create_company(db, current_user)
    application = db.get(Application, application_id)
    if not application or application.internship.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    application.status = payload.status
    db.commit()
    db.refresh(application)
    return serialize_application(application)
