# Model table class here
from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)    # can be empty for Google users
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    google_id = Column(String, unique=True, nullable=True)  # Google ID for Google users
    avatar_url = Column(String, nullable=True)  # Avatar url for Google users

    def __repr__(self):
        return f"User(email={self.email})"