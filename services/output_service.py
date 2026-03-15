from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from models.article import DraftDocument, ReviewDecision


class OutputService:
    def save_outputs(
        self,
        base_dir: Path,
        file_stem: str,
        draft: DraftDocument,
        review: ReviewDecision,
        html: str,
        publish_result: dict[str, object],
    ) -> dict[str, Path]:
        base_dir.mkdir(parents=True, exist_ok=True)

        stem = self._sanitize_stem(file_stem)
        if stem == "mock_output":
            markdown_path = base_dir / "mock_output.md"
            html_path = base_dir / "mock_output.html"
            publish_path = base_dir / "mock_publish_result.json"
            review_path = base_dir / "mock_review.json"
        else:
            markdown_path = base_dir / f"{stem}.md"
            html_path = base_dir / f"{stem}.html"
            publish_path = base_dir / f"{stem}_publish_result.json"
            review_path = base_dir / f"{stem}_review.json"

        markdown_path.write_text(draft.markdown, encoding="utf-8")
        html_path.write_text(html, encoding="utf-8")
        publish_path.write_text(json.dumps(publish_result, indent=2), encoding="utf-8")
        review_path.write_text(json.dumps(asdict(review), indent=2), encoding="utf-8")

        return {
            "markdown": markdown_path,
            "html": html_path,
            "publish": publish_path,
            "review": review_path,
        }

    def _sanitize_stem(self, value: str) -> str:
        cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value.strip())
        return cleaned or "output"
