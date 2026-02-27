from pydantic import BaseModel, Field, ConfigDict

class PostBase (BaseModel):
    author: str = Field(min_length=1, max_length= 20)
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    
class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes= True)

    id: int
    date_posted: str

