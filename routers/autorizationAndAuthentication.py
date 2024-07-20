from fastapi import Depends, status, HTTPException, APIRouter, Body, Response, Request
import schemas, models
from database import get_sql_db, get_no_sql_db
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List
from security.hashing import Hasher
from datetime import datetime, timedelta
from bson import ObjectId

router = APIRouter(
    prefix='/user',
    tags=['user'])



@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register_user(request:schemas.User, db: Session = Depends(get_sql_db)):
    new_user = models.User(username = request.username, email = request.email, password = Hasher.get_password_hash(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.delete('/delete/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_user_id(user_id: int, db: Session = Depends(get_sql_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} dosen't exist")
    db.delete(user)
    db.commit()
    return None

@router.put('/update/{user_id}', response_model=schemas.User)
async def update_user_by_user_id(user_id: int, request: schemas.User, db: Session = Depends(get_sql_db)):
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


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(data:schemas.UserLogin, response: Response, db: Session = Depends(get_sql_db), no_db: Session = Depends(get_no_sql_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if user:
        if user.username == data.username and Hasher.verify_password(data.password, user.password):
            id = uuid4()
            new_student = await no_db.insert_one(
                models.Session(id=ObjectId(None), session_id=str(id), expiration_date=datetime.utcnow() + timedelta(seconds=800)).model_dump(by_alias=True, exclude=["id"])
            )
            created_student = await no_db.find_one(
                {"_id": new_student.inserted_id}
            )
            content = {"session_id": created_student["session_id"],
                       "expiration_date": str(created_student["expiration_date"])}
            response = JSONResponse(content=content)
            response.set_cookie(key="Authorization", value=id)
            return response
        raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={'WWW-Authenticate': 'Bearer'},
                )
    raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    headers={'WWW-Authenticate': 'Bearer'},
                )


@router.post("/logout")
async def logout_user(id: str, response: Response,  no_db: Session = Depends(get_no_sql_db)):
    response.delete_cookie(key="Authorization")
    
    delete_result = await no_db.delete_one({"session_id": id})
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return {"status": "logged out"}

async def get_auth_user(id: schemas.SessionToken, request: Request, no_db: Session = Depends(get_no_sql_db)):
    """verify that user has a valid session"""
    session_id = request.cookies.get("Authorization")
    if not id.session_id:
        raise HTTPException(status_code=401)
    if (
        student := await no_db.find_one({"session_id": id.session_id})
    ) is None:
        raise HTTPException(status_code=403)
        
    return True


@router.get("/", dependencies=[Depends(get_auth_user)])
async def secret():
    return status.HTTP_200_OK

