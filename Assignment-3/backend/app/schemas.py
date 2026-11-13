from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Position = Literal["GK", "DF", "MF", "FW"]

class LeagueIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    country: str = Field(min_length=1, max_length=100)

class LeagueOut(LeagueIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class TeamIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    league_id: int

class TeamOut(TeamIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    

class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    position: Position
    age: int = Field(ge=15, le=50)
    shirt_number: int = Field(ge=1, le=99)

class PlayerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    position: Position | None = None
    age: int | None = Field(default=None, ge=15, le=50)
    shirt_number: int | None = Field(default=None, ge=1, le=99)

class PlayerOut(PlayerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    team_id: int
