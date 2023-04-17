from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, status, Form
from fastapi.security import HTTPBasicCredentials, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.src.base import logger
from app.src.auth import schemas, service, models, crud
from app.src.auth.crud import crud_token
from app.src.auth.models import Token
from app.src.base import get_session, settings
from app.src.base.exceptions import WeakPassword

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


async def get_context(request: Request, session: AsyncSession = Depends(get_session)):
    logger.log(f"{datetime.now()} - (auth.routes) Get context for {request.url.path}")
    access_token = await service.auth_service.get_access_token_from_cookie(
        request.cookies.get("access_token")
    )
    if access_token:
        username = await service.auth_service.get_username_from_token(
            session=session, access_token=access_token
        )
    else:
        username = None

    logger.log(
        f"{datetime.now()} - (auth.routes) Context: {request.url.path} - {access_token} - {username}"
    )

    return {"request": request, "access_token": access_token, "username": username}


@router.get("/register")
async def register(request: Request, context: dict = Depends(get_context)):
    logger.log(f"{datetime.now()} - (auth.routes) Get register page")
    return templates.TemplateResponse("register.html", context)


@router.post("/register")
async def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    logger.log(f"{datetime.now()} - (auth.routes) Register post")
    try:
        user = schemas.UserCreate(
            full_name=full_name, email=email, username=username, password=password
        )
    except WeakPassword:
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "Weak password"}
        )

    password_hash = service.auth_service.get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = password_hash
    new_user = models.User(**user_dict)
    new_user: models.User = await crud.crud_user.create(db=session, obj_in=new_user)

    access_token = service.auth_service.create_access_token(
        {"username": new_user.username}
    )
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,
        expires=1800,
        secure=True,
    )

    # Save access token in database
    await service.auth_service.create_token(
        session=session, username=new_user.username, access_token=access_token
    )

    logger.log(
        f"{datetime.now()} - (auth.routes) Register post - {new_user.__dict__} - {access_token}"
    )

    return response


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request, context: dict = Depends(get_context), next: str = ""):
    logger.log(f"{datetime.now()} - (auth.routes) Get login page")
    context["next"] = next
    logger.log(f"{datetime.now()} - (auth.routes) Get login page - {context}")
    return templates.TemplateResponse("login.html", context)


@router.post("/login")
async def login_post(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    context: dict = Depends(get_context),
    next: str = None,
):
    logger.log(f"{datetime.now()} - (auth.routes) Login post")
    user = await service.auth_service.authenticate_user(
        username=form_data.username, password=form_data.password, session=session
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = service.auth_service.create_access_token(data={"sub": user.username})
    token = Token(token=access_token, user_id=user.id)
    await crud_token.create(session, obj_in=token)

    response = RedirectResponse(url="/auth/set_token")
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=True,
    )
    context["current_user"] = user
    context["access_token"] = access_token
    context["next"] = next
    logger.log(
        f"{datetime.now()} - (auth.routes) Login post - {user.__dict__} - {access_token}"
    )
    return response


@router.get("/logout", response_class=HTMLResponse)
async def logout(
    request: Request,
    access_token: str = Cookie(None),
    session: AsyncSession = Depends(get_session),
):
    logger.log(f"{datetime.now()} - (auth.routes) Logout")
    if access_token:
        await crud_token.revoke(session, access_token)

    response = RedirectResponse(url="/auth/login")
    response.delete_cookie(key="access_token")
    logger.log(f"{datetime.now()} - (auth.routes) Logout - {access_token}")
    return response


@router.post("/set_token", response_class=HTMLResponse)
async def set_token_view(request: Request, context: dict = Depends(get_context)):
    logger.log(f"{datetime.now()} - (auth.routes) Set token")
    return templates.TemplateResponse("set_token.html", context)


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    logger.log(f"{datetime.now()} - (auth.routes) Login for access token")
    user = await service.auth_service.authenticate_user(
        session, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = service.auth_service.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    token = Token(token=access_token, user_id=user.id)
    await crud_token.create(session, obj_in=token)
    logger.log(
        f"{datetime.now()} - (auth.routes) Login for access token - {user.__dict__} - {access_token}"
    )
    return access_token
