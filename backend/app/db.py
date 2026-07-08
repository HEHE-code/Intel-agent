"""SQLAlchemy 引擎与会话。"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()
settings.db_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.sqlite_url,
    connect_args={"check_same_thread": False},  # SQLite 多线程（FastAPI 需要）
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    """提供事务作用域的会话上下文。"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
