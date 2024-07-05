from fastapi import Depends, status, HTTPException, APIRouter
import schemas, models
from database import get_db
from sqlalchemy.orm import Session
from typing import List
from security.hashing import Hasher

router = APIRouter(
    prefix='/user',
    tags=['user'])



@router.post('/post', status_code=status.HTTP_201_CREATED)
async def create(request:schemas.User, db: Session = Depends(get_db)):
    new_user = models.User(username = request.username, email = request.email, password = Hasher.get_password_hash(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.delete('/delete/all', status_code=status.HTTP_204_NO_CONTENT)
async def delete(db: Session = Depends(get_db)):
    user = db.query(models.User).all()
    for us in user:
        db.delete(us)
    db.commit()
    return None

@router.delete('/delete/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} dosen't exist")
    db.delete(user)
    db.commit()
    return None

@router.get('/get/all', response_model=List[schemas.User])
async def get(db: Session = Depends(get_db)):
    user = db.query(models.User).all()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'There are no existing users')
    return user

@router.get('/get/{user_id}', response_model=schemas.User)
async def get(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} dosen't exist")
    return user


@router.put('/{user_id}', response_model=schemas.User)
async def update(user_id: int, request: schemas.User, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} dosen't exist")
    
    user.username = request.username if request.username else user.username
    user.email = request.email if request.email else user.email
    if request.password:
        user.password = Hasher.get_password_hash(request.password)
    
    db.commit()
    db.refresh(user)
    return user


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