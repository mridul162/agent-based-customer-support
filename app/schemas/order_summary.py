from datetime import datetime

from pydantic import BaseModel

from app.models.order import OrderStatus


class OrderSummary(BaseModel):
    order_id: str
    customer_id: str
    status: OrderStatus
    total_amount: float
    delivery_address: str
    created_at: datetime
    updated_at: datetime
