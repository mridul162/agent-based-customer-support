"""
app/database/init_db.py

Purpose:
--------
Create all database tables defined in ORM models.

Run once on startup or during development setup:
    python -m app.database.init_db

In production this is replaced by Alembic migrations.
For Milestone 11, direct table creation is sufficient.
"""

from app.database.connection import Base, engine

# Import all models so their table definitions are registered with Base.metadata.
# If a model is not imported here, its table will not be created.
from app.models.conversation_message_model import ConversationMessageDB  # noqa: F401
from app.models.ticket_model import Ticket  # noqa: F401


def init_db() -> None:
    """Create all tables. Safe to call repeatedly — skips existing tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    init_db()