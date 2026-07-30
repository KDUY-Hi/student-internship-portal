from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import ApplicationStatus, ForumPostStatus, ForumPostType, PostStatus, UserRole


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


class JobPositionBase(BaseModel):
    name: str
    category: str | None = None
    description: str | None = None
    suggested_skills: str | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_position_name(cls, value):
        if not value.strip():
            raise ValueError("Job position name is required")
        return value.strip()

    @field_validator("category", "description", "suggested_skills", mode="before")
    @classmethod
    def empty_position_fields_to_none(cls, value):
        if value == "":
            return None
        return value


class JobPositionCreate(JobPositionBase):
    pass


class JobPositionUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    suggested_skills: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_optional_position_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Job position name is required")
        return value.strip() if value is not None else value

    @field_validator("category", "description", "suggested_skills", mode="before")
    @classmethod
    def empty_update_position_fields_to_none(cls, value):
        if value == "":
            return None
        return value


class JobPositionRead(JobPositionBase):
    id: int

    model_config = {"from_attributes": True}


class InternshipPostCreate(BaseModel):
    position_id: int
    title: str
    description: str
    requirements: str | None = None
    required_skills: str | None = None
    experience_level: str | None = None
    job_type: str | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    education_requirement: str | None = None
    location: str | None = None
    work_type: str | None = None
    allowance: str | None = None
    duration: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    deadline: str | None = None

    @field_validator("required_skills", "experience_level", "job_type", "education_requirement", mode="before")
    @classmethod
    def empty_market_fields_to_none(cls, value):
        if value == "":
            return None
        return value

    @field_validator("salary_max")
    @classmethod
    def validate_salary_range(cls, value, info):
        salary_min = info.data.get("salary_min")
        if value is not None and salary_min is not None and value < salary_min:
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return value

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
    position_id: int | None = None
    position_name: str | None = None
    position_category: str | None = None
    title: str
    description: str
    requirements: str | None = None
    required_skills: str | None = None
    experience_level: str | None = None
    job_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    education_requirement: str | None = None
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


class AnalyticsItem(BaseModel):
    label: str
    count: int
    percentage: float | None = None


class SalarySummary(BaseModel):
    minimum: int | None = None
    maximum: int | None = None
    average_min: float | None = None
    average_max: float | None = None
    popular_ranges: list[AnalyticsItem] = Field(default_factory=list)


class JobMarketSummary(BaseModel):
    total_posts: int
    top_skills: list[AnalyticsItem]
    top_positions: list[AnalyticsItem]
    top_experience_levels: list[AnalyticsItem]
    top_locations: list[AnalyticsItem]
    salary: SalarySummary


class ForumCategoryCreate(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_category_name(cls, value):
        if not value.strip():
            raise ValueError("Forum category name is required")
        return value.strip()

    @field_validator("description", mode="before")
    @classmethod
    def empty_category_description_to_none(cls, value):
        if value == "":
            return None
        return value


class ForumCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_optional_category_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Forum category name is required")
        return value.strip() if value is not None else value


class ForumCategoryRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class ForumPostCreate(BaseModel):
    category_id: int
    title: str
    content: str
    post_type: ForumPostType

    @field_validator("title", "content")
    @classmethod
    def validate_forum_text(cls, value):
        if not value.strip():
            raise ValueError("This field is required")
        return value.strip()


class ForumPostStatusUpdate(BaseModel):
    status: ForumPostStatus


class ForumCommentCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_comment_content(cls, value):
        if not value.strip():
            raise ValueError("Comment content is required")
        return value.strip()


class ForumCommentRead(BaseModel):
    id: int
    post_id: int
    user_id: int
    author_name: str | None = None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ForumPostRead(BaseModel):
    id: int
    user_id: int
    author_name: str | None = None
    category_id: int
    category_name: str | None = None
    title: str
    content: str
    post_type: ForumPostType
    status: ForumPostStatus
    created_at: datetime
    like_count: int = 0
    comment_count: int = 0
    save_count: int = 0
    is_liked: bool = False
    is_saved: bool = False

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
