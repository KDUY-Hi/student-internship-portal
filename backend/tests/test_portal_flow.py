from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import create_access_token, hash_password
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Company, InternshipPost, PostStatus, User, UserRole


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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

    post = client.post(
        "/company/internships",
        json={
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

    invalid_quantity = client.post(
        "/company/internships",
        json={"title": "Bad Quantity", "description": "Invalid", "quantity": 0},
        headers=auth_headers(company),
    )
    assert invalid_quantity.status_code == 422

    post = client.post(
        "/company/internships",
        json={"title": "Backend Intern", "description": "API work", "deadline": "2099-12-31"},
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
