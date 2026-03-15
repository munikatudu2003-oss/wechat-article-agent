from __future__ import annotations

from models.article import ArticleTask


class LLMService:
    def generate_article(self, task: ArticleTask) -> str:
        key_points = [
            f"Column type: {task.column_type}" if task.column_type else "",
            f"Keywords: {task.keywords}" if task.keywords else "",
            f"Target word count: {task.target_words}" if task.target_words else "",
            f"Reference material: {task.source_material}" if task.source_material else "",
        ]

        sections = [
            f"# {task.title}",
            "",
            "## Summary",
            task.summary,
            "",
            "## Key Points",
        ]

        sections.extend(f"- {point}" for point in key_points if point)
        sections.extend(
            [
                "",
                "## Suggested Structure",
                "Start with the business context, then explain the workflow, and end with a practical next step.",
                "",
                "## Source",
                f"- Feishu record: {task.record_id}",
                f"- Reference link: {task.source_url}",
            ]
        )
        return "\n".join(sections)
