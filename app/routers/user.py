#  User logic here.
from fastapi import APIRouter, status, Depends, HTTPException
from ..database import get_db
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2
from uuid import UUID

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.get("/get_all_users", status_code=status.HTTP_200_OK, response_model=dict)
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return {
        "message": "Users!",
        "users": schemas.UsersResponse(count=len(users), users=users)     
    }

@router.get("/get_user/{id}", status_code=status.HTTP_200_OK, response_model=dict)
def get_user(id: UUID, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_all_current_user)):
    user_query = db.query(models.User).filter_by(id=id)
    user = user_query.first()
    if user:
        return {
            "message": "User!",
            "user": schemas.UserResponse.from_orm(user)
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No user with the id: {id}")

@router.delete("/delete_user/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: UUID, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_all_current_user)):
    user_query = db.query(models.User).filter_by(id=id)
    user = user_query.first()

    if user is not None:   
        if current_user.id == user.id:
            user_query.delete(synchronize_session=False)
            db.commit()
            return {
                # "message": "Your account has been deleted successfully!",
                "status": status.HTTP_204_NO_CONTENT
            }
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"You can only delete your account!")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No user with the id: {id}")