from __future__ import annotations

from datetime import datetime, timezone
from asynco.database import Base

from sqlalchemy import DateTime, String, INTEGER, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(INTEGER, primary_key= True, index= True)
    name: Mapped[str] = mapped_column(String(20), unique= True, nullable= False)
    email: Mapped[str] = mapped_column(String(120), unique= True, nullable= False)
    password_hash: Mapped[str] = mapped_column(String(120), unique=False, nullable=False)
    posts: Mapped[list[Post]] = relationship(back_populates='author')

class Post(Base): 
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(INTEGER, primary_key= True, index= True)
    title: Mapped[str] = mapped_column(String(100), unique= True, nullable= False)
    content: Mapped[str] = mapped_column(Text, nullable = False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable= False, index= True)
    date_posted: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    author:Mapped[User] = relationship(back_populates="posts")