"""T1.2 应用入口测试：system/info、静态托管回退、引导页。"""
from pathlib import Path

import main
import store


def test_system_info(client, isolated_data):
    res = client.get("/api/system/info")
    assert res.status_code == 200
    body = res.json()
    assert body["port"] == 8321
    assert body["version"] == "1.0"
    assert body["data_dir"] == str(store.DATA_DIR.resolve())
    assert body["lan_ip"]  # 有 IP 值即可（CI 环境可能是 127.0.0.1）


def test_guide_page_when_dist_missing(client, monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DIST_DIR", tmp_path / "dist")  # 不存在
    res = client.get("/")
    assert res.status_code == 200
    assert "构建" in res.text


def test_spa_fallback_to_index(client, monkeypatch, tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html><body>SPA</body></html>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    monkeypatch.setattr(main, "DIST_DIR", dist)

    assert client.get("/").text == "<html><body>SPA</body></html>"
    # SPA 前端路由回退
    assert client.get("/today").status_code == 200
    assert "SPA" in client.get("/fitness/diet").text
    # 静态资源文件
    assert client.get("/assets/app.js").text == "console.log(1)"


def test_unknown_api_returns_404(client, monkeypatch, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>SPA</html>", encoding="utf-8")
    monkeypatch.setattr(main, "DIST_DIR", dist)
    assert client.get("/api/not-exist").status_code == 404


def test_data_dir_real_layout(client):
    """系统信息中的 data_dir 指向 store 当前生效目录。"""
    res = client.get("/api/system/info")
    assert res.json()["data_dir"]
