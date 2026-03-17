from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings  # noqa: E402
from services.feishu_service import FeishuService  # noqa: E402


def _normalize_url(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        return text
    raise ValueError("publish_url must start with http:// or https://")


def _resolve_content_status(publish_status: str, explicit_content_status: str) -> str:
    if explicit_content_status.strip():
        return explicit_content_status.strip()

    normalized = publish_status.strip().lower()
    if normalized == "published":
        return settings.FEISHU_STATUS_PUBLISHED
    if normalized in {"publishing", "publish_submitted"}:
        return settings.FEISHU_STATUS_PUBLISHING
    if normalized in {"publish_failed", "failed"}:
        return settings.FEISHU_STATUS_PUBLISH_FAILED
    return settings.FEISHU_STATUS_GENERATED


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write a manual WeChat publish result back into Feishu after a human publishes from the MP backend."
    )
    parser.add_argument("--mode", choices=["mock", "real"], default="mock")
    parser.add_argument("--record-id", required=True)
    parser.add_argument("--publish-url", default="")
    parser.add_argument("--publish-status", default="published")
    parser.add_argument("--content-status", default="")
    parser.add_argument("--publish-id", default="")
    parser.add_argument("--clear-error", default="true", help="true/false, default true")
    args = parser.parse_args()

    clear_error = str(args.clear_error).strip().lower() in {"1", "true", "yes", "y", "on"}
    publish_status = args.publish_status.strip() or "published"
    publish_url = _normalize_url(args.publish_url)
    content_status = _resolve_content_status(publish_status, args.content_status)

    if publish_status.lower() == "published" and not publish_url:
        raise ValueError("published status requires --publish-url")

    feishu_service = FeishuService(source_mode=args.mode)
    record = feishu_service.get_record_by_id(args.record_id)

    print(f"[manual-publish] source_mode={feishu_service.source_mode}")
    print(f"[manual-publish] record={record.record_id} title={record.title}")
    print(f"[manual-publish] existing_draft_id={record.draft_id or '-'}")

    result = feishu_service.update_record_status(
        record.record_id,
        content_status=content_status,
        review_status=record.review_status,
        draft_id=record.draft_id,
        publish_status=publish_status,
        publish_id=args.publish_id.strip() or record.publish_id,
        publish_url=publish_url or record.publish_url,
        last_error="" if clear_error else record.last_error,
    )

    print(
        f"[manual-publish] updated record={record.record_id} "
        f"content_status={content_status} publish_status={publish_status} "
        f"publish_id={args.publish_id.strip() or record.publish_id or '-'} "
        f"publish_url={publish_url or record.publish_url or '-'}"
    )
    print(f"[manual-publish] response={result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
