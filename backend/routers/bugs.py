"""开发工作 · Bug 清单 /api/bugs"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

import store
from utils import now_str

router = APIRouter(prefix="/bugs", tags=["bugs"])

PRIORITIES = {"high", "medium", "low"}
STATUSES = {"open", "in_progress", "resolved"}


class BugIn(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    solution: Optional[str] = None
    project_id: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None

    @field_validator("title")
    @classmethod
    def _title_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("title 不能为空")
        return v

    @field_validator("priority")
    @classmethod
    def _valid_priority(cls, v):
        if v is not None and v not in PRIORITIES:
            raise ValueError("priority 须为 high/medium/low")
        return v

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v):
        if v is not None and v not in STATUSES:
            raise ValueError("status 须为 open/in_progress/resolved")
        return v


@router.get("")
def list_bugs(status: Optional[str] = None, project_id: Optional[int] = None):
    if status is not None and status not in STATUSES:
        raise HTTPException(422, "status 须为 open/in_progress/resolved")
    items = store.load("bugs")
    if status is not None:
        items = [b for b in items if b["status"] == status]
    if project_id is not None:
        items = [b for b in items if b.get("project_id") == project_id]
    return sorted(items, key=lambda b: (b["created_at"], b["id"]), reverse=True)


@router.post("")
def create_bug(body: BugIn):
    if body.title is None:
        raise HTTPException(422, "title 必填")
    _check_project_exists(body.project_id)

    created = {}
    ts = now_str()

    def _create(bugs):
        bug = {
            "id": store.next_id(bugs),
            "title": body.title.strip(),
            "description": body.description or "",
            "solution": "",
            "project_id": body.project_id,
            "priority": body.priority or "medium",
            "status": "open",
            "created_at": ts,
            "updated_at": ts,
        }
        bugs.append(bug)
        created["item"] = bug
        return bugs

    store.update("bugs", _create)
    return created["item"]


def _check_project_exists(project_id):
    if project_id is None:
        return
    if not any(p["id"] == project_id for p in store.load("projects")):
        raise HTTPException(422, "关联项目不存在")


@router.put("/{bug_id}")
def update_bug(bug_id: int, body: BugIn):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "没有需要更新的字段")
    if "project_id" in changes:
        _check_project_exists(changes["project_id"])
    updated = {}

    def _apply(bugs):
        for b in bugs:
            if b["id"] == bug_id:
                b.update(changes)
                b["updated_at"] = now_str()
                updated["item"] = b
                return bugs
        raise HTTPException(404, "Bug 不存在")

    store.update("bugs", _apply)
    return updated["item"]


@router.delete("/{bug_id}")
def delete_bug(bug_id: int):
    def _drop(bugs):
        remain = [b for b in bugs if b["id"] != bug_id]
        if len(remain) == len(bugs):
            raise HTTPException(404, "Bug 不存在")
        return remain

    store.update("bugs", _drop)
    return {"deleted": True}
