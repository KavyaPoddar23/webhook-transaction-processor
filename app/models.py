from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Text,
    Index,
)

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Transaction(Base):

    __tablename__ = "transactions"

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Unique transaction identifier
    transaction_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # Transaction details
    amount = Column(
        Numeric(12, 2),
        nullable=False
    )

    currency = Column(
        String(10),
        nullable=False
    )

    # Processing status
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )

    # Number of processing attempts
    attempts = Column(
        Integer,
        nullable=False,
        default=0
    )

    # Maximum retry attempts
    max_attempts = Column(
        Integer,
        nullable=False,
        default=3
    )

    # Timing information
    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    processing_started_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    processed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now
    )

    # Retry scheduling
    next_attempt_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Error information
    error_message = Column(
        Text,
        nullable=True
    )
    
    result = Column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<Transaction "
            f"id={self.id} "
            f"transaction_id={self.transaction_id} "
            f"status={self.status}>"
        )


# Index to help the worker find pending jobs efficiently
Index(
    "ix_transactions_status_received",
    Transaction.status,
    Transaction.received_at
)