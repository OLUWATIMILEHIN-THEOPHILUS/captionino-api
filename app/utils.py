# Hash, verify password, send_email and other utility functions here (subscription check).
from passlib.context import CryptContext
import smtplib
from email.message import EmailMessage
from .config import settings
from sqlalchemy.orm import Session
from . import models
from fastapi import Depends
from .database import get_db
from datetime import datetime, timezone

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
