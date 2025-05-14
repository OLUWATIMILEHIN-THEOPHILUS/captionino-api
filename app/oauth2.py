#  Authentication logics here
from jose import jwt, JWTError
from .config import settings
from datetime import datetime, timedelta, timezone
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

    now = datetime.now(timezone.utc)

    to_encode = data.copy()
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

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

# For App Auth
def get_current_user(app_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate credentials!", headers={"WWW-Authentication": "Bearer"})

    token = verify_access_token(app_token, credentials_exception)
    user = db.query(models.User).filter_by(id=token.id).first()
    return user


# For Supabase Auth
async def get_current_supabase_user(supabase_token: str = Security(security)):
    # verify Supabase JWT token and return user details.
    try:
        user = supabase.auth.get_user(supabase_token.credentials)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")

# For both App and Supabase users
async def get_all_current_user(app_token: str = Depends(oauth2_scheme), supabase_token: str = Security(security), db: Session = Depends(get_db)):    
    try:
        print("Trying App authentication!!!")
        return get_current_user(app_token=app_token, db=db)
    except:
        print("App Authenication failed!")
    
    try:
        print("Trying Supabase authentication!!!")
        supabase_user = await get_current_supabase_user(supabase_token=supabase_token)
        user = db.query(models.User).filter_by(google_id=supabase_user.user.user_metadata['sub']).first()
        return user

    except Exception:
        print("Supabase Authentication failed!")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed!")

# For password reset
def create_reset_token(email: dict):

    now = datetime.now(timezone.utc)

    to_encode = email.copy()

    expire = now + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
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