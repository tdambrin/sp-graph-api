from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import commons
import config
from commons import str_to_values
from tasks import StatusManager, TaskManager

spg_api = FastAPI()

origins = [
    # "http://localhost",
    "*",
]

spg_api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@spg_api.get("/api/search/{keywords}/{selected_types}")
def search(keywords: str, selected_types: str):
    # Parse params
    keywords = commons.str_to_values(keywords, sep="+")
    selected_types = commons.str_to_values(selected_types, sep="+")

    # Start search
    ctrl = TaskManager(selected_types=selected_types)
    return ctrl.search_task(keywords=keywords, save=True)


@spg_api.get("/api/expand/{node_id}/{selected_types}")
def start_expand(node_id: str, selected_types: str):
    ctrl = TaskManager(selected_types=str_to_values(selected_types, sep="+"))
    task_id = ctrl.start_expand_task(node_id=node_id)
    return task_id


@spg_api.get("/api/tasks/{task_id}/status")
def get_task_status(task_id: str):
    return StatusManager().get_status_and_result(task_id=task_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(spg_api, host="127.0.0.1", port=8502, log_level="info")

    # Thread version
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
