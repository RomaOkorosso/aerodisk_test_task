from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Depends, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger
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
        """
        Return user by access_token
        :param session: AsyncSession
        :param token: str (get from Depends)
        :return: str (token)
        """
        logger.log(f"{datetime.now()} - get current user")
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
        logger.log(f"{datetime.now()} - get current user - {user}")
        return token

    @staticmethod
    def create_access_token(
            data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        create access_token by data
        :param data: dict
        :param expires_delta: datetime.timedelta
        :return: str
        """
        logger.log(f"{datetime.now()} - create access token")
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
        logger.log(f"{datetime.now()} - create access token - {encoded_jwt}")
        return encoded_jwt

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        logger.log(f"{datetime.now()} - verify password")
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        logger.log(f"{datetime.now()} - get password hash")
        return pwd_context.hash(password)

    @staticmethod
    async def authenticate_user(
            username: str, password: str, session: AsyncSession
    ) -> Optional[User]:
        """
        auth user by log/pass pair
        :param username: str
        :param password: str
        :param session: AsyncSession
        :return: models.User
        """
        logger.log(f"{datetime.now()} - authenticate user")
        user = await crud_user.get_user_by_username(session=session, username=username)
        if not user:
            return None
        if not auth_service.verify_password(password, user.password):
            return None
        logger.log(f"{datetime.now()} - authenticate user - {user}")
        return user

    @staticmethod
    async def get_access_token_from_cookie(
            access_token: Optional[str] = Cookie(None),
    ) -> Optional[str]:
        """
        receive Cookie and return access_token
        :param access_token: Cookie
        :return: str
        """
        logger.log(f"{datetime.now()} - get access token from cookie")
        if not access_token:
            return None
        logger.log(f"{datetime.now()} - get access token from cookie - {access_token}")
        return access_token

    @staticmethod
    async def is_user_authed(access_token: Optional[str] = Cookie(None)):
        """
        Check is user authed
        :param access_token: Cookie
        :return: str
        :raise: Unauthorized
        """
        logger.log(f"{datetime.now()} - is user authed")
        if not access_token:
            raise exceptions.Unauthorized("No token in cookies")
        logger.log(f"{datetime.now()} - is user authed - {access_token}")
        return access_token

    @staticmethod
    async def create_token(session: AsyncSession, username: str, access_token: str):
        """
        create token and fill it into db
        :param session: AsyncSession
        :param username: str
        :param access_token: str
        :return: models.Token
        """
        logger.log(f"{datetime.now()} - create token")
        db_user: User = await crud_user.get_user_by_username(
            session=session, username=username
        )
        token = Token(user_id=db_user.id, token=access_token)
        logger.log(f"{datetime.now()} - create token - {token}")
        return await crud_token.create(db=session, obj_in=token)

    @staticmethod
    async def get_username_from_token(
            session: AsyncSession, access_token: str
    ) -> Optional[str]:
        """
        pars access_token and return username
        :param session: AsyncSession
        :param access_token: str
        :return: str
        """
        logger.log(f"{datetime.now()} - get username from token")
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

        logger.log(f"{datetime.now()} - get username from token - {user.username}")
        return user.username

    @staticmethod
    async def get_username_from_cookie(
            session: AsyncSession, access_token: Optional[str] = Cookie(None)
    ) -> Optional[str]:
        """
        Parse Cookie and return username
        :param session: AsyncSession
        :param access_token: str
        :return: str
        """
        logger.log(f"{datetime.now()} - get username from cookie")
        if not access_token:
            return None
        logger.log(f"{datetime.now()} - get username from cookie - {access_token}")
        return await auth_service.get_username_from_token(session, access_token)


auth_service = AuthService()
