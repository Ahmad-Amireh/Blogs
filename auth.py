from datetime import datetime, timedelta, timezone
import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) ->str: 
    return password_hash.hash(password)

def verify_password(password:str, hashed_password:str):
    return password_hash.verify(password, hashed_password) # hashing is not reviersable
