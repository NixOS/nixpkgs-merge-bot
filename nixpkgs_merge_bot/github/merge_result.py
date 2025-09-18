from dataclasses import dataclass
from typing import override

from .http_response import HttpResponse


@dataclass(frozen=True)
class MergeResult:
    response: HttpResponse

    def summary_md(self) -> str:
        raise NotImplementedError


class DirectMergeResult(MergeResult):
    @override
    def summary_md(self) -> str:
        return "Merge completed"

    @override
    def __str__(self) -> str:
        return "Merge"


class AutoMergeResult(MergeResult):
    @override
    def summary_md(self) -> str:
        return "Enabled Auto Merge"

    @override
    def __str__(self) -> str:
        return "AutoMerge"


class QueuedMergeResult(MergeResult):
    def queue_url(self) -> str:
        json = self.response.json()
        data = json["data"]
        merge_queue_entry = data["enqueuePullRequest"]["mergeQueueEntry"]
        return merge_queue_entry["mergeQueue"]["url"]

    @override
    def summary_md(self) -> str:
        return f"[Queued]({self.queue_url()}) for merge"

    @override
    def __str__(self) -> str:
        return "Enqueue"
