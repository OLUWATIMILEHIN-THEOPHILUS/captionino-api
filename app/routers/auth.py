# Authentication endpoints and logic here
from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models, utils, oauth2
from starlette.requests import Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse as FastAPIRedirectResponse
from ..config import settings
from ..supabase_client import supabase    #for supabase Auth

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

        # check if user exists in DB
        user = db.query(models.User).filter(models.User.email == email).first()

        if not user:
            # if user doesn't exist, create a new user with the user_info
            new_user = models.User(email=email, password="", google_id=google_id)
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

@router.post("/set_password", status_code=status.HTTP_201_CREATED)
def set_password(user_data: schemas.SetPassword, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="User not authenticated!")
    user = db.query(models.User).filter(models.User.email == current_user.email).first()
    
    if user_data.email != user.email:
        raise HTTPException(status_code=404, detail="Invalid email!")

    if not user.google_id or user.password:  # if they already have a password, they don’t need this
        raise HTTPException(status_code=400, detail="Password already set")

    if user_data.password != user_data.password_confirm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Password does not match!")

    # hash and store the new password
    user.password = utils.hash(user_data.password)
    db.commit()

    return {"message": "Password set successfully. You can now log in with email/password."}

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
    # print("Received Token:", token)  # for debugging
    if not token:
        return {"error": "No token received"}

    # extract user details
    email = current_user.user.email
    google_id = current_user.user.user_metadata['sub']

    # check if user exists in DB
    existing_user = db.query(models.User).filter_by(email=email).first()
    if existing_user:
        return {"message": "User already exists!"}    

    # save new user
    new_user = models.User(email=email, google_id=google_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User created successfully!",
        "user": schemas.UserResponse.from_orm(new_user)
    }


@router.post("/change_password", status_code=status.HTTP_202_ACCEPTED)
def change_password(user_data: schemas.ChangePassword, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter_by(id=current_user.id).first()
    if not utils.verify(user_data.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Old password is incorrect!")
    if user_data.password != user_data.password_confirm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Password does not macth!")
    if utils.verify(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"New password can not be the same as Old password!")
    
    hashed_password = utils.hash(user_data.password)
    user.password = hashed_password
    db.commit()

    return {"message": "Your password has been changed successfully!"}

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

@router.post("/forgot_password", status_code=status.HTTP_200_OK)
async def forgot_password(user_data: schemas.ForgotPassword, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email=user_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid email!")
    
    # create reset token and reset link
    reset_token = oauth2.create_reset_token(email={"sub": user.email})
    reset_link = f"https://dev-captionino-api.onrender.com/auth/reset_password?token={reset_token}"

    # send email with the reset link
    await utils.send_email(user.email, "Password Reset Request", f"Click here to reset your password: {reset_link}")

    return {"message": "Password reset email sent!"}

@router.post("/reset_password", status_code=status.HTTP_201_CREATED)
async def reset_password(user_data: schemas.ResetPassword, db: Session = Depends(get_db)):
    email = oauth2.verify_reset_token(user_data.token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid or expired token!")
    
    user = db.query(models.User).filter_by(email=email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found!")
    
    if user_data.password != user_data.password_confirm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Password does not match!")
    
    if utils.verify(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"New password can not be the same as Old password!")

    hashed_password = utils.hash(user_data.password)
    user.password = hashed_password
    db.commit()

    return {"message": "Password reset was successful!"}