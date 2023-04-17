import os
import platform
import shutil
import subprocess
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.src import logger
from app.src.disk_manager.crud import crud_disk
from app.src.disk_manager.models import Disk


class DiskService:
    pass


disk_service = DiskService()
