from fastapi import FastAPI

app = FastAPI(title="Secure LLM Gateway")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}