import os
import ssl
from pathlib import Path
from contextlib import asynccontextmanager

# Corporate SSL bypass
ssl._create_default_https_context = ssl._create_unverified_context
os.environ.setdefault("CURL_CA_BUNDLE", "")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db
from routers import user, tts, practice, diagnostic

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    yield

app = FastAPI(title="Accent Trainer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(user.router)
app.include_router(tts.router)
app.include_router(practice.router)
app.include_router(diagnostic.router)

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve main app
@app.get("/")
def serve_app():
    # Check for new static/index.html first, fall back to legacy app.html
    new_index = Path(__file__).parent / "static" / "index.html"
    legacy_index = Path(__file__).parent / "app.html"

    if new_index.exists():
        return FileResponse(new_index)
    elif legacy_index.exists():
        return FileResponse(legacy_index)
    else:
        return {"message": "Accent Trainer API", "docs": "/docs"}

@app.get("/diagnostic")
def serve_diagnostic():
    return FileResponse(Path(__file__).parent / "static" / "diagnostic.html")

@app.get("/profile")
def serve_profile():
    return FileResponse(Path(__file__).parent / "static" / "profile.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8001, reload=True)
