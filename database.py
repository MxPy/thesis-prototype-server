import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import sqlalchemy.ext.declarative as _declarative
import motor.motor_asyncio
from pymongo import ReturnDocument

#TODO: put it into .env moron
DATABASE_URL = "postgresql://postgres:mysecretpassword@db/users"


engine = _sql.create_engine(DATABASE_URL)
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://Username:Password@mongo/sessions?retryWrites=true&w=majority")

SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = _declarative.declarative_base()

def get_sql_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_no_sql_db():
    db = client.sessions
    sessions_collection = db.get_collection("sessions")
    try:
        yield sessions_collection
    finally:
        pass