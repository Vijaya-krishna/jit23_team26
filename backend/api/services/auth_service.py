import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from backend.utils.config import settings
from backend.api.repositories.user_repository import IUserRepository
from backend.database.schemas.user_schema import UserCreate, UserLogin, TokenResponse
from backend.database.models.user_model import UserModel

# Configure log reporting
logger = logging.getLogger("auth_service")
logging.basicConfig(level=logging.INFO)

# Setup password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Business service layer managing user registration, authentication, and JWT lifecycle.
    """

    def __init__(self, user_repository: IUserRepository):
        """
        Dependency injects user repository interface.
        Follows Dependency Inversion Principle.
        """
        self.user_repo = user_repository

    def hash_password(self, password: str) -> str:
        """
        Securely hash clear-text passwords using bcrypt algorithm.
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Compare plain password string with DB hashed representation.
        """
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Generate signed JWT access token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    def register_user(self, user_data: UserCreate) -> UserModel:
        """
        Register a new administrator or operator user.
        Raises HTTP exceptions if username or email is already registered.
        """
        logger.info(f"Attempting to register user: {user_data.username}")

        # Check unique constraint for username
        existing_username = self.user_repo.get_by_username(user_data.username)
        if existing_username:
            logger.warning(f"Registration failed: Username '{user_data.username}' already exists.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already registered."
            )

        # Check unique constraint for email
        existing_email = self.user_repo.get_by_email(user_data.email)
        if existing_email:
            logger.warning(f"Registration failed: Email '{user_data.email}' already exists.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered."
            )

        # Hashing and writing record
        hashed_pw = self.hash_password(user_data.password)
        db_user = self.user_repo.create(user_data, hashed_password=hashed_pw)
        logger.info(f"Successfully registered user: {db_user.username} with ID {db_user.id}")
        return db_user

    def authenticate_user(self, login_data: UserLogin) -> TokenResponse:
        """
        Verify login credentials and issue signed JWT token.
        """
        logger.info(f"Authenticating user login: {login_data.username}")

        user = self.user_repo.get_by_username(login_data.username)
        # If not found by username, try by email
        if not user:
            user = self.user_repo.get_by_email(login_data.username)

        if not user or not self.verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Failed authentication attempt for: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning(f"Authentication rejected: User account {user.username} is deactivated.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is deactivated."
            )

        # Issue JWT Access Token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_payload = {
            "sub": user.username,
            "role": user.role,
            "email": user.email
        }
        access_token = self.create_access_token(
            data=token_payload,
            expires_delta=access_token_expires
        )

        logger.info(f"Successfully authenticated user: {user.username}")
        return TokenResponse(
            access_token=access_token,
            role=user.role,
            username=user.username
        )
