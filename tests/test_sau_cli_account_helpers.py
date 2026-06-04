import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sau_cli_account_helpers import resolve_account_file


class ResolveAccountFileTests(unittest.TestCase):
    """验证账号文件路径生成只接受安全账号名，并且不会逃出 cookies 目录。"""

    def test_rejects_invalid_account_names(self) -> None:
        """路径分隔符必须被账号名白名单直接拒绝。"""

        for account_name in ("../evil", "a/b", "a\\b"):
            with self.subTest(account_name=account_name):
                with self.assertRaises(ValueError):
                    resolve_account_file("douyin", account_name)

    def test_rejects_paths_that_escape_cookies_directory(self) -> None:
        """即使绕过账号名白名单，最终解析路径也不能逃出 cookies 目录。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            cookies_root = Path(temp_dir)

            with patch("sau_cli_account_helpers.resolve_runtime_home", return_value=cookies_root):
                with patch("sau_cli_account_helpers._require_safe_account_name", side_effect=lambda value: value):
                    with self.assertRaises(ValueError):
                        resolve_account_file("douyin", "x/../../evil")
