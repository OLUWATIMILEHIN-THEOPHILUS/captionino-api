# Authentication endpoints and logic here.
from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models, utils, oauth2
from starlette.requests import Request

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/signin", status_code=status.HTTP_200_OK, response_model=dict)
async def signin(user_data: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter_by(email=user_data.email)
    user = user_query.first()

    if user:
        # if the user signed up with Google and hasn't set a password yet, redirect to Google OAuth
        if not user.password and user.google_id:
            redirect_uri = request.url_for("google_auth_callback")  # redirect URL
            return await oauth.google.authorize_redirect(request, redirect_uri)

        if utils.verify(user_data.password, user.password):
            access_token = oauth2.create_access_token(data = {"sub": str(user.id)})
            token_type = "bearer"

            return {
                "message": "User signed in successfully!",
                "token": schemas.Token(access_token=access_token, token_type=token_type)
            }

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid credentials!")     


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=dict)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    email_exists = db.query(models.User).filter_by(email=user_data.email).first()
    if email_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email has already been used!")

    if user_data.password != user_data.password_confirm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Password does not match!")

    hashed_password = utils.hash(user_data.password)
    user_data.password = hashed_password
    # new_user = models.User(**user_data.dict())
    new_user = models.User(email=user_data.email, password=user_data.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = oauth2.create_access_token(data = {"sub": str(new_user.id)})
    token_type = "bearer"

    return {
        "message": "User created successfully!",
        "user": schemas.UserResponse.from_orm(new_user),
        "token": schemas.Token(access_token=access_token, token_type=token_type)
    }
