"""
app/tools/order_tools.py

Purpose:
--------
Application tools for customer order operations.

Responsibilities:
-----------------
- Retrieve order status.
- Cancel customer orders.
- Update delivery addresses.

These tools are intentionally thin wrappers around OrderService.

This module DOES NOT:
---------------------
- Implement business rules.
- Execute SQL.
- Manage transactions.
- Format customer-facing responses.
- Know about LangGraph nodes.

Architecture:
-------------
Agent
   │
   ▼
Order Tool
   │
   ▼
OrderService
   │
   ▼
OrderRepository
   │
   ▼
PostgreSQL

Design Notes:
-------------
- One tool represents one business capability.
- Services own business logic.
- Tools remain orchestration-free.
"""

from __future__ import annotations

from app.database.connection import SessionLocal
from app.schemas.order_summary import OrderSummary
from app.services.order_service import OrderService


def get_order_status_tool(
    order_id: str,
) -> OrderSummary | None:
    """
    Retrieve a customer's order.
    """

    with SessionLocal() as session:
        service = OrderService(session)

        return service.get_order_status(
            order_id=order_id,
        )  # type: ignore


def cancel_order_tool(
    order_id: str,
) -> OrderSummary | None:
    """
    Cancel an existing order.

    Business rules are enforced by OrderService.
    """

    with SessionLocal() as session:
        service = OrderService(session)

        return service.cancel_order(
            order_id=order_id,
        )  # type: ignore


def update_delivery_address_tool(
    order_id: str,
    new_address: str,
) -> OrderSummary | None:
    """
    Update a customer's delivery address.

    Business rules are enforced by OrderService.
    """

    with SessionLocal() as session:
        service = OrderService(session)

        return service.update_delivery_address(
            order_id=order_id,
            new_address=new_address,
        )  # type: ignore


def estimate_delivery_time_tool(
    order_id: str,
) -> OrderSummary | None:
    """
    Estimate the delivery time for a customer's order.

    Business rules are enforced by OrderService.
    """

    with SessionLocal() as session:
        service = OrderService(session)

        return service.estimate_delivery_time(
            order_id=order_id,
        )  # type: ignore
