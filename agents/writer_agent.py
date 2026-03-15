from __future__ import annotations

from config.settings import COVER_TODO_TEXT
from models.article import DraftDocument, MockFeishuRecord
from services.llm_service import LLMService


class WriterAgent:
    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    def write(self, record: MockFeishuRecord) -> DraftDocument:
        markdown = self._llm_service.generate_article(record)
        return DraftDocument(
            title=record.title,
            summary=record.summary,
            markdown=markdown,
            cover_todo=COVER_TODO_TEXT,
        )
