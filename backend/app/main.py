from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.scans import router as scans_router

app = FastAPI(title="loom", version="0.1.0")

# Phase 0: wide open for local dev (Vite on 5173/5180 talking to uvicorn on
# 8000). Tighten to the real deployed frontend origin once Phase 3 deploys
# (SPEC.md §12).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scans_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
