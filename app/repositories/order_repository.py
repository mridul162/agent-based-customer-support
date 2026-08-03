"""
app/repositories/order_repository.py

Purpose:
--------
Repository responsible for all Order persistence operations.

Responsibilities:
-----------------
- Retrieve customer orders.
- Retrieve individual orders.
- Update order status.
- Update delivery address.
- Encapsulate all SQLAlchemy queries.

This repository DOES NOT:
--------------------------
- Apply business rules.
- Validate cancellation policies.
- Decide whether an order can be modified.
- Manage commits or rollbacks.
- Know anything about agents or tools.

Architecture:
-------------
         OrderService
               │
               ▼
       OrderRepository
               │
               ▼
          SQLAlchemy ORM
               │
               ▼
          PostgreSQL

Design Notes:
-------------
- This is the single persistence layer for Order entities.
- Services own business decisions.
- Repository methods should be small, predictable, and database-focused.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus


class OrderRepository:
    """
    Persistence layer for Order entities.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_order(
        self,
        order_id: str,
    ) -> Order | None:
        """
        Retrieve a single order by its ID.
        """
        return self.session.get(Order, order_id)

    def list_orders(
        self,
        customer_id: str,
    ) -> list[Order]:
        """
        Retrieve all orders belonging to a customer.

        Orders are returned newest first.
        """
        statement = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
        )

        return list(self.session.scalars(statement).all())

    def update_status(
        self,
        order: Order,
        status: OrderStatus,
    ) -> Order:
        """
        Update the status of an order.

        The caller is responsible for committing the transaction.
        """
        order.status = status
        self.session.add(order)

        return order

    def update_address(
        self,
        order: Order,
        address: str,
    ) -> Order:
        """
        Update the delivery address for an order.

        The caller is responsible for committing the transaction.
        """
        order.delivery_address = address
        self.session.add(order)

        return order
