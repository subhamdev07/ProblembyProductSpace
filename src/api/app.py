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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
    if os.path.exists(frontend_dir):
        @app.get("/", include_in_schema=False)
        async def serve_index():
            return FileResponse(os.path.join(frontend_dir, "index.html"))

        @app.get("/login", include_in_schema=False)
        async def serve_login():
            return FileResponse(os.path.join(frontend_dir, "login.html"))

        @app.get("/teacher", include_in_schema=False)
        async def serve_teacher():
            return FileResponse(os.path.join(frontend_dir, "teacher.html"))

        @app.get("/index.css", include_in_schema=False)
        async def serve_index_css():
            return FileResponse(os.path.join(frontend_dir, "index.css"), media_type="text/css")

        @app.get("/index.js", include_in_schema=False)
        async def serve_index_js():
            return FileResponse(os.path.join(frontend_dir, "index.js"), media_type="application/javascript")

        @app.get("/teacher.css", include_in_schema=False)
        async def serve_teacher_css():
            return FileResponse(os.path.join(frontend_dir, "teacher.css"), media_type="text/css")

        @app.get("/teacher.js", include_in_schema=False)
        async def serve_teacher_js():
            return FileResponse(os.path.join(frontend_dir, "teacher.js"), media_type="application/javascript")

        student_routes = [
            "/dashboard",
            "/diagnostic",
            "/exam",
            "/board-exam",
            "/examination-hub",
            "/mastery",
            "/concept-graph",
            "/doubt-solver",
            "/practice",
            "/adaptive",
            "/remediation",
            "/revision",
            "/misconceptions",
        ]

        def create_student_handler():
            async def handler():
                return FileResponse(os.path.join(frontend_dir, "index.html"))
            return handler

        for r in student_routes:
            app.add_api_route(r, create_student_handler(), methods=["GET"], include_in_schema=False)

        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    return app


app = create_app()
