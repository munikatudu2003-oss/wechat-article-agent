from __future__ import annotations

from typing import Any

from models.article import DraftDocument, ReviewDecision
from services.wechat_publisher_service import WechatPublisherService
from utils.time_utils import now_iso


class PublisherAgent:
    def __init__(self, wechat_publisher_service: WechatPublisherService | None = None):
        self._wechat_publisher_service = wechat_publisher_service or WechatPublisherService()

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

    def publish(
        self,
        draft: DraftDocument,
        review: ReviewDecision,
        *,
        html: str,
        confirm_publish: bool,
        source_url: str,
    ) -> dict[str, Any]:
        if not confirm_publish:
            return self.publish_dry_run(draft, review)

        if review.status != "approved":
            return {
                "mode": "blocked",
                "status": "review_blocked",
                "draft_id": "",
                "title": draft.title,
                "review_status": review.status,
                "cover": draft.cover_todo,
                "published_at": now_iso(),
                "note": "Real publish is blocked until the review status is approved.",
            }

        return self._wechat_publisher_service.publish_article(
            draft=draft,
            html=html,
            review=review,
            source_url=source_url,
        )
