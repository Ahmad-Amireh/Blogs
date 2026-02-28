from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime



class UserBase(BaseModel):
    name:str = Field(min_length=1, max_length=20)
    email: EmailStr = Field(max_length=120)

class UserCreate(BaseModel): 
    pass

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id:str 

class PostBase (BaseModel):
    author: str = Field(min_length=1, max_length= 20)
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    
class PostCreate(PostBase):
    user_id: int #temp

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes= True)

    id: int
    user_id: int
    date_posted: datetime
    author: UserResponse

