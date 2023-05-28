import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger
from app.src.base.db.session import get_session_
from app.src.disk_manager.crud import crud_disk
from app.src.disk_manager.service import disk_service
from app.src.disk_manager.schemas import DiskCreate


async def init(session: AsyncSession) -> None:
    """
    For first initial backend service, fill DB with PC mounted disks
    :param session: AsyncSession
    :return: None (results will be filled in DB)
    """
    logger.log("Init disks in db")
    disks = await disk_service.get_disks()
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
    """
    main func for call init disks in DB
    :return: None
    """
    session = await get_session_()
    logger.log(f"{datetime.datetime.now()} - open connection and fill disks in db")
    try:
        await init(session)
        logger.log(f"{datetime.datetime.now()} - filling disks to the DB was successful")
    finally:
        await session.close()
        logger.log(f"{datetime.datetime.now()} - close connection was successful")
