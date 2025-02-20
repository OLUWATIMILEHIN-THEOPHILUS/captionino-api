# Schemas and response validation here.
from pydantic import BaseModel, EmailStr, validator
from uuid import UUID
from datetime import datetime
from typing import List, Optional, AnyStr
import re

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

    @validator("password")
    def check_password(cls, value):
        return validate_password(value)

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase, PasswordMixin):
    password_confirm: str

class UserResponse(UserBase):
    id: UUID
    created: datetime

    class Config:
        from_attributes = True

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
