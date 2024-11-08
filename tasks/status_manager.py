"""
Singleton to manage task status and results
"""
from typing import Any, Dict, Optional
from enum import Enum

from commons import ThreadSafeSingleton


class ValidStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    CREATED = "created"
    FAILED = "failed"
    COMPLETED = "completed"
    NOT_FOUND = "not_found"


class StatusManager(metaclass=ThreadSafeSingleton):

    def __init__(self):
        self.status: Dict[str, ValidStatus] = {}
        self.results = {}
        self.errors = {}

    def _set_status(self, task_id: str, status: ValidStatus, error: Exception = None) -> ValidStatus:
        self.status[task_id] = status
        if error is not None:
            self.errors[task_id] = error
        return self.status[task_id]

    def _set_result(self, task_id: str, result: Any):
        self.results[task_id] = result

    def create_task(self, task_id: str) -> ValidStatus:
        return self._set_status(task_id=task_id, status=ValidStatus.CREATED)

    def run_task(self, task_id: str) -> ValidStatus:
        return self._set_status(task_id=task_id, status=ValidStatus.RUNNING)

    def fail_task(self, task_id: str, error: Exception = None):
        self._set_status(task_id=task_id, status=ValidStatus.FAILED,  error=error)

    def complete_task(
        self,
        task_id: str,
        status: ValidStatus,
        result: Optional[Any] = None,
    ) -> ValidStatus:
        self._set_status(task_id=task_id, status=status)
        if result is not None:
            self._set_result(task_id=task_id, result=result)
        return self.status[task_id]

    def get_status(self, task_id: str) -> str:
        return self.status.get(task_id, ValidStatus.NOT_FOUND).value

    def get_status_and_result(self, task_id: str) -> Dict[str, Any]:
        """
        Return task status and result

        Args:
            task_id: uuid of the task

        Returns:
            dict with 'status', 'result' and 'error' keys
        """
        return {
            "status": self.status.get(task_id, ValidStatus.NOT_FOUND).value,
            "result": self.results.get(task_id),
            "error": self.errors.get(task_id)
        }
