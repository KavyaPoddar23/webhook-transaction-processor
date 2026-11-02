import time
import logging
from datetime import datetime, timezone

from sqlalchemy import select, or_

from app.database import SessionLocal
from app.models import Transaction
from app.config import settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def utc_now():
    return datetime.now(timezone.utc)


def claim_transaction():
    """
    Atomically claim one pending transaction.
    SKIP LOCKED allows multiple workers to run safely.
    """

    with SessionLocal() as db:
        try:
            statement = (
                select(Transaction)
                .where(
                    Transaction.status == "pending",
                    or_(
                        Transaction.next_attempt_at.is_(None),
                        Transaction.next_attempt_at <= utc_now()
                    )
                )
                .order_by(Transaction.received_at)
                .limit(1)
                .with_for_update(skip_locked=True)
            )

            transaction = db.execute(statement).scalar_one_or_none()

            if transaction is None:
                return None

            transaction.status = "processing"
            transaction.attempts += 1
            transaction.processing_started_at = utc_now()
            transaction.updated_at = utc_now()

            db.commit()

            logger.info(
                "Claimed transaction: %s",
                transaction.transaction_id
            )

            return transaction.id

        except Exception:
            db.rollback()
            logger.exception("Failed to claim transaction")
            return None


def process_transaction(transaction_id):
    """
    Simulate an external API operation that takes 30 seconds.
    """

    with SessionLocal() as db:
        transaction = db.get(Transaction, transaction_id)

        if transaction is None:
            logger.error("Transaction record not found: %s", transaction_id)
            return

        try:
            logger.info(
                "Processing transaction: %s",
                transaction.transaction_id
            )

            time.sleep(settings.PROCESSING_DELAY_SECONDS)

            # Simulated successful external API response
            transaction.result = (
                f"Transaction {transaction.transaction_id} "
                f"processed successfully. "
                f"Amount: {transaction.amount} "
                f"{transaction.currency}."
            )

            transaction.status = "completed"
            transaction.processed_at = utc_now()
            transaction.updated_at = utc_now()
            transaction.error_message = None
            transaction.next_attempt_at = None

            db.commit()

            logger.info(
                "Completed transaction: %s",
                transaction.transaction_id
            )

        except Exception as error:
            db.rollback()

            logger.exception(
                "Processing failed for transaction: %s",
                transaction_id
            )

            transaction = db.get(Transaction, transaction_id)

            if transaction is None:
                return

            transaction.error_message = str(error)
            transaction.updated_at = utc_now()

            if transaction.attempts < transaction.max_attempts:
                transaction.status = "pending"
                transaction.next_attempt_at = utc_now()
                logger.info("Transaction queued for retry")
            else:
                transaction.status = "failed"
                transaction.processed_at = utc_now()
                logger.error("Maximum retry attempts reached")

            db.commit()

def recover_stale_transactions():
    """
    Requeue transactions that have been stuck in processing
    for more than 2 minutes.
    """

    from datetime import timedelta

    cutoff_time = utc_now() - timedelta(minutes=2)

    with SessionLocal() as db:
        try:
            stale_transactions = (
                db.query(Transaction)
                .filter(
                    Transaction.status == "processing",
                    Transaction.processing_started_at < cutoff_time
                )
                .all()
            )

            for transaction in stale_transactions:
                transaction.error_message = (
                    "Worker interrupted during processing. "
                    "Transaction recovered."
                )
                transaction.updated_at = utc_now()

                if transaction.attempts < transaction.max_attempts:
                    transaction.status = "pending"
                    transaction.next_attempt_at = utc_now()
                    logger.warning(
                        "Recovered transaction: %s",
                        transaction.transaction_id
                    )
                else:
                    transaction.status = "failed"
                    transaction.processed_at = utc_now()
                    logger.error(
                        "Transaction permanently failed: %s",
                        transaction.transaction_id
                    )

            db.commit()

        except Exception:
            db.rollback()
            logger.exception("Failed to recover stale transactions")

def run_worker():
    logger.info("Background worker started")

    last_recovery_check = 0

    while True:
        # Check for interrupted transactions periodically
        current_time = time.time()

        if current_time - last_recovery_check >= 30:
            recover_stale_transactions()
            last_recovery_check = current_time

        transaction_id = claim_transaction()

        if transaction_id is None:
            time.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
            continue

        process_transaction(transaction_id)


if __name__ == "__main__":
    try:
        run_worker()
    except KeyboardInterrupt:
        logger.info("Background worker stopped")