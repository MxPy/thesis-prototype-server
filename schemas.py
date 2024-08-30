from pydantic import BaseModel

class User(BaseModel):
    username: str
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
    
class ResetPassword(BaseModel):
    username: str 
    password_reset_code: str
    new_password: str 
    class Config:
        orm_mode=True