from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    BackgroundTasks,
    Request,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas import (
    UserCreate,
    Token,
    User,
    RequestEmail,
    TokenRefreshRequest,
)
from src.services.auth import (
    create_access_token,
    Hash,
    create_refresh_token,
    update_refresh_token,
    verify_refresh_token,
)
from src.services.users import UserService
from src.services.email import send_confirm_email, send_reset_password_email
from src.services.auth import get_email_from_token
from src.database.db import get_db

"""
Authentication and authorization API module.

This module provides endpoints for managing user authentication and authorization. 
It includes functionality for user registration, login, email confirmation, 
password reset, and token management.

Routes:
    /auth/register: Register a new user.
    /auth/login: Authenticate a user and return access and refresh tokens.
    /auth/confirmed_email/{token}: Confirm a user's email address.
    /auth/request-email: Request a new email confirmation.
    /auth/refresh-token: Refresh the access token using a refresh token.
    /auth/reset-password-request: Request a password reset email.
    /auth/reset-password-form/{token}: Display the reset password form.
    /auth/reset-password: Reset the user's password.

Dependencies:
    - Database session (`AsyncSession`) is used for database operations.
    - Background tasks (`BackgroundTasks`) are used for sending emails asynchronously.

Exception Handling:
    - Raises `HTTPException` for invalid data, unauthorized access, or other errors.

"""

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Register a new user.

    Args:
        user_data (UserCreate): The data for the new user.
        background_tasks (BackgroundTasks): Background tasks for sending confirmation email.
        request (Request): The HTTP request object.
        db (AsyncSession): The database session.

    Returns:
        User: The newly created user.

    Raises:
        HTTPException: If the email or username already exists.
    """
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with such email already exists",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with such username already exists",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_confirm_email, new_user.email, new_user.username, request.base_url
    )
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Authenticate a user.

    Args:
        form_data (OAuth2PasswordRequestForm): The login form data containing username and password.
        db (AsyncSession): The database session.

    Returns:
        Token: The access and refresh tokens for the authenticated user.

    Raises:
        HTTPException: If the username or password is invalid, or if the email is not confirmed.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not valid password or username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email must be confirmed",
        )

    access_token = await create_access_token(data={"sub": user.username})
    refresh_token = await create_refresh_token(
        data={"sub": user.username}, user_id=user.id, db=db
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token.token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Confirm a user's email address.

    Args:
        token (str): The confirmation token sent to the user's email.
        db (AsyncSession): The database session.

    Returns:
        dict: A message indicating the result of the confirmation process.

    Raises:
        HTTPException: If the token is invalid or the user does not exist.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Email confirmed successfully"}


@router.post("/request-email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request a new confirmation email.

    Args:
        body (RequestEmail): The email address of the user.
        background_tasks (BackgroundTasks): Background tasks for sending the email.
        request (Request): The HTTP request object.
        db (AsyncSession): The database session.

    Returns:
        dict: A message indicating the result of the request.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_confirm_email, user.email, user.username, request.base_url
        )
        print(
            f"Email sent to {user.email}, username: {user.username}, host: {request.base_url}"
        )
    return {"message": "Check your mailbox for confirmation email"}


@router.post("/refresh-token", response_model=Token)
async def new_token(
    request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Refresh the access token using the refresh token.

    Args:
        request (TokenRefreshRequest): The refresh token request data.
        db (AsyncSession): The database session.

    Returns:
        Token: The new access token and the same refresh token.

    Raises:
        HTTPException: If the refresh token is invalid or expired.
    """
    user = await verify_refresh_token(request.refresh_token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    new_access_token = await create_access_token(data={"sub": user.username})
    await update_refresh_token(
        data={"sub": user.username},
        old_refresh_token=request.refresh_token,
        user_id=user.id,
        db=db,
    )
    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
    }


@router.post("/reset-password-request")
async def reset_password_request(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request a password reset email for the user.

    Args:
        body (RequestEmail): The email address of the user requesting the password reset.
        background_tasks (BackgroundTasks): Background tasks for sending the reset email.
        request (Request): The HTTP request object.
        db (AsyncSession): The database session.

    Returns:
        dict: A message indicating that the reset password email has been sent.

    Raises:
        HTTPException: If the user does not exist or their email is not confirmed.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email must be confirmed",
        )
    background_tasks.add_task(
        send_reset_password_email, user.email, user.username, request.base_url
    )
    return {"message": "Check your mailbox for reset password email"}


@router.get("/reset-password-form/{token}", response_class=HTMLResponse)
async def reset_password_form(
    token: str, request: Request, db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    """
    Display the reset password form.

    Args:
        token (str): The token sent to the user's email for password reset.
        request (Request): The HTTP request object.
        db (AsyncSession): The database session.

    Returns:
        HTMLResponse: The reset password form rendered as an HTML response.

    Raises:
        HTTPException: If the token is invalid or the user does not exist.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    templates = Jinja2Templates(directory="src/templates")

    return templates.TemplateResponse(
        "reset_password_form.html", {"request": request, "token": token}
    )


@router.post("/reset-password")
async def reset_password(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reset the user's password using the provided token and new password.

    Args:
        request (Request): The HTTP request object containing the form data.
        db (AsyncSession): The database session.

    Returns:
        dict: A message indicating that the password has been reset successfully.

    Raises:
        HTTPException: If the token or new password is missing, or if the user does not exist.
    """
    form_data = await request.form()
    token = form_data.get("token")
    new_password = form_data.get("new_password")
    if not token or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid data"
        )
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )

    hashed_password = Hash().get_password_hash(new_password)
    await user_service.reset_password(email, hashed_password)

    return {"message": "Password has been reset successfully"}
