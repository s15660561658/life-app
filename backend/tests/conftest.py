"""pytest 公共夹具：隔离数据目录 + TestClient。"""
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

import store  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    """每个测试使用独立临时数据目录，互不污染真实数据。"""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    yield tmp_path


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app

    return TestClient(app)
