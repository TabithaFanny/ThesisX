"""Register .wtz file-type association on Windows.

Called once during application startup. Writes to HKCU (no admin required).
Skips silently on non-Windows platforms or if anything goes wrong.
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

_EXTENSION = ".wtz"
_PROG_ID = "ThesisX.wtz"
_FILE_DESC = "ThesisX 文档"
_ICO_NAME = "wtz_file_icon.ico"


def _get_resource_dir() -> str:
    """Return the absolute path to app/resources, works both in dev and packaged mode."""
    if getattr(sys, "frozen", False):
        # PyInstaller packaged: resources under _MEIPASS or next to exe
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(base, "app", "resources")
    else:
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources",
        )


def _get_open_command() -> str:
    """Return the shell open command for .wtz files."""
    if getattr(sys, "frozen", False):
        # Packaged exe — just use ThesisX.exe itself
        exe = sys.executable
        return f'"{exe}" "%1"'
    else:
        # Dev mode — use pythonw + main.py
        python = sys.executable
        main_py = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "main.py",
        )
        return f'"{python}" "{main_py}" "%1"'


def register_wtz_file_type():
    """Register .wtz file association in Windows registry (HKCU).

    Safe to call on every startup — it's fast and idempotent.
    """
    if sys.platform != "win32":
        return

    ico_path = os.path.join(_get_resource_dir(), _ICO_NAME)
    if not os.path.isfile(ico_path):
        logger.warning("WTZ 图标文件不存在，跳过文件关联注册: %s", ico_path)
        return

    open_cmd = _get_open_command()

    try:
        import winreg

        # 1. .wtz -> ThesisX.wtz
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{_EXTENSION}") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, _PROG_ID)

        # 2. ProgID description
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{_PROG_ID}") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, _FILE_DESC)

        # 3. DefaultIcon
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, rf"Software\Classes\{_PROG_ID}\DefaultIcon"
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, ico_path)

        # 4. shell\open\command
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, rf"Software\Classes\{_PROG_ID}\shell\open\command"
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, open_cmd)

        # Notify Explorer so icons refresh without reboot
        import ctypes

        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0)

        logger.info("WTZ 文件关联已注册: icon=%s", ico_path)
    except Exception as e:
        logger.warning("WTZ 文件关联注册失败: %s", e)
