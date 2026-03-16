from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.feishu_service import FeishuService  # noqa: E402
from services.wechat_mp_service import WechatMPService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync WeChat publish status back into Feishu.")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    feishu_service = FeishuService(source_mode=args.mode)
    wechat_service = WechatMPService()

    records = feishu_service.list_status_sync_records(limit=max(1, int(args.limit)))
    print(f"[sync-status] source_mode={feishu_service.source_mode}")

    if not records:
        print("[sync-status] no publish records waiting for sync")
        return 0

    processed = 0
    failed = 0

    for record in records:
        try:
            if feishu_service.source_mode == "mock":
                processed += 1
                print(f"[sync-status] mock sync skipped record={record.record_id}")
                continue

            status_payload = wechat_service.get_publish_status(record.publish_id)
            normalized = wechat_service.normalize_publish_status(status_payload)

            publish_url = normalized["publish_url"]
            article_id = str(normalized.get("article_id", ""))
            if not publish_url and article_id:
                article_payload = wechat_service.get_published_article(article_id)
                publish_url = wechat_service.extract_article_url_from_payload(article_payload)

            feishu_service.update_record_status(
                record.record_id,
                content_status=str(normalized["content_status"]),
                publish_status=str(normalized["publish_status"]),
                publish_id=str(normalized["publish_id"]) or record.publish_id,
                publish_url=publish_url or record.publish_url,
                last_error=str(normalized["last_error"]),
            )

            processed += 1
            print(
                f"[sync-status] record={record.record_id} "
                f"publish_id={record.publish_id} status={normalized['publish_status']} "
                f"status_code={normalized['publish_status_code']} article_id={normalized['article_id'] or '-'} "
                f"url={publish_url or '-'}"
            )
        except Exception as error:
            failed += 1
            print(f"[sync-status] failed record={record.record_id}: {error}", file=sys.stderr)
            if feishu_service.source_mode == "real":
                feishu_service.update_record_status(
                    record.record_id,
                    last_error=str(error),
                )

    print(f"[sync-status] processed={processed} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
