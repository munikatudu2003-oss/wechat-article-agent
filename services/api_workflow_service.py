from __future__ import annotations

from dataclasses import asdict

from agents import FormatterAgent, ReviewAgent, WriterAgent
from config import settings
from config.settings import COVER_TODO_TEXT, DRAFTS_DIR
from models.article import DraftDocument, ReviewDecision
from services.feishu_service import FeishuService
from services.llm_service import LLMService
from services.markdown_service import MarkdownService
from services.output_service import OutputService
from services.wechat_mp_service import WechatMPService


class ApiWorkflowService:
    def __init__(self, source_mode: str | None = None) -> None:
        self._feishu = FeishuService(source_mode=source_mode)
        self._writer = WriterAgent(LLMService())
        self._reviewer = ReviewAgent()
        self._formatter = FormatterAgent(MarkdownService())
        self._wechat = WechatMPService()
        self._outputs = OutputService()

    @property
    def source_mode(self) -> str:
        return self._feishu.source_mode

    def _resolve_record(self, record_id: str | None, *, kind: str) -> object:
        if record_id:
            return self._feishu.get_record_by_id(record_id)
        if kind == "pending":
            records = self._feishu.list_pending_records(limit=1)
        elif kind == "publish_queue":
            records = self._feishu.list_publish_queue_records(limit=1)
        elif kind == "sync":
            records = self._feishu.list_status_sync_records(limit=1)
        else:
            raise ValueError(f"Unknown record selector: {kind}")
        if not records:
            raise ValueError("No records available for requested operation.")
        return records[0]

    def pick_record(self, *, kind: str, record_id: str | None = None) -> dict[str, object]:
        if record_id:
            record = self._feishu.get_record_by_id(record_id)
            return {
                "status": "ok",
                "stage": "record_selected",
                "record_id": record.record_id,
                "record": asdict(record),
            }

        if kind == "pending":
            records = self._feishu.list_pending_records(limit=1)
        elif kind == "publish_queue":
            records = self._feishu.list_publish_queue_records(limit=1)
        elif kind == "sync":
            records = self._feishu.list_status_sync_records(limit=1)
        else:
            raise ValueError(f"Unknown record selector: {kind}")

        if not records:
            return {
                "status": "ok",
                "stage": "none_available",
                "record_id": "",
                "record": None,
            }

        record = records[0]
        return {
            "status": "ok",
            "stage": "record_selected",
            "record_id": record.record_id,
            "record": asdict(record),
        }

    def _review_from_payload(self, status: str | None, notes: list[str] | None) -> ReviewDecision:
        normalized_status = (status or "approved").strip() or "approved"
        normalized_notes = [note.strip() for note in (notes or []) if note and note.strip()]
        if not normalized_notes:
            normalized_notes = ["External workflow supplied the review decision."]
        return ReviewDecision(status=normalized_status, notes=normalized_notes)

    def ingest_draft(
        self,
        *,
        record_id: str,
        title: str | None,
        summary: str,
        markdown: str,
        cover_prompt: str | None = None,
        review_status: str | None = None,
        review_notes: list[str] | None = None,
    ) -> dict[str, object]:
        record = self._feishu.get_record_by_id(record_id)
        draft = DraftDocument(
            title=(title or record.title).strip(),
            summary=summary.strip(),
            markdown=markdown.strip(),
            cover_todo=(cover_prompt or record.cover_prompt or COVER_TODO_TEXT).strip(),
        )
        review = self._review_from_payload(review_status, review_notes)
        html = self._formatter.to_html(draft, review)

        file_stem = "mock_output" if self._feishu.source_mode == "mock" else f"{record.record_id}_output"
        output_paths = self._outputs.save_outputs(
            DRAFTS_DIR,
            file_stem,
            draft,
            review,
            html,
            {
                "mode": "external_ingest",
                "status": "generated",
                "record_id": record.record_id,
                "review_status": review.status,
            },
        )
        output_payload = {key: str(path) for key, path in output_paths.items()}

        self._feishu.update_record_status(
            record.record_id,
            content_status=settings.FEISHU_STATUS_GENERATED,
            review_status=review.status,
            summary=draft.summary,
            content_markdown=draft.markdown,
            cover_prompt=draft.cover_todo,
            cover_path=record.cover_path,
            last_error="",
        )

        return {
            "status": "ok",
            "stage": "generated",
            "record_id": record.record_id,
            "review_status": review.status,
            "outputs": output_payload,
        }

    def generate_draft(self, record_id: str | None = None) -> dict[str, object]:
        record = self._resolve_record(record_id, kind="pending")

        draft = self._writer.write(record)
        review = self._reviewer.review(draft)
        html = self._formatter.to_html(draft, review)

        file_stem = "mock_output" if self._feishu.source_mode == "mock" else f"{record.record_id}_output"
        output_paths = self._outputs.save_outputs(DRAFTS_DIR, file_stem, draft, review, html, {})
        output_payload = {key: str(path) for key, path in output_paths.items()}

        self._feishu.update_record_status(
            record.record_id,
            content_status=settings.FEISHU_STATUS_GENERATED,
            review_status=review.status,
            summary=draft.summary,
            content_markdown=draft.markdown,
            cover_prompt=draft.cover_todo,
            cover_path=record.cover_path,
            last_error="",
        )

        return {
            "status": "ok",
            "stage": "generated",
            "record_id": record.record_id,
            "review_status": review.status,
            "outputs": output_payload,
        }

    def create_draft(self, record_id: str | None = None) -> dict[str, object]:
        record = self._resolve_record(record_id, kind="publish_queue")

        markdown = record.content_markdown.strip() or LLMService().generate_article(record)
        draft = DraftDocument(
            title=record.title,
            summary=record.summary,
            markdown=markdown,
            cover_todo=record.cover_prompt.strip() or COVER_TODO_TEXT,
        )

        review = (
            ReviewDecision(status=record.review_status, notes=["Using stored review status from Feishu."])
            if record.review_status
            else self._reviewer.review(draft)
        )

        if review.status != "approved":
            if self._feishu.source_mode == "real":
                self._feishu.update_record_status(
                    record.record_id,
                    content_status=settings.FEISHU_STATUS_FAILED,
                    publish_status="review_blocked",
                    last_error=f"Review status is {review.status}",
                )
            return {
                "status": "failed",
                "stage": "review_blocked",
                "record_id": record.record_id,
                "review_status": review.status,
            }

        if record.draft_id and not record.draft_id.startswith("mock-"):
            return {
                "status": "ok",
                "stage": "draft_exists",
                "record_id": record.record_id,
                "draft_id": record.draft_id,
            }

        html = self._formatter.to_html(draft, review)
        draft_id = (
            "mock-draft-001"
            if self._feishu.source_mode == "mock"
            else self._wechat.create_draft(draft=draft, html=html, source_url=record.source_url)
        )

        self._feishu.update_record_status(
            record.record_id,
            content_status=settings.FEISHU_STATUS_GENERATED,
            review_status=review.status,
            draft_id=draft_id,
            publish_status="draft_created",
            publish_id="",
            summary=draft.summary,
            content_markdown=draft.markdown,
            cover_prompt=draft.cover_todo,
            cover_path=record.cover_path,
            last_error="",
        )

        return {
            "status": "ok",
            "stage": "draft_created",
            "record_id": record.record_id,
            "draft_id": draft_id,
        }

    def submit_publish(self, record_id: str | None = None) -> dict[str, object]:
        record = self._resolve_record(record_id, kind="publish_queue")

        if self._feishu.source_mode == "mock":
            draft_id = record.draft_id or "mock-draft-001"
            publish_id = "mock-publish-001"
            self._feishu.update_record_status(
                record.record_id,
                content_status=settings.FEISHU_STATUS_PUBLISHING,
                draft_id=draft_id,
                publish_status="publish_submitted",
                publish_id=publish_id,
                publish_url="",
                last_error="",
            )
            return {
                "status": "ok",
                "stage": "publish_submitted",
                "record_id": record.record_id,
                "publish_id": publish_id,
            }

        if not record.draft_id or record.draft_id.startswith("mock-"):
            return {
                "status": "failed",
                "stage": "missing_draft_id",
                "record_id": record.record_id,
            }

        publish_response = self._wechat.submit_publish(record.draft_id)
        publish_id = str(publish_response.get("publish_id", ""))

        self._feishu.update_record_status(
            record.record_id,
            content_status=settings.FEISHU_STATUS_PUBLISHING,
            publish_status="publish_submitted",
            publish_id=publish_id,
            publish_url="",
            last_error="",
        )

        return {
            "status": "ok",
            "stage": "publish_submitted",
            "record_id": record.record_id,
            "publish_id": publish_id,
            "publish_response": publish_response,
        }

    def sync_status(self, record_id: str | None = None) -> dict[str, object]:
        record = self._resolve_record(record_id, kind="sync")

        if self._feishu.source_mode == "mock":
            publish_url = "https://mp.weixin.qq.com/s/mock-publish-url"
            self._feishu.update_record_status(
                record.record_id,
                content_status=settings.FEISHU_STATUS_PUBLISHED,
                publish_status="published",
                publish_id=record.publish_id or "mock-publish-001",
                publish_url=publish_url,
                last_error="",
            )
            return {
                "status": "ok",
                "stage": "published",
                "record_id": record.record_id,
                "publish_status": "published",
                "publish_status_code": 0,
                "publish_url": publish_url,
                "article_id": "mock-article-001",
            }

        if not record.publish_id:
            return {
                "status": "failed",
                "stage": "missing_publish_id",
                "record_id": record.record_id,
            }

        status_payload = self._wechat.get_publish_status(record.publish_id)
        normalized = self._wechat.normalize_publish_status(status_payload)

        publish_url = normalized["publish_url"]
        article_id = str(normalized.get("article_id", ""))
        if not publish_url and article_id:
            article_payload = self._wechat.get_published_article(article_id)
            publish_url = self._wechat.extract_article_url_from_payload(article_payload)

        self._feishu.update_record_status(
            record.record_id,
            content_status=str(normalized["content_status"]),
            publish_status=str(normalized["publish_status"]),
            publish_id=str(normalized["publish_id"]) or record.publish_id,
            publish_url=publish_url or record.publish_url,
            last_error=str(normalized["last_error"]),
        )

        return {
            "status": "ok",
            "stage": str(normalized["publish_status"]),
            "record_id": record.record_id,
            "publish_status": str(normalized["publish_status"]),
            "publish_status_code": normalized["publish_status_code"],
            "publish_url": publish_url,
            "article_id": normalized.get("article_id", ""),
        }

    def mark_manual_publish(self, record_id: str, publish_url: str) -> dict[str, object]:
        record = self._feishu.get_record_by_id(record_id)

        self._feishu.update_record_status(
            record.record_id,
            content_status=settings.FEISHU_STATUS_PUBLISHED,
            publish_status="published",
            publish_url=publish_url,
            last_error="",
        )

        return {
            "status": "ok",
            "stage": "published",
            "record_id": record.record_id,
            "publish_url": publish_url,
        }

    def get_record(self, record_id: str) -> dict[str, object]:
        record = self._feishu.get_record_by_id(record_id)
        return {"status": "ok", "record": asdict(record)}
