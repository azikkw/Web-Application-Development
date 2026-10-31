from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import HuntLog, WantedCriminal
from ..schemas import HuntLogCreate, HuntLogOut, HuntLogUpdate

router = APIRouter(prefix="/api/hunts", tags=["Bounty Hunting Journal"])

def get_hunt_or_404(hunt_id: int, db: Session) -> HuntLog:
    hunt = db.get(HuntLog, hunt_id)

    if hunt is None:
        raise HTTPException(status_code=404, detail="Hunt log not found")
    
    return hunt


@router.get("/", response_model=list[HuntLogOut])
def list_hunts(criminal_id: int | None = Query(None), db: Session = Depends(get_db)):
    stmt = select(HuntLog).order_by(HuntLog.id)

    if criminal_id is not None:
        stmt = stmt.where(HuntLog.criminal_id == criminal_id)

    return db.scalars(stmt).all()


@router.get("/{hunt_id}/", response_model=HuntLogOut)
def get_hunt(hunt_id: int, db: Session = Depends(get_db)):
    return get_hunt_or_404(hunt_id, db)


@router.post("/", response_model=HuntLogOut, status_code=status.HTTP_201_CREATED)
def create_hunt(data: HuntLogCreate, db: Session = Depends(get_db)):
    if db.get(WantedCriminal, data.criminal_id) is None:
        raise HTTPException(status_code=404, detail="Criminal not found")
    
    hunt = HuntLog(criminal_id=data.criminal_id, success=data.success, notes=data.notes)

    db.add(hunt)
    db.commit()
    db.refresh(hunt)

    return hunt


@router.patch("/{hunt_id}/", response_model=HuntLogOut)
def update_hunt(hunt_id: int, data: HuntLogUpdate, db: Session = Depends(get_db)):
    hunt = get_hunt_or_404(hunt_id, db)

    if data.success is not None:
        hunt.success = data.success
    if data.notes is not None:
        hunt.notes = data.notes

    db.commit()
    db.refresh(hunt)

    return hunt


@router.delete("/{hunt_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_hunt(hunt_id: int, db: Session = Depends(get_db)):
    hunt = get_hunt_or_404(hunt_id, db)

    db.delete(hunt)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
