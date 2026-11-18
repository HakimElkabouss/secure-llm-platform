import hmac
import os

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

# --- Configuration ---------------------------------------------------------
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:1.5b"  # M3 : le modèle est choisi par la gateway, jamais par l'utilisateur

# M2 : les clés autorisées viennent de l'environnement, jamais du code
API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]

app = FastAPI(title="Secure LLM Gateway")


# --- Format des messages ----------------------------------------------------
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str

# --- Sécurité ---------------------------------------------------------------
def verify_api_key(authorization: str | None = Header(default=None)) -> None:
    """M2 : refuse toute requête sans clé valide."""
    token = (authorization or "").removeprefix("Bearer ").strip()
    if not token or not any(hmac.compare_digest(token, key) for key in API_KEYS):
        raise HTTPException(status_code=401, detail="invalid or missing API key")

# --- Routes -----------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
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