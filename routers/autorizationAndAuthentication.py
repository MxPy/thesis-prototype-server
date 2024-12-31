from fastapi import Depends, status, HTTPException, APIRouter, Body, Response, Request
import schemas, models
from database import get_sql_db, get_no_sql_db
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List
from random import randint
from security.hashing import Hasher
from datetime import datetime, timedelta
import logging
import asyncio
import auth_pb2
import auth_pb2_grpc
import user_auth_pb2
import user_auth_pb2_grpc
import grpc

logger = logging.getLogger()
import contextlib
from bson import ObjectId

SESSION_EXPIRATION_TIME_S = 800

router = APIRouter(
    prefix='/auth',
    tags=['auth'])

def get_auth_stub():
    channel = grpc.insecure_channel('app-postgres-wrapper:50053')
    return user_auth_pb2_grpc.AuthUserServiceStub(channel)

# async def populate_admin(name: str):
#     get_db_wrapper = contextlib.contextmanager(get_sql_db)
#     with get_db_wrapper() as db:
#         user = db.query(models.User).filter(models.User.username == name).first()
#         if not user:
#             code = f"{randint(0, 999999):06d}"
#             new_user = models.User(id=str(uuid4()), username = name, password = Hasher.get_password_hash(name), password_reset_code = Hasher.get_password_hash(code), permission_level=2)
#             logger.info(f"created {name}")
#             db.add(new_user)
#             db.commit()
#             db.refresh(new_user)

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register_user(request: schemas.User):
    stub = get_auth_stub()
    try:
        code = f"{randint(0, 999999):06d}"
        hashed_password = Hasher.get_password_hash(request.password)
        hashed_code = Hasher.get_password_hash(code)
        
        response = stub.RegisterUser(
            user_auth_pb2.RegisterRequest(
                username=request.username,
                password=hashed_password,
                password_reset_code=hashed_code
            )
        )
        return {"user_id": response.user_id, "password_reset_code": code}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.ALREADY_EXISTS:
            raise HTTPException(status_code=403, detail=f"User with username: {request.username} already exists")
        raise HTTPException(status_code=500, detail="Internal server error")



@router.put('/reset_password')
async def reset_password(request: schemas.ResetPassword):
    stub = get_auth_stub()
    try:
        # First get the user to verify the reset code and current password
        user_response = stub.GetUserByNickname(user_auth_pb2.UserNickRequest(username=request.username))
        logger.info(user_response)
        if not Hasher.verify_password(request.password_reset_code, user_response.password_reset_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={'WWW-Authenticate': 'Bearer'},
                detail="Wrong username or password reset code"
            )
            
        if Hasher.verify_password(request.new_password, user_response.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={'WWW-Authenticate': 'Bearer'},
                detail="Password can't be same as old one"
            )
            
        new_code = f"{randint(0, 999999):06d}"
        hashed_new_password = Hasher.get_password_hash(request.new_password)
        hashed_new_code = Hasher.get_password_hash(new_code)
        
        response = stub.ResetPassword(
            user_auth_pb2.ResetPasswordRequest(
                username=request.username,
                password_reset_code=hashed_new_code,
                new_password=hashed_new_password
            )
        )
        return {"password_reset_code": new_code}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"User with username: {request.username} doesn't exist")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(data:schemas.UserLogin, response: Response, db: Session = Depends(get_sql_db), no_db: Session = Depends(get_no_sql_db)):
    stub = get_auth_stub()
    try:
        user = stub.GetUserByNickname(user_auth_pb2.UserNickRequest(username=data.username))
        logger.info(user)
        if user:
            if user.username == data.username and Hasher.verify_password(data.password, user.password):
                id = uuid4()
                time = SESSION_EXPIRATION_TIME_S
                if(user.permission_level == 2):
                    time = 6969696969
                    #logger.info("chuuuuuuuuj")
                new_student = await no_db.insert_one(
                    models.Session(id=ObjectId(None), session_id=str(id), expiration_date=datetime.utcnow() + timedelta(seconds=time), permission_level=user.permission_level).model_dump(by_alias=True, exclude=["id"])
                )
                created_student = await no_db.find_one(
                    {"_id": new_student.inserted_id}
                )
                content = {"session_id": created_student["session_id"],
                        "expiration_date": str(created_student["expiration_date"])}
                return {"session_id": created_student["session_id"],"user_id": user.id,}
            raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        headers={'WWW-Authenticate': 'Bearer'},
                    )
        raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        headers={'WWW-Authenticate': 'Bearer'},
                    )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"User with username: {data.username} doesn't exist")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")



@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(request:schemas.SessionToken, response: Response,  no_db: Session = Depends(get_no_sql_db)):
    delete_result = await no_db.delete_one({"session_id": request.session_id})
    if delete_result.deleted_count != 1:
        return Response(status_code=500)

    return {"logout": True}

# LEGACY AUTH
# async def get_auth_user(id: schemas.SessionToken, request: Request, no_db: Session = Depends(get_no_sql_db)):
#     """verify that user has a valid session"""
#     #session_id = request.cookies.get("Authorization")
#     if not id.session_id:
#         raise HTTPException(status_code=401,  detail=f"Wrong session_id")
#     if (
#         student := await no_db.find_one({"session_id": id.session_id})
#     ) is None:
#         raise HTTPException(status_code=403)
#     if (student["expiration_date"] < datetime.utcnow()):
#          raise HTTPException(status_code=401, detail=f"session_id expired")
     
#     new_expiration = datetime.utcnow() + timedelta(seconds=SESSION_EXPIRATION_TIME_S)
#     await no_db.update_one(
#         {"session_id": id.session_id},
#         {"$set": {"expiration_date": new_expiration}}
#     )
#     return True

# async def get_auth_admin(id: schemas.SessionToken, request: Request, no_db: Session = Depends(get_no_sql_db)):
#     """verify that user has a valid session"""
#     #session_id = request.cookies.get("Authorization")
#     if not id.session_id:
#         raise HTTPException(status_code=401,  detail=f"Wrong session_id")
#     if (
#         student := await no_db.find_one({"session_id": id.session_id})
#     ) is None:
#         raise HTTPException(status_code=403)
#     if student["permission_level"] < 1:
#         raise HTTPException(status_code=401)
#     if (student["expiration_date"] < datetime.utcnow()):
#          raise HTTPException(status_code=401, detail=f"session_id expired")
#     new_expiration = datetime.utcnow() + timedelta(seconds=SESSION_EXPIRATION_TIME_S)
#     await no_db.update_one(
#         {"session_id": id.session_id},
#         {"$set": {"expiration_date": new_expiration}}
#     )
#     return True

# async def get_auth_backend_admin(id: schemas.SessionToken, request: Request, no_db: Session = Depends(get_no_sql_db)):
#     """verify that user has a valid session"""
#     #session_id = request.cookies.get("Authorization")
#     if not id.session_id:
#         raise HTTPException(status_code=401,  detail=f"Wrong session_id")
#     if (
#         student := await no_db.find_one({"session_id": id.session_id})
#     ) is None:
#         raise HTTPException(status_code=403)
#     if student["permission_level"] < 2:
#         raise HTTPException(status_code=401)
#     new_expiration = datetime.utcnow() + timedelta(seconds=6969696969)
#     await no_db.update_one(
#         {"session_id": id.session_id},
#         {"$set": {"expiration_date": new_expiration}}
#     )
#     return True


# @router.get("/", dependencies=[Depends(get_auth_user)])
# async def secret():
#     return status.HTTP_200_OK
# @router.get("/admin", dependencies=[Depends(get_auth_admin)])
# async def secret():
#     return status.HTTP_200_OK
# @router.get("/backend_admin", dependencies=[Depends(get_auth_backend_admin)])
# async def secret():
#     return status.HTTP_200_OK
class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    def __init__(self):
        # Pobranie instancji bazy danych z generatora
        self.no_db = next(get_no_sql_db())

    async def AuthUser(self, request: auth_pb2.Token, context: grpc.aio.ServicerContext) -> auth_pb2.AuthResponse:
        try:
            if not request.session_id:
                return auth_pb2.AuthResponse(code=401, detail="Wrong session_id")
            
            # Wykonanie asynchronicznej operacji w aktywnej pętli zdarzeń
            student = await self.no_db.find_one({"session_id": request.session_id})
            if not student:
                return auth_pb2.AuthResponse(code=403, detail="Session not found")

            # Sprawdzanie uprawnień
            if request.user_type >= 1 and student["permission_level"] < request.user_type:
                return auth_pb2.AuthResponse(code=401, detail="Insufficient permissions")

            # Sprawdzanie wygaśnięcia sesji
            if request.user_type != 2 and student["expiration_date"] < datetime.utcnow():
                return auth_pb2.AuthResponse(code=401, detail="session_id expired")

            # Aktualizacja czasu wygaśnięcia
            new_expiration = datetime.utcnow() + timedelta(
                seconds=6969696969 if request.user_type == 2 
                else SESSION_EXPIRATION_TIME_S
            )
            
            await self.no_db.update_one(
                {"session_id": request.session_id},
                {"$set": {"expiration_date": new_expiration}}
            )

            return auth_pb2.AuthResponse(code=200, detail="OK")

        except Exception as e:
            logger.error(f"Unexpected error in AuthUser: {str(e)}")
            return auth_pb2.AuthResponse(code=500, detail=str(e))