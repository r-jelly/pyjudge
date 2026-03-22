from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database.base import Base, engine
from database.models import User, Problem, TestCase, Submission  # noqa: F401 – needed for metadata
from routers import auth, problems, submissions

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Python Online Judge", version="1.0.0")

# 서버리스 환경에서도 경로가 깨지지 않도록 절대 경로 사용
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# API routers
app.include_router(auth.router)
app.include_router(problems.router)
app.include_router(submissions.router)


# ---------- Page routes (return HTML) ----------

@app.get("/", response_class=HTMLResponse)
async def page_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/problems", response_class=HTMLResponse)
async def page_problems(request: Request):
    return templates.TemplateResponse("problems/list.html", {"request": request})


@app.get("/problems/create", response_class=HTMLResponse)
async def page_create_problem(request: Request):
    return templates.TemplateResponse("problems/create.html", {"request": request})


@app.get("/problems/{problem_id}", response_class=HTMLResponse)
async def page_problem_detail(request: Request, problem_id: int):
    return templates.TemplateResponse("problems/detail.html", {"request": request, "problem_id": problem_id})


@app.get("/submissions/{submission_id}", response_class=HTMLResponse)
async def page_submission_result(request: Request, submission_id: int):
    return templates.TemplateResponse("submissions/result.html", {"request": request, "submission_id": submission_id})


@app.get("/login", response_class=HTMLResponse)
async def page_login(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def page_register(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})
