from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from . import models
from .config import settings
from .database import get_db

def check_free_trial_eligibility(user_id: int, db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter_by(id=user_id).first()

    trials_left = user.trials_left

    if trials_left > 0:
        has_trials_left = True
        return has_trials_left
    else:
        has_trials_left = False
        return has_trials_left
        

def decrement_trials_left(user_id: int, has_active_sub: bool, db: Session = Depends(get_db)):
    # Only decrement if the user does not have a subscription 
    user = db.query(models.User).filter_by(id=user_id).first()

    if not has_active_sub and user.trials_left > 0:
        user.trials_left -= 1
        db.commit()
        # the below to return bool for used_free_trial?
        # return True  # Indicate that a trial was used
    
    # return False  # No trial was used
