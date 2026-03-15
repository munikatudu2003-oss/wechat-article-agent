from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
FEISHU_PAGE_SIZE = max(1, int(os.getenv("FEISHU_PAGE_SIZE", "1")))

FEISHU_FIELD_TITLE = os.getenv("FEISHU_FIELD_TITLE", "文章标题").strip()
FEISHU_FIELD_SUMMARY = os.getenv("FEISHU_FIELD_SUMMARY", "摘要").strip()
FEISHU_FIELD_CATEGORY = os.getenv("FEISHU_FIELD_CATEGORY", "栏目类型").strip()
FEISHU_FIELD_KEYWORDS = os.getenv("FEISHU_FIELD_KEYWORDS", "关键词").strip()
FEISHU_FIELD_REFERENCE = os.getenv("FEISHU_FIELD_REFERENCE", "参考素材").strip()
FEISHU_FIELD_WORD_COUNT = os.getenv("FEISHU_FIELD_WORD_COUNT", "目标字数").strip()
