# Google Auth endpoints and logic here.
from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models, oauth2
from starlette.requests import Request
from authlib.integrations.starlette_client import OAuth
from ..config import settings

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# Load OAuth credentials
GOOGLE_CLIENT_ID = settings.google_client_id
GOOGLE_CLIENT_SECRET = settings.google_client_secret

# OAuth setup
oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params={"scope": "openid email profile"},         #optional
    access_token_url="https://oauth2.googleapis.com/token",
    access_token_params=None,                                   #optional
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    # userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",    #alternative
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",  #required
)


# Route to redirect users to Google login
@router.get("/google", status_code=status.HTTP_200_OK)
async def continue_with_google(request: Request):
    redirect_uri = request.url_for("google_auth_callback")  # redirect URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

# Route to handle OAuth callback from Google
@router.get("/google/callback", status_code=status.HTTP_200_OK, response_model=dict)
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # fetch the token using the authorization function
        token = await oauth.google.authorize_access_token(request)

        response = await oauth.google.get("https://www.googleapis.com/oauth2/v3/userinfo", token=token)
        user_info = response.json()

        # Signup logic
        # extract user details
        # name = user_info.get("name", "")
        email = user_info["email"]
        google_id = user_info["sub"]
        avatar_url = user_info['picture']

        # check if user exists in DB
        user = db.query(models.User).filter(models.User.email == email).first()

        if not user:
            # if user doesn't exist, create a new user with the user_info
            new_user = models.User(email=email, password="", google_id=google_id, avatar_url=avatar_url)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

            # generate JWT token for new_user
            access_token = oauth2.create_access_token(data={"sub": str(new_user.id)})
            token_type = "bearer"

            return {
                "message": "User created successfully!",
                "user": schemas.UserResponse.from_orm(new_user),
                "token": schemas.Token(access_token=access_token, token_type=token_type)
            }
        # generate JWT token for existing user
        access_token = oauth2.create_access_token(data={"sub": str(user.id)})
        token_type = "bearer"

        return {
            "message": "User signed in successfully!",
            "token": schemas.Token(access_token=access_token, token_type=token_type)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail="Google authentication failed")