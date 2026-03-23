from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import settings
from services.api_workflow_service import ApiWorkflowService


class RecordRequest(BaseModel):
    record_id: Optional[str] = None
    source_mode: Optional[str] = None


class IngestDraftRequest(BaseModel):
    record_id: str
    source_mode: Optional[str] = None
    title: Optional[str] = None
    summary: str
    markdown: str
    cover_prompt: Optional[str] = None
    review_status: Optional[str] = "approved"
    review_notes: list[str] = []


class ManualPublishRequest(BaseModel):
    record_id: str
    publish_url: str


def _verify_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not settings.API_BEARER_TOKEN:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    token = authorization.split(" ", 1)[1]
    if token != settings.API_BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid bearer token.")


def create_app() -> FastAPI:
    app = FastAPI(title="wechat-article-agent-api")

    @app.exception_handler(ValueError)
    def handle_value_error(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"status": "failed", "error": str(exc)})

    @app.exception_handler(Exception)
    def handle_unhandled_error(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"status": "failed", "error": str(exc)})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/generate-draft")
    def generate_draft(
        payload: RecordRequest,
        _: None = Depends(_verify_token),
    ) -> dict[str, object]:
        service = ApiWorkflowService(source_mode=payload.source_mode)
        return service.generate_draft(record_id=payload.record_id)

    @app.post("/create-draft")
    def create_draft(
        payload: RecordRequest,
        _: None = Depends(_verify_token),
    ) -> dict[str, object]:
        service = ApiWorkflowService(source_mode=payload.source_mode)
        return service.create_draft(record_id=payload.record_id)

    @app.post("/ingest-draft")
    def ingest_draft(
        payload: IngestDraftRequest,
        _: None = Depends(_verify_token),
    ) -> dict[str, object]:
        service = ApiWorkflowService(source_mode=payload.source_mode)
        return service.ingest_draft(
            record_id=payload.record_id,
            title=payload.title,
            summary=payload.summary,
            markdown=payload.markdown,
            cover_prompt=payload.cover_prompt,
            review_status=payload.review_status,
            review_notes=payload.review_notes,
        )

    @app.post("/submit-publish")
    def submit_publish(
        payload: RecordRequest,
        _: None = Depends(_verify_token),
    ) -> dict[str, object]:
        service = ApiWorkflowService(source_mode=payload.source_mode)
        return service.submit_publish(record_id=payload.record_id)

    @app.post("/sync-status")
    def sync_status(
        payload: RecordRequest,
        _: None = Depends(_verify_token),
    ) -> dict[str, object]:
        service = ApiWorkflowService(source_mode=payload.source_mode)
        return service.sync_status(record_id=payload.record_id)

    @app.post("/mark-manual-publish")
    def mark_manual_publish(
        payload: ManualPublishRequest,
        _: None = Depends(_verify_token),
    ) -> dict[str, object]:
        service = ApiWorkflowService()
        return service.mark_manual_publish(record_id=payload.record_id, publish_url=payload.publish_url)

    @app.post("/get-record")
    def get_record(
        payload: RecordRequest,
        _: None = Depends(_verify_token),
    ) -> dict[str, object]:
        if not payload.record_id:
            raise HTTPException(status_code=400, detail="record_id is required.")
        service = ApiWorkflowService(source_mode=payload.source_mode)
        return service.get_record(record_id=payload.record_id)

    return app


app = create_app()
