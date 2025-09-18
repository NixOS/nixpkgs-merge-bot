from dataclasses import dataclass
from typing import Any, override

from .http_response import HttpResponse


@dataclass(frozen=True)
class MergeResult:
    response: HttpResponse

    def summary_md(self) -> str:
        raise NotImplementedError


class DirectMergeResult(MergeResult):
    @override
    def __str__(self) -> str:
        return "Merge"

    @override
    def summary_md(self) -> str:
        return "Merge completed"


class AutoMergeResult(MergeResult):
    @override
    def __str__(self) -> str:
        return "AutoMerge"

    @override
    def summary_md(self) -> str:
        return "Enabled Auto Merge"


class QueuedMergeResult(MergeResult):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        json = self.response.json()
        self.queue_url = json["data"]["mergeQueueEntry"]["mergeQueue"]["url"]

    @override
    def __str__(self) -> str:
        return "Enqueue"

    @override
    def summary_md(self) -> str:
        return f"[Queued]({self.queue_url}) for merge"
