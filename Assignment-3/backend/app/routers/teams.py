from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import League, Player, Team
from ..schemas import PlayerCreate, PlayerOut, TeamIn, TeamOut

router = APIRouter(prefix="/api/teams", tags=["Teams"])

def get_team_or_404(team_id: int, db: Session) -> Team:
    team = db.get(Team, team_id)

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return team

def ensure_league_exists(league_id: int, db: Session) -> None:
    if db.get(League, league_id) is None:
        raise HTTPException(status_code=404, detail="League not found")

@router.get("", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db)):
    return db.scalars(select(Team).order_by(Team.id)).all()

@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    return get_team_or_404(team_id, db)

@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(data: TeamIn, db: Session = Depends(get_db)):
    ensure_league_exists(data.league_id, db)
    team = Team(**data.model_dump())

    db.add(team)
    db.commit()
    db.refresh(team)

    return team

@router.put("/{team_id}", response_model=TeamOut)
def update_team(team_id: int, data: TeamIn, db: Session = Depends(get_db)):
    team = get_team_or_404(team_id, db)
    ensure_league_exists(data.league_id, db)

    for key, value in data.model_dump().items():
        setattr(team, key, value)

    db.commit()
    db.refresh(team)

    return team

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = get_team_or_404(team_id, db)

    db.delete(team)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{team_id}/players", response_model=list[PlayerOut])
def list_team_players(team_id: int, db: Session = Depends(get_db)):
    get_team_or_404(team_id, db)

    return db.scalars(select(Player).where(Player.team_id == team_id).order_by(Player.id)).all()

@router.post("/{team_id}/players", response_model=PlayerOut, status_code=status.HTTP_201_CREATED)
def create_team_player(team_id: int, data: PlayerCreate, db: Session = Depends(get_db)):
    get_team_or_404(team_id, db)
    player = Player(team_id=team_id, **data.model_dump())

    db.add(player)
    db.commit()
    db.refresh(player)

    return player
