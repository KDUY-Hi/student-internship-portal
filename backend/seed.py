from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Company, Skill, StudentProfile, User, UserRole


DEMO_PASSWORD = "Password123!"

DEMO_USERS = [
    ("Student Demo", "student@example.com", UserRole.student),
    ("Company Demo", "company@example.com", UserRole.company),
    ("Admin Demo", "admin@example.com", UserRole.admin),
]

DEMO_SKILLS = ["AWS", "Python", "React", "SQL", "Marketing"]


def seed_user(db, name: str, email: str, role: UserRole) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            role=role,
        )
        db.add(user)
        db.flush()

    if role == UserRole.student and not user.student_profile:
        db.add(StudentProfile(user_id=user.id, university="Demo University", major="Information Technology"))
    elif role == UserRole.company and not user.company:
        db.add(
            Company(
                user_id=user.id,
                company_name="AWS Cloud Co",
                description="Cloud internship demo company",
                address="Ho Chi Minh City",
            )
        )
    return user


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for name, email, role in DEMO_USERS:
            seed_user(db, name, email, role)

        for skill_name in DEMO_SKILLS:
            existing = db.query(Skill).filter(Skill.name == skill_name).first()
            if not existing:
                db.add(Skill(name=skill_name))

        db.commit()
    finally:
        db.close()

    print("Seed complete.")
    print(f"Demo password for all accounts: {DEMO_PASSWORD}")
    for _, email, role in DEMO_USERS:
        print(f"- {role.value}: {email}")


if __name__ == "__main__":
    main()
