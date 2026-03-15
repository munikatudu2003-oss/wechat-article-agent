from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mock_pipeline import (  # noqa: E402
    FormatterAgent,
    LLMService,
    PublisherAgent,
    ReviewAgent,
    WriterAgent,
    build_mock_record,
    save_mock_outputs,
)


def main() -> int:
    output_dir = PROJECT_ROOT / "data" / "drafts"
    mock_record = build_mock_record()

    llm_service = LLMService()
    writer = WriterAgent(llm_service)
    review_agent = ReviewAgent()
    formatter = FormatterAgent()
    publisher = PublisherAgent()

    draft = writer.write(mock_record)
    review = review_agent.review(draft)
    html = formatter.to_html(draft, review)
    publish_result = publisher.publish_dry_run(draft, review)
    output_paths = save_mock_outputs(output_dir, draft, review, html, publish_result)

    print("[mock] Feishu record loaded:", mock_record.record_id)
    print("[mock] WriterAgent -> LLMService skeleton completed")
    print("[mock] ReviewAgent status:", review.status)
    print("[mock] FormatterAgent wrote HTML to:", output_paths["html"])
    print("[mock] PublisherAgent dry run:", publish_result["status"], publish_result["draft_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
