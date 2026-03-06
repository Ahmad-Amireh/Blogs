from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models 
from asynco.database import get_db
from schemas import PostResponse, UserCreate, UserResponse, UserUpdate


router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(models.User)
    users = (await db.execute(stmt)).scalars().all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
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

@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
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


@router.patch("/{user_id}", response_model=UserResponse)
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

