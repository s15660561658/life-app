"""开发工作 · 笔记 /api/notes"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

import store
from utils import now_str

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteIn(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("title")
    @classmethod
    def _title_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("title 不能为空")
        return v


@router.get("")
def list_notes(q: Optional[str] = None, tag: Optional[str] = None):
    items = store.load("notes")
    if q:
        kw = q.lower()
        items = [n for n in items if kw in n["title"].lower() or kw in n.get("content", "").lower()]
    if tag:
        items = [n for n in items if tag in n.get("tags", [])]
    return sorted(items, key=lambda n: (n["created_at"], n["id"]), reverse=True)


@router.post("")
def create_note(body: NoteIn):
    if body.title is None:
        raise HTTPException(422, "title 必填")
    created = {}
    ts = now_str()

    def _create(notes):
        note = {
            "id": store.next_id(notes),
            "title": body.title.strip(),
            "content": body.content or "",
            "tags": body.tags or [],
            "created_at": ts,
            "updated_at": ts,
        }
        notes.append(note)
        created["item"] = note
        return notes

    store.update("notes", _create)
    return created["item"]


@router.put("/{note_id}")
def update_note(note_id: int, body: NoteIn):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "没有需要更新的字段")
    updated = {}

    def _apply(notes):
        for n in notes:
            if n["id"] == note_id:
                n.update(changes)
                n["updated_at"] = now_str()
                updated["item"] = n
                return notes
        raise HTTPException(404, "笔记不存在")

    store.update("notes", _apply)
    return updated["item"]


@router.delete("/{note_id}")
def delete_note(note_id: int):
    def _drop(notes):
        remain = [n for n in notes if n["id"] != note_id]
        if len(remain) == len(notes):
            raise HTTPException(404, "笔记不存在")
        return remain

    store.update("notes", _drop)
    return {"deleted": True}
