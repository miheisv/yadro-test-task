import os
from contextlib import contextmanager

from fastapi import HTTPException, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import EdgeModel, GraphModel, NodeModel
from app.schemas import (
    AdjacencyListResponse,
    ErrorResponse,
    GraphCreate,
    GraphCreateResponse,
    GraphReadResponse,
    HTTPValidationError,
    ValidationError,
)

USER = os.environ.get("DB_USER", "postgres")
PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
HOST = os.environ.get("DB_HOST", "localhost")
SQLALCHEMY_DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_acyclic(nodes: list[str], edges: list[tuple[str, str]]):
    graph = {}

    for node in nodes:
        graph[node.name] = []

    for edge in edges:
        graph[edge.source].append(edge.target)

    visited = set()
    visiting = set()

    def dfs(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True

        visiting.add(node)
        for neighbor in graph[node]:
            if not dfs(neighbor):
                return False
        visiting.remove(node)
        visited.add(node)
        return True

    for node in nodes:
        if node not in visited:
            if not dfs(node):
                return False

    return True


def validate_data(data: GraphCreate):
    errors = HTTPValidationError()
    if len(data.nodes) == 0:
        errors.append(
            ValidationError(
                loc=["body", "nodes"],
                msg="There aren't any vertex!",
                type="value_error",
            )
        )

    if any(not node.name.isalpha() for node in data.nodes):
        errors.append(
            ValidationError(
                loc=["body", "nodes"],
                msg="There are nodes with incorrect names!",
                type="value_error",
            )
        )

    if any(len(node.name) > 255 for node in data.nodes):
        errors.append(
            ValidationError(
                loc=["body", "nodes"],
                msg="There are nodes with too long names",
                type="value_error",
            )
        )

    node_names = [node.name for node in data.nodes]
    if len(node_names) != len(set(node_names)):
        errors.append(
            ValidationError(
                loc=["body", "nodes"],
                msg="There are vertex with the same name!",
                type="value_error",
            )
        )

    seen_edges = set()
    for edge in data.edges:
        if edge.source not in node_names or edge.target not in node_names:
            errors.append(
                ValidationError(
                    loc=["body", "edges"],
                    msg=f"Edge contains unknown nodes: {edge.source} -> {edge.target}",
                    type="value_error",
                )
            )
        if (edge.source, edge.target) in seen_edges:
            errors.append(
                ValidationError(
                    loc=["body", "edges"],
                    msg=f"Duplicate edge: {edge.source} -> {edge.target}",
                    type="value_error.duplicate",
                )
            )
        if (edge.target, edge.source) in seen_edges:
            errors.append(
                ValidationError(
                    loc=["body", "edges"],
                    msg=f"Duplicate reverse edge: {edge.target} -> {edge.source}",
                    type="value_error.duplicate",
                )
            )
        seen_edges.add((edge.source, edge.target))

    if is_acyclic(
        [node.name for node in data.nodes],
        [(edge.source, edge.target) for edge in data.edges],
    ):
        errors.append(
            ValidationError(
                loc=["body", "edges"],
                msg="There is a cycle in graph!",
                type="value_error.cycle",
            )
        )
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    return None


def create_graph(data: GraphCreate):
    validate_data(data)

    with get_db() as db:
        try:
            graph = GraphModel()
            db.add(graph)
            db.flush()

            nodes = {}
            for node_data in data.nodes:
                node = NodeModel(name=node_data.name, graph=graph)
                db.add(node)
                nodes[node.name] = node

            for edge_data in data.edges:
                edge = EdgeModel(
                    graph=graph,
                    source=nodes[edge_data.source],
                    target=nodes[edge_data.target],
                )
                db.add(edge)

            db.commit()
            db.refresh(graph)
            return GraphCreateResponse(id=graph.id)
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=400, detail=ErrorResponse(msg="Failed to add graph")
            ) from exc


def get_graph(graph_id: int):
    with get_db() as db:
        return db.query(GraphModel).filter(GraphModel.graph_id == graph_id).first()


def graph_as_lists(graph_id: int):
    graph = get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph entity not found")
    return GraphReadResponse(
        id=graph_id,
        nodes=[{"name": node.name} for node in graph.nodes],
        edges=[
            {"source": edge.source.name, "target": edge.target.name}
            for edge in graph.edges
        ],
    )


def graph_as_adj(graph_id: int):
    graph = get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph entity not found")
    adj = {node.name: [] for node in graph.nodes}
    for edge in graph.edges:
        adj[edge.source.name].append(edge.target.name)
    return AdjacencyListResponse(adjacency_list=adj)


def graph_as_reverse_adj(graph_id: int):
    graph = get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph entity not found")
    reverse_adj = {node.name: [] for node in graph.nodes}
    for edge in graph.edges:
        reverse_adj[edge.target.name].append(edge.source.name)
    return AdjacencyListResponse(adjacency_list=reverse_adj)


def delete_node_by_name(graph_id: int, node_name: str):
    graph = get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph entity not found")

    with get_db() as db:
        node = db.query(NodeModel).filter_by(graph_id=graph_id, name=node_name).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node entity not found")

        db.query(EdgeModel).filter(
            (EdgeModel.source_id == node.id) | (EdgeModel.target_id == node.id)
        ).delete(synchronize_session=False)

        db.delete(node)
        db.commit()

        return None
