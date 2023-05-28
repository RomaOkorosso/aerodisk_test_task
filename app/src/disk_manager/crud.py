from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.base import CRUDBase
from logger import logger
from app.src.disk_manager.models import Disk
from app.src.disk_manager.schemas import DiskCreate, DiskUpdate


class CRUDDisk(CRUDBase[Disk, DiskCreate, DiskUpdate]):
    async def get_by_name(self, session: AsyncSession, name: str) -> Disk:
        """
        Get disks from DB by name and return it
        :param session: AsyncSession
        :param name: str
        :return: models.Disk
        """
        logger.log(f"Get disk by name: {name}")
        return (
            (await session.execute(select(self.model).where(self.model.name == name)))
            .scalars()
            .first()
        )

    async def create_or_skip(self, session: AsyncSession, obj_in: DiskCreate) -> Disk:
        """
        Create new disk in DB or skip if it is presented yet
        :param session: AsyncSession
        :param obj_in: schemas.DiskCreate
        :return: models.Disk
        """
        logger.log(f"Create or skip disk: {obj_in}")
        if not obj_in.name:
            obj_in.name = obj_in.name
        obj = await self.get_by_name(session, name=obj_in.name)
        if obj:
            return obj
        return await self.create(session, obj_in=obj_in)


crud_disk = CRUDDisk(Disk)
