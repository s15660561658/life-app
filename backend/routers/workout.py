"""健身 · 周计划 + 训练打卡 /api/workout"""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

import store
from utils import now_str, today_str

router = APIRouter(prefix="/workout", tags=["workout"])


class Exercise(BaseModel):
    name: str = Field(min_length=1)
    sets: int = Field(ge=1)
    reps: int = Field(ge=1)
    rest_seconds: int = Field(default=0, ge=0)  # 打卡日志可省略，计划表建议显式传入


class PlanDayIn(BaseModel):
    exercises: List[Exercise]


class LogIn(BaseModel):
    date: Optional[str] = None
    duration_seconds: int = Field(ge=0)
    exercises: List[Exercise] = []

    @field_validator("date")
    @classmethod
    def _valid_date(cls, v):
        if v is not None:
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("date 须为 YYYY-MM-DD")
        return v


@router.get("/plan")
def get_plan():
    return store.load("workout_plan")


@router.put("/plan/{day}")
def replace_plan_day(day: int, body: PlanDayIn):
    if not 1 <= day <= 7:
        raise HTTPException(422, "day 须为 1~7（周一~周日）")

    def _replace(plan):
        plan[str(day)] = [e.model_dump() for e in body.exercises]
        return plan

    return store.update("workout_plan", _replace)


@router.get("/logs")
def list_logs(limit: Optional[int] = None):
    items = sorted(store.load("workout_logs"), key=lambda l: (l["date"], l["id"]), reverse=True)
    if limit is not None:
        items = items[: max(limit, 0)]
    return items


@router.post("/logs")
def create_log(body: LogIn):
    created = {}

    def _create(logs):
        log = {
            "id": store.next_id(logs),
            "date": body.date or today_str(),
            "duration_seconds": body.duration_seconds,
            "exercises": [e.model_dump(exclude={"rest_seconds"}) for e in body.exercises],
            "created_at": now_str(),
        }
        logs.append(log)
        created["item"] = log
        return logs

    store.update("workout_logs", _create)
    return created["item"]


@router.delete("/logs/{log_id}")
def delete_log(log_id: int):
    def _drop(logs):
        remain = [l for l in logs if l["id"] != log_id]
        if len(remain) == len(logs):
            raise HTTPException(404, "打卡记录不存在")
        return remain

    store.update("workout_logs", _drop)
    return {"deleted": True}


def _summary_counts():
    logs = store.load("workout_logs")
    dates = {l["date"] for l in logs}
    total = len(logs)

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_count = sum(1 for d in dates if date.fromisoformat(d) >= monday)

    # 连续天数：今天或昨天有记录则连续，向前逐日累计
    streak = 0
    cursor = today if today.isoformat() in dates else today - timedelta(days=1)
    if cursor.isoformat() in dates:
        while cursor.isoformat() in dates:
            streak += 1
            cursor -= timedelta(days=1)
    return total, week_count, streak


@router.get("/summary")
def workout_summary():
    total, week_count, streak = _summary_counts()
    return {"total": total, "week_count": week_count, "streak_days": streak}
