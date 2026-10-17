from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Language(str, Enum):
    python = "python"
    javascript = "javascript"
    typescript = "typescript"
    java = "java"
    go = "go"
    sql = "sql"
    bash = "bash"
    docker = "docker"
    other = "other"

class Category(str, Enum):
    syntax = "syntax"
    logic = "logic"
    config = "config"
    dependency = "dependency"
    network = "network"
    database = "database"
    typo = "typo"
    other = "other"

class BugBase(BaseModel):
    """Writable fields of a bug (used for POST and PUT)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "CORS error when calling the API from the frontend",
                "error_message": "Access to fetch at 'http://localhost:8000/bugs' has been blocked by CORS policy",
                "language": "javascript",
                "category": "config",
                "severity": 2,
                "cause": "The backend did not send Access-Control-Allow-Origin headers",
                "solution": "Added CORSMiddleware with the frontend origin to the allowed list",
                "time_wasted_min": 35,
                "fixed": True,
                "tags": ["cors", "browser", "fastapi"],
            }
        }
    )

    title: str = Field(min_length=1, max_length=120, description="Short summary of the bug")
    error_message: str = Field(min_length=1, description="The error text exactly as you saw it")
    language: Language = Field(description="Language or technology where the bug lived")
    category: Category = Field(description="Kind of mistake")
    severity: int = Field(ge=1, le=5, description="1 = annoying, 5 = production is on fire")
    cause: str | None = Field(default=None, description="What actually caused the bug")
    solution: str | None = Field(default=None, description="How it was fixed. Required when `fixed` is true")
    time_wasted_min: int = Field(default=0, ge=0, description="Minutes spent on this bug")
    fixed: bool = Field(default=False, description="Has the bug been fixed?")
    tags: list[str] = Field(default_factory=list, max_length=10, description="Free-form tags (max 10)")
    created_at: datetime | None = Field(
        default=None, description="When the bug happened. Defaults to now (on PUT: keeps the stored value)"
    )
    fixed_at: datetime | None = Field(
        default=None,
        description="When it was fixed. Only allowed if `fixed` is true; defaults to now. Must not be earlier than `created_at`",
    )

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for tag in value:
            tag = tag.strip().lower()
            if not tag:
                raise ValueError("tags must not contain empty strings")
            if len(tag) > 30:
                raise ValueError("each tag must be at most 30 characters")
            if tag not in cleaned:
                cleaned.append(tag)
        return cleaned

    @field_validator("created_at", "fixed_at")
    @classmethod
    def make_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @model_validator(mode="after")
    def check_business_rules(self) -> "BugBase":
        if self.fixed and not (self.solution and self.solution.strip()):
            raise ValueError("solution is required when fixed is true")
        if self.fixed and not (self.cause and self.cause.strip()):
            raise ValueError("cause is required when fixed is true")
        if not self.fixed and self.fixed_at is not None:
            raise ValueError("fixed_at can only be set when fixed is true")
        if self.fixed_at and self.created_at and self.fixed_at < self.created_at:
            raise ValueError("fixed_at must not be earlier than created_at")
        return self

class BugCreate(BugBase):
    pass

class BugUpdate(BaseModel):
    """Partial update: send only the fields you want to change."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"time_wasted_min": 50, "severity": 3}}
    )

    title: str | None = Field(default=None, min_length=1, max_length=120)
    error_message: str | None = Field(default=None, min_length=1)
    language: Language | None = None
    category: Category | None = None
    severity: int | None = Field(default=None, ge=1, le=5)
    cause: str | None = None
    solution: str | None = None
    time_wasted_min: int | None = Field(default=None, ge=0)
    fixed: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=10)
    created_at: datetime | None = None
    fixed_at: datetime | None = None

class BugOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "CORS error when calling the API from the frontend",
                "error_message": "Access to fetch at 'http://localhost:8000/bugs' has been blocked by CORS policy",
                "language": "javascript",
                "category": "config",
                "severity": 2,
                "cause": "The backend did not send Access-Control-Allow-Origin headers",
                "solution": "Added CORSMiddleware with the frontend origin to the allowed list",
                "time_wasted_min": 35,
                "fixed": True,
                "tags": ["cors", "browser", "fastapi"],
                "created_at": "2026-10-17T09:00:00Z",
                "fixed_at": "2026-10-17T09:35:00Z",
            }
        },
    )

    id: int
    title: str
    error_message: str
    language: Language
    category: Category
    severity: int
    cause: str | None
    solution: str | None
    time_wasted_min: int
    fixed: bool
    tags: list[str]
    created_at: datetime
    fixed_at: datetime | None

class BugList(BaseModel):
    items: list[BugOut]
    total: int = Field(description="Total number of bugs matching the filters (ignores limit/offset)")
    limit: int
    offset: int

class GroupStat(BaseModel):
    count: int
    time_wasted_min: int

class BugStats(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_bugs": 8,
                "fixed": 7,
                "unfixed": 1,
                "total_time_wasted_min": 355,
                "by_category": {"network": {"count": 1, "time_wasted_min": 45}},
                "by_language": {"python": {"count": 4, "time_wasted_min": 275}},
                "most_expensive_category": "logic",
                "most_expensive_language": "javascript",
            }
        }
    )

    total_bugs: int
    fixed: int
    unfixed: int
    total_time_wasted_min: int
    by_category: dict[str, GroupStat]
    by_language: dict[str, GroupStat]
    most_expensive_category: str | None = Field(description="Category with the most minutes wasted, null if no bugs")
    most_expensive_language: str | None = Field(description="Language with the most minutes wasted, null if no bugs")

class ErrorResponse(BaseModel):
    detail: str

class HealthOut(BaseModel):
    status: str
    database: str
