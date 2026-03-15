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
from services.wechat_publisher_service import WechatPublisherService


class WorkflowService:
    def run(self, options: WorkflowOptions | None = None) -> WorkflowRunResult:
        workflow_options = options or WorkflowOptions()
        feishu_service = FeishuService(source_mode=workflow_options.source_mode)
        writer = WriterAgent(LLMService())
        review_agent = ReviewAgent()
        formatter = FormatterAgent(MarkdownService())
        publisher = PublisherAgent(WechatPublisherService())
        output_service = OutputService()

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
                if feishu_service.source_mode == "real":
                    feishu_service.update_record_status(
                        record.record_id,
                        content_status=settings.FEISHU_STATUS_PROCESSING,
                        last_error="",
                    )

                draft = writer.write(record)
                review = review_agent.review(draft)
                html = formatter.to_html(draft, review)
                publish_result = publisher.publish(
                    draft,
                    review,
                    html=html,
                    confirm_publish=workflow_options.confirm_publish,
                    source_url=record.source_url,
                )

                file_stem = "mock_output" if feishu_service.source_mode == "mock" and index == 1 else f"{record.record_id}_output"
                output_paths = output_service.save_outputs(DRAFTS_DIR, file_stem, draft, review, html, publish_result)

                if feishu_service.source_mode == "real":
                    feishu_service.update_record_status(
                        record.record_id,
                        content_status=settings.FEISHU_STATUS_GENERATED,
                        review_status=review.status,
                        draft_id=str(publish_result.get("draft_id", "")),
                        summary=draft.summary,
                        content_markdown=draft.markdown,
                        cover_prompt=draft.cover_todo,
                        cover_path=record.cover_path,
                        last_error="",
                    )

                print(f"[{feishu_service.source_mode}] Feishu record loaded:", record.record_id)
                print(f"[{feishu_service.source_mode}] WriterAgent -> LLMService completed")
                print(f"[{feishu_service.source_mode}] ReviewAgent status:", review.status)
                print(f"[{feishu_service.source_mode}] FormatterAgent wrote HTML to:", output_paths["html"])
                print(f"[{feishu_service.source_mode}] PublisherAgent result:", publish_result["status"], publish_result["draft_id"])

                results.append(
                    WorkflowRecordResult(
                        record_id=record.record_id,
                        review_status=review.status,
                        publish_status=str(publish_result.get("status", "")),
                        draft_id=str(publish_result.get("draft_id", "")),
                        output_html=output_paths["html"],
                        output_markdown=output_paths["markdown"],
                        source_mode=feishu_service.source_mode,
                    )
                )
            except Exception as error:
                failed_count += 1
                print(f"[error] Failed to process record {record.record_id}: {error}", file=sys.stderr)
                if feishu_service.source_mode == "real":
                    try:
                        feishu_service.update_record_status(
                            record.record_id,
                            content_status=settings.FEISHU_STATUS_FAILED,
                            last_error=str(error),
                        )
                    except Exception as update_error:
                        print(f"[error] Failed to write error status for {record.record_id}: {update_error}", file=sys.stderr)

        return WorkflowRunResult(
            success=failed_count == 0,
            processed_count=len(results),
            failed_count=failed_count,
            source_mode=feishu_service.source_mode,
            confirm_publish=workflow_options.confirm_publish,
            records=results,
        )
