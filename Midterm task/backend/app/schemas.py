from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CriminalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str | None
    nickname: str
    reward: float
    last_known_latitude: float | None
    last_known_longitude: float | None
    last_known_note: str | None
    difficulty: int
    armed: bool
    has_crew: bool
    escape_master: bool

class HuntLogCreate(BaseModel):
    criminal_id: int
    success: bool
    notes: str

class HuntLogUpdate(BaseModel):
    success: bool | None = None
    notes: str | None = None

class HuntLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    criminal_id: int
    success: bool
    notes: str
    created_at: datetime
