"""
app/services/order_service.py

Purpose:
--------
Manage customer order operations.

Responsibilities:
-----------------
- Retrieve order status.
- Cancel eligible orders.
- Update delivery address.
- Estimate delivery information.
- Define transaction boundaries for order operations.

This service DOES NOT:
----------------------
- Execute SQL directly.
- Know ORM implementation details.
- Manage HTTP requests or responses.
- Know about agents, tools, or LangGraph.
- Contain presentation logic.

Architecture:
-------------
      Agent / API
            │
            ▼
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
- Business rules belong here.
- Persistence belongs in OrderRepository.
- Repository methods remain simple CRUD operations.
- The service owns commits and rollbacks.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.mappers.order_mapper import OrderMapper
from app.mappers.order_mapper import OrderMapper
from app.models.order import Order, OrderStatus
from app.repositories.order_repository import OrderRepository


class OrderService:
    """
    Business service for customer orders.
    """

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session
        self.repository = OrderRepository(session)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_order_status(
        self,
        order_id: str,
    ) -> Order | None:
        """
        Retrieve an order by ID.

        Returns
        -------
        Order | None
            The order if it exists.
        """
        return self.repository.get_order(order_id)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def cancel_order(
        self,
        order_id: str,
    ) -> Order | None:
        """
        Cancel an order.

        Business Rules
        --------------
        - Only pending or processing orders may be cancelled.
        - Delivered or shipped orders cannot be cancelled.

        Returns
        -------
        Order | None
            Updated order or None if not found.

        Raises
        ------
        ValueError
            If the order cannot be cancelled.
        """

        order = self.repository.get_order(order_id)

        if order is None:
            return None

        if order.status in (
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ):
            raise ValueError(
                f"Order '{order_id}' cannot be cancelled "
                f"because it is {order.status.value}."
            )

        self.repository.update_status(
            order,
            OrderStatus.CANCELLED,
        )

        order.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(order)

        return OrderMapper.to_summary(order) #type: ignore

    def update_delivery_address(
        self,
        order_id: str,
        new_address: str,
    ) -> Order | None:
        """
        Update an order's delivery address.

        Business Rules
        --------------
        - Cancelled orders cannot be modified.
        - Delivered orders cannot be modified.

        Returns
        -------
        Order | None
            Updated order or None if not found.

        Raises
        ------
        ValueError
            If the address cannot be changed.
        """

        order = self.repository.get_order(order_id)

        if order is None:
            return None

        if order.status in (
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ):
            raise ValueError(
                f"Delivery address cannot be updated "
                f"for a {order.status.value} order."
            )

        self.repository.update_address(
            order,
            new_address,
        )

        order.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(order)

        return OrderMapper.to_summary(order) #type: ignore

    # ------------------------------------------------------------------
    # Business Logic
    # ------------------------------------------------------------------

    def estimate_delivery_time(
        self,
        order_id: str,
    ) -> str | None:
        """
        Estimate delivery based on the current order status.

        This is intentionally simple and can later be replaced
        by courier tracking or logistics integration.

        Returns
        -------
        str | None
            Human-readable delivery estimate.
        """

        order = self.repository.get_order(order_id)

        if order is None:
            return None

        match order.status:

            case OrderStatus.PENDING:
                return (
                    "Your order is awaiting processing."
                )

            case OrderStatus.PROCESSING:
                return (
                    "Your order is being prepared for shipment."
                )

            case OrderStatus.SHIPPED:
                return (
                    "Your order is on the way and is expected "
                    "to arrive within 3–5 business days."
                )

            case OrderStatus.DELIVERED:
                return (
                    "Your order has already been delivered."
                )

            case OrderStatus.CANCELLED:
                return (
                    "This order has been cancelled."
                )

        return None