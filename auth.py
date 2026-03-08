from datetime import datetime, timedelta, timezone
import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from config import settings

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token") #Extract Token from auth header. #makes auth box.


def hash_password(password: str) ->str: 
    return password_hash.hash(password)

def verify_password(password:str, hashed_password:str):
    return password_hash.verify(password, hashed_password) # hashing is not reviersable

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm
    )

    return encoded_jwt

def verify_access_token(token: str) ->str | None: 
    try: 
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp","sub"]}
        )
    except jwt.InvalidTokenError:
        return None

    else:
        return payload.get("sub") #user_id
    

    



    