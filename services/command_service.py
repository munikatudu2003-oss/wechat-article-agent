from __future__ import annotations

import re

from models.workflow import WorkflowOptions


class CommandService:
    def parse_instruction(self, instruction: str) -> WorkflowOptions:
        lowered = instruction.strip().lower()

        source_mode = None
        if "mode=real" in lowered or "source_mode=real" in lowered:
            source_mode = "real"
        elif "mode=mock" in lowered or "source_mode=mock" in lowered:
            source_mode = "mock"

        confirm_publish = any(
            token in lowered
            for token in (
                "confirm_publish=true",
                "dry_run=false",
            )
        )

        return WorkflowOptions(
            confirm_publish=confirm_publish,
            limit=self._parse_limit(lowered),
            source_mode=source_mode,
        )

    def _parse_limit(self, lowered: str) -> int:
        match = re.search(r"limit\s*=\s*(\d+)", lowered)
        if match:
            return max(1, int(match.group(1)))
        return 1
