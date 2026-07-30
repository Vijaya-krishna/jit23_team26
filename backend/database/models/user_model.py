from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from backend.database.session import Base

class UserModel(Base):
    """
    User database model representing admins and system operators.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="operator", nullable=False)  # 'admin' or 'operator'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<UserModel id={self.id} username={self.username} role={self.role}>"
