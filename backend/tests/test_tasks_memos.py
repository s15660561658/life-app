"""T1.3 接口批次一测试：今日计划 + 备忘录。"""


# ---------- 今日计划 ----------

def _create_task(client, **kw):
    body = {"title": "任务", "date": "2026-10-16", **kw}
    res = client.post("/api/tasks", json=body)
    assert res.status_code == 200, res.text
    return res.json()


def test_task_create_returns_full_entity(client):
    t = _create_task(client, title="晨会材料准备", start_time="09:00", end_time="10:00")
    assert t["id"] == 1
    assert t["done"] is False
    assert t["note"] == ""
    assert t["start_time"] == "09:00"


def test_task_sort_allday_first_then_time_asc(client):
    _create_task(client, title="有时间", start_time="09:00")
    _create_task(client, title="全天任务")
    _create_task(client, title="更晚", start_time="15:00")

    res = client.get("/api/tasks", params={"date": "2026-10-16"})
    titles = [t["title"] for t in res.json()]
    assert titles == ["全天任务", "有时间", "更晚"]


def test_task_filter_by_date(client):
    _create_task(client, date="2026-10-16")
    _create_task(client, date="2026-10-17")
    assert len(client.get("/api/tasks", params={"date": "2026-10-16"}).json()) == 1
    assert len(client.get("/api/tasks", params={"date": "2026-10-17"}).json()) == 1
    assert client.get("/api/tasks", params={"date": "2026-10-18"}).json() == []


def test_task_put_toggle_done_and_edit(client):
    t = _create_task(client, title="写周报", start_time="10:30", end_time="11:30")
    res = client.put(f"/api/tasks/{t['id']}", json={"done": True})
    assert res.status_code == 200
    assert res.json()["done"] is True
    # 局部更新：只改标题，done 保持
    res2 = client.put(f"/api/tasks/{t['id']}", json={"title": "写月报"})
    assert res2.json()["title"] == "写月报"
    assert res2.json()["done"] is True


def test_task_put_and_delete_404(client):
    assert client.put("/api/tasks/999", json={"done": True}).status_code == 404
    assert client.delete("/api/tasks/999").status_code == 404


def test_task_delete(client):
    t = _create_task(client)
    assert client.delete(f"/api/tasks/{t['id']}").json() == {"deleted": True}
    assert client.get("/api/tasks", params={"date": "2026-10-16"}).json() == []


def test_task_validation(client):
    assert client.post("/api/tasks", json={"title": "  "}).status_code == 422  # 空标题
    assert client.post("/api/tasks", json={"title": "x", "date": "2026-13-01"}).status_code == 422  # 非法日期
    assert client.post("/api/tasks", json={"title": "x", "start_time": "9:0"}).status_code == 422  # 非法时间
    assert client.post("/api/tasks", json={}).status_code == 422  # 缺 title
    assert client.get("/api/tasks").status_code == 422  # 缺 date 参数
    assert client.get("/api/tasks", params={"date": "bad"}).status_code == 422


def test_task_id_increments_across_dates(client):
    a = _create_task(client, date="2026-10-16")
    b = _create_task(client, date="2026-10-17")
    assert b["id"] == a["id"] + 1


# ---------- 备忘录 ----------

def _create_memo(client, content):
    res = client.post("/api/memos", json={"content": content})
    assert res.status_code == 200, res.text
    return res.json()


def test_memo_create_with_backend_timestamp(client):
    m = _create_memo(client, "买咖啡豆")
    assert m["id"] == 1
    assert len(m["created_at"]) == 16  # YYYY-MM-DD HH:MM
    assert m["created_at"][4] == "-" and m["created_at"][10] == " "


def test_memo_desc_order_and_limit(client):
    _create_memo(client, "第一条")
    _create_memo(client, "第二条")
    _create_memo(client, "第三条")

    all_items = client.get("/api/memos").json()
    assert [m["content"] for m in all_items] == ["第三条", "第二条", "第一条"]

    limited = client.get("/api/memos", params={"limit": 2}).json()
    assert [m["content"] for m in limited] == ["第三条", "第二条"]


def test_memo_update_and_delete(client):
    m = _create_memo(client, "原内容")
    res = client.put(f"/api/memos/{m['id']}", json={"content": "改内容"})
    assert res.json()["content"] == "改内容"
    assert client.delete(f"/api/memos/{m['id']}").status_code == 200
    assert client.get("/api/memos").json() == []
    assert client.put("/api/memos/999", json={"content": "x"}).status_code == 404


def test_memo_validation(client):
    assert client.post("/api/memos", json={"content": ""}).status_code == 422
    assert client.post("/api/memos", json={}).status_code == 422
