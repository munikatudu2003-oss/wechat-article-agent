from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib import parse, request

from config import settings
from models.article import ArticleTask
from utils.time_utils import now_epoch_millis


class FeishuService:
    def __init__(self, source_mode: str | None = None):
        self._source_mode = (source_mode or settings.FEISHU_SOURCE_MODE).strip().lower()
        if self._source_mode not in {"mock", "real"}:
            raise ValueError("FEISHU_SOURCE_MODE must be either 'mock' or 'real'.")
        self._tenant_access_token: str | None = None
        self._field_name_cache: dict[str, str] | None = None

    @property
    def source_mode(self) -> str:
        return self._source_mode

    def get_record(self) -> ArticleTask:
        records = self.list_pending_records(limit=1)
        if not records:
            raise ValueError(f"No records available in FeishuService mode '{self._source_mode}'.")
        return records[0]

    def get_record_by_id(self, record_id: str) -> ArticleTask:
        if self._source_mode == "mock":
            record = self.get_mock_record()
            if record.record_id != record_id:
                raise ValueError(f"Mock Feishu record '{record_id}' was not found.")
            return record

        self._validate_real_mode_settings()
        tenant_access_token = self._get_tenant_access_token()
        record = self._fetch_bitable_record(tenant_access_token, record_id)
        fields = record.get("fields")
        if not isinstance(fields, dict):
            raise ValueError(f"Feishu record '{record_id}' does not contain valid fields.")
        return self._map_record_fields(record, fields)

    def list_pending_records(self, limit: int | None = None) -> list[ArticleTask]:
        if self._source_mode == "mock":
            records = [self.get_mock_record()]
        else:
            records = self.get_real_records(limit=limit or settings.FEISHU_MAX_RECORDS)

        if limit is not None:
            return records[:limit]
        return records

    def list_publish_queue_records(self, limit: int | None = None) -> list[ArticleTask]:
        max_records = limit or settings.FEISHU_MAX_RECORDS
        if self._source_mode == "mock":
            return [self.get_mock_record()][:max_records]
        records = self._list_filtered_records(
            limit=max_records,
            content_statuses={settings.FEISHU_STATUS_GENERATED},
        )
        queued: list[ArticleTask] = []
        for record in records:
            if not record.content_markdown.strip():
                continue
            if not self._can_queue_for_publish(record):
                continue
            queued.append(record)
            if len(queued) >= max_records:
                break
        return queued

    def list_status_sync_records(self, limit: int | None = None) -> list[ArticleTask]:
        max_records = limit or settings.FEISHU_MAX_RECORDS
        if self._source_mode == "mock":
            return []
        records = self._list_filtered_records(limit=max_records * 5)
        syncing: list[ArticleTask] = []
        for record in records:
            publish_id = record.publish_id.strip()
            if not publish_id or publish_id.startswith("mock-"):
                continue
            syncing.append(record)
            if len(syncing) >= max_records:
                break
        return syncing

    def get_mock_record(self) -> ArticleTask:
        return ArticleTask(
            record_id="mock-record-001",
            title="Turning a Feishu note into a WeChat article draft",
            summary="This mock draft shows the full offline pipeline from a local record through review, formatting, and a dry-run publish result.",
            column_type="Automation",
            keywords="wechat, feishu, mock",
            target_words=800,
            source_material="Local mock record for smoke testing.",
            content_markdown="",
            cover_prompt="TODO: add cover asset before real publish",
            cover_path="",
            source_url="mock://feishu/article-record/001",
            review_status="approved",
            content_status=settings.FEISHU_STATUS_GENERATED,
        )

    def get_real_records(self, limit: int) -> list[ArticleTask]:
        return self._list_filtered_records(
            limit=limit,
            content_statuses={settings.FEISHU_STATUS_PENDING} if settings.FEISHU_PENDING_ONLY else None,
        )

    def _list_filtered_records(
        self,
        *,
        limit: int,
        content_statuses: set[str] | None = None,
    ) -> list[ArticleTask]:
        if self._source_mode == "mock":
            records = [self.get_mock_record()]
            return records[:limit]

        self._validate_real_mode_settings()
        tenant_access_token = self._get_tenant_access_token()
        raw_records = self._fetch_bitable_records(tenant_access_token, limit=limit)
        tasks: list[ArticleTask] = []
        normalized_statuses = {status.strip() for status in (content_statuses or set()) if status.strip()}

        for record in raw_records:
            fields = record.get("fields")
            if not isinstance(fields, dict):
                continue
            title = self._coerce_to_text(
                self._get_field_value(fields, settings.FEISHU_FIELD_TITLE, aliases=("title", "Title"))
            )
            if not title:
                # Empty starter rows are common in fresh bitables; skip them.
                continue

            content_status = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_CONTENT_STATUS))
            if normalized_statuses and content_status not in normalized_statuses:
                continue

            tasks.append(self._map_record_fields(record, fields))
            if len(tasks) >= limit:
                break

        return tasks

    def _can_queue_for_publish(self, record: ArticleTask) -> bool:
        publish_id = record.publish_id.strip()
        draft_id = record.draft_id.strip()
        publish_status = record.publish_status.strip().lower()

        if publish_id and not publish_id.startswith("mock-"):
            return False

        if publish_status in {"publish_submitted", "publishing", "published"}:
            return False

        if draft_id and not draft_id.startswith("mock-") and publish_status == "draft_created":
            return True

        if not draft_id or draft_id.startswith("mock-"):
            return True

        return publish_status in {"", "draft_ready", "draft_created"}

    def update_record_status(
        self,
        record_id: str,
        *,
        content_status: str | None = None,
        review_status: str | None = None,
        draft_id: str | None = None,
        publish_status: str | None = None,
        publish_id: str | None = None,
        publish_url: str | None = None,
        summary: str | None = None,
        content_markdown: str | None = None,
        cover_prompt: str | None = None,
        cover_path: str | None = None,
        last_error: str | None = None,
    ) -> dict[str, Any]:
        fields: dict[str, Any] = {}

        if content_status is not None:
            fields[settings.FEISHU_FIELD_CONTENT_STATUS] = content_status
        if review_status is not None:
            fields[settings.FEISHU_FIELD_REVIEW_STATUS] = review_status
        if draft_id is not None:
            fields[settings.FEISHU_FIELD_DRAFT_ID] = draft_id
        if publish_status is not None:
            fields[settings.FEISHU_FIELD_PUBLISH_STATUS] = publish_status
        if publish_id is not None:
            fields[settings.FEISHU_FIELD_PUBLISH_ID] = publish_id
        if publish_url is not None:
            fields[settings.FEISHU_FIELD_PUBLISH_URL] = publish_url
        if summary is not None:
            fields[settings.FEISHU_FIELD_SUMMARY] = summary
        if content_markdown is not None:
            fields[settings.FEISHU_FIELD_CONTENT_MARKDOWN] = content_markdown
        if cover_prompt is not None:
            fields[settings.FEISHU_FIELD_COVER_PROMPT] = cover_prompt
        if cover_path is not None:
            fields[settings.FEISHU_FIELD_COVER_PATH] = cover_path
        if last_error is not None:
            fields[settings.FEISHU_FIELD_LAST_ERROR] = last_error

        fields[settings.FEISHU_FIELD_PROCESSED_AT] = now_epoch_millis()

        if self._source_mode == "mock":
            return {"mode": "mock", "record_id": record_id, "fields": fields}

        self._validate_real_mode_settings()
        tenant_access_token = self._get_tenant_access_token()
        resolved_fields = self._resolve_update_fields(tenant_access_token, record_id, fields)
        return self._update_bitable_record(tenant_access_token, record_id, resolved_fields)

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
        if self._tenant_access_token:
            return self._tenant_access_token

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
        self._tenant_access_token = token
        return token

    def _fetch_bitable_records(self, tenant_access_token: str, limit: int) -> list[dict[str, Any]]:
        page_size = max(settings.FEISHU_PAGE_SIZE, min(max(limit * 20, 20), 100))
        query: dict[str, str] = {"page_size": str(page_size)}
        if settings.FEISHU_VIEW_ID:
            query["view_id"] = settings.FEISHU_VIEW_ID

        records: list[dict[str, Any]] = []
        page_token = ""

        while True:
            current_query = dict(query)
            if page_token:
                current_query["page_token"] = page_token

            data = self._request_json(
                method="GET",
                path=f"/bitable/v1/apps/{settings.FEISHU_APP_TOKEN}/tables/{settings.FEISHU_TABLE_ID}/records",
                headers={"Authorization": f"Bearer {tenant_access_token}"},
                query=current_query,
            )

            items = data.get("items")
            if not isinstance(items, list):
                raise ValueError("Feishu bitable returned an invalid records list.")

            records.extend(item for item in items if isinstance(item, dict))
            if len(records) >= page_size and not data.get("has_more"):
                break
            if not data.get("has_more"):
                break

            page_token = self._coerce_to_text(data.get("page_token"))
            if not page_token:
                break

        if not records:
            raise ValueError("Feishu bitable returned no records.")

        return records

    def _update_bitable_record(self, tenant_access_token: str, record_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        return self._request_json(
            method="PUT",
            path=f"/bitable/v1/apps/{settings.FEISHU_APP_TOKEN}/tables/{settings.FEISHU_TABLE_ID}/records/{record_id}",
            headers={
                "Authorization": f"Bearer {tenant_access_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            payload={"fields": fields},
        )

    def _fetch_bitable_record(self, tenant_access_token: str, record_id: str) -> dict[str, Any]:
        data = self._request_json(
            method="GET",
            path=f"/bitable/v1/apps/{settings.FEISHU_APP_TOKEN}/tables/{settings.FEISHU_TABLE_ID}/records/{record_id}",
            headers={"Authorization": f"Bearer {tenant_access_token}"},
        )
        record = data.get("record")
        if not isinstance(record, dict):
            raise ValueError("Feishu bitable did not return a valid record object.")
        return record

    def _resolve_update_fields(
        self,
        tenant_access_token: str,
        record_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        if self._field_name_cache is None:
            record = self._fetch_bitable_record(tenant_access_token, record_id)
            record_fields = record.get("fields")
            if not isinstance(record_fields, dict):
                raise ValueError("Feishu record fields are missing while resolving field names.")
            self._field_name_cache = {
                key: self._find_field_key(record_fields, key) or key
                for key in fields.keys()
            }

        resolved: dict[str, Any] = {}
        for key, value in fields.items():
            resolved_key = (self._field_name_cache or {}).get(key) or key
            resolved[resolved_key] = value
        return resolved

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
        try:
            with request.urlopen(req, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as error:
            raw = error.read().decode("utf-8", errors="replace")
            try:
                parsed_error = json.loads(raw)
            except json.JSONDecodeError:
                raise ValueError(f"Feishu API HTTP {error.code}: {raw}") from error

            if isinstance(parsed_error, dict):
                code = parsed_error.get("code", error.code)
                msg = parsed_error.get("msg") or parsed_error.get("message") or raw
                raise ValueError(f"Feishu API error {code}: {msg}") from error

            raise ValueError(f"Feishu API HTTP {error.code}: {raw}") from error

        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Feishu API returned a non-object JSON response.")

        code = parsed.get("code", 0)
        if code not in (0, "0", None):
            msg = parsed.get("msg") or parsed.get("message") or "Unknown Feishu API error."
            raise ValueError(f"Feishu API error {code}: {msg}")

        data = parsed.get("data")
        if not isinstance(data, dict):
            # Some Feishu endpoints, including tenant_access_token, return useful
            # fields at the top level instead of nesting them under data.
            top_level = {
                key: value
                for key, value in parsed.items()
                if key not in {"code", "msg", "message"}
            }
            if top_level:
                return top_level
            raise ValueError("Feishu API response did not include a valid data object.")
        return data

    def _map_record_fields(self, record: dict[str, Any], fields: dict[str, Any]) -> ArticleTask:
        title = self._coerce_to_text(
            self._get_field_value(fields, settings.FEISHU_FIELD_TITLE, aliases=("title", "Title"))
        )
        if not title:
            raise ValueError("Could not map a title field from the Feishu record.")

        summary = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_SUMMARY))
        category = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_CATEGORY))
        keywords = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_KEYWORDS))
        reference = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_REFERENCE))
        source_url = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_SOURCE_URL))
        word_count = self._coerce_to_int(self._get_field_value(fields, settings.FEISHU_FIELD_WORD_COUNT))
        content_markdown = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_CONTENT_MARKDOWN))
        cover_prompt = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_COVER_PROMPT))
        cover_path = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_COVER_PATH))
        content_status = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_CONTENT_STATUS))
        review_status = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_REVIEW_STATUS))
        draft_id = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_DRAFT_ID))
        publish_status = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_PUBLISH_STATUS))
        publish_id = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_PUBLISH_ID))
        publish_url = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_PUBLISH_URL))
        last_error = self._coerce_to_text(self._get_field_value(fields, settings.FEISHU_FIELD_LAST_ERROR))

        if not summary:
            summary = "Imported from a live Feishu record. Review the mapped fields before using this draft for real publishing."

        record_id = self._coerce_to_text(record.get("record_id")) or "feishu-record"
        return ArticleTask(
            record_id=record_id,
            title=title,
            summary=summary,
            column_type=category,
            keywords=keywords,
            target_words=word_count,
            source_material=reference,
            content_markdown=content_markdown,
            cover_prompt=cover_prompt,
            cover_path=cover_path,
            source_url=source_url or f"feishu://bitable/{record_id}",
            content_status=content_status,
            review_status=review_status,
            draft_id=draft_id,
            publish_status=publish_status,
            publish_id=publish_id,
            publish_url=publish_url,
            last_error=last_error,
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
            for key in ("text", "name", "value", "link", "url", "email"):
                text = self._coerce_to_text(value.get(key))
                if text:
                    return text
            if isinstance(value.get("text"), dict):
                nested = self._coerce_to_text(value.get("text"))
                if nested:
                    return nested
            return json.dumps(value, ensure_ascii=False)
        return str(value).strip()

    def _coerce_to_int(self, value: Any) -> int | None:
        text = self._coerce_to_text(value)
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError:
            return None

    def _get_field_value(self, fields: dict[str, Any], configured_name: str, aliases: tuple[str, ...] = ()) -> Any:
        matched_key = self._find_field_key(fields, configured_name, aliases=aliases)
        if matched_key is not None:
            return fields[matched_key]
        return None

    def _find_field_key(self, fields: dict[str, Any], configured_name: str, aliases: tuple[str, ...] = ()) -> str | None:
        candidates = [configured_name, *aliases]
        for candidate in candidates:
            if candidate and candidate in fields:
                return candidate

        lowered = {str(key).strip().lower(): key for key in fields.keys()}
        for candidate in candidates:
            if not candidate:
                continue
            matched_key = lowered.get(candidate.strip().lower())
            if matched_key is not None:
                return matched_key

        for candidate in candidates:
            token = candidate.strip()
            if not token:
                continue
            for key in fields.keys():
                key_text = str(key).strip()
                if key_text.endswith(token):
                    return str(key)

        return None
