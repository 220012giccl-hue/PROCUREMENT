from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..config.settings import DATABASE_URL

# Setup Engine and Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Only import models here to ensure they are registered with Base
    from . import models
    Base.metadata.create_all(bind=engine)
