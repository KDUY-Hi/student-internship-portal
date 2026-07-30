import os
import tempfile
from pathlib import Path
from uuid import uuid4

os.environ["DATABASE_URL"] = f"sqlite:///{(Path(tempfile.gettempdir()) / 'student_internship_portal_test.db').as_posix()}"
os.environ["REFRESH_COOKIE_SECURE"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.auth import create_access_token, hash_password
from app.config import Settings
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Company, ForumCategory, InternshipPost, JobPosition, PostStatus, RefreshToken, User, UserRole
from app import services


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_position(name: str = "Fullstack Developer") -> int:
    db = SessionLocal()
    try:
        position = JobPosition(
            name=f"{name} {uuid4().hex[:8]}",
            category="IT",
            description="Test position",
            suggested_skills="React, Node.js, MySQL, Git, AWS",
            is_active=True,
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        return position.id
    finally:
        db.close()


def create_forum_category(name: str = "Backend") -> int:
    db = SessionLocal()
    try:
        category = db.query(ForumCategory).filter(ForumCategory.name == name).first()
        if not category:
            category = ForumCategory(name=name, description="Test community", is_active=True)
            db.add(category)
            db.commit()
            db.refresh(category)
        return category.id
    finally:
        db.close()


def register(email: str, role: str):
    response = client.post(
        "/auth/register",
        json={"name": email.split("@")[0], "email": email, "password": "Password123!", "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def create_admin(email: str):
    db = SessionLocal()
    try:
        user = User(
            name=email.split("@")[0],
            email=email,
            password_hash=hash_password("Password123!"),
            role=UserRole.admin,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return create_access_token(str(user.id))
    finally:
        db.close()


def test_student_company_admin_flow():
    suffix = uuid4().hex[:8]
    student = register(f"student-{suffix}@example.com", "student")
    company = register(f"company-{suffix}@example.com", "company")
    admin = create_admin(f"admin-{suffix}@example.com")

    profile = client.post(
        "/company/profile",
        json={"company_name": "AWS Cloud Co", "description": "Cloud internships", "address": "Ho Chi Minh City"},
        headers=auth_headers(company),
    )
    assert profile.status_code == 200

    companies = client.get("/companies?q=AWS&location=Ho Chi Minh")
    assert companies.status_code == 200
    assert len(companies.json()) == 1
    assert companies.json()[0]["company_name"] == "AWS Cloud Co"

    position_id = create_position("Cloud Engineer")
    post = client.post(
        "/company/internships",
        json={
            "position_id": position_id,
            "title": "Cloud Intern",
            "description": "Build AWS projects",
            "requirements": "Python, AWS",
            "location": "Ho Chi Minh City",
            "work_type": "remote",
            "deadline": "2099-12-31",
        },
        headers=auth_headers(company),
    )
    assert post.status_code == 201
    internship_id = post.json()["id"]

    hidden = client.get("/internships")
    assert hidden.status_code == 200
    assert hidden.json() == []

    approved = client.patch(f"/admin/internships/{internship_id}/approve", headers=auth_headers(admin))
    assert approved.status_code == 200
    assert approved.json()["status"] == "Approved"

    visible = client.get("/internships?q=Cloud")
    assert visible.status_code == 200
    assert len(visible.json()) == 1
    visible_page = client.get("/internships?limit=1&offset=0")
    assert visible_page.status_code == 200
    assert len(visible_page.json()) <= 1

    saved_student_profile = client.post(
        "/students/profile",
        json={
            "university": "HCMUT",
            "major": "Software Engineering",
            "skills": "Python, AWS",
            "gpa": 3.5,
        },
        headers=auth_headers(student),
    )
    assert saved_student_profile.status_code == 200

    loaded_student_profile = client.get("/students/profile", headers=auth_headers(student))
    assert loaded_student_profile.status_code == 200
    assert loaded_student_profile.json()["university"] == "HCMUT"
    assert loaded_student_profile.json()["major"] == "Software Engineering"

    cv_profile = client.post(
        "/students/upload-cv",
        files={"file": ("cv.pdf", b"%PDF-1.4 demo", "application/pdf")},
        headers=auth_headers(student),
    )
    assert cv_profile.status_code == 200

    application = client.post("/applications", json={"internship_id": internship_id}, headers=auth_headers(student))
    assert application.status_code == 201
    application_id = application.json()["id"]

    my_applications = client.get("/applications/me", headers=auth_headers(student))
    assert my_applications.status_code == 200
    assert any(item["id"] == application_id for item in my_applications.json())

    submitted_notifications = client.get("/notifications", headers=auth_headers(student))
    assert submitted_notifications.status_code == 200
    assert any("submitted" in item["title"].lower() for item in submitted_notifications.json())

    company_notifications = client.get("/notifications", headers=auth_headers(company))
    assert company_notifications.status_code == 200
    assert any("new application" in item["title"].lower() for item in company_notifications.json())

    company_apps = client.get("/company/applications", headers=auth_headers(company))
    assert company_apps.status_code == 200
    assert len(company_apps.json()) == 1
    company_pending_apps = client.get("/company/applications?status_filter=Pending&limit=10", headers=auth_headers(company))
    assert company_pending_apps.status_code == 200
    assert len(company_pending_apps.json()) == 1

    updated = client.patch(
        f"/company/applications/{application_id}/status",
        json={"status": "Interview"},
        headers=auth_headers(company),
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "Interview"

    company_cv = client.get(f"/company/applications/{application_id}/cv", headers=auth_headers(company))
    assert company_cv.status_code == 200
    assert company_cv.json()["cv_url"]

    student_notifications = client.get("/notifications", headers=auth_headers(student))
    assert student_notifications.status_code == 200
    assert any("status" in item["title"].lower() for item in student_notifications.json())

    admin_stats = client.get("/admin/dashboard", headers=auth_headers(admin))
    assert admin_stats.status_code == 200
    assert admin_stats.json()["applications"] >= 1
    admin_students = client.get("/admin/users?role=student&limit=10", headers=auth_headers(admin))
    assert admin_students.status_code == 200
    assert all(item["role"] == "student" for item in admin_students.json())

    skill = client.post("/admin/skills", json={"name": "AWS"}, headers=auth_headers(admin))
    assert skill.status_code == 201
    skills = client.get("/skills")
    assert skills.status_code == 200
    assert any(item["name"] == "AWS" for item in skills.json())

    locked = client.patch("/admin/users/1/status", json={"is_active": False}, headers=auth_headers(admin))
    assert locked.status_code in {200, 400}


def test_role_access_is_blocked():
    student = register(f"student-{uuid4().hex[:8]}@example.com", "student")
    response = client.get("/admin/users", headers=auth_headers(student))
    assert response.status_code == 403


def test_public_admin_registration_is_blocked():
    response = client.post(
        "/auth/register",
        json={
            "name": "Admin",
            "email": f"admin-{uuid4().hex[:8]}@example.com",
            "password": "Password123!",
            "role": "admin",
        },
    )
    assert response.status_code == 403


def test_refresh_token_rotation_logout_and_login_rate_limit():
    suffix = uuid4().hex[:8]
    auth_client = TestClient(app)
    registered = auth_client.post(
        "/auth/register",
        json={"name": "Secure Student", "email": f"secure-{suffix}@example.com", "password": "Password123!", "role": "student"},
    )
    assert registered.status_code == 201
    first_access_token = registered.json()["access_token"]
    assert first_access_token

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == f"secure-{suffix}@example.com").first()
        sessions = db.query(RefreshToken).filter(RefreshToken.user_id == user.id).all()
        assert len(sessions) == 1
        assert sessions[0].token_hash
        assert sessions[0].revoked_at is None
        first_session_id = sessions[0].id
    finally:
        db.close()

    refreshed = auth_client.post("/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    db = SessionLocal()
    try:
        old_session = db.get(RefreshToken, first_session_id)
        active_sessions = (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == old_session.user_id, RefreshToken.revoked_at.is_(None))
            .all()
        )
        assert old_session.revoked_at is not None
        assert old_session.replaced_by_token_id is not None
        assert len(active_sessions) == 1
    finally:
        db.close()

    logout = auth_client.post("/auth/logout")
    assert logout.status_code == 204
    after_logout = auth_client.post("/auth/refresh")
    assert after_logout.status_code == 401

    limited_client = TestClient(app)
    for attempt in range(5):
        failed = limited_client.post(
            "/auth/login",
            json={"email": f"secure-{suffix}@example.com", "password": f"wrong-{attempt}"},
        )
        assert failed.status_code == 401
    blocked = limited_client.post(
        "/auth/login",
        json={"email": f"secure-{suffix}@example.com", "password": "Password123!"},
    )
    assert blocked.status_code == 429


def test_admin_can_manage_job_positions():
    suffix = uuid4().hex[:8]
    admin = create_admin(f"admin-position-{suffix}@example.com")

    created = client.post(
        "/admin/job-positions",
        json={
            "name": f"Fullstack Developer {suffix}",
            "category": "IT",
            "description": "Build web apps",
            "suggested_skills": "React, Node.js, MySQL, Git, AWS",
        },
        headers=auth_headers(admin),
    )
    assert created.status_code == 201
    position_id = created.json()["id"]

    updated = client.patch(
        f"/admin/job-positions/{position_id}",
        json={"category": "Software", "is_active": False},
        headers=auth_headers(admin),
    )
    assert updated.status_code == 200
    assert updated.json()["category"] == "Software"
    assert updated.json()["is_active"] is False

    public_positions = client.get("/job-positions")
    assert public_positions.status_code == 200
    assert all(item["id"] != position_id for item in public_positions.json())

    admin_positions = client.get("/admin/job-positions", headers=auth_headers(admin))
    assert admin_positions.status_code == 200
    assert any(item["id"] == position_id for item in admin_positions.json())

    deleted = client.delete(f"/admin/job-positions/{position_id}", headers=auth_headers(admin))
    assert deleted.status_code == 204


def test_duplicate_apply_expired_deadline_account_locked_and_role_boundaries():
    suffix = uuid4().hex[:8]
    student = register(f"student-extra-{suffix}@example.com", "student")
    company = register(f"company-extra-{suffix}@example.com", "company")
    admin = create_admin(f"admin-extra-{suffix}@example.com")

    profile = client.post(
        "/company/profile",
        json={"company_name": "Boundary Co", "website": "https://boundary.example.com"},
        headers=auth_headers(company),
    )
    assert profile.status_code == 200

    position_id = create_position("Backend Developer")
    invalid_quantity = client.post(
        "/company/internships",
        json={"position_id": position_id, "title": "Bad Quantity", "description": "Invalid", "quantity": 0},
        headers=auth_headers(company),
    )
    assert invalid_quantity.status_code == 422

    post = client.post(
        "/company/internships",
        json={"position_id": position_id, "title": "Backend Intern", "description": "API work", "deadline": "2099-12-31"},
        headers=auth_headers(company),
    )
    assert post.status_code == 201
    internship_id = post.json()["id"]
    assert client.patch(f"/admin/internships/{internship_id}/approve", headers=auth_headers(admin)).status_code == 200

    invalid_gpa = client.post("/students/profile", json={"gpa": 5}, headers=auth_headers(student))
    assert invalid_gpa.status_code == 422

    large_cv = client.post(
        "/students/upload-cv",
        files={"file": ("large.pdf", b"x" * (5 * 1024 * 1024 + 1), "application/pdf")},
        headers=auth_headers(student),
    )
    assert large_cv.status_code == 400

    cv_profile = client.post(
        "/students/upload-cv",
        files={"file": ("cv.pdf", b"%PDF-1.4 demo", "application/pdf")},
        headers=auth_headers(student),
    )
    assert cv_profile.status_code == 200

    first_apply = client.post("/applications", json={"internship_id": internship_id}, headers=auth_headers(student))
    assert first_apply.status_code == 201
    duplicate_apply = client.post("/applications", json={"internship_id": internship_id}, headers=auth_headers(student))
    assert duplicate_apply.status_code == 409

    company_cannot_apply = client.post("/applications", json={"internship_id": internship_id}, headers=auth_headers(company))
    assert company_cannot_apply.status_code == 403

    db = SessionLocal()
    try:
        company_user = db.query(User).filter(User.email == f"company-extra-{suffix}@example.com").first()
        company_profile = db.query(Company).filter(Company.user_id == company_user.id).first()
        expired_post = InternshipPost(
            company_id=company_profile.id,
            title="Expired Intern",
            description="Expired",
            deadline="2000-01-01",
            status=PostStatus.approved,
        )
        db.add(expired_post)
        db.commit()
        db.refresh(expired_post)
        expired_id = expired_post.id
    finally:
        db.close()

    expired_apply = client.post("/applications", json={"internship_id": expired_id}, headers=auth_headers(student))
    assert expired_apply.status_code == 400
    expired_list = client.get("/internships")
    assert expired_list.status_code == 200
    assert any(item["id"] == expired_id for item in expired_list.json())

    current_student = client.get("/auth/me", headers=auth_headers(student))
    assert current_student.status_code == 200
    locked = client.patch(
        f"/admin/users/{current_student.json()['id']}/status",
        json={"is_active": False},
        headers=auth_headers(admin),
    )
    assert locked.status_code == 200
    locked_login = client.post(
        "/auth/login",
        json={"email": f"student-extra-{suffix}@example.com", "password": "Password123!"},
    )
    assert locked_login.status_code == 403


def test_job_market_analytics():
    suffix = uuid4().hex[:8]
    company_token = register(f"company-analytics-{suffix}@example.com", "company")
    admin_token = create_admin(f"admin-analytics-{suffix}@example.com")

    profile = client.post(
        "/company/profile",
        json={"company_name": "Analytics Co", "description": "Market data", "address": "Ho Chi Minh City"},
        headers=auth_headers(company_token),
    )
    assert profile.status_code == 200

    db = SessionLocal()
    try:
        position = JobPosition(name=f"Fullstack Developer {suffix}", category="IT", description="Web product role")
        db.add(position)
        db.commit()
        db.refresh(position)
        position_id = position.id
    finally:
        db.close()

    post = client.post(
        "/company/internships",
        json={
            "position_id": position_id,
            "title": "Fullstack Developer Intern",
            "description": "Build web features",
            "required_skills": "React, Node.js, MySQL, AWS",
            "requirements": "Fresher with web project experience",
            "experience_level": "Fresher",
            "job_type": "Internship",
            "salary_min": 3000000,
            "salary_max": 6000000,
            "education_requirement": "IT students",
            "location": "Ho Chi Minh City",
            "deadline": "2099-12-31",
        },
        headers=auth_headers(company_token),
    )
    assert post.status_code == 201
    assert client.patch(f"/admin/internships/{post.json()['id']}/approve", headers=auth_headers(admin_token)).status_code == 200

    summary = client.get("/analytics/job-market-summary")
    assert summary.status_code == 200
    data = summary.json()
    assert any(item["label"] == "React" for item in data["top_skills"])
    assert any(item["label"] == f"Fullstack Developer {suffix}" for item in data["top_positions"])
    assert data["salary"]["minimum"] == 3000000

    skills = client.get(f"/analytics/skill-by-position/{position_id}")
    assert skills.status_code == 200
    assert skills.json()["skills"][0]["label"] in {"React", "Node.js", "MySQL", "AWS"}


def test_professional_forum_flow_and_moderation():
    suffix = uuid4().hex[:8]
    student = register(f"student-forum-{suffix}@example.com", "student")
    admin = create_admin(f"admin-forum-{suffix}@example.com")
    category_id = create_forum_category("Backend")

    question = client.post(
        "/forum/posts",
        json={
            "category_id": category_id,
            "title": "How to prepare for backend internship?",
            "content": "Which API project should I build?",
            "post_type": "Question",
        },
        headers=auth_headers(student),
    )
    assert question.status_code == 201
    assert question.json()["status"] == "Approved"
    post_id = question.json()["id"]

    comment = client.post(
        f"/forum/posts/{post_id}/comments",
        json={"content": "Build one CRUD API and deploy it."},
        headers=auth_headers(student),
    )
    assert comment.status_code == 201

    liked = client.post(f"/forum/posts/{post_id}/like", headers=auth_headers(student))
    assert liked.status_code == 200
    assert liked.json()["like_count"] == 1
    saved = client.post(f"/forum/posts/{post_id}/save", headers=auth_headers(student))
    assert saved.status_code == 200
    assert saved.json()["is_saved"] is True

    academic = client.post(
        "/forum/posts",
        json={
            "category_id": category_id,
            "title": "Academic note about REST APIs",
            "content": "A structured learning note.",
            "post_type": "Academic Post",
        },
        headers=auth_headers(student),
    )
    assert academic.status_code == 201
    assert academic.json()["status"] == "Pending"
    academic_id = academic.json()["id"]

    public_posts = client.get("/forum/posts", headers=auth_headers(student))
    assert all(item["id"] != academic_id for item in public_posts.json())

    admin_posts = client.get("/admin/forum/posts", headers=auth_headers(admin))
    assert admin_posts.status_code == 200
    assert any(item["id"] == academic_id for item in admin_posts.json())

    approved = client.patch(
        f"/admin/forum/posts/{academic_id}/status",
        json={"status": "Approved"},
        headers=auth_headers(admin),
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "Approved"

    hidden = client.patch(
        f"/admin/forum/posts/{academic_id}/status",
        json={"status": "Hidden"},
        headers=auth_headers(admin),
    )
    assert hidden.status_code == 200
    assert hidden.json()["status"] == "Hidden"


def test_s3_cv_references_use_presigned_urls(monkeypatch):
    class FakeS3Client:
        def generate_presigned_url(self, operation, Params, ExpiresIn):
            assert operation == "get_object"
            assert Params == {"Bucket": "private-cv-bucket", "Key": "cvs/student-1/demo.pdf"}
            assert ExpiresIn == 600
            return "https://signed.example.com/cvs/student-1/demo.pdf"

    monkeypatch.setattr(services.settings, "s3_bucket_name", "private-cv-bucket")
    monkeypatch.setattr(services.settings, "s3_presigned_url_expire_seconds", 600)
    monkeypatch.setattr(services.boto3, "client", lambda *args, **kwargs: FakeS3Client())

    assert services.create_presigned_cv_url("cvs/student-1/demo.pdf") == "https://signed.example.com/cvs/student-1/demo.pdf"


def test_production_cookie_and_cors_settings_are_strict():
    settings = Settings(
        environment="production",
        backend_cors_origins="https://app.example.com",
        backend_cors_origin_regex="",
        refresh_cookie_secure=True,
        refresh_cookie_samesite="None",
    )

    assert settings.cors_origins == ["https://app.example.com"]
    assert settings.backend_cors_origin_regex is None
    assert settings.refresh_cookie_samesite == "none"

    with pytest.raises(ValueError):
        Settings(
            environment="production",
            backend_cors_origins="http://app.example.com",
            backend_cors_origin_regex="",
            refresh_cookie_secure=True,
            refresh_cookie_samesite="none",
        )

    with pytest.raises(ValueError):
        Settings(
            environment="production",
            backend_cors_origins="https://app.example.com",
            backend_cors_origin_regex=r"https?://localhost(:\d+)?",
            refresh_cookie_secure=True,
            refresh_cookie_samesite="none",
        )
