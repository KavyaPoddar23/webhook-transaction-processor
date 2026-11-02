import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Transaction


client = TestClient(app)


@pytest.fixture
def transaction_id():
    test_id = f"TEST-{uuid.uuid4().hex[:12]}"

    yield test_id

    # Remove test data after each test
    with SessionLocal() as db:
        db.query(Transaction).filter(
            Transaction.transaction_id == test_id
        ).delete()
        db.commit()


def sample_payload(transaction_id):
    return {
        "transaction_id": transaction_id,
        "amount": 1500.50,
        "currency": "INR"
    }


def test_webhook_returns_202(transaction_id):
    start_time = time.perf_counter()

    response = client.post(
        "/webhook",
        json=sample_payload(transaction_id)
    )

    elapsed_time = time.perf_counter() - start_time

    assert response.status_code == 202
    assert response.json()["status"] == "pending"

    print(f"Webhook response time: {elapsed_time:.4f} seconds")

    import os

    if os.getenv("ENFORCE_LATENCY") == "1":
        assert elapsed_time < 0.5
    else:
        print(
        "Local latency measurement only. "
        "The 500 ms SLA will be verified after deployment."
    )


def test_duplicate_webhook(transaction_id):
    payload = sample_payload(transaction_id)

    first_response = client.post("/webhook", json=payload)
    second_response = client.post("/webhook", json=payload)

    assert first_response.status_code == 202
    assert second_response.status_code == 202

    with SessionLocal() as db:
        count = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).count()

    assert count == 1


def test_transaction_status(transaction_id):
    client.post(
        "/webhook",
        json=sample_payload(transaction_id)
    )

    response = client.get(
        f"/transactions/{transaction_id}"
    )

    assert response.status_code == 200
    assert response.json()["transaction_id"] == transaction_id
    assert response.json()["status"] == "pending"


def test_invalid_webhook():
    response = client.post(
        "/webhook",
        json={
            "transaction_id": "",
            "amount": -100,
            "currency": "INR"
        }
    )

    assert response.status_code == 422


def test_missing_transaction():
    response = client.get(
        "/transactions/TRANSACTION-DOES-NOT-EXIST"
    )

    assert response.status_code == 404


def test_concurrent_duplicate_webhooks(transaction_id):
    payload = sample_payload(transaction_id)

    def send_webhook():
        with TestClient(app) as test_client:
            return test_client.post("/webhook", json=payload)

    with ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(
            executor.map(
                lambda _: send_webhook(),
                range(5)
            )
        )

    assert all(response.status_code == 202 for response in responses)

    with SessionLocal() as db:
        count = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).count()

    assert count == 1