from collections import Counter
import re

from sqlalchemy.orm import Session

from app.models import InternshipPost, JobPosition, PostStatus
from app.schemas import AnalyticsItem, JobMarketSummary, SalarySummary


SKILL_SPLIT_RE = re.compile(r"[,;/\n]+")


def approved_posts_query(db: Session):
    return db.query(InternshipPost).filter(InternshipPost.status == PostStatus.approved)


def split_skills(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in SKILL_SPLIT_RE.split(value) if item.strip()]


def item_list(counter: Counter[str], total: int, limit: int = 10) -> list[AnalyticsItem]:
    if total <= 0:
        return []
    return [
        AnalyticsItem(label=label, count=count, percentage=round((count / total) * 100, 2))
        for label, count in counter.most_common(limit)
    ]


def top_skills(db: Session, position_id: int | None = None, limit: int = 10) -> list[AnalyticsItem]:
    query = approved_posts_query(db)
    if position_id:
        query = query.filter(InternshipPost.position_id == position_id)
    posts = query.all()
    counter: Counter[str] = Counter()
    for post in posts:
        skills = split_skills(post.required_skills) or split_skills(post.requirements)
        counter.update(dict.fromkeys(skills, 1))
    return item_list(counter, len(posts), limit)


def top_positions(db: Session, limit: int = 10) -> list[AnalyticsItem]:
    posts = approved_posts_query(db).all()
    counter: Counter[str] = Counter()
    for post in posts:
        label = post.position.name if post.position else post.title
        if label:
            counter[label] += 1
    return item_list(counter, len(posts), limit)


def top_experience_levels(db: Session, limit: int = 10) -> list[AnalyticsItem]:
    posts = approved_posts_query(db).all()
    counter = Counter(post.experience_level for post in posts if post.experience_level)
    return item_list(counter, len(posts), limit)


def top_locations(db: Session, limit: int = 10) -> list[AnalyticsItem]:
    posts = approved_posts_query(db).all()
    counter = Counter(post.location for post in posts if post.location)
    return item_list(counter, len(posts), limit)


def salary_summary(db: Session) -> SalarySummary:
    posts = [post for post in approved_posts_query(db).all() if post.salary_min is not None or post.salary_max is not None]
    if not posts:
        return SalarySummary()

    minimums = [post.salary_min for post in posts if post.salary_min is not None]
    maximums = [post.salary_max for post in posts if post.salary_max is not None]
    range_counter: Counter[str] = Counter()
    for post in posts:
        if post.salary_min is not None and post.salary_max is not None:
            label = f"{post.salary_min:,} - {post.salary_max:,}"
        elif post.salary_min is not None:
            label = f"From {post.salary_min:,}"
        else:
            label = f"Up to {post.salary_max:,}"
        range_counter[label] += 1

    return SalarySummary(
        minimum=min(minimums) if minimums else None,
        maximum=max(maximums) if maximums else None,
        average_min=round(sum(minimums) / len(minimums), 2) if minimums else None,
        average_max=round(sum(maximums) / len(maximums), 2) if maximums else None,
        popular_ranges=item_list(range_counter, len(posts), 5),
    )


def skill_by_position(db: Session, position_id: int, limit: int = 10) -> dict:
    position = db.get(JobPosition, position_id)
    return {
        "position": position.name if position else None,
        "skills": top_skills(db, position_id=position_id, limit=limit),
    }


def market_summary(db: Session) -> JobMarketSummary:
    total = approved_posts_query(db).count()
    return JobMarketSummary(
        total_posts=total,
        top_skills=top_skills(db),
        top_positions=top_positions(db),
        top_experience_levels=top_experience_levels(db),
        top_locations=top_locations(db),
        salary=salary_summary(db),
    )
