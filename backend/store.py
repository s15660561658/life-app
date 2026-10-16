"""JSON 存储层：按模块读写 data/*.json

- 原子写入：先写 *.tmp 再 os.replace，防止断电/崩溃损坏
- 线程锁：所有写操作（含"读-改-写"复合操作）共用一把可重入锁
- 首次访问自动创建缺失文件（含默认值）
"""
import json
import os
import threading
from pathlib import Path

# 允许测试通过环境变量重定向数据目录
DATA_DIR = Path(os.environ.get("LIFE_APP_DATA_DIR", Path(__file__).resolve().parent / "data"))

# 全局可重入锁：包住所有写操作与"读-改-写"复合操作
lock = threading.RLock()

# 模块默认值（首次访问自动创建）
DEFAULTS = {
    "tasks": [],
    "memos": [],
    "projects": [],
    "bugs": [],
    "notes": [],
    "workout_plan": {str(d): [] for d in range(1, 8)},
    "workout_logs": [],
    "body": [],
    "diet": [],
    "events": [],
    "settings": {"calorie_target": 2000, "default_rest_seconds": 60},
}

VALID_MODULES = set(DEFAULTS.keys())


def _path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def _default(name: str):
    """深拷贝默认值，避免共享可变结构。"""
    return json.loads(json.dumps(DEFAULTS[name]))


def _write_atomic(path: Path, data) -> None:
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _load_unlocked(name: str):
    """不加锁读取；文件缺失时在锁内原子创建默认文件。"""
    path = _path(name)
    if not path.exists():
        data = _default(name)
        _write_atomic(path, data)
        return data
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load(name: str):
    """按模块名读取数据；缺失文件自动创建默认值。"""
    with lock:
        return _load_unlocked(name)


def save(name: str, data) -> None:
    """按模块名原子写入。"""
    with lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _write_atomic(_path(name), data)


def update(name: str, fn):
    """原子"读-改-写"：fn(data) -> new_data（必须返回完整模块数据），整个过程持锁。"""
    with lock:
        data = _load_unlocked(name)
        new_data = fn(data)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _write_atomic(_path(name), new_data)
        return new_data


def next_id(items) -> int:
    """取现有最大 id + 1；空列表从 1 开始。须在写锁内调用。"""
    ids = [x["id"] for x in items if isinstance(x, dict) and "id" in x]
    return max(ids) + 1 if ids else 1
