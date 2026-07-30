import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    company = "company"
    admin = "admin"


class PostStatus(str, enum.Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"
    closed = "Closed"


class ApplicationStatus(str, enum.Enum):
    pending = "Pending"
    reviewed = "Reviewed"
    interview = "Interview"
    accepted = "Accepted"
    rejected = "Rejected"


class ForumPostType(str, enum.Enum):
    question = "Question"
    academic = "Academic Post"
    experience = "Experience Sharing"
    resource = "Resource"
    discussion = "Discussion"


class ForumPostStatus(str, enum.Enum):
    pending = "Pending"
    approved = "Approved"
    hidden = "Hidden"
    rejected = "Rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student_profile: Mapped["StudentProfile | None"] = relationship(back_populates="user", uselist=False)
    company: Mapped["Company | None"] = relationship(back_populates="user", uselist=False)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    replaced_by_token_id: Mapped[int | None] = mapped_column(Integer)
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    university: Mapped[str | None] = mapped_column(String(255))
    major: Mapped[str | None] = mapped_column(String(255))
    skills: Mapped[str | None] = mapped_column(Text)
    gpa: Mapped[float | None] = mapped_column(Float)
    experience: Mapped[str | None] = mapped_column(Text)
    cv_url: Mapped[str | None] = mapped_column(Text)
    github: Mapped[str | None] = mapped_column(String(255))
    linkedin: Mapped[str | None] = mapped_column(String(255))

    user: Mapped[User] = relationship(back_populates="student_profile")
    applications: Mapped[list["Application"]] = relationship(back_populates="student")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(255))
    logo_url: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="company")
    internship_posts: Mapped[list["InternshipPost"]] = relationship(back_populates="company")


class JobPosition(Base):
    __tablename__ = "job_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    suggested_skills: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    internship_posts: Mapped[list["InternshipPost"]] = relationship(back_populates="position")


class InternshipPost(Base):
    __tablename__ = "internship_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    position_id: Mapped[int | None] = mapped_column(ForeignKey("job_positions.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text)
    required_skills: Mapped[str | None] = mapped_column(Text)
    experience_level: Mapped[str | None] = mapped_column(String(80), index=True)
    job_type: Mapped[str | None] = mapped_column(String(80), index=True)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    education_requirement: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255), index=True)
    work_type: Mapped[str | None] = mapped_column(String(50), index=True)
    allowance: Mapped[str | None] = mapped_column(String(100))
    duration: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[int | None] = mapped_column(Integer)
    deadline: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), default=PostStatus.pending, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company: Mapped[Company] = relationship(back_populates="internship_posts")
    position: Mapped[JobPosition | None] = relationship(back_populates="internship_posts")
    applications: Mapped[list["Application"]] = relationship(back_populates="internship")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("student_id", "internship_id", name="uq_student_internship"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    internship_id: Mapped[int] = mapped_column(ForeignKey("internship_posts.id"), index=True)
    cv_url: Mapped[str] = mapped_column(Text)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.pending, index=True
    )
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student: Mapped[StudentProfile] = relationship(back_populates="applications")
    internship: Mapped[InternshipPost] = relationship(back_populates="applications")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship()


class ForumCategory(Base):
    __tablename__ = "forum_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    posts: Mapped[list["ForumPost"]] = relationship(back_populates="category")


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("forum_categories.id"), index=True)
    title: Mapped[str] = mapped_column(String(220), index=True)
    content: Mapped[str] = mapped_column(Text)
    post_type: Mapped[ForumPostType] = mapped_column(Enum(ForumPostType), index=True)
    status: Mapped[ForumPostStatus] = mapped_column(Enum(ForumPostStatus), default=ForumPostStatus.approved, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship()
    category: Mapped[ForumCategory] = relationship(back_populates="posts")
    comments: Mapped[list["ForumComment"]] = relationship(back_populates="post")
    likes: Mapped[list["ForumLike"]] = relationship(back_populates="post")
    saves: Mapped[list["ForumSave"]] = relationship(back_populates="post")


class ForumComment(Base):
    __tablename__ = "forum_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_posts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    post: Mapped[ForumPost] = relationship(back_populates="comments")
    user: Mapped[User] = relationship()


class ForumLike(Base):
    __tablename__ = "forum_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_forum_like_post_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_posts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    post: Mapped[ForumPost] = relationship(back_populates="likes")
    user: Mapped[User] = relationship()


class ForumSave(Base):
    __tablename__ = "forum_saves"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_forum_save_post_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_posts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    post: Mapped[ForumPost] = relationship(back_populates="saves")
    user: Mapped[User] = relationship()
