from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Player
from ..schemas import PlayerOut, PlayerUpdate

router = APIRouter(prefix="/api/players", tags=["Players"])

def get_player_or_404(player_id: int, db: Session) -> Player:
    player = db.get(Player, player_id)

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    return player

@router.get("/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, db: Session = Depends(get_db)):
    return get_player_or_404(player_id, db)

@router.patch("/{player_id}", response_model=PlayerOut)
def update_player(player_id: int, data: PlayerUpdate, db: Session = Depends(get_db)):
    player = get_player_or_404(player_id, db)

    for key, value in data.model_dump(exclude_none=True).items():
        setattr(player, key, value)

    db.commit()
    db.refresh(player)

    return player

@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: int, db: Session = Depends(get_db)):
    player = get_player_or_404(player_id, db)

    db.delete(player)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
