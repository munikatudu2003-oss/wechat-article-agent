# wechat-article-agent

Minimal local skeleton for an automated WeChat article pipeline.

This repository now supports a local mock workflow, a real Feishu read and write-back path, and a gated WeChat publish entrypoint that only goes live when you explicitly confirm it.

## Goal

The long-term target is a full article automation flow:

1. Read article tasks from Feishu tables.
2. Generate article drafts with an LLM.
3. Convert markdown into publishable HTML.
4. Review article quality automatically.
5. Publish or submit drafts to WeChat Official Accounts.
6. Later add publish queue handling and publish status sync.

## Current Status

What is already working:

- local mock draft generation
- markdown output
- HTML output
- review result output
- publisher dry-run output
- switchable `FeishuService` entrypoint with `mock` and `real` modes
- real-mode pending record listing and record status write-back skeleton
- one-line command parsing through `tasks/run_claw_command.py`
- real publish gate that requires both `confirm_publish=true` and `WECHAT_PUBLISH_MODE=real`
- placeholder publish queue script
- placeholder publish status sync script

What is not implemented yet:

- fully validated live Feishu field mapping against your production table
- fully validated live WeChat publishing against your production credentials
- real publish status sync
- cover generation beyond a TODO placeholder
- Codex CLI or API-backed article generation

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
  - `WechatPublisherService`
- `models/`
  - shared dataclasses for article tasks and workflow results
- `utils/`
  - small helpers such as time formatting
- `config/`
  - project paths and constants
- `tasks/run_generate_draft.py`
  - runs the end-to-end draft flow in safe dry-run mode
- `tasks/run_claw_command.py`
  - runs the workflow from a single natural-language command
- `tasks/run_publish_queue.py`
  - placeholder publish queue entrypoint
- `tasks/run_sync_status.py`
  - placeholder status sync entrypoint
- `data/drafts/`
  - generated outputs
- `.env.example`
  - example environment variables for Feishu and WeChat mode switching

## Python Environment Note

The system default `python` on this machine is currently unreliable and may fail with:

```text
No module named 'encodings'
```

Use this temporary interpreter for local testing:

```powershell
C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe
```

## Run The Mock Smoke Test

Open a terminal in the repository root, then run:

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_generate_draft.py'
```

Run the one-line command entrypoint in mock mode:

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_claw_command.py' `
  'Generate the latest Feishu article, mode=mock, confirm_publish=false, limit=1'
```

## Switch Feishu Between Mock And Real Mode

By default, the workflow uses:

```powershell
$env:FEISHU_SOURCE_MODE='mock'
```

To prepare for real Feishu table reads, set:

```powershell
$env:FEISHU_SOURCE_MODE='real'
$env:FEISHU_APP_ID='your_app_id'
$env:FEISHU_APP_SECRET='your_app_secret'
$env:FEISHU_APP_TOKEN='your_bitable_app_token'
$env:FEISHU_TABLE_ID='your_table_id'
```

Optional settings:

```powershell
$env:FEISHU_VIEW_ID='your_view_id'
$env:FEISHU_PAGE_SIZE='1'
$env:FEISHU_FIELD_TITLE='ArticleTitle'
$env:FEISHU_FIELD_SUMMARY='ArticleSummary'
$env:FEISHU_FIELD_CATEGORY='Category'
$env:FEISHU_FIELD_KEYWORDS='Keywords'
$env:FEISHU_FIELD_REFERENCE='ReferenceMaterial'
$env:FEISHU_FIELD_WORD_COUNT='TargetWordCount'
```

Replace those field names with the real column names from your Feishu table.

In `real` mode, the service now:

- requests a tenant access token
- lists records from the configured bitable table
- filters pending records by content status unless disabled
- maps configured field names into the existing draft model
- writes generation results back into the source record
- keeps the rest of the pipeline unchanged

## Run The One-Line Command Workflow

Safe dry-run against the latest real Feishu record:

```powershell
$env:FEISHU_SOURCE_MODE='real'
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_claw_command.py' `
  'Generate the latest Feishu article, run WriterAgent, FormatterAgent, ReviewAgent, keep local backups, mode=real, confirm_publish=false, limit=1'
```

Real publish only after review approval:

```powershell
$env:FEISHU_SOURCE_MODE='real'
$env:WECHAT_PUBLISH_MODE='real'
$env:WECHAT_APP_ID='your_wechat_app_id'
$env:WECHAT_APP_SECRET='your_wechat_app_secret'
$env:WECHAT_THUMB_MEDIA_ID='your_thumb_media_id'
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_claw_command.py' `
  'Publish the latest Feishu article to WeChat, mode=real, confirm_publish=true, limit=1'
```

The real publish path is intentionally double-gated:

- `confirm_publish=true` must be present in the instruction
- `WECHAT_PUBLISH_MODE=real` must be set in the environment
- `ReviewAgent` must return `approved`

If any of those checks fail, the workflow will keep the generated files locally and skip the live WeChat publish request.

## Run The Placeholder Scripts

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_publish_queue.py'
```

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_sync_status.py'
```

## Expected Outputs

After running `run_generate_draft.py`, these files should exist in `data/drafts/`:

- `mock_output.md`
- `mock_output.html`
- `mock_review.json`
- `mock_publish_result.json`

In `real` mode, generated files use the record id as a prefix, for example:

- `rec_real_001_output.md`
- `rec_real_001_output.html`
- `rec_real_001_output_review.json`
- `rec_real_001_output_publish_result.json`

These outputs confirm:

- mock record ingestion works
- the writer flow runs locally
- markdown conversion works
- review status is produced
- publish preparation is simulated without any live API call unless both publish gates are enabled
- real-mode records can be read and updated without changing the rest of the pipeline

## Risks And Current Limits

- the default Python installation on this machine is not stable yet
- real Feishu mode still needs your actual credentials and table schema
- real publishing still needs your actual WeChat credentials and should be tested with a safe account first
- cover handling is still a placeholder and should be replaced before production publishing
- the current repository is a minimal skeleton, not a full production implementation

## Next Steps

Recommended order:

1. Repair the default Python environment.
2. Validate `real` Feishu mode against your actual bitable schema.
3. Validate the WeChat draft publish path with a safe test account and real thumb media id.
4. Swap the local `LLMService` skeleton for a real content generator.
5. Add a richer markdown and HTML formatting layer if needed.
6. Implement real publish queue and publish status sync.
7. Add a real cover generation step when the publish interface is ready.

## One-Click Publish (v1)

新增一键执行入口：

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_one_click_publish.py' `
  --mode mock --limit 1 --confirm-publish false
```

参数说明：

- `--mode mock|real`
- `--limit 1`
- `--confirm-publish true|false`（默认 `false`，安全 dry-run）

执行链路固定为：

- `WriterAgent -> FormatterAgent -> ReviewAgent -> PublisherAgent`

行为说明：

1. `confirm_publish=false`：只执行 dry-run，生成本地 markdown/html/review/publish JSON 备份，不调用真实公众号发布。
2. `confirm_publish=true`：只有当 `ReviewAgent` 返回 `approved` 才继续调用公众号发布逻辑。
3. 当 `ReviewAgent` 返回 `needs_manual_check`：终止发布并回写 Feishu 状态。
4. real 模式下会回写 Feishu 字段：`publish_status`、`review_status`、`draft_id/publish_id`、`publish_url`（若可用）。

真实发布示例：

```powershell
$env:FEISHU_SOURCE_MODE='real'
$env:WECHAT_PUBLISH_MODE='real'
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_one_click_publish.py' `
  --mode real --limit 1 --confirm-publish true
```

> 说明：当前版本 `publish_url` 仍依赖微信异步发布查询接口，代码中保留了 TODO。
