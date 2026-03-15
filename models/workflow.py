from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkflowOptions:
    confirm_publish: bool = False
    limit: int = 1
    source_mode: str | None = None


@dataclass
class WorkflowRecordResult:
    record_id: str
    review_status: str
    publish_status: str
    draft_id: str
    output_html: Path
    output_markdown: Path
    source_mode: str


@dataclass
class WorkflowRunResult:
    success: bool
    processed_count: int
    failed_count: int
    source_mode: str
    confirm_publish: bool
    records: list[WorkflowRecordResult]
