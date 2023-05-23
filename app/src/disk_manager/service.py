import datetime
import platform
import subprocess
import json
from typing import Union

from app.src.base import settings
from app.src.base.exceptions import CommandRun
from logger import logger


class DiskService:
    @staticmethod
    def run_shell_command(command: Union[str, list[str]]) -> str:
        sudo_password = settings.SUDO_PASSWORD
        logger.log(f"{datetime.datetime.now()} - command: {command}")

        if type(command) is str:
            command: list[str] = command.split(" ")

        if platform.system() == "Linux":
            if "sudo" in command:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False,
                    text=True,
                )
                process.communicate(sudo_password + "\n")
            else:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    text=True,
                )
        else:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
            )
        logger.log(f"{datetime.datetime.now()} - {command} returncode: {process.returncode}")
        if ("mount" in command or "umount" in command) and (process.returncode == 0 or process.returncode == 64):
            return "OK"

        stdout, stderr = process.communicate()

        if stderr != "":
            logger.log(
                f"Error {stderr} while running command with params command={command}"
            )
            raise CommandRun(
                f"Error while running command: {stderr} with params command={command}"
            )

        return stdout.strip()

    @staticmethod
    def convert_size_to_mb(size_str: str):
        size_str = size_str.replace(",", ".")
        size = float(size_str[:-1])
        unit = size_str[-1].upper()
        if unit == "G":
            size *= 1024
        elif unit == "T":
            size *= 1024 * 1024
        return int(size)

    @staticmethod
    def get_win_disks():
        disks = []
        command = "wmic logicaldisk get caption,size,filesystem,volumename"
        output = disk_service.run_shell_command(command)
        lines = output.strip().split("\n")[1:]
        for line in lines:
            values = line.split()
            disks.append(
                {
                    "name": values[0],
                    "size": int(values[2]) // 1024,
                    "filesystem": values[1],
                    "mountpoint": values[3] if len(values) > 3 else "",
                }
            )
        return disks

    @staticmethod
    def get_linux_disks():
        disks = []
        command = "lsblk -J"
        output = disk_service.run_shell_command(command)
        if output == "":
            return []
        json_output = json.loads(output)
        for device in json_output["blockdevices"]:
            if device["type"] == "disk":
                size = disk_service.convert_size_to_mb(
                    device["size"]
                )  # конвертация размера диска в МБ
                disks.append(
                    {
                        "name": device["name"],
                        "size": size,
                        "filesystem": "ext4",  # дополнительную информацию нужно получать через другие команды
                        "mountpoint": device.get("mountpoint", ""),
                    }
                )
        return disks

    @staticmethod
    async def get_disks():
        logger.log(f"{datetime.datetime.now()} - Get disks")
        disks = []
        if platform.system() == "Windows":
            disks = disk_service.get_win_disks()
        elif platform.system() == "Linux":
            disks = disk_service.get_linux_disks()
        else:
            logger.log(f"{datetime.datetime.now()} - Unknown OS")
        logger.log(f"{datetime.datetime.now()} - Disks: {disks}")

        return disks


disk_service = DiskService()
