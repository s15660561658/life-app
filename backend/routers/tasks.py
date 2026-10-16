"""今日计划 /api/tasks"""
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

import store
from utils import today_str

router = APIRouter(prefix="/tasks", tags=["tasks"])

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _valid_date_str(v: str) -> bool:
    return bool(_DATE_PATTERN.match(v)) and bool(_try_date(v))


def _try_date(v: str):
    try:
        return datetime.strptime(v, "%Y-%m-%d")
    except ValueError:
        return None


class TaskIn(BaseModel):
    date: Optional[str] = None
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    note: Optional[str] = None
    done: Optional[bool] = None

    @field_validator("date")
    @classmethod
    def _valid_date(cls, v):
        if v is not None and not _valid_date_str(v):
            raise ValueError("date 须为合法 YYYY-MM-DD")
        return v

    @field_validator("title")
    @classmethod
    def _title_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("title 不能为空")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def _valid_time(cls, v):
        if v is not None and not _TIME_PATTERN.match(v):
            raise ValueError("时间须为 HH:MM（两位）")
        return v


def _sort_key(t: dict):
    # 全天优先（start_time 为 null 在前），再按开始时间升序
    return (t.get("start_time") is not None, t.get("start_time") or "", t.get("end_time") or "", t["id"])


@router.get("")
def list_tasks(date: str):
    if not _valid_date_str(date):
        raise HTTPException(422, "date 须为 YYYY-MM-DD")
    items = [t for t in store.load("tasks") if t.get("date") == date]
    items.sort(key=_sort_key)
    return items


@router.post("")
def create_task(body: TaskIn):
    if body.title is None:
        raise HTTPException(422, "title 必填")
    item = {
        "id": 0,
        "date": body.date or today_str(),
        "title": body.title.strip(),
        "start_time": body.start_time,
        "end_time": body.end_time,
        "note": body.note or "",
        "done": body.done or False,
    }
    created = {}

    def _create(tasks):
        item["id"] = store.next_id(tasks)
        tasks.append(dict(item))
        created["item"] = item
        return tasks

    store.update("tasks", _create)
    return created["item"]


@router.put("/{task_id}")
def update_task(task_id: int, body: TaskIn):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "没有需要更新的字段")

    updated = {}

    def _apply(tasks):
        for t in tasks:
            if t["id"] == task_id:
                t.update(changes)
                updated["item"] = t
                return tasks
        raise HTTPException(404, "任务不存在")

    store.update("tasks", _apply)
    return updated["item"]


@router.delete("/{task_id}")
def delete_task(task_id: int):
    def _drop(tasks):
        remain = [t for t in tasks if t["id"] != task_id]
        if len(remain) == len(tasks):
            raise HTTPException(404, "任务不存在")
        return remain

    store.update("tasks", _drop)
    return {"deleted": True}
