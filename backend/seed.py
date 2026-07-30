from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import (
    Company,
    ForumCategory,
    ForumPost,
    ForumPostStatus,
    ForumPostType,
    InternshipPost,
    JobPosition,
    PostStatus,
    Skill,
    StudentProfile,
    User,
    UserRole,
)


DEMO_PASSWORD = "Password123!"

DEMO_USERS = [
    ("Student Demo", "student@example.com", UserRole.student),
    ("Company Demo", "company@example.com", UserRole.company),
    ("Admin Demo", "admin@example.com", UserRole.admin),
]

DEMO_SKILLS = ["AWS", "Python", "React", "SQL", "Marketing"]
DEMO_POSITIONS = [
    ("Fullstack Developer", "IT", "Build frontend and backend web features.", "React, Node.js, MySQL, Git, API, AWS"),
    ("Frontend Developer", "IT", "Build user interfaces and client-side flows.", "React, JavaScript, HTML, CSS, Git, Figma"),
    ("Backend Developer", "IT", "Build APIs, data models, and backend services.", "Python, Node.js, SQL, API, Docker, AWS"),
    ("Part-time Staff", "Service", "Support daily service operations.", "Customer Service, Communication, POS, Teamwork"),
    ("Chef", "Food & Beverage", "Prepare dishes and support kitchen operations.", "Food Safety, Preparation, Menu Planning, Teamwork"),
    ("Digital Marketing Intern", "Marketing", "Support content, ads, and analytics campaigns.", "Content Marketing, SEO, Google Analytics, Facebook Ads"),
    ("Sales Assistant", "Business", "Support sales operations and customer follow-up.", "Sales, CRM, Communication, Excel, Customer Service"),
]
DEMO_FORUM_CATEGORIES = [
    ("Frontend", "React, Vue, UI engineering, accessibility, and frontend internship topics."),
    ("Backend", "APIs, databases, authentication, system design, and backend services."),
    ("Tester / QA", "Manual testing, automation testing, QA process, and test case practice."),
    ("DevOps / Cloud", "Docker, Kubernetes, CI/CD, Linux, AWS, and cloud deployment."),
    ("Mobile", "Flutter, React Native, Android, iOS, and mobile app internships."),
    ("Data / AI", "Data engineering, machine learning, analytics, and AI application topics."),
    ("Cybersecurity", "Security fundamentals, web security, IAM, and defensive practice."),
]

LEGACY_DEMO_FORUM_CATEGORIES = [
    "Information Technology",
    "Marketing",
    "Logistics",
    "Business",
    "Food & Beverage",
    "Hospitality",
    "Part-time Jobs",
]


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

        for name, category, description, suggested_skills in DEMO_POSITIONS:
            position = db.query(JobPosition).filter(JobPosition.name == name).first()
            if not position:
                db.add(
                    JobPosition(
                        name=name,
                        category=category,
                        description=description,
                        suggested_skills=suggested_skills,
                        is_active=True,
                    )
                )
            else:
                position.category = category
                position.description = description
                position.suggested_skills = suggested_skills
                position.is_active = True

        for name, description in DEMO_FORUM_CATEGORIES:
            category = db.query(ForumCategory).filter(ForumCategory.name == name).first()
            if not category:
                db.add(ForumCategory(name=name, description=description, is_active=True))
            else:
                category.description = description
                category.is_active = True

        for legacy_name in LEGACY_DEMO_FORUM_CATEGORIES:
            legacy_category = db.query(ForumCategory).filter(ForumCategory.name == legacy_name).first()
            if legacy_category:
                legacy_category.is_active = False

        db.commit()

        company = db.query(Company).join(User).filter(User.email == "company@example.com").first()
        position = db.query(JobPosition).filter(JobPosition.name == "Fullstack Developer").first()
        if company and position:
            demo_post = (
                db.query(InternshipPost)
                .filter(InternshipPost.company_id == company.id, InternshipPost.title == "Fullstack Developer Intern")
                .first()
            )
            if not demo_post:
                db.add(
                    InternshipPost(
                        company_id=company.id,
                        position_id=position.id,
                        title="Fullstack Developer Intern",
                        description="Build student-facing web features with React and backend APIs.",
                        requirements="React, Node.js, MySQL, Git, AWS",
                        required_skills="React, Node.js, MySQL, Git, AWS",
                        experience_level="Fresher",
                        job_type="Internship",
                        salary_min=3000000,
                        salary_max=6000000,
                        education_requirement="IT students or related majors",
                        location="Ho Chi Minh City",
                        work_type="hybrid",
                        quantity=2,
                        deadline="2099-12-31",
                        status=PostStatus.approved,
                    )
                )
            db.commit()

        student = db.query(User).filter(User.email == "student@example.com").first()
        it_category = db.query(ForumCategory).filter(ForumCategory.name == "Backend").first()
        if student and it_category:
            demo_forum_post = (
                db.query(ForumPost)
                .filter(ForumPost.user_id == student.id, ForumPost.title == "How should I prepare for a Fullstack internship?")
                .first()
            )
            if not demo_forum_post:
                db.add(
                    ForumPost(
                        user_id=student.id,
                        category_id=it_category.id,
                        title="How should I prepare for a Fullstack internship?",
                        content="I am learning React and backend APIs. Which projects should I build before applying?",
                        post_type=ForumPostType.question,
                        status=ForumPostStatus.approved,
                    )
                )
            else:
                demo_forum_post.category_id = it_category.id
            db.commit()
    finally:
        db.close()

    print("Seed complete.")
    print(f"Demo password for all accounts: {DEMO_PASSWORD}")
    for _, email, role in DEMO_USERS:
        print(f"- {role.value}: {email}")


if __name__ == "__main__":
    main()
