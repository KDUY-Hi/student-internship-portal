from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import ApplicationStatus, PostStatus, UserRole


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class StudentProfileBase(BaseModel):
    university: str | None = None
    major: str | None = None
    skills: str | None = None
    gpa: float | None = None
    experience: str | None = None
    github: str | None = None
    linkedin: str | None = None


class StudentProfileRead(StudentProfileBase):
    id: int
    user_id: int
    cv_url: str | None = None

    model_config = {"from_attributes": True}


class CompanyBase(BaseModel):
    company_name: str
    description: str | None = None
    website: str | None = None
    address: str | None = None
    logo_url: str | None = None


class CompanyRead(CompanyBase):
    id: int
    user_id: int

    model_config = {"from_attributes": True}


class InternshipPostCreate(BaseModel):
    title: str
    description: str
    requirements: str | None = None
    location: str | None = None
    work_type: str | None = None
    allowance: str | None = None
    duration: str | None = None
    quantity: int | None = None
    deadline: str | None = None


class InternshipPostRead(InternshipPostCreate):
    id: int
    company_id: int
    company_name: str | None = None
    status: PostStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationCreate(BaseModel):
    internship_id: int


class ApplicationRead(BaseModel):
    id: int
    student_id: int
    internship_id: int
    cv_url: str
    status: ApplicationStatus
    applied_at: datetime
    internship_title: str | None = None
    company_name: str | None = None
    student_name: str | None = None
    student_email: str | None = None

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class UserStatusUpdate(BaseModel):
    is_active: bool


class InternshipStatusUpdate(BaseModel):
    status: PostStatus


class SkillCreate(BaseModel):
    name: str


class SkillRead(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class NotificationRead(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    users: int | None = None
    students: int | None = None
    companies: int | None = None
    internships: int | None = None
    applications: int | None = None
    pending_internships: int | None = None
    approved_internships: int | None = None
    accepted_applications: int | None = None
    rejected_applications: int | None = None
