import uuid
from enum import Enum
from functools import reduce
from operator import add
from typing import Annotated, List, Optional

import commons
import config
import constants
from api_clients.wrappers import SpotifyWrapper
from commons import str_to_values
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from items import ItemStore
from status import StatusManager
from tasks import TaskManager


class Tags(Enum):
    SESSION = "Session"
    CACHE = "Cache"
    ITEMS = "Items"
    TASKS = "Tasks"
    INTERACTIONS = "Interactions"
    TECHNICAL = "Technical"


spg_api = FastAPI(
    title="Spotify Graph API",
    default_response_class=JSONResponse,
)

origins = [
    "http://localhost:8080",
    "http://192.168.1.155:8080",
    "http://localhost:8502",
    "https://tdambrin.github.io/",
    # "*",
]

spg_api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
    ],
    allow_headers=["*"],
)


# --- Sessions ---


@spg_api.get("/api/sessions/create", tags=[Tags.SESSION])
def get_session_params():
    return {"session_id": str(uuid.uuid4())}


@spg_api.get("/api/sessions/restore", tags=[Tags.SESSION])
def get_session_params(
    session_id: Annotated[str, Header()],
):
    graphs = ItemStore().get_graphs(session_id=session_id)
    if not graphs:
        return {}
    return {
        "graph_keys": list(graphs.keys()),
        "nodes": reduce(
            add,
            [
                commons.nodes_edges_to_list_of_dict(
                    graph_, which=constants.NODES
                )
                for graph_ in graphs.values()
            ],
        ),
        "edges": reduce(
            add,
            [
                commons.nodes_edges_to_list_of_dict(
                    graph_, which=constants.EDGES, system_=constants.VIS_JS_SYS
                )
                for graph_ in graphs.values()
            ],
        ),
    }


# --- Graph Interactions ---


@spg_api.get("/api/search/{keywords}", tags=[Tags.INTERACTIONS])
def search(
    keywords: str,
    selected_types: str,
    session_id: Annotated[str, Header()],
):
    # Parse params
    keywords_: List[str] = commons.str_to_values(keywords, sep="+")
    selected_types_: List[str] = commons.str_to_values(selected_types, sep="+")

    # Start search
    ctrl = TaskManager(session_id=session_id, selected_types=selected_types_)
    return ctrl.search_task(keywords=keywords_, save=False)


@spg_api.get("/api/expand/{graph_key}/{node_id}", tags=[Tags.INTERACTIONS])
def start_expand(
    graph_key: str,
    node_id: str,
    selected_types: str,
    session_id: Annotated[str, Header()],
    item_type: Optional[str] = None,
):
    ctrl = TaskManager(
        session_id=session_id,
        graph_key=graph_key,
        selected_types=str_to_values(selected_types, sep="+"),
    )
    task_id = ctrl.start_expand_task(
        node_id=node_id, item_type=item_type, save=False
    )
    return {"task_id": task_id}


@spg_api.get("/api/tasks/{task_id}/status", tags=[Tags.TASKS])
def get_task_status(task_id: str):
    return StatusManager().get_status_and_result(task_id=task_id)


@spg_api.get("/api/tasks", tags=[Tags.TASKS])
def get_all_tasks():
    return StatusManager().all_tasks


@spg_api.get("/api/cache/items", tags=[Tags.CACHE])
def get_cached_items():
    return {"items": ItemStore().get_all_items()}


@spg_api.get("/api/cache/items/{item_id}", tags=[Tags.CACHE])
def get_cached_item(item_id: str):
    return {"item": ItemStore().get(item_id)}


@spg_api.get("/api/items/{item_id}/successors", tags=[Tags.ITEMS])
def get_item_successors(
    item_id: str,
    graph_key: str,
    session_id: Annotated[str, Header()],
    recursive: bool = True,
):
    return ItemStore().get_successors(
        session_id=session_id,
        graph_key=graph_key,
        node_id=item_id,
        recursive=recursive,
    )


@spg_api.get("/api/items/{item_id}/predecessors", tags=[Tags.ITEMS])
def get_item_successors(
    item_id: str,
    graph_key: str,
    session_id: Annotated[str, Header()],
    recursive: bool = True,
):
    return ItemStore().get_predecessors(
        session_id=session_id,
        graph_key=graph_key,
        node_id=item_id,
        recursive=recursive,
    )


@spg_api.get("/api/items/{item_id}", tags=[Tags.ITEMS])
def get_item_from_spotify(item_id: str, item_type: str):
    return {
        "item": SpotifyWrapper().find(item_id=item_id, item_type=item_type)
    }


@spg_api.get("/docs", include_in_schema=False, tags=[Tags.TECHNICAL])
async def get_documentation():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@spg_api.get("/health", include_in_schema=False, tags=[Tags.TECHNICAL])
async def health():
    return {"state": "up"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(spg_api, host="127.0.0.1", port=8502, log_level="info")

    # Thread version - not reached
    import threading

    threading.Thread(
        target=uvicorn.run,
        kwargs={
            "app": spg_api,
            "host": config.API_HOST,
            "port": config.API_PORT,
            "log_level": "info",
        },
    ).start()
