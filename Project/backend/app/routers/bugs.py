from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from pydantic import ValidationError
from ..database import get_db
from ..models import Bug
from ..schemas import (
    BugCreate,
    BugList,
    BugOut,
    BugStats,
    BugUpdate,
    Category,
    ErrorResponse,
    Language,
)

router = APIRouter(prefix="/bugs", tags=["bugs"])

SORT_FIELDS = {"id", "title", "severity", "time_wasted_min", "created_at", "fixed_at", "language", "category"}
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Bug not found"}}

def _get_or_404(db: Session, bug_id: int) -> Bug:
    bug = db.get(Bug, bug_id)
    if bug is None:
        raise HTTPException(status_code=404, detail=f"Bug {bug_id} not found")
    return bug

def _to_columns(
    payload: BugCreate | BugUpdate,
    existing_created_at: datetime | None = None,
    existing_fixed_at: datetime | None = None,
) -> dict:
    """Convert a validated payload into column values and apply the date rules."""
    data = payload.model_dump()
    data["language"] = payload.language.value
    data["category"] = payload.category.value

    now = datetime.now(timezone.utc)
    if data["created_at"] is None:
        data["created_at"] = existing_created_at or now

    if data["fixed"]:
        if data["fixed_at"] is None:
            data["fixed_at"] = existing_fixed_at or max(now, data["created_at"])
        elif data["fixed_at"] < data["created_at"]:
            raise HTTPException(status_code=422, detail="fixed_at must not be earlier than created_at")
    else:
        data["fixed_at"] = None
    return data

@router.get(
    "/stats",
    response_model=BugStats,
    summary="Bug statistics",
    description="Aggregated numbers: totals, time wasted per category and language, and the most expensive category.",
)
def bug_stats(db: Session = Depends(get_db)):
    total, fixed, wasted = db.execute(
        select(
            func.count(Bug.id),
            func.count(Bug.id).filter(Bug.fixed.is_(True)),
            func.coalesce(func.sum(Bug.time_wasted_min), 0),
        )
    ).one()

    def grouped(column) -> dict[str, dict[str, int]]:
        rows = db.execute(
            select(column, func.count(Bug.id), func.coalesce(func.sum(Bug.time_wasted_min), 0)).group_by(column)
        ).all()
        return {key: {"count": count, "time_wasted_min": int(minutes)} for key, count, minutes in rows}

    by_category = grouped(Bug.category)
    by_language = grouped(Bug.language)

    most_expensive_category = (
        max(by_category, key=lambda c: by_category[c]["time_wasted_min"]) if by_category else None
    )

    most_expensive_language = (
        max(by_language, key=lambda c: by_language[c]["time_wasted_min"]) if by_language else None
    )

    return {
        "total_bugs": total,
        "fixed": fixed,
        "unfixed": total - fixed,
        "total_time_wasted_min": int(wasted),
        "by_category": by_category,
        "by_language": grouped(Bug.language),
        "most_expensive_category": most_expensive_category,
        "most_expensive_language": most_expensive_language
    }

@router.get(
    "",
    response_model=BugList,
    summary="List bugs",
    description=(
        "Returns a page of bugs with optional filters.\n\n"
        "**Sorting:** `sort=<field>` ascending or `sort=-<field>` descending. "
        f"Allowed fields: {', '.join(sorted(SORT_FIELDS))}."
    ),
)
def list_bugs(
    language: Language = Query(None, description="Filter by language"),
    category: Category = Query(None, description="Filter by category"),
    fixed: bool | None = Query(None, description="Filter by fixed status"),
    min_time_wasted: int | None = Query(None, ge=0, description="Only bugs that cost at least this many minutes"),
    q: str | None = Query(None, min_length=1, description="Case-insensitive search in title, error message and cause"),
    sort: str = Query("-created_at", description="Sort field, prefix with '-' for descending"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
):
    field = sort.lstrip("-")
    if field not in SORT_FIELDS:
        raise HTTPException(status_code=422, detail=f"Cannot sort by '{field}'. Allowed: {sorted(SORT_FIELDS)}")

    stmt = select(Bug)
    if language:
        stmt = stmt.where(Bug.language == language.value)
    if category:
        stmt = stmt.where(Bug.category == category.value)
    if fixed is not None:
        stmt = stmt.where(Bug.fixed.is_(fixed))
    if min_time_wasted is not None:
        stmt = stmt.where(Bug.time_wasted_min >= min_time_wasted)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(Bug.title.ilike(pattern), Bug.error_message.ilike(pattern), Bug.cause.ilike(pattern))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    column = getattr(Bug, field)
    order = column.desc() if sort.startswith("-") else column.asc()
    items = db.scalars(stmt.order_by(order, Bug.id).limit(limit).offset(offset)).all()
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.get("/{bug_id}", response_model=BugOut, responses=NOT_FOUND, summary="Get a bug by ID")
def get_bug(bug_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, bug_id)

@router.post(
    "",
    response_model=BugOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bug",
    description=(
        "Creates a new bug entry.\n\n"
        "Rules: `solution` is required when `fixed` is true; `fixed_at` is only allowed when `fixed` is true "
        "and must not be earlier than `created_at`. If `fixed` is true and `fixed_at` is omitted, it is set to now."
    ),
)
def create_bug(payload: BugCreate, db: Session = Depends(get_db)):
    bug = Bug(**_to_columns(payload))
    db.add(bug)
    db.commit()
    return bug

@router.patch(
    "/{bug_id}",
    response_model=BugOut,
    responses=NOT_FOUND,
    summary="Update a bug (partial)",
    description="Send only the fields you want to change. Everything else keeps its current value.",
)
def update_bug(bug_id: int, payload: BugUpdate, db: Session = Depends(get_db)):
    bug = _get_or_404(db, bug_id)

    changes = payload.model_dump(exclude_unset=True)
    merged = BugOut.model_validate(bug).model_dump(exclude={"id"}) | changes
    if merged["fixed"] is False and "fixed_at" not in changes:
        merged["fixed_at"] = None

    try:
        full = BugCreate(**merged)
    except ValidationError as exc:
        errors = exc.errors(include_url=False)
        raise RequestValidationError([{**e, "loc": ("body", *e["loc"])} for e in errors])

    for key, value in _to_columns(
        full, existing_created_at=bug.created_at, existing_fixed_at=bug.fixed_at
    ).items():
        setattr(bug, key, value)
    db.commit()
    return bug

@router.delete(
    "/{bug_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Delete a bug",
)
def delete_bug(bug_id: int, db: Session = Depends(get_db)):
    bug = _get_or_404(db, bug_id)
    db.delete(bug)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
