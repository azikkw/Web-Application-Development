from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import HuntLog, WantedCriminal

CRIMINALS = [
    dict(name="Jax Orren", nickname="Red Comet", reward=12000, last_known_latitude=41.2, last_known_longitude=-73.9,
         difficulty=7, armed=True, has_crew=True, escape_master=False),
    dict(name=None, nickname="The Ghost", reward=25000, last_known_note="Seen near the Kessel asteroid belt",
         difficulty=10, armed=True, has_crew=False, escape_master=True),
    dict(name="Mira Vash", nickname="Silver Fox", reward=4500, last_known_latitude=-12.5, last_known_longitude=130.8,
         difficulty=4, armed=False, has_crew=False, escape_master=True),
    dict(name="Dorn Kalt", nickname="Iron Jaw", reward=8000, last_known_note="Hiding on mining station Theta-9",
         difficulty=6, armed=True, has_crew=True, escape_master=False),
    dict(name="Lyra Senn", nickname="Starling", reward=3000, last_known_latitude=55.7, last_known_longitude=37.6,
         difficulty=2, armed=False, has_crew=True, escape_master=False),
    dict(name=None, nickname="Void Walker", reward=18000, last_known_note="Last signal from the Outer Rim",
         difficulty=9, armed=True, has_crew=True, escape_master=True),
]

HUNTS = [
    (1, False, "Target escaped in a stolen freighter."),
    (1, False, "Ambushed by his crew at the docking bay."),
    (2, False, "Target vanished from sensors in the asteroid belt."),
    (2, False, "False lead, nobody at the coordinates."),
    (3, False, "Target escaped through an asteroid field."),
    (3, True, "Captured at a cantina on Tatoo outpost."),
    (4, False, "Station security interfered."),
    (4, True, "Captured after a long firefight."),
    (5, True, "Captured without resistance."),
    (6, False, "Lost the trail near a black hole."),
]

def seed(db: Session) -> None:
    if db.scalar(select(WantedCriminal.id).limit(1)) is not None:
        return
    
    criminals = [WantedCriminal(**c) for c in CRIMINALS]

    db.add_all(criminals)
    db.flush()

    for idx, success, notes in HUNTS:
        db.add(HuntLog(criminal_id=criminals[idx - 1].id, success=success, notes=notes))
        
    db.commit()
