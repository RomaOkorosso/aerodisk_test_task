from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from sqlalchemy import select, insert
from pydantic import BaseModel

from app.src.base.db import Base

# Define custom types for SQLAlchemy model, and Pydantic schemas
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """Base class that can be extended by other action classes.
           Provides basic CRUD and listing operations.
        :param model: The SQLAlchemy model
        :type model: Type[ModelType]
        """
        self.model = model

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        res: Result = await db.execute(select(self.model).offset(skip).limit(limit))
        res: list[ModelType] = res.scalars().all()
        return res

    async def get_by_ids(self, db: AsyncSession, *, ids: list[int]) -> List[ModelType]:
        return (
            (await db.execute(select(self.model).where(self.model.id.in_(ids))))
            .scalars()
            .all()
        )

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        return (
            await db.execute(select(self.model).where(self.model.id == id))
        ).scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        # db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> ModelType:
        obj = (await db.execute(db.query(self.model).get(id))).scalars().first()
        await db.delete(obj)
        await db.commit()
        return obj

    async def get_all(
        self, db: AsyncSession, only_ids: bool = False
    ) -> Union[List[ModelType], List[int]]:
        """
        Get all objects from the database or only object ids
        :param db: The database session
        :type db: AsyncSession
        :param only_ids: If True, only object ids will be returned, defaults to False
        :type only_ids: bool, optional
        :return: List of objects or list of object ids
        """
        if only_ids:
            res: list[tuple[int]] = (
                (await db.execute(select(self.model.id))).scalars().all()
            )
            return [x[0] for x in res]
        return (await db.execute(select(self.model))).scalars().all()
