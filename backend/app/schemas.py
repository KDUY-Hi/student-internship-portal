from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

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
    gpa: float | None = Field(default=None, ge=0, le=4)
    experience: str | None = None
    github: str | None = None
    linkedin: str | None = None

    @field_validator("github", "linkedin", mode="before")
    @classmethod
    def empty_profile_url_to_none(cls, value):
        if value == "":
            return None
        return value

    @field_validator("github", "linkedin")
    @classmethod
    def validate_profile_url(cls, value):
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return value


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

    @field_validator("website", "logo_url", mode="before")
    @classmethod
    def empty_company_url_to_none(cls, value):
        if value == "":
            return None
        return value

    @field_validator("website", "logo_url")
    @classmethod
    def validate_company_url(cls, value):
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return value


class CompanyRead(CompanyBase):
    id: int
    user_id: int

    model_config = {"from_attributes": True}


class CompanySearchRead(CompanyBase):
    id: int
    approved_internships: int = 0
    total_internships: int = 0

    model_config = {"from_attributes": True}


class InternshipPostCreate(BaseModel):
    title: str
    description: str
    requirements: str | None = None
    location: str | None = None
    work_type: str | None = None
    allowance: str | None = None
    duration: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    deadline: str | None = None

    @field_validator("deadline", mode="before")
    @classmethod
    def empty_deadline_to_none(cls, value):
        if value == "":
            return None
        return value

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, value):
        if not value:
            return value
        try:
            deadline = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("deadline must use YYYY-MM-DD") from exc
        if deadline < date.today():
            raise ValueError("deadline cannot be in the past")
        return value


class InternshipPostRead(BaseModel):
    title: str
    description: str
    requirements: str | None = None
    location: str | None = None
    work_type: str | None = None
    allowance: str | None = None
    duration: str | None = None
    quantity: int | None = None
    deadline: str | None = None
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
