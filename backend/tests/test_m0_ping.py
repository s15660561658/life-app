"""M0 冒烟测试：应用可创建、ping 可用。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


def test_ping():
    client = TestClient(app)
    res = client.get("/api/ping")
    assert res.status_code == 200
    assert res.json() == {"pong": True}
