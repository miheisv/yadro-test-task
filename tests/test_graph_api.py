import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///sqlite"
os.environ["DATABASE_URL"] = DATABASE_URL

import app.logic as logic_mod
from app.api import app
from app.logic import Base

test_engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

logic_mod.engine = test_engine
logic_mod.SessionLocal = TestingSessionLocal

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def create_graph():
    payload = {
        "nodes": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
        "edges": [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}],
    }
    resp = client.post("/api/graph/", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def test_create_and_get_graph():
    graph_id = create_graph()
    resp = client.get(f"/api/graph/{graph_id}")
    assert resp.status_code == 200

    data = resp.json()
    assert data["id"] == graph_id
    assert sorted(n["name"] for n in data["nodes"]) == ["A", "B", "C"]
    assert {(e["source"], e["target"]) for e in data["edges"]} == {("A", "B"), ("B", "C")}


def test_duplicate_node():
    payload = {"nodes": [{"name": "A"}, {"name": "A"}], "edges": []}
    resp = client.post("/api/graph/", json=payload)
    assert resp.status_code == 422

    details = resp.json()["detail"]
    assert any("There are vertex with the same name!" in err["msg"] for err in details)


def test_empty_nodes():
    payload = {"nodes": [], "edges": []}
    resp = client.post("/api/graph/", json=payload)
    assert resp.status_code == 422

    details = resp.json()["detail"]
    assert any("There aren't any vertex!" in err["msg"] for err in details)


def test_incorrect_name():
    payload = {"nodes": [{"name": "A1"}], "edges": []}
    resp = client.post("/api/graph/", json=payload)
    assert resp.status_code == 422

    details = resp.json()["detail"]
    assert any("There are nodes with incorrect names!" in err["msg"] for err in details)


def test_long_name():
    long_name = "A" * 256
    payload = {"nodes": [{"name": long_name}], "edges": []}
    resp = client.post("/api/graph/", json=payload)
    assert resp.status_code == 422

    details = resp.json()["detail"]
    assert any("There are nodes with too long names!" in err["msg"] for err in details)


def test_incorrect_edge():
    payload = {
        "nodes": [{"name": "A"}, {"name": "B"}],
        "edges": [{"source": "A", "target": "B"}, {"source": "B1", "target": "A1"}],
    }
    resp = client.post("/api/graph/", json=payload)
    assert resp.status_code == 422

    details = resp.json()["detail"]
    assert any(err["msg"] == "There are incorrect edges!" for err in details)


def test_graph_with_cycle():
    payload = {
        "nodes": [{"name": "A"}, {"name": "B"}],
        "edges": [{"source": "A", "target": "B"}, {"source": "B", "target": "A"}],
    }
    resp = client.post("/api/graph/", json=payload)
    assert resp.status_code == 422

    details = resp.json()["detail"]
    assert any(err["msg"] == "There is a cycle in graph!" for err in details)


def test_graph_as_lists_success():
    graph_id = create_graph()
    resp = client.get(f"/api/graph/{graph_id}/")
    assert resp.status_code == 200

    data = resp.json()
    assert data["id"] == graph_id
    assert sorted(n["name"] for n in data["nodes"]) == ["A", "B", "C"]
    assert {(e["source"], e["target"]) for e in data["edges"]} == {("A", "B"), ("B", "C")}


def test_graph_as_lists_not_found():
    resp = client.get("/api/graph/999/")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Graph not found"


def test_graph_as_adj_success():
    graph_id = create_graph()
    resp = client.get(f"/api/graph/{graph_id}/adjacency_list")
    assert resp.status_code == 200

    assert resp.json()["adjacency_list"] == {
        "A": ["B"],
        "B": ["C"],
        "C": [],
    }


def test_graph_as_adj_not_found():
    resp = client.get("/api/graph/999/adjacency_list")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Graph not found"


def test_graph_as_reverse_adj_success():
    graph_id = create_graph()
    resp = client.get(f"/api/graph/{graph_id}/reverse_adjacency_list")
    assert resp.status_code == 200

    assert resp.json()["adjacency_list"] == {
        "A": [],
        "B": ["A"],
        "C": ["B"],
    }


def test_graph_as_reverse_adj_not_found():
    resp = client.get("/api/graph/999/reverse_adjacency_list")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Graph not found"


def test_delete_node_by_name_success():
    graph_id = create_graph()
    resp = client.delete(f"/api/graph/{graph_id}/node/A")
    assert resp.status_code == 204

    resp = client.get(f"/api/graph/{graph_id}/")
    assert resp.status_code == 200

    data = resp.json()
    assert sorted(n["name"] for n in data["nodes"]) == ["B", "C"]
    assert data["edges"] == [{"source": "B", "target": "C"}]


def test_delete_node_by_name_node_not_found():
    graph_id = create_graph()
    resp = client.delete(f"/api/graph/{graph_id}/node/Z")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Node entity not found"


def test_delete_node_by_name_graph_not_found():
    resp = client.delete("/api/graph/999/node/A")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Graph not found"
