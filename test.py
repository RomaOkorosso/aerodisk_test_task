import pytest
import platform
import subprocess
from unittest.mock import MagicMock, patch

from app.src.base.exceptions import CommandRun
from app.src.disk_manager.service import DiskService, disk_service
import asyncio


# Тест для метода run_shell_command
# Исправленный тест для метода run_shell_command
def test_run_shell_command():
    if platform.system() == "Windows":
        command = "echo test"
        expected_output = "test"
    else:
        command = "printf 'test'"
        expected_output = "test"

    output = disk_service.run_shell_command(command)
    print(output)
    assert output.strip() == expected_output

    # with pytest.raises(CommandRun):
    #     DiskService.run_shell_command("nonexistent_command")


# Тест для метода convert_size_to_mb
def test_convert_size_to_mb():
    assert DiskService.convert_size_to_mb("10M") == 10
    assert DiskService.convert_size_to_mb("1G") == 1024
    assert DiskService.convert_size_to_mb("1T") == 1048576
    assert DiskService.convert_size_to_mb("1,5G") == 1536


# Тест для метода get_win_disks (только для Windows)
@pytest.mark.skipif(platform.system() != "Windows", reason="Тест только для Windows")
def test_get_win_disks():
    disks = DiskService.get_win_disks()
    assert len(disks) > 0
    assert "name" in disks[0]
    assert "size" in disks[0]
    assert "filesystem" in disks[0]
    assert "mountpoint" in disks[0]


# Тест для метода get_linux_disks (только для Linux)
@pytest.mark.skipif(platform.system() != "Linux", reason="Тест только для Linux")
def test_get_linux_disks():
    disks = DiskService.get_linux_disks()
    assert len(disks) > 0
    assert "name" in disks[0]
    assert "size" in disks[0]
    assert "filesystem" in disks[0]
    assert "mountpoint" in disks[0]


# Тест для асинхронного метода get_disks
@pytest.mark.asyncio
@patch("app.src.disk_manager.service.DiskService.get_win_disks")
@patch("app.src.disk_manager.service.DiskService.get_linux_disks")
async def test_get_disks(mock_linux_disks, mock_win_disks):
    mock_win_disks.return_value = [
        {"name": "C:", "size": 1024, "filesystem": "NTFS", "mountpoint": ""}
    ]
    mock_linux_disks.return_value = [
        {"name": "sda", "size": 1024, "filesystem": "ext4", "mountpoint": "/"}
    ]

    with patch.object(platform, "system", return_value="Windows"):
        disks = await DiskService.get_disks()
        assert len(disks) > 0
        assert disks == [
            {"name": "C:", "size": 1024, "filesystem": "NTFS", "mountpoint": ""}
        ]

    with patch.object(platform, "system", return_value="Linux"):
        disks = await DiskService.get_disks()
        assert len(disks) > 0
        assert disks == [
            {"name": "sda", "size": 1024, "filesystem": "ext4", "mountpoint": "/"}
        ]

    with patch.object(platform, "system", return_value="Unknown"):
        disks = await DiskService.get_disks()
        assert len(disks) == 0
