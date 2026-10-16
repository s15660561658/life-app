"""个人工作生活 APP 一键启动：python run.py（或双击 start.bat）"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

import uvicorn  # noqa: E402

from main import PORT, VERSION, _lan_ip, app  # noqa: E402


def main():
    ip = _lan_ip()
    print("=" * 52)
    print(f"  个人工作生活 APP v{VERSION}")
    print()
    print(f"  本机访问:   http://localhost:{PORT}")
    print(f"  局域网访问: http://{ip}:{PORT}")
    print("  （手机连同一 Wi-Fi 后用浏览器打开局域网地址）")
    print()
    print("  数据目录: backend/data  关闭窗口即停止服务")
    print("=" * 52)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
