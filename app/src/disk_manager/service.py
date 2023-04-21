import platform
import subprocess
import json

from app.src import logger


class DiskService:
    @staticmethod
    def run_shell_command(command: str | list[str], shell: bool = False) -> str:
        if type(command) is list:
            command = "".join(c for c in command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        stdout, _ = process.communicate()
        if _ is not None:
            logger.log(f"Error while running command: {_} with params command={command}, shell={shell}")
        output: str = stdout.decode("utf-8")
        return output

    @staticmethod
    def convert_size_to_mb(size_str):
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
        output = disk_service.run_shell_command(command, shell=True)
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
        logger.log("Get disks")
        disks = []
        if platform.system() == "Windows":
            disks = disk_service.get_win_disks()
        elif platform.system() == "Linux":
            disks = disk_service.get_linux_disks()
        else:
            logger.log("Unknown OS")
        logger.log(f"Disks: {disks}")

        return disks


disk_service = DiskService()
