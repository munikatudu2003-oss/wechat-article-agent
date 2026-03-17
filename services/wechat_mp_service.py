from __future__ import annotations

import json
from typing import Any
from urllib import parse, request

from config import settings
from models.article import DraftDocument, ReviewDecision
from utils.time_utils import now_iso


class WechatMPService:
    def __init__(self) -> None:
        self._access_token = settings.WECHAT_ACCESS_TOKEN or None

    def validate_real_draft_requirements(self) -> None:
        missing: list[str] = []
        if not settings.WECHAT_ACCESS_TOKEN:
            if not settings.WECHAT_APP_ID:
                missing.append("WECHAT_APP_ID")
            if not settings.WECHAT_APP_SECRET:
                missing.append("WECHAT_APP_SECRET")
        if not settings.WECHAT_THUMB_MEDIA_ID:
            missing.append("WECHAT_THUMB_MEDIA_ID")

        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(
                "Real WeChat draft/add requires these environment variables: "
                f"{missing_text}. "
                "You can provide WECHAT_ACCESS_TOKEN directly, or WECHAT_APP_ID + WECHAT_APP_SECRET."
            )

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
                "publish_id": "",
                "publish_url": "",
                "title": draft.title,
                "review_status": review.status,
                "cover": draft.cover_todo,
                "published_at": now_iso(),
                "note": "WECHAT_PUBLISH_MODE is not set to real.",
            }

        token = self._get_access_token()
        media_id = self.create_draft(
            draft=draft,
            html=html,
            source_url=source_url,
            access_token=token,
        )

        result: dict[str, Any] = {
            "mode": "real",
            "status": "draft_created",
            "content_status": settings.FEISHU_STATUS_GENERATED,
            "draft_id": media_id,
            "publish_id": "",
            "publish_url": "",
            "title": draft.title,
            "review_status": review.status,
            "cover": draft.cover_todo,
            "published_at": now_iso(),
        }

        if settings.WECHAT_AUTO_SUBMIT_PUBLISH:
            publish_response = self.submit_publish(media_id, access_token=token)
            result["status"] = "publish_submitted"
            result["content_status"] = settings.FEISHU_STATUS_PUBLISHING
            result["publish_id"] = str(publish_response.get("publish_id", ""))
            # TODO: Free publish APIs are async; if needed, call get API later to resolve a final article URL.

        return result

    def create_draft(
        self,
        *,
        draft: DraftDocument,
        html: str,
        source_url: str,
        access_token: str | None = None,
    ) -> str:
        self.validate_real_draft_requirements()
        token = access_token or self._get_access_token()
        return self._add_draft(token, draft, html, source_url)

    def submit_publish(self, media_id: str, *, access_token: str | None = None) -> dict[str, Any]:
        token = access_token or self._get_access_token()
        return self._submit_publish(token, media_id)

    def get_publish_status(self, publish_id: str, *, access_token: str | None = None) -> dict[str, Any]:
        token = access_token or self._get_access_token()
        return self._request_json(
            method="POST",
            url=f"{settings.WECHAT_API_BASE_URL}/cgi-bin/freepublish/get?access_token={parse.quote(token)}",
            payload={"publish_id": publish_id},
        )

    def get_published_article(self, article_id: str, *, access_token: str | None = None) -> dict[str, Any]:
        token = access_token or self._get_access_token()
        return self._request_json(
            method="POST",
            url=f"{settings.WECHAT_API_BASE_URL}/cgi-bin/freepublish/getarticle?access_token={parse.quote(token)}",
            payload={"article_id": article_id},
        )

    def batch_get_publications(
        self,
        *,
        offset: int = 0,
        count: int = 20,
        no_content: int = 1,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        token = access_token or self._get_access_token()
        return self._request_json(
            method="POST",
            url=f"{settings.WECHAT_API_BASE_URL}/cgi-bin/freepublish/batchget?access_token={parse.quote(token)}",
            payload={
                "offset": max(0, offset),
                "count": min(max(1, count), 20),
                "no_content": 1 if no_content else 0,
            },
        )

    def normalize_publish_status(self, response: dict[str, Any]) -> dict[str, Any]:
        code = self._coerce_int(response.get("publish_status"))
        article_id = self._coerce_text(response.get("article_id"))
        publish_id = self._coerce_text(response.get("publish_id"))
        fail_idx = response.get("fail_idx")
        article_detail = response.get("article_detail")
        publish_url = self._extract_article_url(article_detail)

        status_map = {
            0: "published",
            1: "publishing",
            2: "publish_failed_original",
            3: "publish_failed_normal",
            4: "publish_rejected_platform",
            5: "published_deleted",
            6: "published_system_blocked",
        }
        status = status_map.get(code, "unknown")
        last_error = ""
        if code in {2, 3, 4}:
            last_error = f"WeChat publish failed with status {code}"
            if isinstance(fail_idx, list) and fail_idx:
                last_error = f"{last_error}; fail_idx={','.join(str(item) for item in fail_idx)}"
        elif code in {5, 6}:
            last_error = f"WeChat publish ended with status {code}"

        return {
            "publish_id": publish_id,
            "publish_status_code": code,
            "publish_status": status,
            "content_status": self._map_content_status(code),
            "article_id": article_id,
            "publish_url": publish_url,
            "last_error": last_error,
        }

    def extract_article_url_from_payload(self, payload: dict[str, Any]) -> str:
        news_items = payload.get("news_item")
        if not isinstance(news_items, list):
            return ""
        for item in news_items:
            if not isinstance(item, dict):
                continue
            url = self._coerce_text(item.get("url"))
            if url:
                return url
        return ""

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

        source_link = self._normalize_source_url(source_url)

        payload = {
            "articles": [
                {
                    "title": draft.title,
                    "author": settings.WECHAT_AUTHOR,
                    "digest": draft.summary,
                    "content": html,
                    "content_source_url": source_link,
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

    def _extract_article_url(self, article_detail: Any) -> str:
        if not isinstance(article_detail, dict):
            return ""
        items = article_detail.get("item")
        if not isinstance(items, list):
            return ""
        for item in items:
            if not isinstance(item, dict):
                continue
            article_url = self._coerce_text(item.get("article_url"))
            if article_url:
                return article_url
        return ""

    def _coerce_text(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _coerce_int(self, value: Any) -> int | None:
        text = self._coerce_text(value)
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None

    def _map_content_status(self, publish_status_code: int | None) -> str:
        if publish_status_code == 0:
            return settings.FEISHU_STATUS_PUBLISHED
        if publish_status_code == 1:
            return settings.FEISHU_STATUS_PUBLISHING
        if publish_status_code in {2, 3, 4, 5, 6}:
            return settings.FEISHU_STATUS_PUBLISH_FAILED
        return settings.FEISHU_STATUS_PUBLISHING

    def _normalize_source_url(self, source_url: str) -> str:
        candidate = self._coerce_text(source_url)
        if candidate.startswith("http://") or candidate.startswith("https://"):
            return candidate

        fallback = self._coerce_text(settings.WECHAT_CONTENT_SOURCE_URL)
        if fallback.startswith("http://") or fallback.startswith("https://"):
            return fallback

        return ""
