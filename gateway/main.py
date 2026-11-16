import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- Configuration ---------------------------------------------------------
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:1.5b"  # M3 : le modèle est choisi par la gateway, jamais par l'utilisateur

app = FastAPI(title="Secure LLM Gateway")


# --- Format des messages ----------------------------------------------------
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


# --- Routes -----------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": req.question}],
        "stream": False,
    }
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
    except httpx.HTTPError:
        # On ne renvoie jamais le détail technique de l'erreur à l'utilisateur
        raise HTTPException(status_code=502, detail="LLM backend unavailable")

    return ChatResponse(answer=r.json()["message"]["content"])