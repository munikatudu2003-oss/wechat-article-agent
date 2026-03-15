from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MockFeishuRecord:
    record_id: str
    title: str
    summary: str
    bullet_points: list[str]
    source_url: str


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
