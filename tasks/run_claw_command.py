from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.command_service import CommandService  # noqa: E402
from services.workflow_service import WorkflowService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the WeChat article workflow from a single natural-language instruction.")
    parser.add_argument(
        "instruction",
        help="Example: Publish the latest Feishu article to WeChat, mode=real, confirm_publish=true, limit=1",
    )
    args = parser.parse_args()

    command_service = CommandService()
    options = command_service.parse_instruction(args.instruction)
    result = WorkflowService().run(options)

    print("")
    print("[command] instruction:", args.instruction)
    print("[command] source_mode:", result.source_mode)
    print("[command] confirm_publish:", result.confirm_publish)
    print("[command] processed_count:", result.processed_count)
    print("[command] failed_count:", result.failed_count)

    for record in result.records:
        print(
            "[command] record:",
            record.record_id,
            "review=" + record.review_status,
            "publish=" + record.publish_status,
            "draft_id=" + record.draft_id,
        )

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
