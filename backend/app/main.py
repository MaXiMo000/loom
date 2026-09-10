from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.routes.scans import router as scans_router

app = FastAPI(title="loom", version="0.1.0")

# Phase 0 default (`*`) was wide open for local dev (Vite talking to
# uvicorn on a different port). Phase 3 (SPEC.md §12): set LOOM_ALLOWED_ORIGIN
# to the real deployed static site's origin in production — no scan data is
# sensitive, but an open API still shouldn't take requests from arbitrary
# origins by default once there's a real one to restrict to.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scans_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
