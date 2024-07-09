from fastapi import Depends, status, HTTPException, APIRouter, Body, Request
from fastapi.responses import Response
import schemas, models
from database import get_sql_db, get_no_sql_db
from sqlalchemy.orm import Session
from typing import List
from bson import ObjectId
from pymongo.results import DeleteResult

router = APIRouter(
    prefix='/dev',
    tags=['dev'])

@router.delete('/user/delete/all', status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_users(db: Session = Depends(get_sql_db)):
    user = db.query(models.User).all()
    for us in user:
        db.delete(us)
    db.commit()
    return None

@router.get('/user/get/all', response_model=List[schemas.User])
async def get_all_users(db: Session = Depends(get_sql_db)):
    user = db.query(models.User).all()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'There are no existing users')
    return user

@router.get('/user/get/{user_id}', response_model=schemas.User)

async def get_user_by_user_id(user_id: int, db: Session = Depends(get_sql_db)):
    """
    Get the record for a specific session, looked up by `session_id`.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} dosen't exist")
    return user

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


