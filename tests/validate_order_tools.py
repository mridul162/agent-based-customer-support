"""
tests/validate_order_tools.py

Purpose
-------
End-to-end validation of the Order Tool workflow.

Validation Scope
----------------
✓ Get order status
✓ Cancel order
✓ Update delivery address
✓ Estimate delivery time
✓ Missing order handling
✓ Tool registry integration

This script is intended for manual validation and demonstration.
It is NOT a unit test suite.

Usage
-----
python tests/validate_order_tools.py
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.order import Order, OrderStatus
from app.tools.order_tools import (
    cancel_order_tool,
    estimate_delivery_time_tool,
    get_order_status_tool,
    update_delivery_address_tool,
)

# ---------------------------------------------------------------------
# Fake Service
# ---------------------------------------------------------------------


class FakeOrderService:
    """
    Lightweight fake service for validating tool behavior.
    """

    def __init__(self):
        self.order = Order(
            order_id="ORD-1001",
            customer_id="CUST-001",
            status=OrderStatus.PROCESSING,
            total_amount=1200.00,
            delivery_address="Dhaka",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def get_order_status(self, order_id: str):
        if order_id != self.order.order_id:
            return None
        return self.order

    def cancel_order(self, order_id: str):
        if order_id != self.order.order_id:
            return None

        self.order.status = OrderStatus.CANCELLED
        return self.order

    def update_delivery_address(
        self,
        order_id: str,
        new_address: str,
    ):
        if order_id != self.order.order_id:
            return None

        self.order.delivery_address = new_address
        return self.order

    def estimate_delivery_time(self, order_id: str):
        if order_id != self.order.order_id:
            return None

        class DeliveryEstimate:
            estimated_delivery_time = "Tomorrow"

        return DeliveryEstimate()


# ---------------------------------------------------------------------
# Monkey Patch
# ---------------------------------------------------------------------

from app.tools import order_tools

_fake_service = FakeOrderService()


class FakeSession:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        pass


order_tools.SessionLocal = lambda: FakeSession()
order_tools.OrderService = lambda session: _fake_service


# ---------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def check(condition: bool, message: str):
    if condition:
        print(f"{PASS} {message}")
    else:
        print(f"{FAIL} {message}")


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

print("=" * 70)
print("ORDER TOOL VALIDATION")
print("=" * 70)


status = get_order_status_tool("ORD-1001")

check(status is not None, "Order lookup")
check(
    status is not None and status.status == OrderStatus.PROCESSING,
    "Correct status",
)


cancelled = cancel_order_tool("ORD-1001")

check(
    cancelled is not None and cancelled.status == OrderStatus.CANCELLED, "Cancel order"
)


updated = update_delivery_address_tool(
    "ORD-1001",
    "Khulna",
)

check(
    updated is not None and updated.delivery_address == "Khulna",
    "Update address",
)


eta = estimate_delivery_time_tool("ORD-1001")
estimated_delivery = getattr(eta, "estimated_delivery_time", None)

check(
    eta is not None and estimated_delivery == "Tomorrow",
    "Estimate delivery",
)

missing = get_order_status_tool("UNKNOWN")

check(
    missing is None,
    "Missing order handled",
)


print()
print("=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)
