"""T1.1 存储层测试：读写一致性、进程重启持久化、自动重建、自增 ID、原子更新。"""
import json
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

import store  # noqa: E402


def test_default_file_auto_created(isolated_data):
    data = store.load("memos")
    assert data == []
    assert (isolated_data / "memos.json").exists()


def test_settings_and_plan_defaults(isolated_data):
    settings = store.load("settings")
    assert settings == {"calorie_target": 2000, "default_rest_seconds": 60}

    plan = store.load("workout_plan")
    assert sorted(plan.keys()) == ["1", "2", "3", "4", "5", "6", "7"]
    assert all(v == [] for v in plan.values())


def test_write_then_read_consistent(isolated_data):
    memos = [{"id": 1, "content": "买咖啡豆", "created_at": "2026-10-16 14:30"}]
    store.save("memos", memos)
    assert store.load("memos") == memos


def test_survives_process_restart(isolated_data):
    """真实跨进程：子进程写入 → 进程退出（模拟重启）→ 父进程读取一致。"""
    env = {**os.environ, "LIFE_APP_DATA_DIR": str(isolated_data)}
    code = (
        "import store;"
        "store.save('tasks', [{'id': 1, 'date': '2026-10-16', 'title': '写周报',"
        "'start_time': '10:30', 'end_time': '11:30', 'note': '', 'done': False}]);"
        "store.save('settings', {'calorie_target': 1800, 'default_rest_seconds': 120})"
    )
    subprocess.run([sys.executable, "-c", code], cwd=BACKEND_DIR, env=env, check=True)

    tasks = store.load("tasks")
    assert len(tasks) == 1 and tasks[0]["title"] == "写周报"
    assert store.load("settings")["calorie_target"] == 1800


def test_deleted_file_recreated_on_restart(isolated_data):
    store.save("memos", [{"id": 1, "content": "x", "created_at": "2026-10-16 10:00"}])
    (isolated_data / "memos.json").unlink()  # 手工删除文件

    data = store.load("memos")  # 重启后首次访问自动重建
    assert data == []


def test_corrupt_tmp_does_not_break_data(isolated_data):
    """原子写入：残留 .tmp 不影响正式文件。"""
    store.save("memos", [{"id": 1}])
    (isolated_data / "memos.json.tmp").write_text("{broken", encoding="utf-8")
    assert store.load("memos") == [{"id": 1}]


def test_next_id_increments(isolated_data):
    items = [{"id": 3}, {"id": 7}]
    assert store.next_id(items) == 8
    assert store.next_id([]) == 1


def test_update_atomic_read_modify_write(isolated_data):
    store.save("memos", [])
    result = store.update("memos", lambda items: items + [{"id": store.next_id(items), "content": "a"}])
    assert result[0]["id"] == 1
    assert store.load("memos") == result


def test_file_content_is_valid_json(isolated_data):
    store.save("settings", {"calorie_target": 1500, "default_rest_seconds": 90})
    raw = (isolated_data / "settings.json").read_text(encoding="utf-8")
    assert json.loads(raw)["calorie_target"] == 1500
