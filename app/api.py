import fastapi
from app.logic import (
    create_graph,
    delete_node_by_name,
    graph_as_adj,
    graph_as_lists,
    graph_as_reverse_adj,
)
from app.schemas import (
    AdjacencyListResponse,
    ErrorResponse,
    GraphCreate,
    GraphCreateResponse,
    GraphReadResponse,
    HTTPValidationError,
)

app = fastapi.FastAPI()


@app.get("/")
def healthcheck():
    """
    Reports the current status of the service.

    Returns:
        Response: The response containing the status of service.
    """

    return {"message": "Service is healthy"}


@app.post(
    "/api/graph/",
    response_model=GraphCreateResponse,
    status_code=201,
    responses={400: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
    operation_id="create_graph_api_graph__post",
)
def create_graph_api(request: GraphCreate) -> (GraphCreateResponse|ErrorResponse|HTTPValidationError):
    """
    Create a new graph.

    Args:
        request (GraphCreate): Request body containing a list of nodes and a list of edges.

    Returns:
        Response:
            - GraphCreateResponse: data object with id of the new graph.
            - ErrorResponse: error object if graph invalid.
            - HTTPValidationError: a list of validation errors if input data doesn't match schema or invalid.
    """
    response = create_graph(request)
    return response


@app.get(
    "/api/graph/{graph_id}/",
    response_model=GraphReadResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
    operation_id="read_graph_api_graph__graph_id___get",
)
def get_graph_as_lists(graph_id: int) -> (GraphReadResponse|ErrorResponse|HTTPValidationError):
    """
    Represent the graph as a list of nodes and edges.

    Args:
        graph_id (int): The identifier of the graph to represent.

    Returns:
        - GraphReadResponse: object containing lists of nodes and edges.
        - ErrorResponse: error object if graph not found.
        - HTTPValidationError: validation error if parameter is invalid.
    """
    response = graph_as_lists(graph_id)
    return response


@app.get(
    "/api/graph/{graph_id}/adjacency_list",
    response_model=AdjacencyListResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
    operation_id="get_adjacency_list_api_graph__graph_id__adjacency_list_get",
)
def get_graph_as_adj(graph_id: int) -> (AdjacencyListResponse|ErrorResponse|HTTPValidationError):
    """
    Represent the graph as a direct adjacency list.

    Args:
        graph_id (int): The identifier of the graph to represent.

    Returns:
        Response:
            - AdjacencyListResponse: dict where keys are node names, values are lists of neighbor's names.
            - ErrorResponse: error object if graph not found.
            - HTTPValidationError: validation error if parameter is invalid.
    """
    response = graph_as_adj(graph_id)
    return response


@app.get(
    "/api/graph/{graph_id}/reverse_adjacency_list",
    response_model=AdjacencyListResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
    operation_id="get_reverse_adjacency_list_api_graph__graph_id__reverse_adjacency_list_get",
)
def get_graph_as_reverse_adj(graph_id: int) -> (AdjacencyListResponse|ErrorResponse|HTTPValidationError):
    """
    Represent the graph as a reverse adjacency list.

    Args:
        graph_id (int): The identifier of the graph to represent.

    Returns:
        Response:
            - AdjacencyListResponse: dict where keys are node names, values are lists of neighbor's names.
            - ErrorResponse: error object if graph not found.
            - HTTPValidationError: validation error if parameter is invalid.
    """
    response = graph_as_reverse_adj(graph_id)
    return response


@app.delete(
    "/api/graph/{graph_id}/node/{node_name}",
    status_code=204,
    response_model=None,
    operation_id="delete_node_api_graph__graph_id__node__node_name__delete",
    responses={404: {"model": ErrorResponse}, 422: {"model": HTTPValidationError}},
)
def delete_node(graph_id: int, node_name: str) -> (None|ErrorResponse|HTTPValidationError):
    """
    Delete a node from the graph by its name.

    Args:
        graph_id (int): The identifier of the graph.
        node_name (str): The name of the node to delete.

    Returns:
        Response:
            - None: if the node is successfully deleted.
            - ErrorResponse: error object if the node or graph is not found.
            - HTTPValidationError: validation error if parameters are invalid.
    """
    if response := delete_node_by_name(graph_id, node_name):
        return response
    return None
