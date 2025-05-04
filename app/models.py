from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class GraphModel(Base):
    __tablename__ = "graphs"

    id = Column(Integer, primary_key=True)
    nodes = relationship(
        "NodeModel", back_populates="graph", cascade="all, delete-orphan"
    )
    edges = relationship(
        "EdgeModel", back_populates="graph", cascade="all, delete-orphan"
    )


class NodeModel(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    graph_id = Column(Integer, ForeignKey("graphs.id"), nullable=False)
    graph = relationship("GraphModel", back_populates="nodes")

    __table_args__ = (UniqueConstraint("graph_id", "name"),)


class EdgeModel(Base):
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
