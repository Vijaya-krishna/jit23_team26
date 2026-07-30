from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.schemas.user_schema import UserCreate, UserResponse, UserLogin, TokenResponse
from backend.api.repositories.user_repository import UserRepository
from backend.api.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Dependency Injection utility to construct AuthService with UserRepository.
    """
    user_repo = UserRepository(db)
    return AuthService(user_repo)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    """
    Register a new operator or admin user into the simulation environment.
    """
    return auth_service.register_user(user_data)


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    """
    Authenticate users with username/email and password, returning a JWT token.
    """
    return auth_service.authenticate_user(login_data)
