import platform
import string

from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Union
import os
import subprocess

from app.src.auth.service import auth_service
from app.src.base import get_session
from app.src.disk_manager.crud import crud_disk
from app.src.disk_manager.models import Disk
from app.src.disk_manager.schemas import DiskCreate, DiskUpdate

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def get_disks() -> list[dict[str, Union[int, str]]]:
    disks = []
    with open("/proc/mounts", "r") as mounts:
        for line in mounts:
            parts = line.strip().split()
            if parts[2] == "ext4" and "/dev/" in parts[0]:
                cmd = ["df", "-h", parts[1]]
            output = subprocess.check_output(cmd).decode().strip().split("\n")[1]
            parts = output.split()
            disks.append(
                {
                    "name": parts[0],
                    "size": int(parts[1].replace("G", "")),  # remove 'G' from size
                    "filesystem": parts[2],
                    "mountpoint": parts[5],
                }
            )
    return disks


async def get_access_token_from_cookies(request: Request):
    return request.cookies.get("access_token")


@router.get("/disks", response_class=HTMLResponse)
async def get_disks_view(
        request: Request,
        token: str = Depends(auth_service.is_user_authed),
        session: AsyncSession = Depends(get_session),
):
    disks = await crud_disk.get_all(db=session)
    context = {"request": request, "access_token": token, "disks": disks}
    return templates.TemplateResponse("disks.html", context)


@router.post('disks/new')
async def create_disk(
        request: Request,
        disk: DiskCreate,
        session: AsyncSession = Depends(get_session),
        token=Depends(auth_service.is_user_authed)
):
    db_disk = await crud_disk.get_by_name(session=session, name=disk.name)
    if db_disk:
        context = {"request": request, "error": f"Disk with name '{disk.name}' already exists"}
        return templates.TemplateResponse("error.html", context)
    disk.mountpoint = disk.name
    new_disk: Disk = await crud_disk.create(db=session, obj_in=disk)
    return RedirectResponse(url=f"/disks/{new_disk.id}/mount", status_code=303)


@router.get("/disks/{disk_id}", response_class=HTMLResponse)
async def get_disk_view(
        request: Request, disk_id: int, session: AsyncSession = Depends(get_session)
):
    db_disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)
    context = {"request": request, "disk": db_disk}
    return templates.TemplateResponse("disk.html", context)


@router.post("/disks/{disk_id}/update")
async def update_disk(
        request: Request,
        disk_id: int,
        disk: DiskUpdate,
        session: AsyncSession = Depends(get_session),
):
    db_disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)
    await crud_disk.update(session, db_obj=db_disk, obj_in=disk)
    return RedirectResponse(url=f"/disks/{disk_id}")


@router.post("/disks/{disk_id}/format")
async def format_disk(
        request: Request, disk_id: int, session: AsyncSession = Depends(get_session)
):
    db_disk: Disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)
    # Windows disk formatting
    if os.name == "nt":
        cmd = ["format", f"{db_disk.name}:\\", "/fs:NTFS", "/q"]
        subprocess.run(cmd)
    # Unix disk formatting
    else:
        cmd = ["sudo", "mkfs.ext4", db_disk.name]
        subprocess.run(cmd)

    return RedirectResponse(url=f"/disks/{disk_id}")


@router.post("/disks/{disk_id}/mount")
async def mount_disk(
        request: Request, disk_id: int, session: AsyncSession = Depends(get_session)
):
    db_disk: Disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)
    # Mount disk
    if platform.system() == "Windows":
        cmd = ["mountvol", db_disk.name, db_disk.mountpoint]
    else:
        cmd = ["sudo", "mount", db_disk.name, db_disk.mountpoint]
    subprocess.run(cmd)

    return RedirectResponse(url=f"/disks/{disk_id}")


@router.post("/disks/{disk_id}/umount")
async def umount_disk(
        request: Request, disk_id: int, session: AsyncSession = Depends(get_session)
):
    db_disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)

    if os.name == "nt":
        # Get the drive letter from the mountpoint
        drive_letter = db_disk.mountpoint.split(":")[0]

        # Check if the drive letter is valid
        if drive_letter.upper() not in string.ascii_uppercase:
            context = {
                "request": request,
                "error": f"Invalid drive letter for mountpoint {db_disk.mountpoint}",
            }
            return templates.TemplateResponse("error.html", context)

        # Unmount the disk
        cmd = ["mountvol", drive_letter + ":", "/p"]
        subprocess.run(cmd, shell=True)
    else:
        # Unmount the disk
        cmd = ["sudo", "umount", db_disk.mountpoint]
        subprocess.run(cmd)

    return RedirectResponse(url=f"/disks/{disk_id}")


@router.post("/disks/{disk_id}/wipefs")
async def wipefs_disk(
        request: Request, disk_id: int, session: AsyncSession = Depends(get_session)
):
    db_disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)
    # Wipe disk header
    cmd = ["sudo", "wipefs", "-a", db_disk.path]
    subprocess.run(cmd)

    return RedirectResponse(url=f"/disks/{disk_id}")
