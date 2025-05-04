import fastapi
from logic import (
    create_graph,
    delete_node_by_name,
    graph_as_adj,
    graph_as_lists,
    graph_as_reverse_adj,
)
from schemas import (
    AdjacencyListResponse,
    ErrorResponse,
    GraphCreate,
    GraphCreateResponse,
    GraphReadResponse,
    HTTPValidationError,
    ValidationError,
)

app = fastapi.FastAPI()


@app.get("/")
def healthcheck():
    return {"message": "Service is healthy"}


@app.post(
    "/api/graph/",
    response_model=GraphCreateResponse,
    status_code=201,
    responses={400: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
    operation_id="create_graph_api_graph__post",
)
def create_graph_api(request_body: GraphCreate):
    response = create_graph(request_body)
    return response


@app.get(
    "/api/graph/{graph_id}/",
    response_model=GraphReadResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
    operation_id="read_graph_api_graph__graph_id___get",
)
def get_graph_as_lists(graph_id: int):
    response = graph_as_lists(graph_id)
    return response


@app.get(
    "/api/graph/{graph_id}/adjacency_list",
    response_model=AdjacencyListResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
    operation_id="get_adjacency_list_api_graph__graph_id__adjacency_list_get",
)
def get_graph_as_adj(graph_id: int):
    response = graph_as_adj(graph_id)
    return response


@app.get(
    "/api/graph/{graph_id}/reverse_adjacency_list",
    response_model=AdjacencyListResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
    operation_id="get_reverse_adjacency_list_api_graph__graph_id__reverse_adjacency_list_get",
)
def get_graph_as_reverse_adj(graph_id: int):
    response = graph_as_reverse_adj(graph_id)
    return response


@app.delete(
    "/api/graph/{graph_id}/node/{node_name}",
    status_code=204,
    operation_id="delete_node_api_graph__graph_id__node__node_name__delete",
    responses={404: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
)
def delete_node(graph_id: int, node_name: str):
    if response := delete_node_by_name(graph_id, node_name):
        return response
    return None
