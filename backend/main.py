"""个人工作生活 APP · FastAPI 入口

- /api/*   JSON 接口（各模块路由）
- /*       托管 frontend/dist 静态页面（SPA 回退）；未构建时返回引导页
"""
import socket
import sys
from pathlib import Path

# 保证以 `uvicorn backend.main:app`（项目根）或 `uvicorn main:app`（backend/）启动均可导入模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import store
from routers import (body, bugs, diet, events, memos, notes, projects, system,
                     tasks, workout)

VERSION = "1.0"
PORT = 8321
DIST_DIR = Path(__file__).resolve().parents[1] / "frontend" / "dist"

app = FastAPI(title="life-app", version=VERSION)

# 开发期 CORS（vite dev 端口 5173）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _lan_ip() -> str:
    """取本机局域网 IP（UDP 探测，不产生实际流量）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


@app.get("/api/ping")
def ping():
    return {"pong": True}


# ---- 模块路由（挂在 /api 下；须先于 SPA 回退路由注册）----
app.include_router(tasks.router, prefix="/api")
app.include_router(memos.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(bugs.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(workout.router, prefix="/api")
app.include_router(body.router, prefix="/api")
app.include_router(diet.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(system.router, prefix="/api")


@app.get("/api/system/info")
def system_info():
    return {
        "data_dir": str(store.DATA_DIR.resolve()),
        "lan_ip": _lan_ip(),
        "port": PORT,
        "version": VERSION,
    }


_GUIDE_HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>life-app</title></head>
<body style="font-family:sans-serif;max-width:560px;margin:80px auto;line-height:1.8">
<h2>前端尚未构建</h2>
<p>当前只有 API 服务可用。请在 <code>frontend/</code> 目录执行：</p>
<pre>npm install
npm run build</pre>
<p>构建完成后重启本服务即可访问完整页面。接口预览见 <code>API.md</code>。</p>
</body></html>"""


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    """托管前端：已知静态文件直接返回，其余路径回退 index.html（SPA 路由）。"""
    index = DIST_DIR / "index.html"
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    if not index.exists():
        return HTMLResponse(_GUIDE_HTML, status_code=200)
    if full_path and not full_path.startswith("api/"):
        candidate = (DIST_DIR / full_path).resolve()
        if candidate.is_file() and str(candidate).startswith(str(DIST_DIR.resolve())):
            return FileResponse(candidate)
    return FileResponse(index)
