# Supabase Auth endpoints and logic here.
from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models, oauth2
from starlette.requests import Request
from ..supabase_client import supabase

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# For supabase manual signin to get token
@router.post("/login_supabase_user", status_code=status.HTTP_200_OK, response_model=dict)
async def login_supabase_user(user_data: schemas.UserLogin):
    # manually login a user and return a JWT token.
    try:
        response = supabase.auth.sign_in_with_password({"email": user_data.email, "password": user_data.password})
        access_token = response.session.access_token
        token_type = "bearer"

        return {
            "message": "User signed in successfully!",
            "token": schemas.Token(access_token=access_token, token_type=token_type)
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid login")

# For adding supabase users to the database
@router.post("/save_user", status_code=status.HTTP_201_CREATED, response_model=dict)
def save_user(request: Request, current_user = Depends(oauth2.get_current_supabase_user), db: Session = Depends(get_db)):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "No token received"}

    # extract user details
    email = current_user.user.email
    google_id = current_user.user.user_metadata['sub']
    avatar_url = current_user.user.user_metadata['avatar_url']

    # check if user exists in DB
    existing_user = db.query(models.User).filter_by(email=email).first()
    if existing_user:
        return {"message": "User already exists!"}    

    # save new user
    new_user = models.User(email=email, google_id=google_id, avatar_url=avatar_url)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User created successfully!",
        "user": schemas.UserResponse.from_orm(new_user)
    }