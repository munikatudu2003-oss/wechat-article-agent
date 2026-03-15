# wechat-article-agent

Minimal local skeleton for an automated WeChat article pipeline.

This repository is currently focused on an offline mock workflow so the full content chain can be verified before any real Feishu or WeChat integration is added.

## Goal

The long-term target is a full article automation flow:

1. Read article tasks from Feishu tables.
2. Generate article drafts with an LLM.
3. Convert markdown into publishable HTML.
4. Review article quality automatically.
5. Prepare WeChat draft publishing results.
6. Later add real publish queue handling and publish status sync.

## Current Status

What is already working:

- local mock draft generation
- markdown output
- HTML output
- review result output
- publisher dry-run output
- switchable `FeishuService` entrypoint with `mock` and `real` modes
- real-mode pending record listing and record status write-back skeleton
- placeholder publish queue script
- placeholder publish status sync script

What is not implemented yet:

- fully validated live Feishu field mapping against your production table
- real WeChat API publishing
- real publish status sync
- cover generation beyond a TODO placeholder
- Codex CLI or API-backed article generation

## Repository Layout

This repository is intentionally small right now, but the code is now split into clearer modules:

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
- `models/`
  - shared dataclasses for article tasks, drafts, and review results
- `utils/`
  - small helpers such as time formatting
- `config/`
  - project paths and constants
- `tasks/run_generate_draft.py`
  - runs the end-to-end mock draft flow
- `tasks/run_publish_queue.py`
  - placeholder publish queue entrypoint
- `tasks/run_sync_status.py`
  - placeholder status sync entrypoint
- `data/drafts/`
  - generated mock outputs
- `.env.example`
  - example environment variables for Feishu mode switching

## Mock Flow

```text
Mock Feishu record
    ->
WriterAgent + LLMService
    ->
Markdown draft
    ->
FormatterAgent
    ->
HTML
    ->
ReviewAgent
    ->
approved / needs_manual_check
    ->
PublisherAgent dry_run
    ->
mock_output.md
mock_output.html
mock_review.json
mock_publish_result.json
```

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
Get-Location
```

Generate the full mock draft flow:

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_generate_draft.py'
```

## Switch Feishu Between Mock And Real Mode

By default, `run_generate_draft.py` uses:

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

Run the publish queue placeholder:

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_publish_queue.py'
```

Run the publish status sync placeholder:

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
- publish preparation is simulated without any real API call
- real-mode records can be read and updated without changing the rest of the pipeline

## Git Status

This repository has already been initialized and pushed:

- branch: `main`
- initial commit: `4fcdcec init wechat-article-agent mock skeleton`
- remote: `https://github.com/munikatudu2003-oss/wechat-article-agent.git`

## Risks And Current Limits

- the default Python installation on this machine is not stable yet
- all publishing is still dry-run only
- real Feishu mode still needs your actual credentials and table schema
- there is no real WeChat draft creation yet
- the current repository is a minimal skeleton, not a full production implementation

## Next Steps

Recommended order:

1. Repair the default Python environment.
2. Validate `real` Feishu mode against your actual bitable schema.
3. Swap the local `LLMService` skeleton for a real content generator.
4. Add a richer markdown/HTML formatting layer if needed.
5. Implement real WeChat draft publishing.
6. Implement real publish queue and publish status sync.
7. Add a real cover generation step when the publish interface is ready.
