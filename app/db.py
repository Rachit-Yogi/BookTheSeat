import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./booktheseat.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
# Vercel serverless functions should use Supabase transaction pooling (port 6543)
# with NullPool so each invocation does not retain database connections.
engine_options = {"future": True, "pool_pre_ping": True, "connect_args": connect_args}
if os.getenv("VERCEL") == "1":
    engine_options["poolclass"] = NullPool
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

@contextmanager
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
