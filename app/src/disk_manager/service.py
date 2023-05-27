import datetime
import platform
import subprocess
import json
from typing import Union, List

from app.src.base import settings
from app.src.base.exceptions import CommandRun
from logger import logger


class DiskService:
    """
    Class for managing Disks
    """

    @staticmethod
    def run_shell_command(command: Union[str, List[str]]) -> str:
        """
        gets command and run it in shell or cmd and return results
        :param command: Union[str, List[str]]
        :return: str - result of running command
        """
        sudo_password = settings.SUDO_PASSWORD
        logger.log(f"{datetime.datetime.now()} - command: {command}")

        if type(command) is str:
            command: List[str] = command.split(" ")

        if platform.system() == "Linux":
            # run command with sudo will be work normally even in .env will be placed right password
            if "sudo" in command:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False,
                    text=True,
                )
                process.communicate(sudo_password + "\n")  # enter sudo password
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

        logger.log(
            f"{datetime.datetime.now()} - {command} returncode: {process.returncode}"
        )

        stdout, stderr = process.communicate()

        if process.returncode == 0 or process.returncode == 64:
            return stdout

        if stderr != "":
            logger.log(
                f"Error {stderr} while running command with params command={command}"
            )
            raise CommandRun(
                f"Error while running command: {stderr} with params command={command}"
            )

        if not stdout.strip():
            logger.log(f"Empty output while running command={command}")
            return "OK"

        return stdout.strip()

    @staticmethod
    def convert_size_to_mb(size_str: str) -> int:
        """
        convert size from any to mb, ex: `64G` to `65536`
        :param size_str: str
        :return: int
        """
        size_str = size_str.replace(",", ".")
        size = float(size_str[:-1])
        unit = size_str[-1].upper()
        unit_grid = ["M", "G", "T", "P", "E"]
        size = float(size) * (1024 * unit_grid.index(unit))  # get position of unit and multiple on it,
        # ex: 64G -> 64 *  (1024 * 1) => 65536
        return int(size)

    @staticmethod
    def get_win_disks() -> List[dict]:
        """
        get all Windows mounted disks
        :return: List[dict]
        """
        disks = []
        command = "wmic logicaldisk get caption,size,filesystem,volumename"
        output = disk_service.run_shell_command(command)
        lines = output.strip().split("\n")[1:]
        for line in lines:
            values = line.split()
            disks.append(
                {
                    "name": values[0],
                    "size": int(values[2]) // 1024,  # // 1024, bcs in windows size in bytes
                    "filesystem": values[1],
                    "mountpoint": values[3] if len(values) > 3 else "",
                }
            )
        return disks

    @staticmethod
    def get_linux_disks() -> List[dict]:
        """
        get all linux mounted disks and return it
        :return: List[dict]
        """
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
    async def get_disks() -> List[dict]:
        """
        analyze system, get disks and return their
        :return: List[dict]
        """
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
