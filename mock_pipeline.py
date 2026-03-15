from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from typing import Any


@dataclass
class MockFeishuRecord:
    record_id: str
    title: str
    summary: str
    bullet_points: list[str]
    source_url: str


@dataclass
class DraftDocument:
    title: str
    summary: str
    markdown: str
    cover_todo: str


@dataclass
class ReviewDecision:
    status: str
    notes: list[str]


class LLMService:
    def generate_article(self, record: MockFeishuRecord) -> str:
        sections = [
            f"# {record.title}",
            "",
            "## Summary",
            record.summary,
            "",
            "## Key Points",
        ]

        sections.extend(f"- {point}" for point in record.bullet_points)
        sections.extend(
            [
                "",
                "## Suggested Structure",
                "Start with the business context, then explain the workflow, and end with a practical next step.",
                "",
                "## Source",
                f"- Feishu mock record: {record.record_id}",
                f"- Reference link: {record.source_url}",
            ]
        )
        return "\n".join(sections)


class WriterAgent:
    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    def write(self, record: MockFeishuRecord) -> DraftDocument:
        markdown = self._llm_service.generate_article(record)
        return DraftDocument(
            title=record.title,
            summary=record.summary,
            markdown=markdown,
            cover_todo="TODO: add cover asset before real publish"
        )


class ReviewAgent:
    def review(self, draft: DraftDocument) -> ReviewDecision:
        notes: list[str] = []
        if len(draft.markdown) < 180:
            notes.append("Draft is short; review before publish.")

        status = "approved" if not notes else "needs_manual_check"
        return ReviewDecision(status=status, notes=notes)


class FormatterAgent:
    def to_html(self, draft: DraftDocument, review: ReviewDecision) -> str:
        body = markdown_to_html(draft.markdown)
        review_items = "".join(f"<li>{escape(note)}</li>" for note in (review.notes or ["No blocking issues in mock review."]))

        return "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "  <head>",
                '    <meta charset="utf-8" />',
                '    <meta name="viewport" content="width=device-width, initial-scale=1" />',
                f"    <title>{escape(draft.title)}</title>",
                "    <style>",
                "      body { font-family: Georgia, serif; margin: 40px auto; max-width: 760px; line-height: 1.7; color: #1f2937; padding: 0 16px; }",
                "      h1, h2 { color: #111827; }",
                "      .summary { background: #f3f4f6; border-left: 4px solid #2563eb; padding: 16px; margin: 24px 0; }",
                "      .meta { color: #4b5563; font-size: 14px; }",
                "      .todo { color: #b45309; font-weight: 700; }",
                "    </style>",
                "  </head>",
                "  <body>",
                f"    <p class=\"meta\">Mock article generated at {escape(now_iso())}</p>",
                f"    <h1>{escape(draft.title)}</h1>",
                f"    <div class=\"summary\"><strong>Abstract</strong><p>{escape(draft.summary)}</p></div>",
                f"    <p class=\"todo\">{escape(draft.cover_todo)}</p>",
                f"    <p class=\"meta\">Review status: {escape(review.status)}</p>",
                "    <ul>",
                f"      {review_items}",
                "    </ul>",
                f"    {body}",
                "  </body>",
                "</html>",
            ]
        )


class PublisherAgent:
    def publish_dry_run(self, draft: DraftDocument, review: ReviewDecision) -> dict[str, Any]:
        return {
            "mode": "dry_run",
            "status": "draft_created",
            "draft_id": "mock-draft-001",
            "title": draft.title,
            "review_status": review.status,
            "cover": draft.cover_todo,
            "published_at": now_iso(),
        }


def build_mock_record() -> MockFeishuRecord:
    return MockFeishuRecord(
        record_id="mock-record-001",
        title="Turning a Feishu note into a WeChat article draft",
        summary="This mock draft shows the full offline pipeline from a local record through review, formatting, and a dry-run publish result.",
        bullet_points=[
            "WriterAgent asks the local LLMService skeleton for a first draft.",
            "ReviewAgent marks the draft as approved unless it is too short.",
            "FormatterAgent converts markdown into a readable HTML article.",
            "PublisherAgent returns a dry-run payload instead of calling a real API.",
        ],
        source_url="mock://feishu/article-record/001",
    )


def save_mock_outputs(base_dir: Path, draft: DraftDocument, review: ReviewDecision, html: str, publish_result: dict[str, Any]) -> dict[str, Path]:
    base_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = base_dir / "mock_output.md"
    html_path = base_dir / "mock_output.html"
    publish_path = base_dir / "mock_publish_result.json"

    markdown_path.write_text(draft.markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    publish_path.write_text(json.dumps(publish_result, indent=2), encoding="utf-8")

    review_path = base_dir / "mock_review.json"
    review_path.write_text(json.dumps(asdict(review), indent=2), encoding="utf-8")

    return {
        "markdown": markdown_path,
        "html": html_path,
        "publish": publish_path,
        "review": review_path,
    }


def markdown_to_html(markdown: str) -> str:
    parts: list[str] = []
    in_list = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            if in_list:
                parts.append("</ul>")
                in_list = False
            continue

        if line.startswith("# "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h1>{escape(line[2:])}</h1>")
            continue

        if line.startswith("## "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h2>{escape(line[3:])}</h2>")
            continue

        if line.startswith("- "):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"<li>{escape(line[2:])}</li>")
            continue

        if in_list:
            parts.append("</ul>")
            in_list = False
        parts.append(f"<p>{escape(line)}</p>")

    if in_list:
        parts.append("</ul>")

    return "\n    ".join(parts)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
