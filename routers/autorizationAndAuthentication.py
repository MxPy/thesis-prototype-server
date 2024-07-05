from fastapi import Depends, status, HTTPException, APIRouter
import schemas, models
from database import get_db
from sqlalchemy.orm import Session
from typing import List
from security.hashing import Hasher

router = APIRouter(
    prefix='/LaR',
    tags=['LaR'])


#Post methods
@router.post('/post', status_code=status.HTTP_201_CREATED)
async def create(request:schemas.User, db: Session = Depends(get_db)):
    new_user = models.User(username = request.username, email = request.email, password = Hasher.get_password_hash(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

async def check_user(data: schemas.UserLogin, db):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if user:
        if user.username == data.username and Hasher.verify_password(data.password, user.password):
            return True # jwt_handler.signJWT(user.id)
    return False

@router.post("/login", status_code=status.HTTP_200_OK)
async def user_login(user:schemas.UserLogin, db: Session = Depends(get_db)):
    token = await check_user(user, db)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f'Wrong username or password')
    return token