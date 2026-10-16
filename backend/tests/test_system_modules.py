"""T1.6 接口批次四测试：娱乐日程 + 设置/统计/备份/恢复/清空。"""
from datetime import date, datetime, timedelta


def _iso(d):
    return d.isoformat()


def _fmt(d):
    return d.strftime("%Y-%m-%d %H:%M")


# ---------- 娱乐日程 ----------

def _add_event(client, **kw):
    res = client.post("/api/events", json=kw)
    assert res.status_code == 200, res.text
    return res.json()


def test_event_upcoming_past_split(client):
    tomorrow = datetime.now() + timedelta(days=1)
    yesterday = datetime.now() - timedelta(days=1)
    future_ev = _add_event(client, title="和朋友开黑", category="game", start_at=_fmt(tomorrow))
    past_ev = _add_event(client, title="昨天的电影", category="movie", start_at=_fmt(yesterday))

    res = client.get("/api/events").json()
    assert [e["id"] for e in res["upcoming"]] == [future_ev["id"]]
    assert [e["id"] for e in res["past"]] == [past_ev["id"]]
    # 过期自动归入往期；手动标记完成也归入往期
    client.put(f"/api/events/{future_ev['id']}", json={"done": True})
    res = client.get("/api/events").json()
    assert res["upcoming"] == []
    assert {e["id"] for e in res["past"]} == {future_ev["id"], past_ev["id"]}


def test_event_upcoming_asc_past_desc(client):
    now = datetime.now()
    e1 = _add_event(client, title="后天", start_at=_fmt(now + timedelta(days=2)))
    e2 = _add_event(client, title="明天", start_at=_fmt(now + timedelta(days=1)))
    p1 = _add_event(client, title="三天前", start_at=_fmt(now - timedelta(days=3)))
    p2 = _add_event(client, title="一天前", start_at=_fmt(now - timedelta(days=1)))

    res = client.get("/api/events").json()
    assert [e["id"] for e in res["upcoming"]] == [e2["id"], e1["id"]]  # 升序
    assert [e["id"] for e in res["past"]] == [p2["id"], p1["id"]]  # 倒序


def test_event_validation_and_delete(client):
    e = _add_event(client, title="局", category="party", start_at="2026-12-31 20:00")
    assert e["done"] is False and e["category"] == "party"

    assert client.post("/api/events", json={"title": "x"}).status_code == 422  # 缺 start_at
    assert client.post("/api/events", json={"start_at": "2026-12-31 20:00"}).status_code == 422  # 缺 title
    assert client.post("/api/events", json={"title": "x", "start_at": "2026-12-31"}).status_code == 422
    assert client.post("/api/events", json={"title": "x", "start_at": "2026-12-31 20:00", "category": "bad"}).status_code == 422
    assert client.delete(f"/api/events/{e['id']}").json() == {"deleted": True}
    assert client.delete("/api/events/999").status_code == 404


# ---------- 设置 ----------

def test_settings_get_put_partial(client):
    s = client.get("/api/settings").json()
    assert s == {"calorie_target": 2000, "default_rest_seconds": 60}

    res = client.put("/api/settings", json={"calorie_target": 1800}).json()
    assert res == {"calorie_target": 1800, "default_rest_seconds": 60}  # 局部更新

    client.put("/api/settings", json={"default_rest_seconds": 90})
    assert client.get("/api/settings").json() == {"calorie_target": 1800, "default_rest_seconds": 90}

    assert client.put("/api/settings", json={"calorie_target": 0}).status_code == 422
    assert client.put("/api/settings", json={"default_rest_seconds": -1}).status_code == 422
    assert client.put("/api/settings", json={}).status_code == 422

    # 饮食 target 跟随设置（承接 T1.5 场景）
    summary = client.get("/api/diet/summary").json()
    assert summary["target"] == 1800


# ---------- 统计 ----------

def test_stats_matches_manual_data(client):
    today = date.today()
    # 任务：今天 2 条（1 完成），昨天 1 条完成
    t1 = client.post("/api/tasks", json={"date": _iso(today), "title": "A"}).json()
    client.post("/api/tasks", json={"date": _iso(today), "title": "B", "start_time": "09:00"})
    client.put(f"/api/tasks/{t1['id']}", json={"done": True})
    y = client.post("/api/tasks", json={"date": _iso(today - timedelta(days=1)), "title": "C"}).json()
    client.put(f"/api/tasks/{y['id']}", json={"done": True})

    client.post("/api/memos", json={"content": "m1"})
    client.post("/api/memos", json={"content": "m2"})

    p = client.post("/api/projects", json={"name": "P"}).json()  # ongoing
    b1 = client.post("/api/bugs", json={"title": "b1"}).json()  # open
    b2 = client.post("/api/bugs", json={"title": "b2"}).json()
    client.put(f"/api/bugs/{b2['id']}", json={"status": "resolved"})

    client.post("/api/workout/logs", json={"duration_seconds": 600, "exercises": []})  # 今天打卡

    client.post("/api/diet", json={"meal": "lunch", "name": "饭", "calories": 500})
    client.post("/api/diet", json={"date": _iso(today - timedelta(days=1)), "meal": "lunch", "name": "旧饭", "calories": 300})

    ev = client.post("/api/events", json={"title": "下一场", "start_at": "2027-01-01 20:00"}).json()

    s = client.get("/api/stats").json()
    assert s["tasks_done_total"] == 2
    assert s["tasks_today_total"] == 2 and s["tasks_today_done"] == 1
    assert s["memos_count"] == 2
    assert s["projects_ongoing"] == 1 and s["projects_done"] == 0
    assert s["bugs_unresolved"] == 1 and s["bugs_resolved"] == 1
    assert s["workout_total"] == 1 and s["workout_today"] is True
    assert s["diet_intake_today"] == 0  # 未勾选
    assert s["diet_days"] == 2  # 两个不同日期有饮食记录
    assert s["next_event"] == {"id": ev["id"], "title": "下一场", "start_at": "2027-01-01 20:00"}

    # 勾选饮食后摄入变化
    items = client.get("/api/diet", params={"date": _iso(today)}).json()
    client.put(f"/api/diet/{items[0]['id']}", json={"eaten": True})
    assert client.get("/api/stats").json()["diet_intake_today"] == 500


def test_stats_next_event_none_when_empty(client, isolated_data):
    import store
    store.save("events", [])
    assert client.get("/api/stats").json()["next_event"] is None


# ---------- 备份 / 恢复 / 清空 ----------

def test_backup_export_restore_full_cycle(client):
    # 造数据
    client.post("/api/tasks", json={"title": "任务1", "start_time": "09:00"})
    client.post("/api/tasks", json={"title": "全天任务"})
    client.post("/api/memos", json={"content": "备忘"})
    p = client.post("/api/projects", json={"name": "项目"}).json()
    client.post(f"/api/projects/{p['id']}/tasks", json={"title": "子任务"})
    client.post("/api/bugs", json={"title": "bug", "project_id": p["id"]})
    client.post("/api/notes", json={"title": "笔记", "tags": ["py"]})
    client.put("/api/workout/plan/1", json={"exercises": [{"name": "卧推", "sets": 4, "reps": 10, "rest_seconds": 90}]})
    client.post("/api/workout/logs", json={"duration_seconds": 600, "exercises": [{"name": "卧推", "sets": 4, "reps": 10}]})
    client.post("/api/body", json={"weight_kg": 72.5})
    client.post("/api/diet", json={"meal": "lunch", "name": "饭", "calories": 500})
    client.post("/api/events", json={"title": "局", "start_at": "2027-01-01 20:00"})
    client.put("/api/settings", json={"calorie_target": 2200})

    # 导出
    res = client.get("/api/backup/export")
    assert res.status_code == 200
    assert "attachment" in res.headers["content-disposition"]
    backup = res.json()
    assert backup["app"] == "life-app" and backup["version"] == 1
    assert set(backup["data"].keys()) == {"tasks", "memos", "projects", "bugs", "notes",
                                          "workout_plan", "workout_logs", "body", "diet", "events", "settings"}
    assert backup["data"]["settings"]["calorie_target"] == 2200
    assert len(backup["data"]["tasks"]) == 2

    # 清空全部
    assert client.post("/api/data/clear", json={"modules": "all"}).json()["cleared"]
    today = date.today().isoformat()
    assert client.get("/api/tasks", params={"date": today}).json() == []
    assert client.get("/api/memos").json() == []
    assert client.get("/api/projects").json() == []
    # 默认保留设置
    assert client.get("/api/settings").json()["calorie_target"] == 2200

    # 恢复 → 与导出前一致
    assert client.post("/api/backup/restore", json=backup).json() == {"restored": True}
    assert len(client.get("/api/tasks", params={"date": today}).json()) == 2
    assert len(client.get("/api/projects").json()[0]["tasks"]) == 1
    assert client.get("/api/bugs").json()[0]["project_id"] == p["id"]
    assert client.get("/api/settings").json()["calorie_target"] == 2200
    assert client.get("/api/workout/plan").json()["1"][0]["name"] == "卧推"
    assert client.get("/api/system/info")  # 服务正常


def test_backup_restore_validation(client):
    assert client.post("/api/backup/restore", json={"app": "other", "version": 1}).status_code == 400
    assert client.post("/api/backup/restore", json={"app": "life-app", "version": 2, "data": {}}).status_code == 400
    assert client.post("/api/backup/restore", json={"app": "life-app", "version": 1, "data": {"tasks": []}}).status_code == 400


def test_data_clear_by_modules(client):
    client.post("/api/tasks", json={"title": "t"})
    client.post("/api/memos", json={"content": "m"})
    client.put("/api/settings", json={"calorie_target": 2500})

    res = client.post("/api/data/clear", json={"modules": ["tasks"]}).json()
    assert res == {"cleared": ["tasks"]}
    assert client.get("/api/tasks", params={"date": date.today().isoformat()}).json() == []
    assert len(client.get("/api/memos").json()) == 1  # 其他模块不受影响
    assert client.get("/api/settings").json()["calorie_target"] == 2500

    # 显式清 settings → 恢复默认
    client.post("/api/data/clear", json={"modules": ["settings"]})
    assert client.get("/api/settings").json()["calorie_target"] == 2000

    assert client.post("/api/data/clear", json={"modules": ["nope"]}).status_code == 422
    assert client.post("/api/data/clear", json={"modules": 123}).status_code == 422
