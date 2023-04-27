import unittest
import platform
import subprocess
from unittest.mock import MagicMock, patch

from app.src.disk_manager.service import DiskService
import asyncio


class TestDiskService(unittest.TestCase):
    def test_run_shell_command(self):
        if platform.system() == "Windows":
            command = "echo test"
            expected_output = "test"
        else:
            command = "printf 'test'"
            expected_output = "test"

        output = DiskService.run_shell_command(command)
        self.assertEqual(output.strip(), expected_output)

    def test_convert_size_to_mb(self):
        self.assertEqual(DiskService.convert_size_to_mb("1G"), 1024)
        self.assertEqual(DiskService.convert_size_to_mb("1T"), 1024 * 1024)
        self.assertEqual(DiskService.convert_size_to_mb("1024M"), 1024)

    @unittest.skipIf(platform.system() != "Windows", "Skipping Windows specific test")
    def test_get_win_disks(self):
        disks = DiskService.get_win_disks()
        self.assertIsNotNone(disks)
        self.assertGreater(len(disks), 0)

    @unittest.skipIf(platform.system() != "Linux", "Skipping Linux specific test")
    def test_get_linux_disks(self):
        disks = DiskService.get_linux_disks()
        self.assertIsNotNone(disks)
        self.assertGreater(len(disks), 0)

    @patch("app.src.disk_manager.service.DiskService.get_win_disks")
    @patch("app.src.disk_manager.service.DiskService.get_linux_disks")
    def test_get_disks(self, mock_linux_disks, mock_win_disks):
        mock_win_disks.return_value = [
            {"name": "C:", "size": 1024, "filesystem": "NTFS", "mountpoint": ""}
        ]
        mock_linux_disks.return_value = [
            {"name": "sda", "size": 1024, "filesystem": "ext4", "mountpoint": "/"}
        ]

        with patch.object(platform, "system", return_value="Windows"):
            disks = asyncio.run(DiskService.get_disks())
            self.assertGreater(len(disks), 0)
            self.assertEqual(
                disks,
                [{"name": "C:", "size": 1024, "filesystem": "NTFS", "mountpoint": ""}],
            )

        with patch.object(platform, "system", return_value="Linux"):
            disks = asyncio.run(DiskService.get_disks())
            self.assertGreater(len(disks), 0)
            self.assertEqual(
                disks,
                [
                    {
                        "name": "sda",
                        "size": 1024,
                        "filesystem": "ext4",
                        "mountpoint": "/",
                    }
                ],
            )

        with patch.object(platform, "system", return_value="Unknown"):
            disks = asyncio.run(DiskService.get_disks())
            self.assertEqual(len(disks), 0)


if __name__ == "__main__":
    unittest.main()
