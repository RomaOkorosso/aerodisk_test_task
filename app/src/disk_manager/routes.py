import asyncio
import platform
import string
from datetime import datetime

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


async def get_disks():
    disks = []
    if platform.system() == 'Windows':
        command = 'wmic logicaldisk get caption,size,filesystem,volumename'
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, _ = process.communicate()
        output = stdout.decode('utf-8')
        lines = output.strip().split('\n')[1:]
        for line in lines:
            values = line.split()
            disks.append({
                'name': values[0],
                'size': int(values[2]) // 1024,
                'filesystem': values[1],
                'mountpoint': values[3] if len(values) > 3 else ''
            })
    elif platform.system() == 'Linux':
        command = 'df -h'
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, _ = process.communicate()
        output = stdout.decode('utf-8')
        lines = output.strip().split('\n')[1:]
        for line in lines:
            values = line.split()
            size = values[1]
            if size[-1] == 'G':
                size = float(size[:-1]) * 1024
            elif size[-1] == 'M':
                size = float(size[:-1])
            else:
                size = 0
            disks.append({
                'name': values[0],
                'size': size,
                'filesystem': "ext4",
                'mountpoint': values[5]
            })
            with open(f"logs/{datetime.now().date().strftime('%Y-%m-%d')}.log", "a") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {disks[-1]}\n")

    else:
        with open(f"logs/{datetime.now().date().strftime('%Y-%m-%d')}.log", "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Not a valid system\n")

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
