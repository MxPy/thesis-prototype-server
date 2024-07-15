from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    password: str

    class Config:
        orm_mode=True

class UserLogin(BaseModel):
    username: str 
    password: str 
    class Config:
        orm_mode=True

class SessionToken(BaseModel):
    session_id: str