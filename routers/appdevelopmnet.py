from fastapi import Depends, status, HTTPException, APIRouter, Body, Request
from fastapi.responses import Response
import schemas, models
from database import get_sql_db, get_no_sql_db
from sqlalchemy.orm import Session
from typing import List
from bson import ObjectId
from pymongo.results import DeleteResult
import user_auth_pb2
import user_auth_pb2_grpc
import grpc

router = APIRouter(
    prefix='/auth/dev',
    tags=['dev'])

def get_auth_stub():
    channel = grpc.insecure_channel('app-postgres-wrapper:50053')
    return user_auth_pb2_grpc.AuthUserServiceStub(channel)

@router.delete('/user/delete/all', status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_users():
    stub = get_auth_stub()
    try:
        stub.DeleteAllUsers(user_auth_pb2.Empty())
        return None
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get('/user/get/all', response_model=List[schemas.User])
async def get_all_users():
    stub = get_auth_stub()
    try:
        response = stub.GetAllUsers(user_auth_pb2.Empty())
        return [{
            "id": user.id,
            "username": user.username,
            "password": user.password,
            "password_reset_code": user.password_reset_code,
            "permission_level": user.permission_level
        } for user in response.users]
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There are no existing users'
            )
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get('/user/get/{userId}', response_model=schemas.User)
async def get_user_by_user_id(userId: str):
    stub = get_auth_stub()
    try:
        response = stub.GetUserById(user_auth_pb2.UserIdRequest(user_id=userId))
        return {
            "id": response.id,
            "username": response.username,
            "password": response.password,
            "password_reset_code": response.password_reset_code,
            "permission_level": response.permission_level
        }
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id: {userId} doesn't exist"
            )
        raise HTTPException(status_code=500, detail=f"Internal server error {e}")

@router.get(
    "/session/all",
    response_description="Get a all sessions",
    response_model=List[models.Session],
    response_model_by_alias=False,
)
async def get_all_sessions(db: Session = Depends(get_no_sql_db)):
    """
    Get all of sessions.
    """
    if (
        students :=await db.find().to_list(1000)
    ) is not None and students:
        return students

    raise HTTPException(status_code=404, detail=f"any sessions found")


@router.get(
    "/session/{id}",
    response_description="Get a single session by session id",
    response_model=models.Session,
    response_model_by_alias=False,
)
async def get_session_by_session_id(id: str, db: Session = Depends(get_no_sql_db)):
    """
    Get the record for a specific session, looked up by `session_id`.
    """
    if (
        session := await db.find_one({"session_id": id})
    ) is not None:
        return session

    raise HTTPException(status_code=404, detail=f"session_id {id} not found")

@router.delete("/session/all", response_description="Delete a session")
async def delete_all_sessions(db: Session = Depends(get_no_sql_db)):
    """
    Remove all session records from the database.
    """
    delete_result: DeleteResult = await db.delete_many({})

    if delete_result.deleted_count > 0:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail="No sessions found")

@router.delete("/session/{id}", response_description="Delete a session")
async def delete_session_by_session_id(id: str, db: Session = Depends(get_no_sql_db)):
    """
    Remove a single session record from the database, looked up by `session_id`.
    """
    delete_result = await db.delete_one({"session_id": id})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"session_id {id} not found")



@router.post(
    "/session/",
    response_description="Add new session",
    response_model=models.Session,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def post_custom_session(student: models.Session = Body(...), db: Session = Depends(get_no_sql_db)):
    """
    Insert a new session record.

    A unique `id` will be created and provided in the response.
    """
    new_student = await db.insert_one(
        student.model_dump(by_alias=True, exclude=["id"])
    )
    created_student = await db.find_one(
        {"_id": new_student.inserted_id}
    )
    return created_student


