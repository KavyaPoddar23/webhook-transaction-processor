from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime


class WebhookRequest(BaseModel):
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=12,
        decimal_places=2
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=10
    )


class WebhookResponse(BaseModel):
    message: str
    transaction_id: str
    status: str


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    amount: Decimal
    currency: str
    status: str
    attempts: int
    received_at: datetime
    processing_started_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[str] = None