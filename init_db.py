from app.database import engine, Base
from app.models import Transaction


def initialize_database():

    print("Connecting to PostgreSQL...")

    # Create all tables defined in our models
    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")


if __name__ == "__main__":
    initialize_database()