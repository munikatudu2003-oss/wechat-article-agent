from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.workflow import WorkflowOptions  # noqa: E402
from services import WorkflowService  # noqa: E402


def main() -> int:
    result = WorkflowService().run(WorkflowOptions(confirm_publish=False, limit=1))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
