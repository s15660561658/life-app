"""系统 · 设置 / 统计 / 备份 / 清空 /api"""
import json
from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

import store
from routers.workout import _summary_counts
from utils import now_str, today_str

router = APIRouter(tags=["system"])

BACKUP_APP = "life-app"
BACKUP_VERSION = 1


# ---------- 设置 ----------

class SettingsIn(BaseModel):
    calorie_target: Optional[int] = Field(default=None, gt=0)
    default_rest_seconds: Optional[int] = Field(default=None, ge=0)


@router.get("/settings")
def get_settings():
    return store.load("settings")


@router.put("/settings")
def update_settings(body: SettingsIn):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "没有需要更新的字段")
    return store.update("settings", lambda s: {**s, **changes})


# ---------- 统计 ----------

@router.get("/stats")
def stats():
    tasks = store.load("tasks")
    today = today_str()
    today_tasks = [t for t in tasks if t["date"] == today]

    projects = store.load("projects")
    bugs = store.load("bugs")
    memos = store.load("memos")
    diet = store.load("diet")

    workout_total, workout_week_count, streak = _summary_counts()
    workout_today = any(l["date"] == today for l in store.load("workout_logs"))

    today_diet = [e for e in diet if e["date"] == today and e.get("eaten")]
    intake = round(sum(e.get("calories", 0) for e in today_diet))
    target = store.load("settings").get("calorie_target", 2000)

    next_event = _next_event()

    return {
        "tasks_done_total": sum(1 for t in tasks if t.get("done")),
        "tasks_today_total": len(today_tasks),
        "tasks_today_done": sum(1 for t in today_tasks if t.get("done")),
        "memos_count": len(memos),
        "projects_ongoing": sum(1 for p in projects if p["status"] == "ongoing"),
        "projects_done": sum(1 for p in projects if p["status"] == "done"),
        "bugs_unresolved": sum(1 for b in bugs if b["status"] != "resolved"),
        "bugs_resolved": sum(1 for b in bugs if b["status"] == "resolved"),
        "workout_total": workout_total,
        "workout_week_count": workout_week_count,
        "workout_streak_days": streak,
        "workout_today": workout_today,
        "diet_intake_today": intake,
        "diet_target": target,
        "diet_days": len({e["date"] for e in diet}),
        "next_event": next_event,
    }


def _next_event():
    now = now_str()
    upcoming = [e for e in store.load("events") if not e.get("done") and e["start_at"] >= now]
    if not upcoming:
        return None
    e = min(upcoming, key=lambda x: (x["start_at"], x["id"]))
    return {"id": e["id"], "title": e["title"], "start_at": e["start_at"]}


# ---------- 备份 / 恢复 / 清空 ----------

def _export_payload():
    data = {name: store.load(name) for name in sorted(store.VALID_MODULES)}
    return {
        "app": BACKUP_APP,
        "version": BACKUP_VERSION,
        "exported_at": now_str(),
        "data": data,
    }


@router.get("/backup/export")
def backup_export():
    payload = _export_payload()
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    filename = f"life-app-backup-{now_str().replace(':', '').replace(' ', '-').replace('-', '')[:14]}.json"
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/backup/restore")
def backup_restore(payload: dict):
    if payload.get("app") != BACKUP_APP or payload.get("version") != BACKUP_VERSION:
        raise HTTPException(400, "备份文件格式不合法（app/version 不匹配）")
    data = payload.get("data")
    if not isinstance(data, dict) or not set(data.keys()) == store.VALID_MODULES:
        raise HTTPException(400, "备份文件缺少必要的数据模块")

    with store.lock:
        for name in sorted(store.VALID_MODULES):
            store.save(name, data[name])
    return {"restored": True}


class ClearIn(BaseModel):
    modules: Union[str, List[str]]


@router.post("/data/clear")
def data_clear(body: ClearIn):
    if body.modules == "all":
        targets = set(store.VALID_MODULES) - {"settings"}  # 默认保留设置项
    elif isinstance(body.modules, list):
        invalid = [m for m in body.modules if m not in store.VALID_MODULES]
        if invalid:
            raise HTTPException(422, f"未知模块：{invalid}")
        targets = set(body.modules)
    else:
        raise HTTPException(422, "modules 须为 'all' 或模块名数组")

    with store.lock:
        for name in sorted(targets):
            if name == "settings":
                store.save(name, dict(store.DEFAULTS["settings"]))  # 清设置 = 恢复默认值
            else:
                store.save(name, store.DEFAULTS[name])
    return {"cleared": sorted(targets)}
