"""
app/database/connection.py

Purpose:
--------
Centralize SQLAlchemy database configuration and transaction management.

Responsibilities:
-----------------
- Read DATABASE_URL from application settings.
- Create the SQLAlchemy engine.
- Create SessionLocal for database sessions.
- Expose Base for ORM model registration.
- Provide get_session() for transaction-scoped session management.

This module DOES NOT:
---------------------
- Create tables (init_db.py owns that).
- Execute queries.
- Contain repository logic.
- Know about tickets, conversations, or agents.

Architecture:
-------------
    Settings
        ↓
    connection.py
        ↓
    engine / SessionLocal / Base / get_session
        ↓
    Repositories
        ↓
    Services
        ↓
    API / Graph Nodes

Transaction Ownership:
----------------------
Repositories should NOT call:

    session.commit()
    session.rollback()

Repositories are responsible only for:

    - queries
    - inserts
    - updates
    - deletes

Transaction boundaries are managed by get_session().

Example:
--------

    with get_session() as session:
        repo = TicketRepository(session)
        repo.create_ticket(...)
        repo.update_ticket(...)

    # commit automatically occurs on successful exit
    # rollback automatically occurs on exception
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.settings import settings


# ---------------------------------------------------------------------------
# SQLAlchemy Base
#
# All ORM models inherit from Base.
# Base.metadata is used by init_db.py to create tables.
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Engine
#
# SQLAlchemy connection pool and database engine.
# ---------------------------------------------------------------------------

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)


# ---------------------------------------------------------------------------
# Session Factory
#
# Creates new Session objects on demand.
#
# Example:
#
#     session = SessionLocal()
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Transaction-Scoped Session Context Manager
#
# Responsibilities:
#   - Create session
#   - Commit on success
#   - Rollback on failure
#   - Close session automatically
#
# Example:
#
#     with get_session() as session:
#         repo = TicketRepository(session)
#         repo.create_ticket(...)
# ---------------------------------------------------------------------------

from collections.abc import Generator
from sqlalchemy.orm import Session

@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()

    try:
        # print("SESSION OPEN")
        yield session
        # print("COMMITTING")
        session.commit()
        # print("COMMITTED")

    except Exception:
        # print("ROLLBACK")
        session.rollback()
        raise

    finally:
        # print("SESSION CLOSED")
        session.close()