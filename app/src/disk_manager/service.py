import os
import platform
import shutil
import subprocess
import psutil
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.disk_manager.crud import crud_disk
from app.src.disk_manager.models import Disk


class DiskService:
    @staticmethod
    def get_windows_disks():
        partitions = psutil.disk_partitions()
        disks = []
        for partition in partitions:
            if "cdrom" in partition.opts or partition.fstype == "":
                continue
            disk = partition.mountpoint
            size = int(shutil.disk_usage(disk).total / 1024)
            disks.append(Disk(path=disk, name=os.path.basename(disk), size=size))

        return disks

    @staticmethod
    def get_unix_disks():
        output = subprocess.check_output(["df"])
        lines = output.decode().strip().split("\n")[1:]
        disks = []
        for line in lines:
            parts = line.split()
            path = parts[-1]
            size = int(int(parts[1]) / 1024)
            disks.append(Disk(path=path, name=os.path.basename(path), size=size))
        return disks

    @staticmethod
    async def get_disks(session: AsyncSession) -> list[Disk]:
        disks = []
        if platform.system() == "Windows":
            disks += disk_service.get_windows_disks()
        else:
            disks += disk_service.get_unix_disks()
        for disk in disks:
            await crud_disk.create_or_skip(session, obj_in=disk)
        return disks


disk_service = DiskService()
