from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.workflow import WorkflowOptions  # noqa: E402
from services.workflow_service import WorkflowService  # noqa: E402


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description="One-click publish workflow for WeChat MP article.")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--confirm-publish", default="false", help="true/false, default false for safe dry-run")
    args = parser.parse_args()

    options = WorkflowOptions(
        source_mode=args.mode,
        limit=max(1, int(args.limit)),
        confirm_publish=_to_bool(str(args.confirm_publish)),
    )
    result = WorkflowService().run(options)

    print("")
    print("[one-click] source_mode:", result.source_mode)
    print("[one-click] confirm_publish:", result.confirm_publish)
    print("[one-click] processed_count:", result.processed_count)
    print("[one-click] failed_count:", result.failed_count)
    for record in result.records:
        print(
            "[one-click] record:",
            record.record_id,
            "review=" + record.review_status,
            "publish=" + record.publish_status,
            "draft_id=" + record.draft_id,
        )

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
