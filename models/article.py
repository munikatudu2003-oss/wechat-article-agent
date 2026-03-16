from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ArticleTask:
    record_id: str
    title: str
    summary: str
    column_type: str
    keywords: str
    target_words: int | None
    source_material: str
    content_markdown: str
    cover_prompt: str
    cover_path: str
    source_url: str
    content_status: str = ""
    review_status: str = ""
    draft_id: str = ""
    publish_status: str = ""
    publish_id: str = ""
    publish_url: str = ""
    last_error: str = ""


@dataclass
class DraftDocument:
    title: str
    summary: str
    markdown: str
    cover_todo: str


@dataclass
class ReviewDecision:
    status: str
    notes: list[str]
