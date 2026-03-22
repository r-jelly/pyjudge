from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer, String, Text, Boolean, Float, DateTime,
    ForeignKey, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    problems: Mapped[list["Problem"]] = relationship("Problem", back_populates="author")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="user")


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")  # easy / medium / hard
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    time_limit: Mapped[int] = mapped_column(Integer, default=5)  # seconds

    author: Mapped["User"] = relationship("User", back_populates="problems")
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="problem", order_by="TestCase.order_index"
    )
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="problem")


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id"))
    stdin: Mapped[Optional[str]] = mapped_column(Text, default="")
    expected_stdout: Mapped[str] = mapped_column(Text, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    problem: Mapped["Problem"] = relationship("Problem", back_populates="test_cases")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # accepted / wrong_answer / time_limit_exceeded / runtime_error
    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    results: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    problem: Mapped["Problem"] = relationship("Problem", back_populates="submissions")
    user: Mapped["User"] = relationship("User", back_populates="submissions")
