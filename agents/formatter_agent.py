from __future__ import annotations

from html import escape

from models.article import DraftDocument, ReviewDecision
from services.markdown_service import MarkdownService
from utils.time_utils import now_iso


class FormatterAgent:
    def __init__(self, markdown_service: MarkdownService):
        self._markdown_service = markdown_service

    def to_html(self, draft: DraftDocument, review: ReviewDecision) -> str:
        body = self._markdown_service.markdown_to_html(draft.markdown)
        review_items = "".join(
            f"<li>{escape(note)}</li>" for note in (review.notes or ["No blocking issues in mock review."])
        )

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
                f'    <p class="meta">Mock article generated at {escape(now_iso())}</p>',
                f"    <h1>{escape(draft.title)}</h1>",
                f'    <div class="summary"><strong>Abstract</strong><p>{escape(draft.summary)}</p></div>',
                f'    <p class="todo">{escape(draft.cover_todo)}</p>',
                f'    <p class="meta">Review status: {escape(review.status)}</p>',
                "    <ul>",
                f"      {review_items}",
                "    </ul>",
                f"    {body}",
                "  </body>",
                "</html>",
            ]
        )
