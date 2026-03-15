from __future__ import annotations

from models.article import MockFeishuRecord


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
