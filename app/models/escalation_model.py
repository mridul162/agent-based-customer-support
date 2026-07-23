"""
app/models/escalation_model.py

Purpose:
--------
SQLAlchemy ORM model for the escalations table.
Mirrors ticket_model.py in structure.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.schemas.escalation import EscalationQueue, EscalationStatus


class Escalation(Base):
    __tablename__ = "escalations"

    escalation_id: Mapped[str]               = mapped_column(String,                  primary_key=True)
    customer_id:   Mapped[str]               = mapped_column(String,                  nullable=False, index=True)
    reason:        Mapped[str]               = mapped_column(Text,                    nullable=False)
    queue:         Mapped[EscalationQueue]   = mapped_column(Enum(EscalationQueue),   nullable=False, default=EscalationQueue.GENERAL)
    status:        Mapped[EscalationStatus]  = mapped_column(Enum(EscalationStatus),  nullable=False, default=EscalationStatus.OPEN)
    created_at:    Mapped[datetime]          = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Escalation {self.escalation_id} queue={self.queue} status={self.status}>"