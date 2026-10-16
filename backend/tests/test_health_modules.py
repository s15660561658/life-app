"""T1.5 接口批次三测试：健身（周计划/打卡/summary）+ 身体数据 + 饮食。"""
from datetime import date, timedelta

from routers.workout import _summary_counts


def _monday():
    today = date.today()
    return today - timedelta(days=today.weekday())


def _iso(d):
    return d.isoformat()


# ---------- 周计划 ----------

def test_plan_default_7_empty_keys(client):
    plan = client.get("/api/workout/plan").json()
    assert sorted(plan.keys()) == ["1", "2", "3", "4", "5", "6", "7"]
    assert all(v == [] for v in plan.values())


def test_plan_replace_day_and_validation(client):
    exercises = [{"name": "卧推", "sets": 4, "reps": 10, "rest_seconds": 90}]
    res = client.put("/api/workout/plan/1", json={"exercises": exercises})
    assert res.status_code == 200
    plan = client.get("/api/workout/plan").json()
    assert plan["1"] == exercises
    assert plan["2"] == []  # 其他天不受影响

    # 复制到另一天（前端取 A 天 PUT 到 B 天）
    client.put("/api/workout/plan/3", json={"exercises": plan["1"]})
    plan = client.get("/api/workout/plan").json()
    assert plan["3"] == exercises

    assert client.put("/api/workout/plan/8", json={"exercises": []}).status_code == 422
    assert client.put("/api/workout/plan/0", json={"exercises": []}).status_code == 422
    bad = [{"name": "", "sets": 4, "reps": 10, "rest_seconds": 90}]
    assert client.put("/api/workout/plan/1", json={"exercises": bad}).status_code == 422
    bad_sets = [{"name": "卧推", "sets": 0, "reps": 10, "rest_seconds": 90}]
    assert client.put("/api/workout/plan/1", json={"exercises": bad_sets}).status_code == 422
    bad_rest = [{"name": "卧推", "sets": 4, "reps": 10, "rest_seconds": -1}]
    assert client.put("/api/workout/plan/1", json={"exercises": bad_rest}).status_code == 422


# ---------- 训练打卡 ----------

def test_log_create_list_delete(client):
    log = client.post("/api/workout/logs", json={
        "date": "2026-10-16", "duration_seconds": 3600,
        "exercises": [{"name": "卧推", "sets": 4, "reps": 10, "rest_seconds": 90}],
    }).json()
    assert log["id"] == 1
    assert log["exercises"][0]["name"] == "卧推"
    assert "created_at" in log

    client.post("/api/workout/logs", json={"duration_seconds": 1800,
                                          "exercises": [{"name": "深蹲", "sets": 3, "reps": 12}]})
    logs = client.get("/api/workout/logs").json()
    assert logs[0]["date"] >= logs[-1]["date"]  # 日期倒序

    assert client.delete(f"/api/workout/logs/{log['id']}").json() == {"deleted": True}
    assert len(client.get("/api/workout/logs").json()) == 1
    assert client.delete("/api/workout/logs/999").status_code == 404


def test_summary_streak_and_week_count(client):
    monday = _monday()
    # 本周两天 + 上周一天
    for d in [monday, monday + timedelta(days=1), monday - timedelta(days=3)]:
        client.post("/api/workout/logs", json={"date": _iso(d), "duration_seconds": 600, "exercises": []})

    total, week_count, _ = _summary_counts()
    assert total == 3
    assert week_count == 2  # 只统计本周（周一起算）

    summary = client.get("/api/workout/summary").json()
    assert summary["total"] == 3 and summary["week_count"] == 2


def test_summary_streak_consecutive_days(client, isolated_data):
    import store
    today = date.today()
    # 昨天+今天连续 → streak 2
    dates = {today.isoformat(), (today - timedelta(days=1)).isoformat(),
             (today - timedelta(days=3)).isoformat()}  # 断档一天
    store.save("workout_logs", [
        {"id": i + 1, "date": d, "duration_seconds": 60, "exercises": [], "created_at": ""}
        for i, d in enumerate(sorted(dates, reverse=True))
    ])
    _, _, streak = _summary_counts()
    assert streak == 2  # 今天、昨天连续；前天缺失中断

    # 只有上周记录 → streak 0
    store.save("workout_logs", [
        {"id": 1, "date": (today - timedelta(days=10)).isoformat(), "duration_seconds": 60,
         "exercises": [], "created_at": ""}
    ])
    _, _, streak = _summary_counts()
    assert streak == 0


# ---------- 身体数据 ----------

def test_body_crud_and_desc(client):
    b1 = client.post("/api/body", json={"weight_kg": 72.5}).json()  # date 缺省今天
    assert b1["date"] == date.today().isoformat()
    client.post("/api/body", json={"date": "2026-10-10", "weight_kg": 73.0})

    listed = client.get("/api/body").json()
    assert listed[0]["date"] >= listed[-1]["date"]

    assert client.delete(f"/api/body/{b1['id']}").status_code == 200
    assert client.post("/api/body", json={"weight_kg": -1}).status_code == 422
    assert client.post("/api/body", json={"date": "bad", "weight_kg": 70}).status_code == 422


# ---------- 饮食 ----------

def _add_diet(client, **kw):
    res = client.post("/api/diet", json=kw)
    assert res.status_code == 200, res.text
    return res.json()


def test_diet_create_default_eaten_false_and_sort(client):
    d = "2026-10-16"
    _add_diet(client, date=d, meal="lunch", name="鸡胸肉沙拉", calories=450)
    _add_diet(client, date=d, meal="breakfast", name="鸡蛋", calories=200)
    _add_diet(client, date=d, meal="snack", name="酸奶", calories=150)

    items = client.get("/api/diet", params={"date": d}).json()
    assert [i["meal"] for i in items] == ["breakfast", "lunch", "snack"]  # 按餐段顺序
    assert all(i["eaten"] is False for i in items)

    assert client.get("/api/diet", params={"date": "2026-10-17"}).json() == []
    assert client.get("/api/diet").status_code == 422  # 缺 date


def test_diet_check_eaten_and_summary(client):
    d = "2026-10-16"
    e1 = _add_diet(client, date=d, meal="breakfast", name="鸡蛋", calories=200)
    e2 = _add_diet(client, date=d, meal="lunch", name="鸡胸肉沙拉", calories=450)
    _add_diet(client, date=d, meal="snack", name="酸奶", calories=150)  # 不勾

    client.put(f"/api/diet/{e1['id']}", json={"eaten": True})
    client.put(f"/api/diet/{e2['id']}", json={"eaten": True})

    summary = client.get("/api/diet/summary", params={"date": d}).json()
    assert summary["intake"] == 650  # 只算已勾选两条
    assert summary["target"] == 2000  # 读设置默认值
    assert summary["by_meal"] == {"breakfast": 200, "lunch": 450, "dinner": 0, "snack": 0}


def test_diet_validation(client):
    assert client.post("/api/diet", json={"name": "x"}).status_code == 422  # 缺 meal
    assert client.post("/api/diet", json={"meal": "supper", "name": "x"}).status_code == 422  # 非法餐段
    assert client.post("/api/diet", json={"meal": "lunch", "name": ""}).status_code == 422
    assert client.post("/api/diet", json={"meal": "lunch", "name": "x", "calories": -5}).status_code == 422
    assert client.put("/api/diet/999", json={"eaten": True}).status_code == 404
