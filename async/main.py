from contextlib import  asynccontextmanager # new
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler #new
from fastapi import FastAPI, status, HTTPException, Request, Depends
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from schemas import PostResponse, PostCreate, UserCreate, UserResponse, PostUpdate, UserUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession #new
from sqlalchemy.orm import selectinload
from typing import Annotated

import models
from .database import Base, engine, get_db


#Base.metadata.create_all(bind= engine) # create_all is sync so we need to remove it 

app =  FastAPI()

# add life span : is a modern way to startup and shutdown event . (Replaced old decorators)
@asynccontextmanager
async def lifespan(_app= FastAPI):
    #start up 
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


@app.get('/', include_in_schema= False)
def home (): 
    return {"message": "Hello World"}

@app.get("/api/users", response_model=list[UserResponse])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(models.User)
    users = (await db.execute(stmt)).scalars().all()
    return users

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db:Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(models.User).where(models.User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user: 
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail="User not found")
    return user 


@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


    if user_update.name is not None and user_update.name != user.name:
        stmt = select(models.User).where(models.User.name == user_update.name)
        exist_user = (await db.execute(stmt)).scalar_one_or_none()
        if exist_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )

    if user_update.email is not None and user_update.email != user.email:
        stmt = select(models.User).where(models.User.email == user_update.email)
        exist_email = (await db.execute(stmt)).scalar_one_or_none()
        if exist_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

    if user_update.name is not None:
        user.name = user_update.name
    if user_update.email is not None:
        user.email = user_update.email
        

    await db.commit()
    await db.refresh(user)

    return user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await db.delete(user)
    await db.commit()


@app.post("/api/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user (user: UserCreate, db:Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(models.User).where(models.User.name == user.name)
    exist_user = (await db.execute(stmt)).scalar_one_or_none()
    if exist_user: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user already exists")
    
    stmt =  select(models.User).where(models.User.email == user.email)
    exist_email = (await db.execute(stmt)).scalar_one_or_none()
    if exist_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    
    new_user= models.User(
        name= user.name,
        email= user.email
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    stmt = select(models.User).where(models.User.id == user_id)
    user_exist = (await db.execute(stmt)).scalar_one_or_none()

    if not user_exist:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = (
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
    )

    posts = (await db.execute(stmt)).scalars().all()

    return posts

@app.get("/api/posts", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(models.Post).options(selectinload(models.Post.author))
    posts = (await db.execute(stmt)).scalars().all()
    return posts

@app.post("/api/posts", status_code=status.HTTP_201_CREATED, response_model=PostResponse)

async def create_post(post: PostCreate, db:Annotated[AsyncSession,Depends(get_db)]):
    stmt = select(models.User).where(models.User.id == post.user_id)
    user = (await db.execute(stmt)).scalar_one_or_none ()
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
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])

    return new_post


@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    stmt = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id)

    post = (await db.execute(stmt)).scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not Found"
        )

    return post

@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int, 
    post_data: PostCreate, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    post = await db.get(models.Post, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not Found")

    user = await db.get(models.User, post_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not Found")

    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    await db.commit()
    await db.refresh(post, ["author"])

    return post

@app.patch("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int, 
    post_data: PostUpdate, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    post = await db.get(models.Post, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not Found")

    update_data = post_data.model_dump(exclude_unset= True) #to remove default values
    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, ["author"])

    return post

@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db:Annotated[AsyncSession, Depends(get_db)]):
    post = await db.get(models.Post, post_id)
    if not post: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    await db.delete(post)
    await db.commit()

@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    return await http_exception_handler(request, exception)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    return await request_validation_exception_handler(request, exception)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("async.main:app", host="127.0.0.1", port=8000, reload=True)