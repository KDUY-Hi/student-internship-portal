from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics_service import market_summary, salary_summary, skill_by_position, top_locations, top_positions, top_skills
from app.database import get_db
from app.schemas import AnalyticsItem, JobMarketSummary, SalarySummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-skills", response_model=list[AnalyticsItem])
def get_top_skills(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    return top_skills(db, limit=limit)


@router.get("/top-positions", response_model=list[AnalyticsItem])
def get_top_positions(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    return top_positions(db, limit=limit)


@router.get("/top-locations", response_model=list[AnalyticsItem])
def get_top_locations(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    return top_locations(db, limit=limit)


@router.get("/salary-summary", response_model=SalarySummary)
def get_salary_summary(db: Session = Depends(get_db)):
    return salary_summary(db)


@router.get("/skill-by-position/{position_id}")
def get_skill_by_position(position_id: int, limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    return skill_by_position(db, position_id=position_id, limit=limit)


@router.get("/job-market-summary", response_model=JobMarketSummary)
def get_job_market_summary(db: Session = Depends(get_db)):
    return market_summary(db)
