import os
from contextlib import contextmanager

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DataError, IntegrityError

from models import EdgeModel, GraphModel, NodeModel, Base
from schemas import (
    AdjacencyListResponse,
    ErrorResponse,
    GraphCreate,
    GraphCreateResponse,
    GraphReadResponse,
    HTTPValidationError,
    ValidationError,
)

USER = os.environ.get("POSTGRES_USER", "postgres")
PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
HOST = os.environ.get("DB_HOST", "localhost")
PORT = os.environ.get("DB_PORT", "5432")
SQLALCHEMY_DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@contextmanager
def get_db():
    """
    Provide a database session.

    Yields:
        Session: SQLAlchemy Session object.

    Guarantuee the session will be closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_acyclic(nodes: list[str], edges: list[tuple[str, str]]) -> bool:
    """
    Check directed graph is acyclic.

    Args:
        nodes(List[str]): list of node names.
        edges(List[Tuple[str, str]]): list of (source, target) pairs.

    Returns:
        bool: True if no cycle exists, False otherwise.
    """
    graph = {}

    for node in nodes:
        graph[node] = []

    for edge in edges:
        graph.get(edge[0], []).append(edge[1])

    visited = set()
    visiting = set()

    def dfs(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True

        visiting.add(node)
        for neighbor in graph.get(node, []):
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


def validate_data(data: GraphCreate) -> None:
    """
    Validate graph creation data.

    Args:
        data (GraphCreate): input data with nodes and edges.

    Raises:
        HTTPException(422):
            - if no nodes in graph.
            - if node names are non-alphabetic or too long(>255).
            - if duplicate node names exist.
            - if any edge contains unknown nodes.
            - if the graph contains a cycle.
    """
    errors = HTTPValidationError(detail=[])
    if len(data.nodes) == 0:
        errors.detail.append(
            ValidationError(
                loc=["body", "nodes"],
                msg="There aren't any vertex!",
                type="value_error",
            )
        )

    if any(not node.name.isalpha() for node in data.nodes):
        errors.detail.append(
            ValidationError(
                loc=["body", "nodes"],
                msg="There are nodes with incorrect names!",
                type="value_error",
            )
        )

    if any(len(node.name) > 255 for node in data.nodes):
        errors.detail.append(
            ValidationError(
                loc=["body", "nodes"],
                msg="There are nodes with too long names",
                type="value_error",
            )
        )

    node_names = [node.name for node in data.nodes]
    if len(node_names) != len(set(node_names)):
        errors.detail.append(
            ValidationError(
                loc=["body", "nodes"],
                msg="There are vertex with the same name!",
                type="value_error",
            )
        )

    if set([edge.source for edge in data.edges] + [edge.target for edge in data.edges]) - set(node_names):
        errors.detail.append(
            ValidationError(
                loc=["body", "nodes"],
                msg="There are incorrect edges!",
                type="value_error",
            )
        )

    if not is_acyclic(
        [node.name for node in data.nodes],
        [(edge.source, edge.target) for edge in data.edges],
    ):
        errors.detail.append(
            ValidationError(
                loc=["body", "edges"],
                msg="There is a cycle in graph!",
                type="value_error.cycle",
            )
        )
    if errors.detail:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": d.loc,
                    "msg": d.msg,
                    "type": d.type
                }
                for d in errors.detail
            ]
        )    
    return None


def create_graph(data: GraphCreate) -> GraphCreateResponse:
    """
    Create a new graph.

    Args:
        data (GraphCreate): input data with nodes and edges.

    Returns:
        GraphCreateResponse: contains the created graph's ID.

    Raises:
        HTTPException(400):
            - if edges contains duplicates.
            - if general failure to add graph.
    """
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

        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Duplicate node or edge constraint violated"
            ) from exc

        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=400, detail="Failed to add graph"
            ) from exc


def graph_as_lists(graph_id: int) -> GraphReadResponse:
    """
    Represent a graph as lists of nodes and edges.

    Args:
        graph_id (int): the identifier of the graph to represent.

    Returns:
        GraphReadResponse: contains node and edge lists.

    Raises:
        HTTPException(404): if the graph is not found.
    """
    with get_db() as db:
        try:
            graph = db.query(GraphModel).filter(GraphModel.id == graph_id).first()
        except Exception as exc:
            raise HTTPException(status_code=404, detail="Graph entity not found") from exc
        if not graph:
            raise HTTPException(404, "Graph not found")
        return GraphReadResponse(
            id=graph_id,
            nodes=[{"name": node.name} for node in graph.nodes],
            edges=[
                {"source": edge.source.name, "target": edge.target.name}
                for edge in graph.edges
            ],
        )


def graph_as_adj(graph_id: int) -> AdjacencyListResponse:
    """
    Represent a graph as an adjacency list.

    Args:
        graph_id (int): the identifier of the graph to represent.

    Returns:
        AdjacencyListResponse: dict where keys are node names, values are lists of neighbor's names.

    Raises:
        HTTPException(404): if the graph is not found.
    """
    with get_db() as db:
        try:
            graph = db.query(GraphModel).filter(GraphModel.id == graph_id).first()
        except Exception as exc:
            raise HTTPException(status_code=404, detail="Graph entity not found") from exc
        if not graph:
            raise HTTPException(404, "Graph not found")
        adj = {node.name: [] for node in graph.nodes}
        for edge in graph.edges:
            adj[edge.source.name].append(edge.target.name)
        return AdjacencyListResponse(adjacency_list=adj)


def graph_as_reverse_adj(graph_id: int) -> AdjacencyListResponse:
    """
    Represent a graph as a reverse adjacency list.

    Args:
        graph_id (int): the identifier of the graph to represent.

    Returns:
        AdjacencyListResponse: dict where keys are node names, values are lists of neighbor's names.

    Raises:
        HTTPException(404): if the graph is not found.
    """
    with get_db() as db:
        try:
            graph = db.query(GraphModel).filter(GraphModel.id == graph_id).first()
        except Exception as exc:
            raise HTTPException(status_code=404, detail="Graph entity not found") from exc
        if not graph:
            raise HTTPException(404, "Graph not found")
        reverse_adj = {node.name: [] for node in graph.nodes}
        for edge in graph.edges:
            reverse_adj[edge.target.name].append(edge.source.name)
        return AdjacencyListResponse(adjacency_list=reverse_adj)


def delete_node_by_name(graph_id: int, node_name: str) -> None:
    """
    Delete a node and its connected edges from the graph.

    Args:
        graph_id (int): the identifier of the graph.
        node_name (str): name of the node to delete.

    Raises:
        HTTPException(404):
            - if the graph is not found.
            - if the node is not found.
    """
    with get_db() as db:
        try:
            graph = db.query(GraphModel).filter(GraphModel.id == graph_id).first()
        except Exception as exc:
            raise HTTPException(status_code=404, detail="Graph entity not found") from exc
        if not graph:
            raise HTTPException(404, "Graph not found")

        node = db.query(NodeModel).filter_by(graph_id=graph_id, name=node_name).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node entity not found")

        db.query(EdgeModel).filter(
            (EdgeModel.source_id == node.id) | (EdgeModel.target_id == node.id)
        ).delete(synchronize_session=False)

        db.delete(node)
        db.commit()

        return None
