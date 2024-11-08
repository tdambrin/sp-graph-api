from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tasks import TaskManager, StatusManager
from commons import str_to_values

api_v2 = FastAPI()

origins = [
    # "http://localhost",
    "*",
]

api_v2.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_v2.post("/api/tasks/{task_id}/status")
def get_task_status(task_id: str):
    return StatusManager().get_status_and_result(task_id=task_id)


@api_v2.post("/api/expand/{node_id}/{selected_types}")
def start_expand(node_id: str, selected_types: str):
    ctrl = TaskManager(selected_types=str_to_values(selected_types, sep="+"))
    task_id = ctrl.start_expand_task(node_id=node_id)
    return task_id


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api_v2, host="127.0.0.1", port=8502, log_level="info")

    # Thread version
    import threading

    threading.Thread(
        target=uvicorn.run,
        kwargs={
            "app": api_v2,
            "host": "127.0.0.1",
            "port": 8502,
            "log_level": "info",

        },
    ).start()