import platform
import string
from datetime import datetime

from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder

from app.src.base.exceptions import CommandRun
from logger import logger
from app.src.auth.service import auth_service
from app.src.disk_manager.service import disk_service
from app.src.base import get_session
from app.src.disk_manager.crud import crud_disk
from app.src.disk_manager.models import Disk
from app.src.disk_manager.schemas import DiskCreate, DiskUpdate

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def get_access_token_from_cookies(request: Request):
    return request.cookies.get("access_token")


@router.get("/disks", response_class=HTMLResponse)
async def get_disks_view(
    request: Request,
    token: str = Depends(auth_service.is_user_authed),
    session: AsyncSession = Depends(get_session),
):
    logger.log(f"{datetime.now()} - Get disks view")
    disks = await crud_disk.get_all(db=session)
    context = {"request": request, "access_token": token, "disks": disks}
    logger.log(f"{datetime.now()} - Context: {context}")
    return templates.TemplateResponse("disks.html", context)


@router.post("/disks/new")
async def create_disk(
    request: Request,
    disk: DiskCreate,
    session: AsyncSession = Depends(get_session),
    token=Depends(auth_service.is_user_authed),
):
    logger.log(f"{datetime.now()} - Create disk: {disk.dict()}")
    db_disk = await crud_disk.get_by_name(session=session, name=disk.name)

    if db_disk:
        # Вместо возвращения HTML-ответа возвращаем JSON-ответ с кодом ошибки и сообщением
        return JSONResponse(
            content={"error": f"Disk with name '{disk.name}' already exists"},
            status_code=400,
        )

    new_disk: Disk = await crud_disk.create(db=session, obj_in=disk)
    logger.log(f"{datetime.now()} - New disk: {new_disk.__dict__}")

    # Возвращаем JSON-ответ с ID созданного диска и кодом успешного выполнения
    return JSONResponse(content=jsonable_encoder(new_disk), status_code=201)


@router.get("/disks/{disk_id}", response_class=HTMLResponse)
async def get_disk_view(
    request: Request,
    disk_id: int,
    session: AsyncSession = Depends(get_session),
    token=Depends(auth_service.is_user_authed),
):
    logger.log(f"{datetime.now()} - Get disk view with id '{disk_id}'")
    db_disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)
    context = {"request": request, "disk": db_disk, "access_token": token}
    return templates.TemplateResponse("disk.html", context)


@router.post("/disks/{disk_id}/update")
async def update_disk(
    request: Request,
    disk_id: int,
    disk: DiskUpdate,
    session: AsyncSession = Depends(get_session),
    token=Depends(auth_service.is_user_authed),
):
    logger.log(f"{datetime.now()} - Update disk with id '{disk_id}'")
    db_disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)
    print(f"updated disk: {update_disk}")
    updated_disk = await crud_disk.update_disk(session, db_obj=db_disk, obj_in=disk)
    logger.log(f"{datetime.now()} - Updated disk: {updated_disk.__dict__}")
    return JSONResponse(
        content={"message": "Disk updated", "disk": updated_disk, "access_token": token}
    )


@router.post("/disks/{disk_id}/format")
async def format_disk(
    request: Request,
    disk_id: int,
    session: AsyncSession = Depends(get_session),
    token=Depends(auth_service.is_user_authed),
):
    logger.log(f"{datetime.now()} - Format disk with id '{disk_id}'")
    db_disk: Disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)
    # Windows disk formatting
    if platform.system() == "Windows":
        format_cmd = ["format", db_disk.name, "/FS:NTFS", "/Q"]
    else:
        format_cmd = ["sudo", "mkfs.ext4", db_disk.name]

    try:
        disk_service.run_shell_command(format_cmd)
    except CommandRun as err:
        context = {
            "request": request,
            "error": f"Disk with id '{disk_id}' not formatted, err: {err}",
        }
        return templates.TemplateResponse("error.html", context)

    context = {
        "request": request,
        "access_token": token,
        "disks": await disk_service.get_disks(),
    }
    return templates.TemplateResponse("disks.html", context=context)


@router.post("/disks/{disk_id}/mount")
async def mount_disk(
    request: Request,
    disk_id: int,
    session: AsyncSession = Depends(get_session),
    token=Depends(auth_service.is_user_authed),
):
    logger.log(f"{datetime.now()} - Mount disk with id '{disk_id}'")

    db_disk: Disk = await crud_disk.get(session, disk_id)

    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)

    # Mount disk
    if platform.system() == "Windows":
        mount_cmd = ["mountvol", db_disk.name, db_disk.mountpoint]
    else:
        mount_cmd = [
            "sudo",
            "mount",
            db_disk.name,
            db_disk.mountpoint,
            "-o",
            f"size={db_disk.size}M",
        ]

    try:
        disk_service.run_shell_command(mount_cmd)
    except CommandRun as err:
        context = {
            "request": request,
            "error": f"Disk with id '{disk_id}' not mounted, err: {err}",
        }
        return templates.TemplateResponse("error.html", context)

    logger.log(
        f"{datetime.now()} - disk {disk_id} was successfully formatted and mounted"
    )

    return RedirectResponse(url=f"/disks/{disk_id}")


@router.post("/disks/{disk_id}/unmount")
async def umount_disk(
    request: Request,
    disk_id: int,
    session: AsyncSession = Depends(get_session),
    token=Depends(auth_service.is_user_authed),
):
    logger.log(f"{datetime.now()} - Umount disk with id '{disk_id}'")
    db_disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)

    if platform.system() == "Windows":
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
    else:
        # Unmount the disk
        cmd = ["sudo", "umount", "-l", db_disk.mountpoint]

    try:
        disk_service.run_shell_command(cmd)
    except CommandRun as err:
        context = {
            "request": request,
            "error": f"Disk with id '{disk_id}' not unmounted, err: {err}",
        }
        return templates.TemplateResponse("error.html", context)
    logger.log(f"{datetime.now()} - delete disk, disk.id={disk_id}")
    await crud_disk.remove(db=session, id=db_disk.id)
    logger.log(f"{datetime.now()} - disk deleted")

    return RedirectResponse(url=f"/disks/{disk_id}")


@router.post("/disks/{disk_id}/wipefs")
async def wipefs_disk(
    request: Request,
    disk_id: int,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(auth_service.is_user_authed),
):
    db_disk = await crud_disk.get(session, disk_id)
    if not db_disk:
        context = {"request": request, "error": f"Disk with id '{disk_id}' not found"}
        return templates.TemplateResponse("error.html", context)
    # Wipe disk header
    cmd = ["sudo", "wipefs", "-a", db_disk.mountpoint]

    try:
        disk_service.run_shell_command(cmd)
    except CommandRun as err:
        context = {
            "request": request,
            "error": f"Disk with id '{disk_id}' not wiped, err: {err}",
        }
        return templates.TemplateResponse("error.html", context)

    context = {
        "request": request,
        "disks": await disk_service.get_disks(),
        "access_token": token,
    }
    return templates.TemplateResponse("disks.html", context=context)
