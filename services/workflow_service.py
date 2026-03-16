from __future__ import annotations

import sys

from agents import FormatterAgent, PublisherAgent, ReviewAgent, WriterAgent
from config import settings
from config.settings import DRAFTS_DIR
from models.workflow import WorkflowOptions, WorkflowRecordResult, WorkflowRunResult
from services.feishu_service import FeishuService
from services.llm_service import LLMService
from services.markdown_service import MarkdownService
from services.output_service import OutputService
from services.wechat_mp_service import WechatMPService


class WorkflowService:
    def _try_update_record_status(self, feishu_service: FeishuService, record_id: str, **fields: str) -> None:
        try:
            feishu_service.update_record_status(record_id, **fields)
        except Exception as error:
            print(
                f"[warn] Failed to update Feishu status for {record_id}: {error}",
                file=sys.stderr,
            )

    def run(self, options: WorkflowOptions | None = None) -> WorkflowRunResult:
        workflow_options = options or WorkflowOptions()
        feishu_service = FeishuService(source_mode=workflow_options.source_mode)
        writer = WriterAgent(LLMService())
        review_agent = ReviewAgent()
        formatter = FormatterAgent(MarkdownService())
        publisher = PublisherAgent(WechatMPService())
        output_service = OutputService()

        print(
            f"[workflow] start mode={feishu_service.source_mode} "
            f"limit={workflow_options.limit} confirm_publish={workflow_options.confirm_publish}"
        )

        try:
            records = feishu_service.list_pending_records(limit=workflow_options.limit)
        except Exception as error:
            print(f"[error] FeishuService ({feishu_service.source_mode}) failed while listing records: {error}", file=sys.stderr)
            return WorkflowRunResult(
                success=False,
                processed_count=0,
                failed_count=1,
                source_mode=feishu_service.source_mode,
                confirm_publish=workflow_options.confirm_publish,
                records=[],
            )

        if not records:
            print(f"[{feishu_service.source_mode}] No pending Feishu records found.")
            return WorkflowRunResult(
                success=True,
                processed_count=0,
                failed_count=0,
                source_mode=feishu_service.source_mode,
                confirm_publish=workflow_options.confirm_publish,
                records=[],
            )

        results: list[WorkflowRecordResult] = []
        failed_count = 0

        for index, record in enumerate(records, start=1):
            try:
                print(f"[workflow] processing record={record.record_id}")
                if feishu_service.source_mode == "real":
                    self._try_update_record_status(
                        feishu_service,
                        record.record_id,
                        content_status=settings.FEISHU_STATUS_PROCESSING,
                        publish_status="processing",
                        last_error="",
                    )

                draft = writer.write(record)
                print(f"[{feishu_service.source_mode}] WriterAgent completed")

                review = review_agent.review(draft)
                print(f"[{feishu_service.source_mode}] ReviewAgent status={review.status}")

                html = formatter.to_html(draft, review)
                print(f"[{feishu_service.source_mode}] FormatterAgent completed")

                if review.status == "needs_manual_check":
                    publish_result: dict[str, object] = {
                        "mode": "blocked",
                        "status": "needs_manual_check",
                        "draft_id": "",
                        "publish_id": "",
                        "publish_url": "",
                        "title": draft.title,
                        "review_status": review.status,
                        "note": "Publish terminated: ReviewAgent requires manual check.",
                    }
                else:
                    publish_result = publisher.publish(
                        draft,
                        review,
                        html=html,
                        confirm_publish=workflow_options.confirm_publish,
                        source_url=record.source_url,
                    )

                file_stem = "mock_output" if feishu_service.source_mode == "mock" and index == 1 else f"{record.record_id}_output"
                output_paths = output_service.save_outputs(DRAFTS_DIR, file_stem, draft, review, html, publish_result)

                draft_id = str(publish_result.get("draft_id", ""))
                publish_id = str(publish_result.get("publish_id", ""))
                publish_url = str(publish_result.get("publish_url", ""))
                publish_status = str(publish_result.get("status", ""))
                content_status = str(publish_result.get("content_status", "")) or settings.FEISHU_STATUS_GENERATED

                if feishu_service.source_mode == "real":
                    self._try_update_record_status(
                        feishu_service,
                        record.record_id,
                        content_status=content_status,
                        review_status=review.status,
                        draft_id=draft_id,
                        publish_status=publish_status,
                        publish_id=publish_id,
                        publish_url=publish_url,
                        summary=draft.summary,
                        content_markdown=draft.markdown,
                        cover_prompt=draft.cover_todo,
                        cover_path=record.cover_path,
                        last_error="",
                    )

                print(
                    f"[{feishu_service.source_mode}] PublisherAgent result "
                    f"status={publish_status} draft_id={draft_id or '-'} publish_id={publish_id or '-'}"
                )
                print(f"[{feishu_service.source_mode}] Backups saved markdown={output_paths['markdown']} html={output_paths['html']}")

                results.append(
                    WorkflowRecordResult(
                        record_id=record.record_id,
                        review_status=review.status,
                        publish_status=publish_status,
                        draft_id=draft_id or publish_id,
                        output_html=output_paths["html"],
                        output_markdown=output_paths["markdown"],
                        source_mode=feishu_service.source_mode,
                    )
                )
            except Exception as error:
                failed_count += 1
                print(f"[error] Failed to process record {record.record_id}: {error}", file=sys.stderr)
                if feishu_service.source_mode == "real":
                    self._try_update_record_status(
                        feishu_service,
                        record.record_id,
                        content_status=settings.FEISHU_STATUS_FAILED,
                        publish_status="failed",
                        last_error=str(error),
                    )

        return WorkflowRunResult(
            success=failed_count == 0,
            processed_count=len(results),
            failed_count=failed_count,
            source_mode=feishu_service.source_mode,
            confirm_publish=workflow_options.confirm_publish,
            records=results,
        )
