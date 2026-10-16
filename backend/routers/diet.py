"""饮食 · 条目（规划+打卡合一）/api/diet"""
import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

import store
from utils import today_str

router = APIRouter(prefix="/diet", tags=["diet"])

MEALS = ("breakfast", "lunch", "dinner", "snack")
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _valid_date_str(v: str) -> bool:
    if not _DATE_PATTERN.match(v):
        return False
    try:
        from datetime import datetime

        datetime.strptime(v, "%Y-%m-%d")
        return True
    except ValueError:
        return False


class DietIn(BaseModel):
    date: Optional[str] = None
    meal: Optional[str] = None
    name: Optional[str] = None
    calories: Optional[float] = Field(default=None, ge=0)
    eaten: Optional[bool] = None
    note: Optional[str] = None

    @field_validator("date")
    @classmethod
    def _valid_date(cls, v):
        if v is not None and not _valid_date_str(v):
            raise ValueError("date 须为 YYYY-MM-DD")
        return v

    @field_validator("meal")
    @classmethod
    def _valid_meal(cls, v):
        if v is not None and v not in MEALS:
            raise ValueError("meal 须为 breakfast/lunch/dinner/snack")
        return v

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("name 不能为空")
        return v


def _sort_key(e: dict):
    return (MEALS.index(e["meal"]), e["id"])


@router.get("")
def list_diet(date: str):
    if not _valid_date_str(date):
        raise HTTPException(422, "date 须为 YYYY-MM-DD")
    items = [e for e in store.load("diet") if e["date"] == date]
    items.sort(key=_sort_key)
    return items


@router.post("")
def create_diet(body: DietIn):
    if body.name is None:
        raise HTTPException(422, "name 必填")
    if body.meal is None:
        raise HTTPException(422, "meal 必填")
    created = {}

    def _create(items):
        item = {
            "id": store.next_id(items),
            "date": body.date or today_str(),
            "meal": body.meal,
            "name": body.name.strip(),
            "calories": body.calories if body.calories is not None else 0,
            "eaten": False,
            "note": body.note or "",
        }
        items.append(item)
        created["item"] = item
        return items

    store.update("diet", _create)
    return created["item"]


@router.put("/{item_id}")
def update_diet(item_id: int, body: DietIn):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "没有需要更新的字段")
    updated = {}

    def _apply(items):
        for e in items:
            if e["id"] == item_id:
                e.update(changes)
                updated["item"] = e
                return items
        raise HTTPException(404, "条目不存在")

    store.update("diet", _apply)
    return updated["item"]


@router.delete("/{item_id}")
def delete_diet(item_id: int):
    def _drop(items):
        remain = [e for e in items if e["id"] != item_id]
        if len(remain) == len(items):
            raise HTTPException(404, "条目不存在")
        return remain

    store.update("diet", _drop)
    return {"deleted": True}


@router.get("/summary")
def diet_summary(date: Optional[str] = None):
    d = date or today_str()
    if not _valid_date_str(d):
        raise HTTPException(422, "date 须为 YYYY-MM-DD")

    items = [e for e in store.load("diet") if e["date"] == d and e.get("eaten")]
    intake = sum(e.get("calories", 0) for e in items)
    by_meal = {m: sum(e.get("calories", 0) for e in items if e["meal"] == m) for m in MEALS}
    target = store.load("settings").get("calorie_target", 2000)
    return {"intake": round(intake), "target": target, "by_meal": {m: round(v) for m, v in by_meal.items()}}
