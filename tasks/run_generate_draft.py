from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.workflow import WorkflowOptions  # noqa: E402
from services import WorkflowService  # noqa: E402


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate draft through Writer -> Formatter -> Review -> Publisher pipeline.")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock", help="Feishu source mode.")
    parser.add_argument("--limit", type=int, default=1, help="How many pending records to process.")
    parser.add_argument(
        "--confirm-publish",
        default="false",
        help="Whether to allow real publish logic (true/false). Default false for safety.",
    )
    args = parser.parse_args()

    result = WorkflowService().run(
        WorkflowOptions(
            source_mode=args.mode,
            limit=max(1, int(args.limit)),
            confirm_publish=_to_bool(str(args.confirm_publish)),
        )
    )
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
