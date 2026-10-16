"""备忘录 /api/memos"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

import store
from utils import now_str

router = APIRouter(prefix="/memos", tags=["memos"])


class MemoIn(BaseModel):
    content: Optional[str] = None

    @field_validator("content")
    @classmethod
    def _not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("content 不能为空")
        return v


@router.get("")
def list_memos(limit: Optional[int] = None):
    items = store.load("memos")
    items = sorted(items, key=lambda m: (m["created_at"], m["id"]), reverse=True)
    if limit is not None:
        if limit < 0:
            raise HTTPException(422, "limit 须为非负整数")
        items = items[:limit]
    return items


@router.post("")
def create_memo(body: MemoIn):
    if body.content is None:
        raise HTTPException(422, "content 必填")

    created = {}

    def _create(memos):
        memo = {
            "id": store.next_id(memos),
            "content": body.content.strip(),
            "created_at": now_str(),
        }
        memos.append(memo)
        created["item"] = memo
        return memos

    store.update("memos", _create)
    return created["item"]


@router.put("/{memo_id}")
def update_memo(memo_id: int, body: MemoIn):
    if body.content is None:
        raise HTTPException(422, "content 必填")

    updated = {}

    def _apply(memos):
        for m in memos:
            if m["id"] == memo_id:
                m["content"] = body.content.strip()
                updated["item"] = m
                return memos
        raise HTTPException(404, "备忘录不存在")

    store.update("memos", _apply)
    return updated["item"]


@router.delete("/{memo_id}")
def delete_memo(memo_id: int):
    def _drop(memos):
        remain = [m for m in memos if m["id"] != memo_id]
        if len(remain) == len(memos):
            raise HTTPException(404, "备忘录不存在")
        return remain

    store.update("memos", _drop)
    return {"deleted": True}
