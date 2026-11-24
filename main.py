"""
Main FastAPI Application Entrypoint.
Initializes SQLite database, registers API routes, and serves the CAD Web Interface.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from contextlib import asynccontextmanager

from app.api import router as api_router
from app.database import init_db

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and seed initial engineering templates
    init_db()
    yield


app = FastAPI(
    title="Parametric Overhead Crane Drawing Generator",
    description="Engineering R&D Tool for Overhead (EOT) Cranes by Modern Crane Co.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for flexible integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(api_router)

# Mount static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Parametric Crane Generator API is running. Access /docs for API documentation."}
