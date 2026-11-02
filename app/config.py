import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    PROCESSING_DELAY_SECONDS: int = int(
        os.getenv("PROCESSING_DELAY_SECONDS", "30")
    )

    WORKER_POLL_INTERVAL_SECONDS: int = int(
        os.getenv("WORKER_POLL_INTERVAL_SECONDS", "2")
    )

    MAX_RETRY_ATTEMPTS: int = int(
        os.getenv("MAX_RETRY_ATTEMPTS", "3")
    )


settings = Settings()