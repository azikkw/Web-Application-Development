from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import WantedCriminal
from ..schemas import CriminalOut

router = APIRouter(prefix="/api/criminals", tags=["Wanted Criminals"])

@router.get("/", response_model=list[CriminalOut])
def list_criminals(
    min_reward: float | None = Query(None),
    max_reward: float | None = Query(None),
    armed: bool | None = Query(None),
    has_crew: bool | None = Query(None),
    escape_master: bool | None = Query(None),
    sort: Literal["reward", "-reward"] | None = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(WantedCriminal)

    if min_reward is not None:
        stmt = stmt.where(WantedCriminal.reward >= min_reward)
    if max_reward is not None:
        stmt = stmt.where(WantedCriminal.reward <= max_reward)
    if armed is not None:
        stmt = stmt.where(WantedCriminal.armed == armed)
    if has_crew is not None:
        stmt = stmt.where(WantedCriminal.has_crew == has_crew)
    if escape_master is not None:
        stmt = stmt.where(WantedCriminal.escape_master == escape_master)

    if sort == "reward":
        stmt = stmt.order_by(WantedCriminal.reward.asc())
    elif sort == "-reward":
        stmt = stmt.order_by(WantedCriminal.reward.desc())
    else:
        stmt = stmt.order_by(WantedCriminal.id)

    return db.scalars(stmt).all()


@router.get("/{criminal_id}/", response_model=CriminalOut)
def get_criminal(criminal_id: int, db: Session = Depends(get_db)):
    criminal = db.get(WantedCriminal, criminal_id)

    if criminal is None:
        raise HTTPException(status_code=404, detail="Criminal not found")
    
    return criminal
