# Webhook Transaction Processor

An asynchronous, reliable, and idempotent webhook transaction processing system built using **Python, FastAPI, and PostgreSQL**.

The system accepts incoming webhooks and immediately acknowledges them with an HTTP `202 Accepted` response. Transactions are stored in PostgreSQL and processed asynchronously by a separate background worker, simulating a 30-second processing delay.

## GitHub Repository

[https://github.com/KavyaPoddar23/webhook-transaction-processor](https://github.com/KavyaPoddar23/webhook-transaction-processor)

## Features

- **Fast Webhook Acknowledgement:** Returns HTTP `202 Accepted` without waiting for transaction processing.
- **Asynchronous Processing:** Uses a separate background worker to process transactions independently of the API.
- **30-Second Processing Simulation:** Simulates delayed transaction processing to demonstrate asynchronous execution.
- **Idempotency:** Prevents duplicate transactions using a unique `transaction_id`.
- **PostgreSQL Persistence:** Stores transactions and their processing information in a PostgreSQL database.
- **Transaction Status Tracking:** Provides an API endpoint to retrieve transaction details and processing status.
- **Retry Mechanism:** Supports retrying failed transactions with configurable retry limits.
- **Stale Transaction Recovery:** Recovers transactions left in the processing state after unexpected worker interruptions.
- **Concurrent Request Handling:** Uses PostgreSQL conflict handling and row-level locking to support concurrent requests safely.
- **Automated Testing:** Includes tests for webhook responses, duplicate prevention, transaction status, validation, and concurrent requests.

## Tech Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Database | PostgreSQL |
| Database Hosting | Neon |
| ORM | SQLAlchemy |
| Database Driver | Psycopg 3 |
| Data Validation | Pydantic |
| API Testing | Pytest, HTTPX |
| API Documentation | Swagger UI |
| Deployment | Render (planned) |

## Architecture

The application uses a decoupled architecture with an API service and a separate worker process.

```text
                 Client
                   |
                   |
                   v
            FastAPI Webhook
                   |
                   v
          Validate Webhook Data
                   |
                   v
          Store Transaction
           in PostgreSQL
                   |
                   v
          HTTP 202 Accepted
                   |
                   |
          -------------------
                   |
                   v
          Background Worker
                   |
                   v
          Fetch Pending Jobs
                   |
                   v
          Simulate 30s Delay
                   |
                   v
          Update Transaction
                   |
                   v
          PostgreSQL Database
                   |
                   v
          Transaction Completed
```

### Processing Flow

1. A client sends a webhook request containing a transaction ID, amount, and currency.
2. FastAPI validates the incoming request.
3. The transaction is stored in PostgreSQL with a `pending` status.
4. The API immediately returns HTTP `202 Accepted`.
5. A separate worker polls the database for pending transactions.
6. The worker claims a transaction and updates its status to `processing`.
7. The worker simulates a 30-second processing delay.
8. Once processing succeeds, the transaction is marked as `completed`.
9. The client can retrieve the latest transaction status through the status API.

## Project Structure

```text
webhook-transaction-processor/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── config.py
│
├── worker/
│   ├── __init__.py
│   └── processor.py
│
├── tests/
│   ├── __init__.py
│   └── test_webhook.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── init_db.py
└── test_latency.py
```

## Prerequisites

Before running the project, make sure you have:

- Python 3.10 or higher
- PostgreSQL database or a Neon PostgreSQL database
- Git
- Visual Studio Code (recommended)

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/KavyaPoddar23/webhook-transaction-processor.git
```

Navigate to the project directory:

```bash
cd webhook-transaction-processor
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory.

Add the following configuration:

```env
DATABASE_URL=postgresql+psycopg://username:password@hostname/database_name?sslmode=require
PROCESSING_DELAY_SECONDS=30
WORKER_POLL_INTERVAL_SECONDS=2
MAX_RETRY_ATTEMPTS=3
```

Replace the database URL with your actual PostgreSQL connection string.

**Important:** Never commit your actual `.env` file or expose database credentials publicly.

### 5. Initialize the Database

Run:

```bash
python init_db.py
```

This creates the required database tables using SQLAlchemy.

## Running the Application

The API and worker must run as separate processes.

### 1. Start the FastAPI Server

Open the first terminal and execute:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 2. Open Swagger Documentation

Visit:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Swagger UI provides an interactive interface for testing the available API endpoints.

### 3. Start the Background Worker

Open a second terminal, activate the virtual environment, and run:

```bash
python -m worker.processor
```

The worker will continuously poll PostgreSQL for pending transactions and process them asynchronously.

## API Endpoints

### 1. Health Check

**Endpoint:**

```http
GET /
```

**Description:** Checks whether the API is running.

**Example Response:**

```json
{
  "message": "Webhook Transaction Processor API is running"
}
```

### 2. Receive Webhook

**Endpoint:**

```http
POST /webhook
```

**Description:** Accepts a transaction webhook, validates the payload, persists the transaction, and immediately acknowledges the request.

**Example Request:**

```json
{
  "transaction_id": "TXN-1001",
  "amount": 1500.50,
  "currency": "INR"
}
```

**Example Response:**

```json
{
  "message": "Webhook accepted for processing",
  "transaction_id": "TXN-1001",
  "status": "pending"
}
```

**HTTP Status Code:** `202 Accepted`

Duplicate requests with the same `transaction_id` do not create additional transaction records.

### 3. Get Transaction Status

**Endpoint:**

```http
GET /transactions/{transaction_id}
```

**Description:** Retrieves transaction details, processing status, timestamps, attempts, and the processing result.

**Example Request:**

```http
GET /transactions/TXN-1001
```

**Example Response:**

```json
{
  "transaction_id": "TXN-1001",
  "amount": "1500.50",
  "currency": "INR",
  "status": "completed",
  "attempts": 1,
  "received_at": "2026-11-02T10:00:00Z",
  "processing_started_at": "2026-11-02T10:00:02Z",
  "processed_at": "2026-11-02T10:00:32Z",
  "error_message": null,
  "result": "Transaction processed successfully"
}
```

The timestamps and result above are illustrative.

Possible transaction statuses:

| Status | Description |
|---|---|
| `pending` | Transaction has been accepted and is waiting for processing. |
| `processing` | Worker is currently processing the transaction. |
| `completed` | Transaction has been processed successfully. |
| `failed` | Transaction could not be processed after the configured retry limit. |

## Idempotency

The system uses `transaction_id` as a unique identifier for each transaction.

- The first webhook request creates a transaction record.
- Repeated requests with the same transaction ID do not create duplicate records.
- PostgreSQL's atomic `INSERT ... ON CONFLICT DO NOTHING` operation handles concurrent duplicate requests.
- The existing transaction status is returned when a duplicate request is received.

This ensures that retries from webhook clients do not result in duplicate transaction records.

## Reliability and Error Handling

The system includes several reliability mechanisms:

- Transactions are persisted before the API returns HTTP `202 Accepted`.
- The worker processes transactions independently of the API server.
- Failed processing attempts can be retried.
- Retry limits are configurable through environment variables.
- Transactions stuck in the `processing` state can be recovered after a worker interruption.
- PostgreSQL row-level locking with `SKIP LOCKED` helps prevent multiple workers from claiming the same pending transaction simultaneously.

## Testing

The project includes automated tests covering the main API and idempotency requirements.

Run the test suite:

```bash
pytest -v
```

The tests cover:

| Test | Purpose |
|---|---|
| Webhook acknowledgement | Verifies HTTP `202 Accepted`. |
| Duplicate webhook | Ensures duplicate requests create only one transaction. |
| Transaction status | Checks transaction retrieval. |
| Invalid webhook | Verifies request validation. |
| Missing transaction | Verifies HTTP `404 Not Found`. |
| Concurrent duplicate requests | Checks idempotency under concurrent requests. |

### Response Time Testing

Run:

```bash
python test_latency.py
```

This measures webhook response times and reports the HTTP status for each request.

The target webhook acknowledgement latency is **less than 500 milliseconds**. Local measurements can be affected by network and database region latency. The production SLA must be verified against the deployed API under realistic conditions.

## Configuration

The following environment variables control the application:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `PROCESSING_DELAY_SECONDS` | Simulated transaction processing delay | `30` |
| `WORKER_POLL_INTERVAL_SECONDS` | Time between worker polling cycles | `2` |
| `MAX_RETRY_ATTEMPTS` | Maximum processing attempts | `3` |

## Deployment

The intended deployment architecture uses two independent services sharing the same Neon PostgreSQL database.

**API Web Service**

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Background Worker Service**

```bash
pip install -r requirements.txt
```

Start command:

```bash
python -m worker.processor
```

Configure the same environment variables for both services.

The API service handles incoming webhook requests, while the worker handles transaction processing independently.

## Future Improvements

- Add authentication and webhook signature verification.
- Implement structured logging and monitoring.
- Add dead-letter queue support for permanently failed transactions.
- Introduce configurable worker concurrency.
- Add metrics for processing duration, queue depth, and failure rates.
- Add integration tests for worker recovery and retry behavior.
- Add production load testing and performance monitoring.

## Author

**Kavya Poddar**

- GitHub: [https://github.com/KavyaPoddar23](https://github.com/KavyaPoddar23)
- LinkedIn: [https://www.linkedin.com/in/kavyapoddar](https://www.linkedin.com/in/kavyapoddar)

---

*Built as a backend engineering assignment to demonstrate asynchronous processing, webhook reliability, idempotency, database persistence, and API performance.*