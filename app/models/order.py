"""
app/models/order.py

Purpose:
--------
SQLAlchemy model representing a customer's order.

Responsibilities:
-----------------
- Persist order information.
- Represent the canonical Order entity.
- Define database constraints and relationships.
- Serve as the persistence model for order operations.

This model DOES NOT:
--------------------
- Contain business logic.
- Perform database queries.
- Validate business rules.
- Manage transactions.
- Execute workflow decisions.

Architecture:
-------------
          API / Agent
                │
                ▼
         OrderService
                │
                ▼
        OrderRepository
                │
                ▼
             Order Model
                │
                ▼
           PostgreSQL

Design Notes:
-------------
- Represents a single customer order.
- Business rules belong in OrderService.
- Database access belongs in OrderRepository.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class OrderStatus(str, Enum):
    """
    Valid lifecycle states for an order.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    """
    SQLAlchemy persistence model for customer orders.
    """

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    customer_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
    )

    total_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    delivery_address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )