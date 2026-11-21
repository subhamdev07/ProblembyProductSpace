import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

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
    no_cache_headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    if os.path.exists(frontend_dir):
        @app.get("/login", include_in_schema=False)
        async def serve_login(request: Request):
            if request.query_params.get("logout") == "1":
                resp = FileResponse(os.path.join(frontend_dir, "login.html"), headers=no_cache_headers)
                resp.delete_cookie("bodhai_role", path="/")
                resp.delete_cookie("bodhai_user_id", path="/")
                resp.delete_cookie("bodhai_token", path="/")
                return resp
            role = request.cookies.get("bodhai_role", "")
            uid = request.cookies.get("bodhai_user_id", "")
            if role == "teacher" or uid.upper().startswith("TCH"):
                return RedirectResponse(url="/teacher", status_code=307)
            elif role == "student" or uid.upper().startswith("STU"):
                return RedirectResponse(url="/dashboard", status_code=307)
            return FileResponse(os.path.join(frontend_dir, "login.html"), headers=no_cache_headers)

        @app.get("/teacher", include_in_schema=False)
        async def serve_teacher(request: Request):
            role = request.cookies.get("bodhai_role", "")
            uid = request.cookies.get("bodhai_user_id", "")
            if role == "student" or (uid and not uid.upper().startswith("TCH")):
                return RedirectResponse(url="/dashboard", status_code=307)
            return FileResponse(os.path.join(frontend_dir, "teacher.html"), headers=no_cache_headers)

        @app.get("/index.css", include_in_schema=False)
        async def serve_index_css():
            return FileResponse(os.path.join(frontend_dir, "index.css"), media_type="text/css")

        @app.get("/index.js", include_in_schema=False)
        async def serve_index_js():
            return FileResponse(os.path.join(frontend_dir, "index.js"), media_type="application/javascript", headers=no_cache_headers)

        @app.get("/teacher.css", include_in_schema=False)
        async def serve_teacher_css():
            return FileResponse(os.path.join(frontend_dir, "teacher.css"), media_type="text/css")

        @app.get("/teacher.js", include_in_schema=False)
        async def serve_teacher_js():
            return FileResponse(os.path.join(frontend_dir, "teacher.js"), media_type="application/javascript", headers=no_cache_headers)

        student_routes = [
            "/",
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
            async def handler(request: Request):
                role = request.cookies.get("bodhai_role", "")
                uid = request.cookies.get("bodhai_user_id", "")
                if role == "teacher" or uid.upper().startswith("TCH"):
                    return RedirectResponse(url="/teacher", status_code=307)
                return FileResponse(os.path.join(frontend_dir, "index.html"), headers=no_cache_headers)
            return handler

        for r in student_routes:
            app.add_api_route(r, create_student_handler(), methods=["GET"], include_in_schema=False)

        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    return app


app = create_app()
