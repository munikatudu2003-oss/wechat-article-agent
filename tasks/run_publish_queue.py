from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.formatter_agent import FormatterAgent  # noqa: E402
from agents.review_agent import ReviewAgent  # noqa: E402
from config.settings import COVER_TODO_TEXT  # noqa: E402
from models.article import DraftDocument, ReviewDecision  # noqa: E402
from services.feishu_service import FeishuService  # noqa: E402
from services.llm_service import LLMService  # noqa: E402
from services.markdown_service import MarkdownService  # noqa: E402
from services.wechat_mp_service import WechatMPService  # noqa: E402


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish queued WeChat articles from generated Feishu records.")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--confirm-publish",
        default="false",
        help="true/false. Real publish only runs when true.",
    )
    args = parser.parse_args()

    confirm_publish = _to_bool(str(args.confirm_publish))
    feishu_service = FeishuService(source_mode=args.mode)
    formatter = FormatterAgent(MarkdownService())
    review_agent = ReviewAgent()
    llm_service = LLMService()
    wechat_service = WechatMPService()

    records = feishu_service.list_publish_queue_records(limit=max(1, int(args.limit)))
    print(f"[publish-queue] source_mode={feishu_service.source_mode} confirm_publish={confirm_publish}")

    if not records:
        print("[publish-queue] no generated records waiting for publish")
        return 0

    processed = 0
    failed = 0

    for record in records:
        markdown = record.content_markdown.strip() or llm_service.generate_article(record)
        draft = DraftDocument(
            title=record.title,
            summary=record.summary,
            markdown=markdown,
            cover_todo=record.cover_prompt.strip() or COVER_TODO_TEXT,
        )

        if record.review_status:
            review = ReviewDecision(status=record.review_status, notes=["Using stored review status from Feishu."])
        else:
            review = review_agent.review(draft)

        html = formatter.to_html(draft, review)

        if review.status != "approved":
            failed += 1
            print(f"[publish-queue] blocked record={record.record_id} review_status={review.status}")
            if feishu_service.source_mode == "real":
                feishu_service.update_record_status(
                    record.record_id,
                    publish_status="review_blocked",
                    last_error=f"Review status is {review.status}",
                )
            continue

        if not confirm_publish:
            processed += 1
            print(
                f"[publish-queue] dry-run record={record.record_id} "
                f"title={record.title} draft_id={record.draft_id or '-'}"
            )
            continue

        try:
            if feishu_service.source_mode == "mock":
                processed += 1
                print(f"[publish-queue] mock publish simulated record={record.record_id}")
                continue

            if record.draft_id and not record.draft_id.startswith("mock-"):
                publish_response = wechat_service.submit_publish(record.draft_id)
                draft_id = record.draft_id
            else:
                draft_id = wechat_service.create_draft(
                    draft=draft,
                    html=html,
                    source_url=record.source_url,
                )
                publish_response = wechat_service.submit_publish(draft_id)

            publish_id = str(publish_response.get("publish_id", ""))
            feishu_service.update_record_status(
                record.record_id,
                review_status=review.status,
                draft_id=draft_id,
                publish_status="publish_submitted",
                publish_id=publish_id,
                summary=draft.summary,
                content_markdown=draft.markdown,
                cover_prompt=draft.cover_todo,
                cover_path=record.cover_path,
                last_error="",
            )
            processed += 1
            print(
                f"[publish-queue] submitted record={record.record_id} "
                f"draft_id={draft_id} publish_id={publish_id or '-'}"
            )
        except Exception as error:
            failed += 1
            print(f"[publish-queue] failed record={record.record_id}: {error}", file=sys.stderr)
            if feishu_service.source_mode == "real":
                feishu_service.update_record_status(
                    record.record_id,
                    publish_status="publish_failed",
                    last_error=str(error),
                )

    print(f"[publish-queue] processed={processed} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
