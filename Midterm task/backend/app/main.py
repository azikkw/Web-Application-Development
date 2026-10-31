import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import Base, SessionLocal, engine
from .routers import criminals, hunts
from .seed import seed

@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    yield

DESCRIPTION = """
**SpaceBounty Hunters** is a REST API for space bounty hunters.
It gives access to a database of wanted criminals and a journal of bounty-hunting attempts.

* **Wanted Criminals** - list criminals with filters and sorting, get criminal details
* **Bounty Hunting Journal** - full CRUD for hunt logs (capture attempts)
"""

app = FastAPI(
    title=os.getenv("APP_NAME", "SpaceBounty Hunters"),
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(criminals.router)
app.include_router(hunts.router)
