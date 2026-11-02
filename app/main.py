from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.database import get_db
from app.models import Transaction
from app.schemas import (
    WebhookRequest,
    WebhookResponse,
    TransactionResponse
)


app = FastAPI(
    title="Webhook Transaction Processor",
    description="Asynchronous and idempotent webhook processing system",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Webhook Transaction Processor API is running"
    }


@app.post(
    "/webhook",
    response_model=WebhookResponse,
    status_code=status.HTTP_202_ACCEPTED
)
def receive_webhook(
    payload: WebhookRequest,
    db: Session = Depends(get_db)
):
    try:
        # Insert only if the transaction ID does not already exist.
        # PostgreSQL handles concurrent duplicate requests atomically.
        statement = (
            insert(Transaction)
            .values(
                transaction_id=payload.transaction_id,
                amount=payload.amount,
                currency=payload.currency.upper(),
                status="pending"
            )
            .on_conflict_do_nothing(
                index_elements=[Transaction.transaction_id]
            )
            .returning(
                Transaction.transaction_id,
                Transaction.status
            )
        )

        result = db.execute(statement).first()

        if result:
            db.commit()

            return WebhookResponse(
                message="Webhook accepted for processing",
                transaction_id=result.transaction_id,
                status=result.status
            )

        # A duplicate was received. Retrieve its existing status.
        existing_status = (
            db.query(Transaction.status)
            .filter(
                Transaction.transaction_id == payload.transaction_id
            )
            .scalar()
        )

        db.commit()

        return WebhookResponse(
            message="Transaction already received",
            transaction_id=payload.transaction_id,
            status=existing_status or "pending"
        )

    except Exception:
        db.rollback()
        raise


@app.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse
)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.transaction_id == transaction_id
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction