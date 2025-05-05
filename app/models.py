from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class GraphModel(Base):
    """
    SQLAlchemy graph model.

    Properties:
        id (int): unique identifier of object.
        nodes (List[NodeModel]): list of nodes in graph.
        edges (List[EdgeModel]): list of edges in graph.


    If graph is removed, all connected nodes and edges are deleted via cascade deletion.
    """
    __tablename__ = "graphs"

    id = Column(Integer, primary_key=True)
    nodes = relationship(
        "NodeModel", back_populates="graph", cascade="all, delete-orphan"
    )
    edges = relationship(
        "EdgeModel", back_populates="graph", cascade="all, delete-orphan"
    )


class NodeModel(Base):
    """
    SQLAlchemy node model.

    Properties:
        id (int): unique identifier of object.
        name (str): name of the node(max lenght 255 chars)
        graph_id(int): Foreign key to the parent graph.
        graph(GraphModel): Reference to the parent GraphModel instance.

    Each node name must be unique within the same graph.
    """
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    graph_id = Column(Integer, ForeignKey("graphs.id"), nullable=False)
    graph = relationship("GraphModel", back_populates="nodes")

    __table_args__ = (UniqueConstraint("graph_id", "name"),)


class EdgeModel(Base):
    """
    SQLAlchemy node model.

    Properties:
        id (int): unique identifier of object.
        graph_id(int): Foreign key to the parent graph.
        source_id(int): Foreign key to the source node.
        target_id(int): Foreign key to the target node.
        graph(GraphModel): Reference to the parent GraphModel instance.
        source(NodeModel): Reference to the source NodeModel instance.
        target(NodeModel): Reference to the target NodeModel instance.

    Each node name must be unique within the same graph.
    """
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True)
    graph_id = Column(Integer, ForeignKey("graphs.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)

    graph = relationship("GraphModel", back_populates="edges")
    source = relationship("NodeModel", foreign_keys=[source_id])
    target = relationship("NodeModel", foreign_keys=[target_id])

    __table_args__ = (
        UniqueConstraint("graph_id", "source_id", "target_id"),
        UniqueConstraint(
            "graph_id",
            "target_id",
            "source_id",
        ),
    )
