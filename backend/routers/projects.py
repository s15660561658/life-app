"""开发工作 · 项目（内嵌任务）/api/projects"""
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

import store
from utils import now_str

router = APIRouter(prefix="/projects", tags=["projects"])

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATUSES = {"ongoing", "done", "paused"}


class ProjectIn(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[str] = None
    note: Optional[str] = None

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("name 不能为空")
        return v

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v):
        if v is not None and v not in STATUSES:
            raise ValueError("status 须为 ongoing/done/paused")
        return v

    @field_validator("deadline")
    @classmethod
    def _valid_deadline(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("deadline 须为 YYYY-MM-DD")
        return v


class ProjectTaskIn(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def _title_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("title 不能为空")
        return v


@router.get("")
def list_projects():
    items = store.load("projects")
    return sorted(items, key=lambda p: (p["created_at"], p["id"]), reverse=True)


@router.post("")
def create_project(body: ProjectIn):
    if body.name is None:
        raise HTTPException(422, "name 必填")
    created = {}

    def _create(projects):
        project = {
            "id": store.next_id(projects),
            "name": body.name.strip(),
            "status": body.status or "ongoing",
            "deadline": body.deadline,
            "note": body.note or "",
            "created_at": now_str(),
            "tasks": [],
        }
        projects.append(project)
        created["item"] = project
        return projects

    store.update("projects", _create)
    return created["item"]


def _find_project(projects, project_id):
    for p in projects:
        if p["id"] == project_id:
            return p
    raise HTTPException(404, "项目不存在")


@router.put("/{project_id}")
def update_project(project_id: int, body: ProjectIn):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "没有需要更新的字段")
    updated = {}

    def _apply(projects):
        p = _find_project(projects, project_id)
        p.update(changes)
        updated["item"] = p
        return projects

    store.update("projects", _apply)
    return updated["item"]


@router.delete("/{project_id}")
def delete_project(project_id: int):
    """删除项目（连同任务）；关联 Bug 的 project_id 置空。"""
    with store.lock:
        projects = store._load_unlocked("projects")
        remain = [p for p in projects if p["id"] != project_id]
        if len(remain) == len(projects):
            raise HTTPException(404, "项目不存在")
        store._write_atomic(store._path("projects"), remain)

        bugs = store._load_unlocked("bugs")
        changed = False
        for b in bugs:
            if b.get("project_id") == project_id:
                b["project_id"] = None
                changed = True
        if changed:
            store._write_atomic(store._path("bugs"), bugs)
    return {"deleted": True}


@router.post("/{project_id}/tasks")
def create_project_task(project_id: int, body: ProjectTaskIn):
    if body.title is None:
        raise HTTPException(422, "title 必填")
    created = {}

    def _add(projects):
        p = _find_project(projects, project_id)
        task = {"id": store.next_id(p["tasks"]), "title": body.title.strip(), "done": False}
        p["tasks"].append(task)
        created["item"] = task
        return projects

    store.update("projects", _add)
    return created["item"]


@router.put("/{project_id}/tasks/{task_id}")
def update_project_task(project_id: int, task_id: int, body: ProjectTaskIn):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "没有需要更新的字段")
    updated = {}

    def _apply(projects):
        p = _find_project(projects, project_id)
        for t in p["tasks"]:
            if t["id"] == task_id:
                t.update(changes)
                updated["item"] = t
                return projects
        raise HTTPException(404, "项目任务不存在")

    store.update("projects", _apply)
    return updated["item"]


@router.delete("/{project_id}/tasks/{task_id}")
def delete_project_task(project_id: int, task_id: int):
    def _drop(projects):
        p = _find_project(projects, project_id)
        remain = [t for t in p["tasks"] if t["id"] != task_id]
        if len(remain) == len(p["tasks"]):
            raise HTTPException(404, "项目任务不存在")
        p["tasks"] = remain
        return projects

    store.update("projects", _drop)
    return {"deleted": True}
