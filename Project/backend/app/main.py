import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from .database import Base, engine
from .routers import bugs
from .schemas import ErrorResponse, HealthOut

@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

DESCRIPTION = """
**Bug Diary** is a personal knowledge base of bugs you have already fixed:
what broke, why, how you fixed it and how many minutes it cost you.
Stop stepping on the same rake twice.

### Business rules
* `solution` / `cause` is required when `fixed` is `true`
* `fixed_at` is only allowed when `fixed` is `true` and must not be earlier than `created_at`
* `severity` is 1-5, `time_wasted_min` is >= 0, `tags` has at most 10 items
"""

app = FastAPI(
    title=os.environ["APP_NAME"],
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "bugs", "description": "CRUD operations and statistics for bug entries"},
        {"name": "system", "description": "Service health"},
    ],
)
app.include_router(bugs.router)

@app.get(
    "/health",
    tags=["system"],
    response_model=HealthOut,
    responses={503: {"model": ErrorResponse, "description": "Database is unreachable"}},
    summary="Health check",
    description="Returns 200 if the service is up and can reach the database.",
)
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Database is unreachable")
    return {"status": "ok", "database": "up"}

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
