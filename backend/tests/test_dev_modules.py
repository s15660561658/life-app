"""T1.4 接口批次二测试：项目（内嵌任务）+ Bug + 笔记。"""


# ---------- 项目 ----------

def _create_project(client, **kw):
    res = client.post("/api/projects", json={"name": "项目", **kw})
    assert res.status_code == 200, res.text
    return res.json()


def test_project_create_and_list_desc(client):
    a = _create_project(client, name="项目A")
    b = _create_project(client, name="项目B", deadline="2026-11-01", note="备注")
    assert a["status"] == "ongoing" and a["tasks"] == []
    assert b["deadline"] == "2026-11-01"

    listed = client.get("/api/projects").json()
    assert [p["name"] for p in listed] == ["项目B", "项目A"]  # 创建时间倒序


def test_project_embedded_task_flow_and_progress(client):
    p = _create_project(client, name="个人APP")
    pid = p["id"]

    t1 = client.post(f"/api/projects/{pid}/tasks", json={"title": "搭建后端"}).json()
    t2 = client.post(f"/api/projects/{pid}/tasks", json={"title": "写前端"}).json()
    t3 = client.post(f"/api/projects/{pid}/tasks", json={"title": "联调"}).json()
    assert [t["id"] for t in (t1, t2, t3)] == [1, 2, 3]

    # 勾选 1 条 → 内嵌 tasks 状态正确
    res = client.put(f"/api/projects/{pid}/tasks/{t1['id']}", json={"done": True})
    assert res.json()["done"] is True

    detail = client.get("/api/projects").json()[0]
    assert len(detail["tasks"]) == 3
    assert detail["tasks"][0]["done"] is True
    done = sum(1 for t in detail["tasks"] if t["done"])
    assert done == 1  # 前端进度 = 1/3 ≈ 33%

    # 改标题
    client.put(f"/api/projects/{pid}/tasks/{t2['id']}", json={"title": "写前端页面"})
    detail = client.get("/api/projects").json()[0]
    assert detail["tasks"][1]["title"] == "写前端页面"

    # 删任务
    client.delete(f"/api/projects/{pid}/tasks/{t3['id']}")
    assert len(client.get("/api/projects").json()[0]["tasks"]) == 2


def test_project_update_status_and_validation(client):
    p = _create_project(client)
    res = client.put(f"/api/projects/{p['id']}", json={"status": "paused"})
    assert res.json()["status"] == "paused"
    assert client.put(f"/api/projects/{p['id']}", json={"status": "bad"}).status_code == 422
    assert client.post("/api/projects", json={"name": ""}).status_code == 422
    assert client.put("/api/projects/999", json={"name": "x"}).status_code == 404


def test_project_delete_clears_bug_project_id(client):
    p = _create_project(client, name="被删项目")
    bug = client.post("/api/bugs", json={"title": "崩溃", "project_id": p["id"], "priority": "high"}).json()
    assert bug["project_id"] == p["id"]

    res = client.delete(f"/api/projects/{p['id']}")
    assert res.json() == {"deleted": True}

    bugs = client.get("/api/bugs").json()
    assert len(bugs) == 1
    assert bugs[0]["project_id"] is None  # Bug 保留但解绑


# ---------- Bug ----------

def _create_bug(client, **kw):
    res = client.post("/api/bugs", json={"title": "Bug", **kw})
    assert res.status_code == 200, res.text
    return res.json()


def test_bug_create_defaults_and_flow(client):
    b = _create_bug(client, title="手机端打勾不生效", description="描述", priority="high")
    assert b["status"] == "open"
    assert b["solution"] == ""
    assert b["created_at"] == b["updated_at"]

    # open → in_progress → resolved，updated_at 自动刷新
    r1 = client.put(f"/api/bugs/{b['id']}", json={"status": "in_progress"}).json()
    assert r1["updated_at"] >= r1["created_at"]
    r2 = client.put(f"/api/bugs/{b['id']}", json={"status": "resolved", "solution": "已修复"}).json()
    assert r2["status"] == "resolved" and r2["solution"] == "已解决" or r2["solution"] == "已修复"
    assert r2["updated_at"] >= r1["updated_at"]


def test_bug_filter_by_status_and_project(client):
    p1 = client.post("/api/projects", json={"name": "P1"}).json()
    b1 = _create_bug(client, title="B1", project_id=p1["id"])  # open
    b2 = _create_bug(client, title="B2", priority="low")  # open
    client.put(f"/api/bugs/{b2['id']}", json={"status": "resolved"})

    assert len(client.get("/api/bugs").json()) == 2
    open_bugs = client.get("/api/bugs", params={"status": "open"}).json()
    assert [b["id"] for b in open_bugs] == [b1["id"]]
    resolved = client.get("/api/bugs", params={"status": "resolved"}).json()
    assert [b["id"] for b in resolved] == [b2["id"]]
    by_proj = client.get("/api/bugs", params={"project_id": p1["id"]}).json()
    assert [b["id"] for b in by_proj] == [b1["id"]]
    # 组合筛选
    both = client.get("/api/bugs", params={"status": "open", "project_id": p1["id"]}).json()
    assert [b["id"] for b in both] == [b1["id"]]


def test_bug_validation(client):
    assert client.post("/api/bugs", json={"title": ""}).status_code == 422
    assert client.post("/api/bugs", json={}).status_code == 422
    assert client.post("/api/bugs", json={"title": "x", "priority": "urgent"}).status_code == 422
    assert client.put("/api/bugs/999", json={"status": "open"}).status_code == 404
    # 关联不存在的项目
    assert client.post("/api/bugs", json={"title": "x", "project_id": 999}).status_code == 422
    assert client.get("/api/bugs", params={"status": "bad"}).status_code == 422


# ---------- 笔记 ----------

def _create_note(client, **kw):
    res = client.post("/api/notes", json={"title": "笔记", **kw})
    assert res.status_code == 200, res.text
    return res.json()


def test_note_create_and_desc_order(client):
    _create_note(client, title="第一篇")
    _create_note(client, title="第二篇", content="正文", tags=["python"])
    listed = client.get("/api/notes").json()
    assert [n["title"] for n in listed] == ["第二篇", "第一篇"]
    assert listed[0]["tags"] == ["python"]


def test_note_search_hits_title_and_content(client):
    _create_note(client, title="FastAPI 局域网配置", content="uvicorn host 设置")
    _create_note(client, title="Vue 路由", content="FastAPI 托管静态文件")
    _create_note(client, title="健身计划", content="卧推组数")

    by_title = client.get("/api/notes", params={"q": "fastapi"}).json()
    titles = {n["title"] for n in by_title}
    assert titles == {"FastAPI 局域网配置", "Vue 路由"}  # 标题和正文都能命中

    assert len(client.get("/api/notes", params={"q": "卧推"}).json()) == 1
    assert client.get("/api/notes", params={"q": "不存在的词"}).json() == []


def test_note_tag_filter_and_update(client):
    n = _create_note(client, title="标签笔记", tags=["python", "fastapi"])
    _create_note(client, title="无标签")

    tagged = client.get("/api/notes", params={"tag": "python"}).json()
    assert [x["title"] for x in tagged] == ["标签笔记"]

    res = client.put(f"/api/notes/{n['id']}", json={"tags": ["vue"], "content": "改了"})
    assert res.json()["tags"] == ["vue"]
    assert res.json()["updated_at"] >= n["updated_at"]
    assert client.get("/api/notes", params={"tag": "python"}).json() == []
    assert client.delete(f"/api/notes/{n['id']}").status_code == 200
