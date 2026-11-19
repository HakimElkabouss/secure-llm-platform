import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict, deque

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

# --- Configuration ---------------------------------------------------------
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:1.5b"  # M3 : le modèle est choisi par la gateway, jamais par l'utilisateur

# M2 : les clés autorisées viennent de l'environnement, jamais du code
API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]

# M4 : limite de requêtes par minute et par clé
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

app = FastAPI(title="Secure LLM Gateway")


# --- Format des messages ----------------------------------------------------
class ChatRequest(BaseModel):
    # M4 : une question ne peut être ni vide, ni trop longue
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str

# --- Sécurité ---------------------------------------------------------------
def verify_api_key(authorization: str | None = Header(default=None)) -> str:
    """M2 : refuse toute requête sans clé valide.
    Renvoie l'empreinte de la clé (jamais la clé elle-même)."""
    token = (authorization or "").removeprefix("Bearer ").strip()
    if not token or not any(hmac.compare_digest(token, key) for key in API_KEYS):
        raise HTTPException(status_code=401, detail="invalid or missing API key")
    return hashlib.sha256(token.encode()).hexdigest()[:12]


# M4 : fenêtre glissante d'une minute, en mémoire
_history: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def check_rate_limit(client_id: str) -> None:
    now = time.monotonic()
    with _lock:
        history = _history[client_id]
        while history and now - history[0] > 60:
            history.popleft()
        if len(history) >= RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail="rate limit exceeded",
                headers={"Retry-After": "60"},
            )
        history.append(now)

# --- Routes -----------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest, client_id: str = Depends(verify_api_key)):
    check_rate_limit(client_id)  # M4
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