import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 로컬: SQLite / 프로덕션: Supabase PostgreSQL (DATABASE_URL 환경변수)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./judge.db")

# 일부 서비스는 postgres:// 형태로 제공 — SQLAlchemy 2.x는 postgresql:// 필요
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Supabase Transaction mode URL에 붙는 ?pgbouncer=true 파라미터 제거
# (SQLAlchemy가 인식하지 못해 오류 발생)
if "pgbouncer=true" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Supabase Connection Pooling (Transaction mode) 대응:
    # - pool_pre_ping: 서버리스 cold start 후 끊긴 커넥션 자동 감지
    # - pool_size=1 / max_overflow=0: 서버리스 환경에서 커넥션 최소화
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
