"""健身 · 身体数据 /api/body"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

import store
from utils import today_str

router = APIRouter(prefix="/body", tags=["body"])


class BodyIn(BaseModel):
    date: Optional[str] = None
    weight_kg: float = Field(gt=0)

    @field_validator("date")
    @classmethod
    def _valid_date(cls, v):
        if v is not None:
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("date 须为 YYYY-MM-DD")
        return v


@router.get("")
def list_body():
    return sorted(store.load("body"), key=lambda b: (b["date"], b["id"]), reverse=True)


@router.post("")
def create_body(body: BodyIn):
    created = {}

    def _create(items):
        item = {"id": store.next_id(items), "date": body.date or today_str(), "weight_kg": body.weight_kg}
        items.append(item)
        created["item"] = item
        return items

    store.update("body", _create)
    return created["item"]


@router.delete("/{item_id}")
def delete_body(item_id: int):
    def _drop(items):
        remain = [b for b in items if b["id"] != item_id]
        if len(remain) == len(items):
            raise HTTPException(404, "记录不存在")
        return remain

    store.update("body", _drop)
    return {"deleted": True}
