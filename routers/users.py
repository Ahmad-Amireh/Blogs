from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models 
from asynco.database import get_db
from schemas import PostResponse, UserCreate, UserPrivateResponse, UserUpdate, UserPublicResponse, Token
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from auth import hash_password, verify_password, create_access_token, verify_access_token, oauth2_scheme
from config import settings

router = APIRouter()


@router.get("", response_model=list[UserPublicResponse])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(models.User)
    users = (await db.execute(stmt)).scalars().all()
    return users

@router.get("/me", response_model=UserPrivateResponse)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    The frontend needs to know who logged in 
    Validate the token is good 
    Get the full user information
    """
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid or Expired Token", # we don't want to reveail which one is incorrect for safty
            headers= {"WWW-Authenticate": "Bearer"}
        )
    
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid or Expired Token", # we don't want to reveail which one is incorrect for safty
            headers= {"WWW-Authenticate": "Bearer"}
        )
    user = await db.get(models.User, user_id_int)
    if not user:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "User not found", # we don't want to reveail which one is incorrect for safty
            headers= {"WWW-Authenticate": "Bearer"}
        )
    return user


@router.get("/{user_id}", response_model=UserPublicResponse)
async def get_user(user_id: int, db:Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(models.User).where(models.User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user: 
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail="User not found")
    return user 



@router.get("/{user_id}/posts", response_model=list[PostResponse])
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

@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserPrivateResponse)
async def create_user (user: UserCreate, db:Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(models.User).where(func.lower(models.User.name) == user.name.lower())
    exist_user = (await db.execute(stmt)).scalar_one_or_none()
    if exist_user: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user already exists")
    
    stmt =  select(models.User).where(func.lower(models.User.email) == user.email.lower())
    exist_email = (await db.execute(stmt)).scalar_one_or_none()
    if exist_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    
    new_user= models.User(
        name= user.name.strip(),
        email= user.email.strip().lower(),
        password_hash = hash_password(user.password)
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

@router.post ("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], #it handles the parsing form data. 
                                                                #Use the field called username but we use it for email.
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    This endpoint generates an access token for a user and returns it.
    First, it checks if a user with the submitted email exists in the database.
    If the user exists, it verifies that the provided password matches the stored hashed password.
    If authentication succeeds, it creates a JWT access token using the user ID as the subject and sets its expiration time. 
    Finally, it returns the token in the response.
    """
    stmt = select(models.User).where(func.lower(models.User.email) == form_data.username.lower())
    user = (await db.execute(stmt)).scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Incorrect Email or Password", # we don't want to reveail which one is incorrect for safty
            headers= {"WWW-Authenticate": "Bearer"}
        )
    
    access_token_expire =  timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": str(user.id)}, 
                                       expires_delta= access_token_expire)
    return Token(access_token=access_token, token_type="bearer")



     


@router.patch("/{user_id}", response_model=UserPrivateResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


    if user_update.name is not None and user_update.name.lower() != user.name.lower():
        stmt = select(models.User).where(func.lower(models.User.name) == user_update.name.lower())
        exist_user = (await db.execute(stmt)).scalar_one_or_none()
        if exist_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )

    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        stmt = select(models.User).where(func.lower(models.User.email) == user_update.email.lower())
        exist_email = (await db.execute(stmt)).scalar_one_or_none()
        if exist_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

    if user_update.name is not None:
        user.name = user_update.name
    if user_update.email is not None:
        user.email = user_update.email.lower()
        

    await db.commit()
    await db.refresh(user)

    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await db.delete(user)
    await db.commit()

