# wechat-article-agent

Minimal local workflow for turning Feishu article tasks into WeChat MP drafts, with safe publish gates, local backups, and Feishu write-back.

## Current Scope

The working pipeline today is:

`Feishu -> Writer -> Review -> Formatter -> Publisher -> local backups -> Feishu write-back`

What is already working:

- `mock` and `real` Feishu source modes
- real Feishu record listing
- skipping empty starter rows
- filtering `pending` records
- writing back `generated`, `approved`, `draft_created`, `DraftId`, and `ProcessedAt`
- one-click CLI entrypoints:
  - `tasks/run_one_click_publish.py`
  - `tasks/run_claw_command.py`
- WeChat MP API shape integration for:
  - access token fetch
  - `draft/add`
  - optional `freepublish/submit`
- publish safety gates:
  - `confirm_publish=true`
  - `WECHAT_PUBLISH_MODE=real`
  - review result must be `approved`

What is not closed yet:

- real WeChat `freepublish/submit` validation on an eligible account
- final public article URL lookup for async publish tasks
- real bot message trigger layer
- real LLM-based article generation
- stronger review and quality control
- cover generation

## Repository Layout

- `agents/`
  - `WriterAgent`
  - `ReviewAgent`
  - `FormatterAgent`
  - `PublisherAgent`
- `services/`
  - `FeishuService`
  - `LLMService`
  - `MarkdownService`
  - `OutputService`
  - `CommandService`
  - `WorkflowService`
  - `WechatMPService`
- `models/`
  - shared dataclasses for records and workflow results
- `utils/`
  - helpers such as timestamp formatting
- `tasks/`
  - runnable entrypoints
- `data/drafts/`
  - sample outputs plus generated local backups

## Python Interpreter

The currently verified interpreter on this machine is:

```powershell
C:\Program Files\AutoClaw\resources\python\python.exe
```

Project-local `.env` values are loaded automatically and override stale machine-level environment variables.

## Quick Start

Run the local mock workflow:

```powershell
& 'C:\Program Files\AutoClaw\resources\python\python.exe' `
  '.\tasks\run_generate_draft.py'
```

Run the one-line command entrypoint in mock mode:

```powershell
& 'C:\Program Files\AutoClaw\resources\python\python.exe' `
  '.\tasks\run_claw_command.py' `
  'Generate the latest Feishu article, mode=mock, confirm_publish=false, limit=1'
```

Run the one-click entrypoint in mock mode:

```powershell
& 'C:\Program Files\AutoClaw\resources\python\python.exe' `
  '.\tasks\run_one_click_publish.py' `
  --mode mock --limit 1 --confirm-publish false
```

## Feishu Configuration

Safe default:

```powershell
$env:FEISHU_SOURCE_MODE='mock'
```

Real Feishu mode:

```powershell
$env:FEISHU_SOURCE_MODE='real'
$env:FEISHU_APP_ID='your_app_id'
$env:FEISHU_APP_SECRET='your_app_secret'
$env:FEISHU_APP_TOKEN='your_bitable_app_token'
$env:FEISHU_TABLE_ID='your_table_id'
```

Optional real-mode settings:

```powershell
$env:FEISHU_VIEW_ID='your_view_id'
$env:FEISHU_PENDING_ONLY='true'
$env:FEISHU_PAGE_SIZE='1'
$env:FEISHU_MAX_RECORDS='1'
```

Field mapping defaults:

```powershell
$env:FEISHU_FIELD_TITLE='ArticleTitle'
$env:FEISHU_FIELD_SUMMARY='ArticleSummary'
$env:FEISHU_FIELD_CATEGORY='Category'
$env:FEISHU_FIELD_KEYWORDS='Keywords'
$env:FEISHU_FIELD_REFERENCE='ReferenceMaterial'
$env:FEISHU_FIELD_WORD_COUNT='TargetWordCount'
$env:FEISHU_FIELD_SOURCE_URL='SourceUrl'
$env:FEISHU_FIELD_CONTENT_MARKDOWN='ContentMarkdown'
$env:FEISHU_FIELD_COVER_PROMPT='CoverPrompt'
$env:FEISHU_FIELD_COVER_PATH='CoverPath'
$env:FEISHU_FIELD_CONTENT_STATUS='ContentStatus'
$env:FEISHU_FIELD_REVIEW_STATUS='ReviewStatus'
$env:FEISHU_FIELD_DRAFT_ID='DraftId'
$env:FEISHU_FIELD_PUBLISH_STATUS='PublishStatus'
$env:FEISHU_FIELD_PUBLISH_ID='PublishId'
$env:FEISHU_FIELD_PUBLISH_URL='PublishUrl'
$env:FEISHU_FIELD_LAST_ERROR='LastError'
$env:FEISHU_FIELD_PROCESSED_AT='ProcessedAt'
```

Status defaults:

```powershell
$env:FEISHU_STATUS_PENDING='pending'
$env:FEISHU_STATUS_PROCESSING='processing'
$env:FEISHU_STATUS_GENERATED='generated'
$env:FEISHU_STATUS_FAILED='failed'
```

## WeChat Publish Modes

By default, WeChat publish stays in dry-run mode:

```powershell
$env:WECHAT_PUBLISH_MODE='dry_run'
```

Real WeChat draft creation needs:

```powershell
$env:WECHAT_PUBLISH_MODE='real'
$env:WECHAT_APP_ID='your_wechat_app_id'
$env:WECHAT_APP_SECRET='your_wechat_app_secret'
$env:WECHAT_THUMB_MEDIA_ID='your_thumb_media_id'
```

Optional WeChat settings:

```powershell
$env:WECHAT_ACCESS_TOKEN=''
$env:WECHAT_AUTHOR='your_author_name'
$env:WECHAT_CONTENT_SOURCE_URL='https://your-source-url'
$env:WECHAT_NEED_OPEN_COMMENT='false'
$env:WECHAT_ONLY_FANS_CAN_COMMENT='false'
$env:WECHAT_AUTO_SUBMIT_PUBLISH='false'
```

Important behavior:

- `WECHAT_AUTO_SUBMIT_PUBLISH=false` means create a real draft only
- `WECHAT_AUTO_SUBMIT_PUBLISH=true` means call `freepublish/submit` after draft creation
- final public article URL lookup is not implemented yet

## Safe Real-Draft Test

This is the recommended next live validation step: create a real WeChat draft, but do not submit it for publish.

```powershell
$env:FEISHU_SOURCE_MODE='real'
$env:WECHAT_PUBLISH_MODE='real'
$env:WECHAT_AUTO_SUBMIT_PUBLISH='false'
$env:WECHAT_APP_ID='your_wechat_app_id'
$env:WECHAT_APP_SECRET='your_wechat_app_secret'
$env:WECHAT_THUMB_MEDIA_ID='your_thumb_media_id'

& 'C:\Program Files\AutoClaw\resources\python\python.exe' `
  '.\tasks\run_one_click_publish.py' `
  --mode real --limit 1 --confirm-publish true
```

Why this is still safe:

- `confirm_publish=true` is required before the publisher touches the real WeChat service
- `WECHAT_PUBLISH_MODE=real` must also be set
- review must be `approved`
- with `WECHAT_AUTO_SUBMIT_PUBLISH=false`, the flow stops at draft creation

## One-Line Command Mode

Natural-language command parsing is intentionally lightweight right now. It only extracts:

- `mode`
- `limit`
- `confirm_publish`

Example:

```powershell
$env:FEISHU_SOURCE_MODE='real'
& 'C:\Program Files\AutoClaw\resources\python\python.exe' `
  '.\tasks\run_claw_command.py' `
  'Publish the latest Feishu article to WeChat, mode=real, confirm_publish=true, limit=1'
```

This is a CLI wrapper, not a real bot message trigger yet.

## Publish Queue And Status Sync

These entrypoints are available now:

```powershell
& 'C:\Program Files\AutoClaw\resources\python\python.exe' `
  '.\tasks\run_publish_queue.py' `
  --mode real --limit 1 --confirm-publish false
```

Safe behavior:

- `confirm_publish=false` means preview only
- `confirm_publish=true` with `WECHAT_AUTO_SUBMIT_PUBLISH=false` means create a real draft only
- `confirm_publish=true` with `WECHAT_AUTO_SUBMIT_PUBLISH=true` means submit the real draft for publish

```powershell
& 'C:\Program Files\AutoClaw\resources\python\python.exe' `
  '.\tasks\run_sync_status.py' `
  --mode real --limit 1
```

`run_sync_status.py` uses `publish_id` to query WeChat async publish status and then writes `publish_status`, `publish_url`, and `content_status` back into Feishu.

## Manual Publish Fallback

If your current WeChat account can create real drafts but cannot call `freepublish/submit`, you can still use a stable semi-automatic flow:

## HTTP API (n8n orchestration)

The repo now exposes a minimal HTTP API for orchestration. Start the API server:

```powershell
& 'C:\Program Files\Python311\python.exe' -m pip install -r '.\requirements-api.txt'

& 'C:\Program Files\AutoClaw\resources\python\python.exe' `
  '.\tasks\run_api_server.py'
```

Optional auth and binding:

```powershell
$env:WECHAT_AGENT_API_HOST='127.0.0.1'
$env:WECHAT_AGENT_API_PORT='8088'
$env:WECHAT_AGENT_API_TOKEN='your_token'
```

When `WECHAT_AGENT_API_TOKEN` is set, requests must include:

```
Authorization: Bearer your_token
```

### Endpoints

- `POST /generate-draft`
- `POST /ingest-draft`
- `POST /create-draft`
- `POST /submit-publish`
- `POST /sync-status`
- `POST /mark-manual-publish`
- `POST /get-record`
- `GET /health`

### Example payload

```json
{"record_id":"rec_xxx","source_mode":"real"}
```

Coze or any external generator can ingest a prepared draft through:

```json
{
  "record_id": "rec_xxx",
  "source_mode": "real",
  "title": "Generated title",
  "summary": "Generated summary",
  "markdown": "# Generated title\n\nGenerated markdown body",
  "cover_prompt": "Optional cover prompt",
  "review_status": "approved",
  "review_notes": ["Generated by external workflow"]
}
```

### Example curl

```powershell
curl -X POST "http://127.0.0.1:8088/generate-draft" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer your_token" `
  -d "{\"record_id\":\"rec_xxx\",\"source_mode\":\"real\"}"
```

## n8n workflow templates

Import-ready workflow templates are available in:

- `automation/n8n/workflows/01-generate-draft.json`
- `automation/n8n/workflows/02-create-and-submit.json`
- `automation/n8n/workflows/03-sync-status.json`

Supporting notes are in:

- `automation/n8n/README.md`

## Coze + n8n + wechat-article-agent

Recommended production role split:

- `Coze`
  - natural-language trigger
  - title / summary / markdown generation
  - review hints
- `n8n`
  - scheduling
  - retries
  - alerts
  - calls local HTTP API
- `wechat-article-agent`
  - Feishu mapping
  - WeChat draft/create/publish
  - publish status sync

Suggested flow:

1. n8n fetches one pending record
2. Coze generates structured content
3. n8n calls `/ingest-draft`
4. n8n calls `/create-draft`
5. n8n calls `/submit-publish`
6. n8n calls `/sync-status`

1. Run the normal pipeline to create a real draft.
2. Open the WeChat MP backend and publish the draft manually.
3. Copy the final article URL.
4. Write the final result back into Feishu with this helper script:

```powershell
& 'C:\Program Files\AutoClaw\resources\python\python.exe' `
  '.\tasks\run_mark_manual_publish.py' `
  --mode real `
  --record-id recve0BoTWMyrb `
  --publish-status published `
  --publish-url 'https://mp.weixin.qq.com/s/example'
```

This updates:

- `内容状态 ContentStatus`
- `发布状态 PublishStatus`
- `发布链接 PublishUrl`
- `草稿ID DraftId`
- `处理时间 ProcessedAt`

This lets the project keep running in a half-automatic mode while certification or publish capability is pending.

## Outputs

Local outputs are written to `data/drafts/`.

Tracked sample outputs:

- `mock_output.md`
- `mock_output.html`
- `mock_review.json`
- `mock_publish_result.json`

Real-mode runs use the Feishu record id as the file prefix, for example:

- `recve0BoTWMyrb_output.md`
- `recve0BoTWMyrb_output.html`
- `recve0BoTWMyrb_output_review.json`
- `recve0BoTWMyrb_output_publish_result.json`

These files are useful for smoke tests, HTML inspection, and rollback/debug traces.

## Known Risks

- some WeChat accounts can create drafts but still lack the `freepublish` capability
- current `LLMService` is template-based, not production-grade generation
- current `ReviewAgent` is too weak for unattended publishing
- cover generation is still a TODO

## Recommended Next Steps

1. Validate `freepublish/submit` on an eligible certified WeChat account.
2. Keep the manual publish fallback available for non-eligible accounts.
3. Replace the placeholder `LLMService` with a real generation backend.
4. Strengthen `ReviewAgent` before enabling unattended publishing.
5. Add the real bot trigger layer on top of the existing CLI entrypoint.
