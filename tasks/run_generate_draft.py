from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents import FormatterAgent, PublisherAgent, ReviewAgent, WriterAgent  # noqa: E402
from config import settings  # noqa: E402
from config.settings import DRAFTS_DIR  # noqa: E402
from services import FeishuService, LLMService, MarkdownService, OutputService  # noqa: E402


def main() -> int:
    feishu_service = FeishuService()
    llm_service = LLMService()
    writer = WriterAgent(llm_service)
    review_agent = ReviewAgent()
    formatter = FormatterAgent(MarkdownService())
    publisher = PublisherAgent()
    output_service = OutputService()
    had_error = False

    try:
        records = feishu_service.list_pending_records()
    except Exception as error:
        print(f"[error] FeishuService ({feishu_service.source_mode}) failed while listing records: {error}", file=sys.stderr)
        return 1

    if not records:
        print(f"[{feishu_service.source_mode}] No pending Feishu records found.")
        return 0

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
            publish_result = publisher.publish_dry_run(draft, review)

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
                    cover_path=str(output_paths["html"]),
                    last_error="",
                )

            print(f"[{feishu_service.source_mode}] Feishu record loaded:", record.record_id)
            print(f"[{feishu_service.source_mode}] WriterAgent -> LLMService skeleton completed")
            print(f"[{feishu_service.source_mode}] ReviewAgent status:", review.status)
            print(f"[{feishu_service.source_mode}] FormatterAgent wrote HTML to:", output_paths["html"])
            print(f"[{feishu_service.source_mode}] PublisherAgent dry run:", publish_result["status"], publish_result["draft_id"])
        except Exception as error:
            had_error = True
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

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
