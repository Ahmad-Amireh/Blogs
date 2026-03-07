from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime



class UserBase(BaseModel):
    name:str = Field(min_length=1, max_length=20)
    email: EmailStr = Field(max_length=120)

class UserCreate(UserBase): 
    password:str = Field(min_length=8)

class UserUpdate(BaseModel):
    name:str | None = Field(default= None, min_length=1, max_length=20)
    email:EmailStr | None = Field(default= None, max_length=120)

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id:int 

class PostBase (BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    
class PostCreate(PostBase):
    user_id: int #temp

class PostUpdate(BaseModel):
    title: str | None = Field(default= None, min_length=1, max_length=100)
    content: str | None = Field(min_length=1, default=None)
class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes= True)

    id: int
    user_id: int
    date_posted: datetime
    author: UserResponse

