from schemas import GraphCreate, GraphCreateResponse, ErrorResponse, GraphReadResponse, AdjacencyListResponse
import fastapi
from app.logic import create_graph, graph_as_lists, graph_as_adj, graph_as_reverse_adj


app = fastapi.FastAPI()


@app.post("/api/graph/", response_model=GraphCreateResponse, status_code=201, responses={400: {"model": ErrorResponse}}, operation_id="create_graph_api_graph__post")
def create_graph(request_body: GraphCreate):
    response = create_graph(request_body)
    return response


@app.get("/api/graph/{graph_id}/", response_model=GraphReadResponse, responses={404: {"model": ErrorResponse}}, operation_id="read_graph_api_graph__graph_id___get")
def get_graph_as_lists(graph_id: int):
    response = graph_as_lists(graph_id)
    return response


@app.get("/api/graph/{graph_id}/adjacency_list", response_model=AdjacencyListResponse, responses={404: {"model": ErrorResponse}}, operation_id="get_adjacency_list_api_graph__graph_id__adjacency_list_get")
def get_graph_as_adj(graph_id: int):
    response = graph_as_adj(graph_id)
    return response


@app.get("/api/graph/{graph_id}/reverse_adjacency_list", response_model=AdjacencyListResponse, responses={404: {"model": ErrorResponse}}, operation_id="get_reverse_adjacency_list_api_graph__graph_id__reverse_adjacency_list_get")
def get_graph_as_reverse_adj(graph_id: int):
    response = graph_as_reverse_adj(graph_id)
    return response


@app.delete("/api/graph/{graph_id}/node/{node_name}", operation_id="delete_node_api_graph__graph_id__node__node_name__delete")
def delete_node():
  pass