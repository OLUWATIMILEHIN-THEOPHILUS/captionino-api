# Schemas and response validation here.
from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from typing import List, Optional, AnyStr
import re
from fastapi import Form
from . import enum

# Pre-compile regex patterns for password validation
LETTER_REGEX = re.compile(r'[A-Za-z]')
NUMBER_REGEX = re.compile(r'\d')
SPECIAL_CHAR_REGEX = re.compile(r'[!@#$%^&*(),.?":{}|<>]')

#Password validation function
def validate_password(value: AnyStr) -> AnyStr:
        if (len(value) < 8):
            raise ValueError("Password must be at least 8 characters")
        if not LETTER_REGEX.search(value):
            raise ValueError('Password must contain at least one letter.')
        if not NUMBER_REGEX.search(value):
            raise ValueError('Password must contain at least one number.')
        if not SPECIAL_CHAR_REGEX.search(value):
            raise ValueError('Password must contain at least one special character') #(!@#$%^&*(),.?":}{|<>).')
        return value
        
#Re-usable password mixin for other schema class
class PasswordMixin(BaseModel):
    password: str

    @field_validator("password")
    def check_password(cls, value):
        return validate_password(value)

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase, PasswordMixin):
    password_confirm: str

class SaveUser(BaseModel):
    timezone: str

class UserResponse(UserBase):
    id: UUID
    created: datetime
    avatar_url: Optional[str]
    trials_left: int
    subscription_status: str
    daily_usage: int
    timezone: str
    captions: List["CaptionResponse"] = []

    model_config = {
        "from_attributes": True
    }

class UsersResponse(BaseModel):
    count: int
    users: List[UserResponse]

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True

class TokenData(BaseModel):
    id: Optional [UUID] = None

class SetPassword(UserBase, PasswordMixin):
    password_confirm: str

class ChangePassword(PasswordMixin):
    old_password: str
    password_confirm: str

class ForgotPassword(UserBase):
    pass

class ResetPassword(PasswordMixin):
    token: str
    password_confirm: str

class CaptionRequest(BaseModel):
    c_type: Optional[str] = enum.CaptionType.social_media
    c_instruction: Optional[str] = ""

    @classmethod
    def as_form(cls, c_type: str = Form(enum.CaptionType.social_media), c_instruction: str = Form("")):
        c_type = c_type.strip() or enum.CaptionType.social_media
        c_instruction = c_instruction.strip() or ""
        return cls(c_type=c_type, c_instruction=c_instruction)

class CaptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    image_url: str
    c_text: str
    c_type: str
    created: datetime

    model_config = {
        'from_attributes': True
    }

class CaptionsResponse(BaseModel):
    count: int
    captions: List[CaptionResponse]

    model_config = {
        "from_attributes": True
    }

class CaptionSaveRequest(BaseModel):
    image_key: str
    c_type: str
    c_text: str
    has_active_sub: bool
    has_trials_left: bool
