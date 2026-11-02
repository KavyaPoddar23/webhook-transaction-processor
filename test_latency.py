import time
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Transaction


transaction_ids = []


def send_request(client, transaction_id):
    payload = {
        "transaction_id": transaction_id,
        "amount": 1500.50,
        "currency": "INR"
    }

    start = time.perf_counter()

    response = client.post("/webhook", json=payload)

    elapsed = time.perf_counter() - start

    print(
        f"{transaction_id}: "
        f"HTTP {response.status_code}, "
        f"{elapsed:.4f} seconds"
    )

    return response


try:
    with TestClient(app) as client:

        # First request warms up the database connection
        warmup_id = f"WARMUP-{uuid.uuid4().hex[:8]}"
        transaction_ids.append(warmup_id)

        print("\n--- Initial connection / warm-up ---")
        send_request(client, warmup_id)

        # Measure five subsequent requests
        print("\n--- Actual response-time measurements ---")

        for i in range(1, 6):
            transaction_id = f"LATENCY-{uuid.uuid4().hex[:8]}"
            transaction_ids.append(transaction_id)

            response = send_request(client, transaction_id)

            assert response.status_code == 202

finally:
    # Clean up test transactions
    with SessionLocal() as db:
        db.query(Transaction).filter(
            Transaction.transaction_id.in_(transaction_ids)
        ).delete(synchronize_session=False)

        db.commit()

    print("\nTest transactions cleaned up.")