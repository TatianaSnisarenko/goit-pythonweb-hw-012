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


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    - **username**: The username of the new user.
    - **email**: The email address of the new user.
    - **password**: The password for the new user (must meet validation criteria - contain at least:
      - one lowercase letter
      - one uppercase letter
      - one digit
      - one special character (@$!%*?&)
      - 8 symbols
    ).
    - verify email: Confirm email address following link in your mailbox.
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
):
    """
    Authenticate a user.
    - **username**: The username of the user.
    - **password**: The password of the user.
    - Email must be confirmed.
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
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirm a user's email address.

    - **token**: The confirmation token sent to the user's email.
    - If the token is valid and the email is not already confirmed, the email will be marked as confirmed.
    - If the email is already confirmed, a message will be returned indicating this.
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
):
    """
    Request a new confirmation email.

    - **email**: The email address of the user.
    - If the email is already confirmed, a message will be returned indicating this.
    - If the email is not confirmed, a new confirmation email will be sent to the user's mailbox.
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
async def new_token(request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh the access token using the refresh token.
    - **refresh_token**: The refresh token used to obtain a new access token.
    - If the refresh token is valid, a new access token will be returned.
    - If the refresh token is invalid or expired, an error will be raised.
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
):
    """
    Reset the user's password using the provided email.
    - **email**: The email address of the user.
    - Check the mailbox for reset password link.
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
):
    """
    Show the reset password form.
    - **token**: The token sent to the user's email for password reset.
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
):
    """
    Reset the user's password using the provided token and new password.
    - **token**: The token sent to the user's email for password reset.
    - **new_password**: The new password for the user.
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
