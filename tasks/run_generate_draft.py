from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents import FormatterAgent, PublisherAgent, ReviewAgent, WriterAgent  # noqa: E402
from config.settings import DRAFTS_DIR  # noqa: E402
from services import FeishuService, LLMService, MarkdownService, OutputService  # noqa: E402


def main() -> int:
    feishu_service = FeishuService()
    try:
        record = feishu_service.get_record()
    except Exception as error:
        print(f"[error] FeishuService ({feishu_service.source_mode}) failed: {error}", file=sys.stderr)
        return 1

    llm_service = LLMService()
    writer = WriterAgent(llm_service)
    review_agent = ReviewAgent()
    formatter = FormatterAgent(MarkdownService())
    publisher = PublisherAgent()
    output_service = OutputService()

    draft = writer.write(record)
    review = review_agent.review(draft)
    html = formatter.to_html(draft, review)
    publish_result = publisher.publish_dry_run(draft, review)
    output_paths = output_service.save_mock_outputs(DRAFTS_DIR, draft, review, html, publish_result)

    print(f"[{feishu_service.source_mode}] Feishu record loaded:", record.record_id)
    print("[mock] WriterAgent -> LLMService skeleton completed")
    print("[mock] ReviewAgent status:", review.status)
    print("[mock] FormatterAgent wrote HTML to:", output_paths["html"])
    print("[mock] PublisherAgent dry run:", publish_result["status"], publish_result["draft_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
