from utils.constants import DB_DIR, SQL_TYPE
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session

Base = declarative_base()
engine = create_engine(SQL_TYPE + DB_DIR + 'mydb.db', echo=False, future=True)
session = Session(engine)