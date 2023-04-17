import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.src import logger
from app.src.base.db.session import get_session_
from app.src.disk_manager.crud import crud_disk
from app.src.disk_manager.routes import get_disks
from app.src.disk_manager.schemas import DiskCreate, DiskUpdate


async def init(session: AsyncSession):
    logger.log("Init disks in db")
    disks = await get_disks()
    logger.log(f"Disks got")
    for disk in disks:
        try:
            db_disk = await crud_disk.get_by_name(session=session, name=disk["name"])
            if not db_disk:
                await crud_disk.create(db=session, obj_in=DiskCreate(**disk))
        except Exception as e:
            with open(
                f"./logs/{datetime.datetime.now().date().strftime('%Y-%m-%d')}.log", "a"
            ) as f:
                f.write(
                    f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {e}\n"
                )
    logger.log(f"Disks inited")


async def init_disks_in_db():
    session = await get_session_()
    try:
        await init(session)
    finally:
        await session.close()
