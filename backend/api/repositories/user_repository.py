from abc import ABC, abstractmethod
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.database.models.user_model import UserModel
from backend.database.schemas.user_schema import UserCreate

class IUserRepository(ABC):
    """
    Interface definition for user repository.
    Enforces Dependency Inversion Principle (DIP).
    """

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[UserModel]:
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[UserModel]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserModel]:
        pass

    @abstractmethod
    def create(self, user: UserCreate, hashed_password: str) -> UserModel:
        pass

    @abstractmethod
    def list_all(self) -> List[UserModel]:
        pass


class UserRepository(IUserRepository):
    """
    SQLAlchemy-specific user data access repository.
    """

    def __init__(self, db: Session):
        """
        Initialize user repository with a database session.
        """
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[UserModel]:
        """
        Retrieve user by their primary key ID.
        """
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[UserModel]:
        """
        Retrieve user by their unique username.
        """
        return self.db.query(UserModel).filter(UserModel.username == username).first()

    def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Retrieve user by their unique email.
        """
        return self.db.query(UserModel).filter(UserModel.email == email).first()

    def create(self, user: UserCreate, hashed_password: str) -> UserModel:
        """
        Save a new user record in the database.
        """
        db_user = UserModel(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            role=user.role,
            is_active=True
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def list_all(self) -> List[UserModel]:
        """
        List all registered user accounts.
        """
        return self.db.query(UserModel).all()
