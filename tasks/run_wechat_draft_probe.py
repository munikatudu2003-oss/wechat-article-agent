from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.formatter_agent import FormatterAgent  # noqa: E402
from agents.review_agent import ReviewAgent  # noqa: E402
from config import settings  # noqa: E402
from config.settings import COVER_TODO_TEXT  # noqa: E402
from models.article import DraftDocument, ReviewDecision  # noqa: E402
from services.feishu_service import FeishuService  # noqa: E402
from services.llm_service import LLMService  # noqa: E402
from services.markdown_service import MarkdownService  # noqa: E402
from services.wechat_mp_service import WechatMPService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate real WeChat draft/add for exactly one Feishu record.")
    parser.add_argument("--mode", choices=["mock", "real"], default="real")
    parser.add_argument("--record-id", required=True)
    args = parser.parse_args()

    feishu_service = FeishuService(source_mode=args.mode)
    llm_service = LLMService()
    formatter = FormatterAgent(MarkdownService())
    review_agent = ReviewAgent()
    wechat_service = WechatMPService()

    record = feishu_service.get_record_by_id(args.record_id)
    markdown = record.content_markdown.strip() or llm_service.generate_article(record)
    draft = DraftDocument(
        title=record.title,
        summary=record.summary,
        markdown=markdown,
        cover_todo=record.cover_prompt.strip() or COVER_TODO_TEXT,
    )

    review = ReviewDecision(status=record.review_status, notes=["Using stored review status from Feishu."])
    if not record.review_status:
        review = review_agent.review(draft)

    if review.status != "approved":
        raise ValueError(f"Record {record.record_id} is not approved for real draft/add: {review.status}")

    html = formatter.to_html(draft, review)
    draft_id = wechat_service.create_draft(
        draft=draft,
        html=html,
        source_url=record.source_url,
    )

    if feishu_service.source_mode == "real":
        feishu_service.update_record_status(
            record.record_id,
            content_status=settings.FEISHU_STATUS_GENERATED,
            review_status=review.status,
            draft_id=draft_id,
            publish_status="draft_created",
            publish_id="",
            publish_url="",
            summary=draft.summary,
            content_markdown=draft.markdown,
            cover_prompt=draft.cover_todo,
            cover_path=record.cover_path,
            last_error="",
        )

    print(f"[draft-probe] record={record.record_id}")
    print(f"[draft-probe] title={record.title}")
    print(f"[draft-probe] review_status={review.status}")
    print(f"[draft-probe] thumb_media_id={settings.WECHAT_THUMB_MEDIA_ID}")
    print(f"[draft-probe] draft_id={draft_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
