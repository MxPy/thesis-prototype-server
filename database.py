import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import sqlalchemy.ext.declarative as _declarative

#TODO: put it into .env moron
DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost/users"

engine = _sql.create_engine(DATABASE_URL)


SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = _declarative.declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()