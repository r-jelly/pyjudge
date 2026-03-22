from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.base import get_db
from database.models import Problem, TestCase, Submission, User
from dependencies import get_current_user, require_user

router = APIRouter(prefix="/api/problems", tags=["problems"])


# ---------- Pydantic schemas ----------

class TestCaseIn(BaseModel):
    stdin: str = ""
    expected_stdout: str
    is_sample: bool = False
    order_index: int = 0


class ProblemCreate(BaseModel):
    title: str
    description: str
    difficulty: str = "medium"
    time_limit: int = 5
    test_cases: list[TestCaseIn]


class TestCaseOut(BaseModel):
    id: int
    stdin: Optional[str]
    expected_stdout: str
    is_sample: bool
    order_index: int

    model_config = {"from_attributes": True}


class ProblemListItem(BaseModel):
    id: int
    title: str
    difficulty: str
    author_username: str
    submission_count: int
    acceptance_rate: float
    created_at: str


class ProblemDetail(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    time_limit: int
    author_username: str
    sample_test_cases: list[TestCaseOut]
    submission_count: int
    acceptance_rate: float
    created_at: str


# ---------- Helpers ----------

def _acceptance_rate(problem_id: int, db: Session) -> tuple[int, float]:
    total = db.query(Submission).filter(Submission.problem_id == problem_id).count()
    if total == 0:
        return 0, 0.0
    accepted = (
        db.query(Submission)
        .filter(Submission.problem_id == problem_id, Submission.status == "accepted")
        .count()
    )
    return total, round(accepted / total * 100, 1)


# ---------- Routes ----------

@router.get("", response_model=list[ProblemListItem])
def list_problems(
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Problem)
    if difficulty:
        q = q.filter(Problem.difficulty == difficulty)
    problems = q.order_by(Problem.created_at.desc()).all()

    result = []
    for p in problems:
        total, rate = _acceptance_rate(p.id, db)
        result.append(ProblemListItem(
            id=p.id,
            title=p.title,
            difficulty=p.difficulty,
            author_username=p.author.username,
            submission_count=total,
            acceptance_rate=rate,
            created_at=p.created_at.strftime("%Y-%m-%d"),
        ))
    return result


@router.get("/{problem_id}", response_model=ProblemDetail)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    p = db.query(Problem).filter(Problem.id == problem_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

    total, rate = _acceptance_rate(p.id, db)
    sample_cases = [tc for tc in p.test_cases if tc.is_sample]

    return ProblemDetail(
        id=p.id,
        title=p.title,
        description=p.description,
        difficulty=p.difficulty,
        time_limit=p.time_limit,
        author_username=p.author.username,
        sample_test_cases=[TestCaseOut.model_validate(tc) for tc in sample_cases],
        submission_count=total,
        acceptance_rate=rate,
        created_at=p.created_at.strftime("%Y-%m-%d"),
    )


@router.post("", status_code=201)
def create_problem(
    body: ProblemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if not body.title.strip():
        raise HTTPException(status_code=400, detail="제목을 입력하세요.")
    if not body.test_cases:
        raise HTTPException(status_code=400, detail="테스트 케이스를 최소 1개 이상 추가하세요.")
    if body.difficulty not in ("easy", "medium", "hard"):
        raise HTTPException(status_code=400, detail="난이도 값이 올바르지 않습니다.")

    problem = Problem(
        title=body.title.strip(),
        description=body.description.strip(),
        difficulty=body.difficulty,
        time_limit=body.time_limit,
        author_id=current_user.id,
    )
    db.add(problem)
    db.flush()  # get problem.id before inserting test cases

    for tc in body.test_cases:
        db.add(TestCase(
            problem_id=problem.id,
            stdin=tc.stdin,
            expected_stdout=tc.expected_stdout,
            is_sample=tc.is_sample,
            order_index=tc.order_index,
        ))

    db.commit()
    return {"id": problem.id}


@router.delete("/{problem_id}", status_code=204)
def delete_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    p = db.query(Problem).filter(Problem.id == problem_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    if p.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
    db.delete(p)
    db.commit()
