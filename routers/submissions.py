from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.base import get_db
from database.models import Problem, Submission, User
from dependencies import require_user
from services.execution_service import judge

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


class SubmitRequest(BaseModel):
    problem_id: int
    code: str


@router.post("", status_code=201)
def submit(
    body: SubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    problem = db.query(Problem).filter(Problem.id == body.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    if not body.code.strip():
        raise HTTPException(status_code=400, detail="코드를 입력하세요.")

    # Run judge with ALL test cases (including hidden ones)
    outcome = judge(body.code, problem.test_cases, problem.time_limit)

    submission = Submission(
        problem_id=problem.id,
        user_id=current_user.id,
        code=body.code,
        status=outcome["status"],
        passed_count=outcome["passed_count"],
        total_count=outcome["total_count"],
        results=outcome["results"],
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return {
        "id": submission.id,
        "status": submission.status,
        "passed_count": submission.passed_count,
        "total_count": submission.total_count,
        "results": submission.results,
        "created_at": submission.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/{submission_id}")
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="제출을 찾을 수 없습니다.")
    if s.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    return {
        "id": s.id,
        "problem_id": s.problem_id,
        "problem_title": s.problem.title,
        "status": s.status,
        "passed_count": s.passed_count,
        "total_count": s.total_count,
        "results": s.results,
        "code": s.code,
        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("")
def my_submissions(
    problem_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    q = db.query(Submission).filter(Submission.user_id == current_user.id)
    if problem_id:
        q = q.filter(Submission.problem_id == problem_id)
    subs = q.order_by(Submission.created_at.desc()).limit(20).all()

    return [
        {
            "id": s.id,
            "problem_id": s.problem_id,
            "problem_title": s.problem.title,
            "status": s.status,
            "passed_count": s.passed_count,
            "total_count": s.total_count,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for s in subs
    ]
