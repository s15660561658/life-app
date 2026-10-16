"""游戏娱乐 · 日程 /api/events"""
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

import store
from utils import now_str

router = APIRouter(prefix="/events", tags=["events"])

CATEGORIES = {"game", "movie", "party", "other"}
_START_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


class EventIn(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    start_at: Optional[str] = None
    note: Optional[str] = None
    done: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def _title_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("title 不能为空")
        return v

    @field_validator("category")
    @classmethod
    def _valid_category(cls, v):
        if v is not None and v not in CATEGORIES:
            raise ValueError("category 须为 game/movie/party/other")
        return v

    @field_validator("start_at")
    @classmethod
    def _valid_start(cls, v):
        if v is not None:
            if not _START_PATTERN.match(v):
                raise ValueError("start_at 须为 YYYY-MM-DD HH:MM")
            try:
                datetime.strptime(v, "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError("start_at 日期时间不合法")
        return v


@router.get("")
def list_events():
    now = now_str()
    items = store.load("events")
    upcoming = [e for e in items if not e.get("done") and e["start_at"] >= now]
    past = [e for e in items if e.get("done") or e["start_at"] < now]
    upcoming.sort(key=lambda e: (e["start_at"], e["id"]))  # 升序
    past.sort(key=lambda e: (e["start_at"], e["id"]), reverse=True)  # 倒序
    return {"upcoming": upcoming, "past": past}


@router.post("")
def create_event(body: EventIn):
    if body.title is None:
        raise HTTPException(422, "title 必填")
    if body.start_at is None:
        raise HTTPException(422, "start_at 必填")
    created = {}

    def _create(events):
        event = {
            "id": store.next_id(events),
            "title": body.title.strip(),
            "category": body.category or "other",
            "start_at": body.start_at,
            "note": body.note or "",
            "done": False,
        }
        events.append(event)
        created["item"] = event
        return events

    store.update("events", _create)
    return created["item"]


@router.put("/{event_id}")
def update_event(event_id: int, body: EventIn):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "没有需要更新的字段")
    updated = {}

    def _apply(events):
        for e in events:
            if e["id"] == event_id:
                e.update(changes)
                updated["item"] = e
                return events
        raise HTTPException(404, "日程不存在")

    store.update("events", _apply)
    return updated["item"]


@router.delete("/{event_id}")
def delete_event(event_id: int):
    def _drop(events):
        remain = [e for e in events if e["id"] != event_id]
        if len(remain) == len(events):
            raise HTTPException(404, "日程不存在")
        return remain

    store.update("events", _drop)
    return {"deleted": True}
