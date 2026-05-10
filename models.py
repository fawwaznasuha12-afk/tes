from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    BANNED = "banned"
    KICKED = "kicked"
    MUTED = "muted"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default=UserRole.USER)
    status = Column(String, default=UserStatus.ACTIVE)
    status_reason = Column(String, nullable=True)
    is_online = Column(Boolean, default=False)
    
    # For Feature Locking (Simple string with comma-separated locked features)
    locked_features = Column(String, default="")
