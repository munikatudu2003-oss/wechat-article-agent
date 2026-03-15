from __future__ import annotations

from models.article import DraftDocument, ReviewDecision


class ReviewAgent:
    def review(self, draft: DraftDocument) -> ReviewDecision:
        notes: list[str] = []
        if len(draft.markdown) < 180:
            notes.append("Draft is short; review before publish.")

        status = "approved" if not notes else "needs_manual_check"
        return ReviewDecision(status=status, notes=notes)
