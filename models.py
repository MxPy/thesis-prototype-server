from database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, String
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator
from typing import Optional
from pydantic import ConfigDict, BaseModel, Field

PyObjectId = Annotated[str, BeforeValidator(str)]

class User(Base):
    __tablename__ = 'auth'
    id = Column(Integer, primary_key=True, index = True)
    username = Column(String)
    password = Column(String)
    password_reset_code = Column(String)
    permission_level = Column(Integer) #0 - user, #1 - admin, #2 - backend admin
    
class Session(BaseModel):
    """
    Container for a single session record.
    """

    # The primary key for the StudentModel, stored as a `str` on the instance.
    # This will be aliased to `_id` when sent to MongoDB,
    # but provided as `id` in the API requests and responses.
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    session_id: str = Field(...)
    expiration_date: datetime = Field(...)
    permission_level: int = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
