from __future__ import annotations

import json
from typing import Any
from urllib import parse, request

from config import settings
from models.article import DraftDocument, ReviewDecision
from utils.time_utils import now_iso


class WechatPublisherService:
    def __init__(self) -> None:
        self._access_token = settings.WECHAT_ACCESS_TOKEN or None

    def publish_article(
        self,
        *,
        draft: DraftDocument,
        html: str,
        review: ReviewDecision,
        source_url: str,
    ) -> dict[str, Any]:
        if settings.WECHAT_PUBLISH_MODE != "real":
            return {
                "mode": "dry_run",
                "status": "publish_skipped",
                "draft_id": "mock-draft-001",
                "title": draft.title,
                "review_status": review.status,
                "cover": draft.cover_todo,
                "published_at": now_iso(),
                "note": "WECHAT_PUBLISH_MODE is not set to real.",
            }

        token = self._get_access_token()
        media_id = self._add_draft(token, draft, html, source_url)

        result = {
            "mode": "real",
            "status": "draft_created",
            "draft_id": media_id,
            "title": draft.title,
            "review_status": review.status,
            "cover": draft.cover_todo,
            "published_at": now_iso(),
        }

        if settings.WECHAT_AUTO_SUBMIT_PUBLISH:
            publish_response = self._submit_publish(token, media_id)
            result["status"] = "publish_submitted"
            result["publish_id"] = str(publish_response.get("publish_id", ""))

        return result

    def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
            raise ValueError("Real WeChat publishing requires WECHAT_ACCESS_TOKEN or WECHAT_APP_ID and WECHAT_APP_SECRET.")

        query = parse.urlencode(
            {
                "grant_type": "client_credential",
                "appid": settings.WECHAT_APP_ID,
                "secret": settings.WECHAT_APP_SECRET,
            }
        )
        data = self._request_json(method="GET", url=f"{settings.WECHAT_API_BASE_URL}/cgi-bin/token?{query}")

        token = data.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise ValueError("WeChat token response did not include access_token.")
        self._access_token = token
        return token

    def _add_draft(self, access_token: str, draft: DraftDocument, html: str, source_url: str) -> str:
        if not settings.WECHAT_THUMB_MEDIA_ID:
            raise ValueError("Real WeChat publishing requires WECHAT_THUMB_MEDIA_ID.")

        payload = {
            "articles": [
                {
                    "title": draft.title,
                    "author": settings.WECHAT_AUTHOR,
                    "digest": draft.summary,
                    "content": html,
                    "content_source_url": source_url or settings.WECHAT_CONTENT_SOURCE_URL,
                    "thumb_media_id": settings.WECHAT_THUMB_MEDIA_ID,
                    "need_open_comment": settings.WECHAT_NEED_OPEN_COMMENT,
                    "only_fans_can_comment": settings.WECHAT_ONLY_FANS_CAN_COMMENT,
                }
            ]
        }

        data = self._request_json(
            method="POST",
            url=f"{settings.WECHAT_API_BASE_URL}/cgi-bin/draft/add?access_token={parse.quote(access_token)}",
            payload=payload,
        )
        media_id = data.get("media_id")
        if not isinstance(media_id, str) or not media_id.strip():
            raise ValueError("WeChat draft add response did not include media_id.")
        return media_id

    def _submit_publish(self, access_token: str, media_id: str) -> dict[str, Any]:
        return self._request_json(
            method="POST",
            url=f"{settings.WECHAT_API_BASE_URL}/cgi-bin/freepublish/submit?access_token={parse.quote(access_token)}",
            payload={"media_id": media_id},
        )

    def _request_json(
        self,
        *,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = None
        headers: dict[str, str] = {}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        req = request.Request(url=url, data=body, headers=headers, method=method)
        with request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")

        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("WeChat API returned a non-object JSON response.")

        errcode = parsed.get("errcode", 0)
        if errcode not in (0, None):
            errmsg = parsed.get("errmsg") or "Unknown WeChat API error."
            raise ValueError(f"WeChat API error {errcode}: {errmsg}")

        return parsed
