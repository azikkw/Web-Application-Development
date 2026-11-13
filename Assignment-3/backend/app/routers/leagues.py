from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import League, Team
from ..schemas import LeagueIn, LeagueOut, TeamOut

router = APIRouter(prefix="/api/leagues", tags=["Leagues"])

def get_league_or_404(league_id: int, db: Session) -> League:
    league = db.get(League, league_id)

    if league is None:
        raise HTTPException(status_code=404, detail="League not found")

    return league

@router.get("", response_model=list[LeagueOut])
def list_leagues(db: Session = Depends(get_db)):
    return db.scalars(select(League).order_by(League.id)).all()

@router.get("/{league_id}", response_model=LeagueOut)
def get_league(league_id: int, db: Session = Depends(get_db)):
    return get_league_or_404(league_id, db)

@router.post("", response_model=LeagueOut, status_code=status.HTTP_201_CREATED)
def create_league(data: LeagueIn, db: Session = Depends(get_db)):
    league = League(**data.model_dump())

    db.add(league)
    db.commit()
    db.refresh(league)

    return league

@router.put("/{league_id}", response_model=LeagueOut)
def update_league(league_id: int, data: LeagueIn, db: Session = Depends(get_db)):
    league = get_league_or_404(league_id, db)

    for key, value in data.model_dump().items():
        setattr(league, key, value)

    db.commit()
    db.refresh(league)

    return league

@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_league(league_id: int, db: Session = Depends(get_db)):
    league = get_league_or_404(league_id, db)

    db.delete(league)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{league_id}/teams", response_model=list[TeamOut])
def list_league_teams(league_id: int, db: Session = Depends(get_db)):
    get_league_or_404(league_id, db)

    return db.scalars(select(Team).where(Team.league_id == league_id).order_by(Team.id)).all()
