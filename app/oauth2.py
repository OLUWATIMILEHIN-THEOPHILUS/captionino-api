#  Authentication logics here
from jose import jwt, JWTError
from .config import settings
from datetime import datetime, timedelta
from . import schemas, models
from .database import get_db
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

# For Supabase Auth
from fastapi import Security
from fastapi.security import HTTPBearer
from .supabase_client import supabase

# For Supabase Auth
security = HTTPBearer()

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
RESET_TOKEN_EXPIRE_MINUTES = settings.reset_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='signin')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("sub")

        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exception

    return token_data

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate credentials!", headers={"WWW-Authentication": "Bearer"})

    token = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter_by(id=token.id).first()
    return user


# For Supabase Auth
async def get_current_supabase_user(token: str = Security(security)):
    # verify Supabase JWT token and return user details
    try:
        user = supabase.auth.get_user(token.credentials)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")


def create_reset_token(email: dict):
    to_encode = email.copy()

    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # to_encode.update({"sub": email, "exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if not email:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User does not exist!")
    except JWTError:
        return None # invalid or expired token
    
    return email
