from __future__ import annotations

from typing import Any

from models.article import DraftDocument, ReviewDecision
from utils.time_utils import now_iso


class PublisherAgent:
    def publish_dry_run(self, draft: DraftDocument, review: ReviewDecision) -> dict[str, Any]:
        return {
            "mode": "dry_run",
            "status": "draft_created",
            "draft_id": "mock-draft-001",
            "title": draft.title,
            "review_status": review.status,
            "cover": draft.cover_todo,
            "published_at": now_iso(),
        }
