from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import User
from .utils import verify_password, hash_password
from .schemas import UserCreate, UserOut
from .database import get_db


router = APIRouter()
security = HTTPBasic()

@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user in the system.

    This endpoint allows a new user to register by providing a username and password.
    It checks if the username already exists in the database and raises an HTTP 400 error
    if the username is already registered. If the registration is successful, the new user
    is added to the database and returned.

    Args:
        user (UserCreate): The user data containing the username and password.
        db (AsyncSession): The database session dependency.

    Returns:
        UserOut: The newly registered user data.

    Raises:
        HTTPException: If the username is already registered (400 Bad Request).
        HTTPException: If an internal server error occurs (500 Internal Server Error).
    """
    try:
        # Check if username exists
        result = await db.execute(select(User).where(User.username == user.username))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        new_user = User(
            username=user.username,
            hashed_password=hash_password(user.password)
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        print("Registration error:", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate and retrieve the current user based on provided HTTP Basic credentials.

    Args:
        credentials (HTTPBasicCredentials): The HTTP Basic authentication credentials provided by the client.
        db (AsyncSession): The asynchronous database session dependency.

    Returns:
        User: The authenticated user object.

    Raises:
        HTTPException: If the username does not exist or the password is invalid. 
                    The exception is raised with a 401 Unauthorized status code.
    """
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user