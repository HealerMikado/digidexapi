import os

import boto3
import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

if not os.getenv("DB_USER"):
    load_dotenv()

db_user = os.getenv("DB_USER")
db_url = os.getenv("DB_ENPOINT")
db_password = os.getenv("DB_PASSWORD")

client = boto3.client("rds")
auth_token = client.generate_db_auth_token(
    DBHostname=db_url, Port=5432, DBUsername=db_user, Region="eu-west-3"
)
try:
    SQLALCHEMY_DATABASE_URL = sqlalchemy.engine.url.URL.create(
        drivername="postgresql+psycopg2",
        username=db_user,
        password=auth_token,
        host=db_url,
        port=5432,
        database="postgres",
    )

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=True,
        connect_args={"sslmode": "verify-full", "sslrootcert": "eu-west-3-bundle.pem"},
    )
except Exception as e:
    print("Database connection failed due to {}".format(e))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
