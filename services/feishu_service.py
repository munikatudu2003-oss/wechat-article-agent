from __future__ import annotations

import json
from typing import Any
from urllib import parse, request

from config import settings
from models.article import MockFeishuRecord


class FeishuService:
    def __init__(self, source_mode: str | None = None):
        self._source_mode = (source_mode or settings.FEISHU_SOURCE_MODE).strip().lower()
        if self._source_mode not in {"mock", "real"}:
            raise ValueError("FEISHU_SOURCE_MODE must be either 'mock' or 'real'.")

    @property
    def source_mode(self) -> str:
        return self._source_mode

    def get_record(self) -> MockFeishuRecord:
        if self._source_mode == "mock":
            return self.get_mock_record()
        return self.get_real_record()

    def get_mock_record(self) -> MockFeishuRecord:
        return MockFeishuRecord(
            record_id="mock-record-001",
            title="Turning a Feishu note into a WeChat article draft",
            summary="This mock draft shows the full offline pipeline from a local record through review, formatting, and a dry-run publish result.",
            bullet_points=[
                "WriterAgent asks the local LLMService skeleton for a first draft.",
                "ReviewAgent marks the draft as approved unless it is too short.",
                "FormatterAgent converts markdown into a readable HTML article.",
                "PublisherAgent returns a dry-run payload instead of calling a real API.",
            ],
            source_url="mock://feishu/article-record/001",
        )

    def get_real_record(self) -> MockFeishuRecord:
        self._validate_real_mode_settings()

        tenant_access_token = self._get_tenant_access_token()
        record = self._fetch_first_bitable_record(tenant_access_token)
        fields = record.get("fields")
        if not isinstance(fields, dict):
            raise ValueError("Feishu record payload is missing a valid 'fields' object.")

        return self._map_record_fields(record, fields)

    def _validate_real_mode_settings(self) -> None:
        required = {
            "FEISHU_APP_ID": settings.FEISHU_APP_ID,
            "FEISHU_APP_SECRET": settings.FEISHU_APP_SECRET,
            "FEISHU_APP_TOKEN": settings.FEISHU_APP_TOKEN,
            "FEISHU_TABLE_ID": settings.FEISHU_TABLE_ID,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(f"Real Feishu mode requires these environment variables: {missing_text}")

    def _get_tenant_access_token(self) -> str:
        payload = {
            "app_id": settings.FEISHU_APP_ID,
            "app_secret": settings.FEISHU_APP_SECRET,
        }
        data = self._request_json(
            method="POST",
            path="/auth/v3/tenant_access_token/internal",
            headers={"Content-Type": "application/json; charset=utf-8"},
            payload=payload,
        )

        token = data.get("tenant_access_token")
        if not isinstance(token, str) or not token.strip():
            raise ValueError("Feishu auth response did not include tenant_access_token.")
        return token

    def _fetch_first_bitable_record(self, tenant_access_token: str) -> dict[str, Any]:
        query: dict[str, str] = {"page_size": str(settings.FEISHU_PAGE_SIZE)}
        if settings.FEISHU_VIEW_ID:
            query["view_id"] = settings.FEISHU_VIEW_ID

        data = self._request_json(
            method="GET",
            path=f"/bitable/v1/apps/{settings.FEISHU_APP_TOKEN}/tables/{settings.FEISHU_TABLE_ID}/records",
            headers={"Authorization": f"Bearer {tenant_access_token}"},
            query=query,
        )

        items = data.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError("Feishu bitable returned no records.")

        first = items[0]
        if not isinstance(first, dict):
            raise ValueError("Feishu bitable returned an invalid record payload.")
        return first

    def _request_json(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = f"{settings.FEISHU_BASE_URL}{path}"
        if query:
            url = f"{url}?{parse.urlencode(query)}"

        body = None
        request_headers = dict(headers or {})
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        req = request.Request(url=url, data=body, headers=request_headers, method=method)
        with request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")

        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Feishu API returned a non-object JSON response.")

        code = parsed.get("code", 0)
        if code not in (0, "0", None):
            msg = parsed.get("msg") or parsed.get("message") or "Unknown Feishu API error."
            raise ValueError(f"Feishu API error {code}: {msg}")

        data = parsed.get("data")
        if not isinstance(data, dict):
            raise ValueError("Feishu API response did not include a valid data object.")
        return data

    def _map_record_fields(self, record: dict[str, Any], fields: dict[str, Any]) -> MockFeishuRecord:
        title = self._coerce_to_text(fields.get(settings.FEISHU_FIELD_TITLE))
        if not title:
            title = self._coerce_to_text(fields.get("title"))
        if not title:
            raise ValueError("Could not map a title field from the Feishu record.")

        summary = self._coerce_to_text(fields.get(settings.FEISHU_FIELD_SUMMARY))
        category = self._coerce_to_text(fields.get(settings.FEISHU_FIELD_CATEGORY))
        keywords = self._coerce_to_text(fields.get(settings.FEISHU_FIELD_KEYWORDS))
        reference = self._coerce_to_text(fields.get(settings.FEISHU_FIELD_REFERENCE))
        word_count = self._coerce_to_text(fields.get(settings.FEISHU_FIELD_WORD_COUNT))

        bullet_points = [
            point
            for point in [
                f"Category: {category}" if category else "",
                f"Keywords: {keywords}" if keywords else "",
                f"Reference: {reference}" if reference else "",
                f"Target word count: {word_count}" if word_count else "",
            ]
            if point
        ]

        if not summary:
            summary = "Imported from a live Feishu record. Review the mapped fields before using this draft for real publishing."

        if not bullet_points:
            bullet_points = ["Imported from Feishu in real mode. Add richer field mapping once the upstream schema is stable."]

        record_id = self._coerce_to_text(record.get("record_id")) or "feishu-record"
        return MockFeishuRecord(
            record_id=record_id,
            title=title,
            summary=summary,
            bullet_points=bullet_points,
            source_url=f"feishu://bitable/{record_id}",
        )

    def _coerce_to_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float, bool)):
            return str(value).strip()
        if isinstance(value, list):
            parts = [self._coerce_to_text(item) for item in value]
            return ", ".join(part for part in parts if part)
        if isinstance(value, dict):
            for key in ("text", "name", "value"):
                text = self._coerce_to_text(value.get(key))
                if text:
                    return text
            return json.dumps(value, ensure_ascii=False)
        return str(value).strip()
