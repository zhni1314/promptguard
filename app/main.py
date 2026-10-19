from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from app.gateway import process
from app.audit import init_db, fetch_logs

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="PromptGuard", version="0.1.0", lifespan=lifespan)

class ChatRequest(BaseModel):
    user_input: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    return process(req.user_input)

@app.get("/logs")
def logs(limit: int = 50):
    return {"logs": fetch_logs(limit)}
