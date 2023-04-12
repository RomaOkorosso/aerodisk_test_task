from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.auth.models import User, Token
from app.src.auth.schemas import UserCreate, UserUpdate, TokenCreate, TokenUpdate
from app.src.base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_user_by_username(self, session: AsyncSession, username: str):
        db_user = (
            await session.execute(
                select(self.model).where(self.model.username == username)
            )
        ).scalar_one_or_none()
        return db_user


crud_user = CRUDUser(User)


class CRUDToken(CRUDBase[Token, TokenCreate, TokenUpdate]):
    async def get_by_access_token(self, session: AsyncSession, access_token: str):
        return (
            await session.execute(
                select(self.model).where(self.model.token == access_token)
            )
        ).scalar_one_or_none()

    async def revoke(self, session: AsyncSession, token: str) -> None:
        query = delete(self.model).where(self.model.token == token)
        await session.execute(query)
        await session.commit()


crud_token = CRUDToken(Token)
