from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Depends, Cookie
from fastapi.logger import logger
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.base import settings
from app.src.auth.crud import crud_user, crud_token
from app.src.auth.models import User, Token
from app.src.auth.schemas import TokenData
from app.src.base.db import get_session
from app.src.base import exceptions

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class AuthService:
    @staticmethod
    async def get_current_user(
        session: AsyncSession = Depends(get_session),
        token: str = Depends(oauth2_scheme),
    ) -> str:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=401, detail="Invalid authentication token"
                )
            token_data = TokenData(username=username, access_token=token)
        except JWTError as e:
            raise HTTPException(
                status_code=401, detail="Invalid authentication token"
            ) from e

        user: User = await crud_user.get_user_by_username(
            session=session, username=token_data.username
        )
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return token

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    async def authenticate_user(
        username: str, password: str, session: AsyncSession
    ) -> Optional[User]:
        user = await crud_user.get_user_by_username(session=session, username=username)
        if not user:
            return None
        if not auth_service.verify_password(password, user.password):
            return None
        return user

    @staticmethod
    async def get_access_token_from_cookie(
        access_token: Optional[str] = Cookie(None),
    ) -> Optional[str]:
        if not access_token:
            return None
        return access_token

    @staticmethod
    async def is_user_authed(access_token: Optional[str] = Cookie(None)):
        if not access_token:
            raise exceptions.Unauthorized("No token in cookies")
        return access_token

    @staticmethod
    async def create_token(session: AsyncSession, username: str, access_token: str):
        db_user: User = await crud_user.get_user_by_username(
            session=session, username=username
        )
        token = Token(user_id=db_user.id, token=access_token)
        return await crud_token.create(db=session, obj_in=token)

    @staticmethod
    async def get_username_from_token(
        session: AsyncSession, access_token: str
    ) -> Optional[str]:
        try:
            payload = jwt.decode(
                access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                return None
            token_data = TokenData(username=username, access_token=access_token)
        except JWTError as e:
            return None

        user = await crud_user.get_user_by_username(
            session=session, username=token_data.username
        )
        if user is None:
            return None
        return user.username

    @staticmethod
    async def get_username_from_cookie(
        session: AsyncSession, access_token: Optional[str] = Cookie(None)
    ) -> Optional[str]:
        if not access_token:
            return None
        return await auth_service.get_username_from_token(session, access_token)


auth_service = AuthService()
