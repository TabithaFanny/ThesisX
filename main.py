import sys
import os
import logging
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# !! 强制使用 IPv4 - 必须在所有其他 import 之前 !!
# 避免 IPv6 超时导致 40+ 秒延迟
import socket
_original_getaddrinfo = socket.getaddrinfo

def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """只返回 IPv4 地址"""
    result = _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    # 记录补丁被调用
    if 'llm.nodai.design' in str(host):
        print(f"[IPv4 PATCH] Resolving {host}:{port} -> {result[0][4] if result else 'FAILED'}")
    return result

socket.getaddrinfo = ipv4_only_getaddrinfo
print(f"[MAIN] IPv4 patch installed: {socket.getaddrinfo}")

# ── High-performance rendering: must be set BEFORE QApplication ──
os.environ["QT_OPENGL"] = "desktop"          # Use native OpenGL (NVIDIA)
os.environ["QSG_RENDER_LOOP"] = "threaded"   # Threaded render loop

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon, QSurfaceFormat
from PyQt6.QtCore import Qt

from app.constants import APP_NAME, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE
from app.ui.main_window import MainWindow
from app.core.file_association import register_wtz_file_type


def _setup_logging():
    log_dir = os.path.join(os.path.expanduser("~"), ".wenbiao")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "wenbiao.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _install_exception_hook():
    """Install a global exception hook to catch unhandled exceptions in Qt slots.

    In PyQt6, unhandled exceptions in signal slots silently terminate the process.
    This hook logs them and prevents the silent crash.
    """
    _logger = logging.getLogger("exception_hook")

    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        _logger.critical(
            "未捕获异常:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )

    sys.excepthook = _hook


def main():
    _setup_logging()
    _install_exception_hook()
    logger = logging.getLogger(__name__)
    logger.info("%s 启动", APP_NAME)

    # Register .wtz file association (idempotent, HKCU only)
    register_wtz_file_type()

    # Workaround: OrayIddDriver
    # Keep full GPU acceleration (GTX 4090ti etc.) but disable only the broken path.
    os.environ.setdefault(
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "--disable-direct-composition "
        "--disable-gpu-driver-bug-workarounds "
        "--enable-gpu-rasterization "
        "--enable-zero-copy "
        "--enable-features=VaapiVideoDecoder "
        "--ignore-gpu-blocklist"
    )
    # Force high-performance GPU on multi-GPU systems (NVIDIA Optimus etc.)
    os.environ.setdefault("SHIM_MCCOMPAT", "0x800000001")

    # ── Set high-performance OpenGL surface format ──
    fmt = QSurfaceFormat()
    fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    fmt.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
    fmt.setSwapInterval(0)       # Disable VSync for max responsiveness
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Raise process priority for UI responsiveness
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetCurrentProcess()
        kernel32.SetPriorityClass(handle, 0x00008000)  # ABOVE_NORMAL_PRIORITY_CLASS
    except Exception:
        pass

    # Set application icon
    icon_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "app", "resources", "thesisx_icon.ico"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    font = QFont(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE)
    app.setFont(font)

    window = MainWindow()
    window.show()

    code = app.exec()
    logger.info("%s 退出，代码 %d", APP_NAME, code)
    sys.exit(code)


if __name__ == "__main__":
    main()
