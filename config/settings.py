from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
DRAFTS_DIR = DATA_DIR / "drafts"
COVER_TODO_TEXT = "TODO: add cover asset before real publish"

FEISHU_SOURCE_MODE = os.getenv("FEISHU_SOURCE_MODE", "mock").strip().lower() or "mock"
FEISHU_BASE_URL = os.getenv("FEISHU_BASE_URL", "https://open.feishu.cn/open-apis").rstrip("/")
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "").strip()
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "").strip()
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN", "").strip()
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID", "").strip()
FEISHU_VIEW_ID = os.getenv("FEISHU_VIEW_ID", "").strip()
FEISHU_PENDING_ONLY = os.getenv("FEISHU_PENDING_ONLY", "true").strip().lower() != "false"
FEISHU_PAGE_SIZE = max(1, int(os.getenv("FEISHU_PAGE_SIZE", "1")))
FEISHU_MAX_RECORDS = max(1, int(os.getenv("FEISHU_MAX_RECORDS", str(FEISHU_PAGE_SIZE))))

FEISHU_FIELD_TITLE = os.getenv("FEISHU_FIELD_TITLE", "ArticleTitle").strip()
FEISHU_FIELD_SUMMARY = os.getenv("FEISHU_FIELD_SUMMARY", "ArticleSummary").strip()
FEISHU_FIELD_CATEGORY = os.getenv("FEISHU_FIELD_CATEGORY", "Category").strip()
FEISHU_FIELD_KEYWORDS = os.getenv("FEISHU_FIELD_KEYWORDS", "Keywords").strip()
FEISHU_FIELD_REFERENCE = os.getenv("FEISHU_FIELD_REFERENCE", "ReferenceMaterial").strip()
FEISHU_FIELD_WORD_COUNT = os.getenv("FEISHU_FIELD_WORD_COUNT", "TargetWordCount").strip()
FEISHU_FIELD_SOURCE_URL = os.getenv("FEISHU_FIELD_SOURCE_URL", "SourceUrl").strip()
FEISHU_FIELD_CONTENT_MARKDOWN = os.getenv("FEISHU_FIELD_CONTENT_MARKDOWN", "ContentMarkdown").strip()
FEISHU_FIELD_COVER_PROMPT = os.getenv("FEISHU_FIELD_COVER_PROMPT", "CoverPrompt").strip()
FEISHU_FIELD_COVER_PATH = os.getenv("FEISHU_FIELD_COVER_PATH", "CoverPath").strip()
FEISHU_FIELD_CONTENT_STATUS = os.getenv("FEISHU_FIELD_CONTENT_STATUS", "ContentStatus").strip()
FEISHU_FIELD_REVIEW_STATUS = os.getenv("FEISHU_FIELD_REVIEW_STATUS", "ReviewStatus").strip()
FEISHU_FIELD_DRAFT_ID = os.getenv("FEISHU_FIELD_DRAFT_ID", "DraftId").strip()
FEISHU_FIELD_PUBLISH_STATUS = os.getenv("FEISHU_FIELD_PUBLISH_STATUS", "PublishStatus").strip()
FEISHU_FIELD_PUBLISH_ID = os.getenv("FEISHU_FIELD_PUBLISH_ID", "PublishId").strip()
FEISHU_FIELD_PUBLISH_URL = os.getenv("FEISHU_FIELD_PUBLISH_URL", "PublishUrl").strip()
FEISHU_FIELD_LAST_ERROR = os.getenv("FEISHU_FIELD_LAST_ERROR", "LastError").strip()
FEISHU_FIELD_PROCESSED_AT = os.getenv("FEISHU_FIELD_PROCESSED_AT", "ProcessedAt").strip()

FEISHU_STATUS_PENDING = os.getenv("FEISHU_STATUS_PENDING", "pending").strip()
FEISHU_STATUS_PROCESSING = os.getenv("FEISHU_STATUS_PROCESSING", "processing").strip()
FEISHU_STATUS_GENERATED = os.getenv("FEISHU_STATUS_GENERATED", "generated").strip()
FEISHU_STATUS_FAILED = os.getenv("FEISHU_STATUS_FAILED", "failed").strip()

WECHAT_PUBLISH_MODE = os.getenv("WECHAT_PUBLISH_MODE", "dry_run").strip().lower() or "dry_run"
WECHAT_API_BASE_URL = os.getenv("WECHAT_API_BASE_URL", "https://api.weixin.qq.com").rstrip("/")
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "").strip()
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "").strip()
WECHAT_ACCESS_TOKEN = os.getenv("WECHAT_ACCESS_TOKEN", "").strip()
WECHAT_THUMB_MEDIA_ID = os.getenv("WECHAT_THUMB_MEDIA_ID", "").strip()
WECHAT_AUTHOR = os.getenv("WECHAT_AUTHOR", "").strip()
WECHAT_CONTENT_SOURCE_URL = os.getenv("WECHAT_CONTENT_SOURCE_URL", "").strip()
WECHAT_NEED_OPEN_COMMENT = 1 if os.getenv("WECHAT_NEED_OPEN_COMMENT", "false").strip().lower() == "true" else 0
WECHAT_ONLY_FANS_CAN_COMMENT = 1 if os.getenv("WECHAT_ONLY_FANS_CAN_COMMENT", "false").strip().lower() == "true" else 0
WECHAT_AUTO_SUBMIT_PUBLISH = os.getenv("WECHAT_AUTO_SUBMIT_PUBLISH", "false").strip().lower() == "true"
