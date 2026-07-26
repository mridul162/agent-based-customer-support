from app.models.order import Order
from app.schemas.order_summary import OrderSummary


class OrderMapper:

    @staticmethod
    def to_summary(order: Order) -> OrderSummary:
        return OrderSummary(
            order_id=order.order_id,
            customer_id=order.customer_id,
            status=order.status,
            total_amount=order.total_amount,
            delivery_address=order.delivery_address,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )