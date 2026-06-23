from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


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


def test_student_company_admin_flow():
    suffix = uuid4().hex[:8]
    student = register(f"student-{suffix}@example.com", "student")
    company = register(f"company-{suffix}@example.com", "company")
    admin = register(f"admin-{suffix}@example.com", "admin")

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

    cv_profile = client.post(
        "/students/upload-cv",
        files={"file": ("cv.pdf", b"%PDF-1.4 demo", "application/pdf")},
        headers=auth_headers(student),
    )
    assert cv_profile.status_code == 200

    application = client.post("/applications", json={"internship_id": internship_id}, headers=auth_headers(student))
    assert application.status_code == 201
    application_id = application.json()["id"]

    company_apps = client.get("/company/applications", headers=auth_headers(company))
    assert company_apps.status_code == 200
    assert len(company_apps.json()) == 1

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
