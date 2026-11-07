"""Shared test fixtures. Nothing here touches the internet: the fake job boards run in-process."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mock_jobboard import generator, server
from pipeline.evaluate import load_truth


@pytest.fixture(scope="session")
def records():
    """300 fake offers, always the same (fixed seed)."""
    return generator.generate_records(300, seed_value=42)


@pytest.fixture(scope="session")
def db_path(records, tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "mock_jobs.db"
    generator.save_to_sqlite(records, path)
    return path


@pytest.fixture(scope="session")
def truth(db_path):
    return load_truth(str(db_path))


@pytest.fixture(scope="session")
def client(db_path):
    """The three fake job boards, served from the temporary database, without a real server."""
    patch = pytest.MonkeyPatch()
    patch.setattr(server, "DB_PATH", str(db_path))
    yield TestClient(server.app)
    patch.undo()