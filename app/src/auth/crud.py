from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger
from app.src.auth.models import User, Token
from app.src.auth.schemas import UserCreate, UserUpdate, TokenCreate, TokenUpdate
from app.src.base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_user_by_username(self, session: AsyncSession, username: str):
        logger.log(f"{datetime.now()} - get user by username: {username}")
        db_user = (
            await session.execute(
                select(self.model).where(self.model.username == username)
            )
        ).scalar_one_or_none()
        logger.log(f"{datetime.now()} - User: {db_user}")
        return db_user


crud_user = CRUDUser(User)


class CRUDToken(CRUDBase[Token, TokenCreate, TokenUpdate]):
    async def get_by_access_token(self, session: AsyncSession, access_token: str):
        logger.log(f"{datetime.now()} - get token by access token: {access_token}")
        return (
            await session.execute(
                select(self.model).where(self.model.token == access_token)
            )
        ).scalar_one_or_none()

    async def revoke(self, session: AsyncSession, token: str) -> None:
        logger.log(f"{datetime.now()} - revoke token: {token}")
        query = delete(self.model).where(self.model.token == token)
        await session.execute(query)
        await session.commit()


crud_token = CRUDToken(Token)
