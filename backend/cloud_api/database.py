from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cloud_api.models import Base

DATABASE_URL = "postgresql://metricsdb_yqja_user:entPz514UvRf9JX3KneevRRy2xpktl9v@dpg-ctf0alt2ng1s738fois0-a.oregon-postgres.render.com/metricsdb_yqja"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize the database and create all tables."""
    Base.metadata.create_all(engine)
    print("Database initialized successfully.")
    