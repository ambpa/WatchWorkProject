# edge_collector/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg2://watchwork:watchwork@localhost:5432/watchwork"

# motore sincrono SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)

# sessione
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)