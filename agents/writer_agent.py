from __future__ import annotations

from config.settings import COVER_TODO_TEXT
from models.article import ArticleTask, DraftDocument
from services.llm_service import LLMService


class WriterAgent:
    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    def write(self, task: ArticleTask) -> DraftDocument:
        markdown = task.content_markdown.strip() if task.content_markdown.strip() else self._llm_service.generate_article(task)
        return DraftDocument(
            title=task.title,
            summary=task.summary,
            markdown=markdown,
            cover_todo=task.cover_prompt.strip() or COVER_TODO_TEXT,
        )
