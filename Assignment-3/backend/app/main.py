from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import Base, engine
from .routers import leagues, players, teams

@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Football API",
    description="REST API for football leagues, their teams and team players.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(leagues.router)
app.include_router(teams.router)
app.include_router(players.router)
