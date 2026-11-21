"""
BodhAI FastAPI Application Factory
Initializes FastAPI, mounts API routers, configures CORS,
and serves the Filko-inspired frontend application.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="BodhAI — Adaptive Exam-Prep Tutor",
        description="CBSE Class 10 Science (2026-27) Integrated Diagnostic Assessment & Learner Model",
        version="3.0.0",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include REST API router
    app.include_router(api_router)

    # Frontend Static Files Serving
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
    if os.path.exists(frontend_dir):
        # Serve index.html at root
        @app.get("/", include_in_schema=False)
        async def serve_index():
            index_path = os.path.join(frontend_dir, "index.html")
            return FileResponse(index_path)

        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    return app


app = create_app()
