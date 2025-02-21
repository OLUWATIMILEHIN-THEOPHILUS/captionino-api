# Password endpoints and logic here.
from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models, utils, oauth2

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/set_password", status_code=status.HTTP_201_CREATED)
def set_password(user_data: schemas.SetPassword, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_all_current_user)):
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

@router.post("/change_password", status_code=status.HTTP_202_ACCEPTED)
def change_password(user_data: schemas.ChangePassword, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_all_current_user)):
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