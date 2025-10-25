from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routes import auth as auth_router
from .routes import profile as profile_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Nebula Arcade",
    description="A social casino experience with original games and reward systems.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api")
app.include_router(profile_router.router, prefix="/api")

static_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")
