from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 — ensures models are registered on Base.metadata
from app.database import Base, SessionLocal, engine
from app.routers import conversations, system_prompt
from app.seed import seed_defaults


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()
    yield


app = FastAPI(title="AI Advisor Chatbot API", lifespan=lifespan)

# Wide open for now — this is a single-user, no-auth app served behind one docker-compose network.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(conversations.router)
app.include_router(system_prompt.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
