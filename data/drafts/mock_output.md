# Turning a Feishu note into a WeChat article draft

## Summary
This mock draft shows the full offline pipeline from a local record through review, formatting, and a dry-run publish result.

## Key Points
- WriterAgent asks the local LLMService skeleton for a first draft.
- ReviewAgent marks the draft as approved unless it is too short.
- FormatterAgent converts markdown into a readable HTML article.
- PublisherAgent returns a dry-run payload instead of calling a real API.

## Suggested Structure
Start with the business context, then explain the workflow, and end with a practical next step.

## Source
- Feishu mock record: mock-record-001
- Reference link: mock://feishu/article-record/001