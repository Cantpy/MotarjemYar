from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    username = Column(String(255), primary_key=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    token_hash = Column(Text, nullable=True)
    expires_at = Column(String(50), nullable=True)  # Using String to match existing ISO format
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to user profile
    profile = relationship("UserProfile", back_populates="user", uselist=False)


class UserProfile(Base):
    __tablename__ = 'user_profiles'

    username = Column(String(255), ForeignKey('users.username'), primary_key=True)
    full_name = Column(String(255), nullable=True)
    role_fa = Column(String(100), nullable=True)

    # Relationship back to user
    user = relationship("User", back_populates="profile")
