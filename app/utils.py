# Hash, verify password, send_email and other utility functions here (subscription check).
from passlib.context import CryptContext
import smtplib
from email.message import EmailMessage
from .config import settings
from sqlalchemy.orm import Session
from . import models
from fastapi import Depends, Request, HTTPException
from .database import get_db
import hmac
import hashlib

LEMONSQUEEZY_WEBHOOK_SECRET = settings.lemonsqueezy_webhook_secret

# For SMTP (Mailtrap Email testing).
SMTP_SERVER = settings.smtp_server
SMTP_PORT = settings.smtp_port
EMAIL_SENDER = settings.email_sender
EMAIL_PASSWORD = settings.email_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def send_email(to_email: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = EMAIL_SENDER
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(message)


def check_active_subscription(user_id: int, db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter_by(id=user_id).first()

    sub_status = user.subscription_status 

    if sub_status == "ACTIVE" or sub_status == "CANCELLED":
        return True
    return False

def check_daily_limit_reached(user_id: int, has_active_sub: bool, db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter_by(id=user_id).first()

    if has_active_sub and user.daily_usage >= settings.max_daily_usage:
        return True
    else:
        return False


def increment_daily_usage(user_id: int, used_subscription: bool, reached_daily_limit: bool, db: Session = Depends(get_db)):
    # Increment daily usage only if the caption was generated using a valid subscription.
    user = db.query(models.User).filter_by(id=user_id).first()

    if not user:
        raise ValueError("User not found.")

    if used_subscription and not reached_daily_limit: 
        user.daily_usage += 1
        db.commit()


def verify_signature(request: Request, body: bytes):
    received_signature = request.headers.get("X-Signature")

    if not received_signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    # Generate HMAC signature using your secret and the raw body
    expected_signature = hmac.new(
        key=LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(received_signature, expected_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    