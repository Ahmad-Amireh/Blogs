from fastapi import FastAPI, status, HTTPException, Request, Depends
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from schemas import PostResponse, PostCreate, UserCreate, UserResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Annotated

import models
from database import Base, engine, get_db


Base.metadata.create_all(bind= engine) # to create Db tabel
app =  FastAPI()


@app.get('/', include_in_schema= False)
def home (): 
    return {"message": "Hello World"}

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db:Annotated[Session, Depends(get_db)]):
    stmt = select(models.User).where(models.User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user: 
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail="User not found")
    return user 


@app.post("/api/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user (user: UserCreate, db:Annotated[Session, Depends(get_db)]):
    stmt = select(models.User).where(models.User.name == user.name)
    exist_user = db.execute(stmt).scalar_one_or_none()
    if exist_user: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user already exists")
    
    stmt = select(models.User).where(models.User.email == user.email)
    exist_email = db.execute(stmt).scalar_one_or_none()
    if exist_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    
    new_user= models.User(
        name= user.name,
        email= user.email
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.get("/api/users/{user_id}/posts", response_model= list[PostResponse]) 
def get_user_posts(user_id:int, db:Annotated[Session, Depends(get_db)]): 
    stmt = select(models.User).where(models.User.id == user_id)
    user_exist = db.execute(stmt).scalar_one_or_none() # or user_exist = db.get(models.User, user_id) for primary key
    if not user_exist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    stmt = select(models.Post).where(models.Post.user_id == user_id)
    posts = db.execute(stmt).scalars().all()
    return posts

@app.get("/api/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    stmt = select(models.Post)
    posts = db.execute(stmt).scalars().all()
    return posts

@app.post("/api/posts", status_code=status.HTTP_201_CREATED, response_model=PostResponse)

def create_post(post: PostCreate, db:Annotated[Session,Depends(get_db)]):
    stmt = select(models.User).where(models.User.id == post.user_id)
    user = db.execute(stmt).scalar_one_or_none ()
    if not user:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "User not found"
        )
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = post.user_id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
  post = db.get(models.Post, post_id)
  if not post:
      raise HTTPException (status_code= status.HTTP_404_NOT_FOUND, detail="Post not Found")
  return post

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occured. Please check your request and try again"
    )

    return JSONResponse(
        status_code= exception.status_code,
        content= {"detail": message}
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Invalid input. Check your path parameters or request body."}
    )
