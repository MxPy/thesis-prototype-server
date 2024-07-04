from database import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = 'auth'
    id = Column(Integer, primary_key=True, index = True)
    username = Column(String)
    email = Column(String)
    password = Column(String)