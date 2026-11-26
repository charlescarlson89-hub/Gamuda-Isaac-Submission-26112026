import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


# Read the .env file beside this Python file.
load_dotenv(Path(__file__).with_name(".env"))

# Build the database connection address.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)

# Prepare the database connection manager.
engine = create_engine(
    DATABASE_URL,
    connect_args={"connect_timeout": 5},
)

# Prepare database sessions for our future API requests.
SessionLocal = sessionmaker(bind=engine, autoflush=False)

# Our future table definitions will use this Base.
Base = declarative_base()


# Run a connection test when this file is executed directly.
if __name__ == "__main__":
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("Connected to PostgreSQL successfully!")