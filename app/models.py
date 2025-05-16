# Model table class here
from .database import Base
from sqlalchemy import Column, Text, String, Integer, Boolean, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.sql.expression import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from . import schemas, enum

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)    # can be empty for Google users
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    google_id = Column(String, unique=True, nullable=True)  # Google ID for Google users
    avatar_url = Column(String, nullable=True)  # Avatar url for Google users
    trials_left = Column(Integer, nullable=False, default=0)
    subscription_status = Column(String, default="FREE", nullable=False)
    daily_usage = Column(Integer, default=0)
    timezone = Column(String, default="Africa/Lagos")
    lemonsqueezy_customer_id = Column(String, nullable=True)
    lemonsqueezy_subscription_id = Column(String, nullable=True)
    subscription_ends_at = Column(TIMESTAMP(timezone=True), nullable=True)
    subscription_renews_at = Column(TIMESTAMP(timezone=True), nullable=True)

    captions = relationship('Caption', back_populates='owner')

    def __repr__(self):
        return f"User(email={self.email})"
    
class Caption(Base):
    __tablename__ = "captions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    c_text = Column(Text, nullable=False)
    c_type = Column(String, nullable=False)
    image_url = Column(String, nullable=False)

    owner = relationship('User', back_populates='captions')
