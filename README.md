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
- placeholder publish queue script
- placeholder publish status sync script

What is not implemented yet:

- real Feishu data loading
- real WeChat API publishing
- real publish status sync
- cover generation beyond a TODO placeholder
- Codex CLI or API-backed article generation

## Repository Layout

This repository is intentionally small right now:

- `mock_pipeline.py`
  - local mock record model
  - `LLMService`
  - `WriterAgent`
  - `ReviewAgent`
  - `FormatterAgent`
  - `PublisherAgent`
- `tasks/run_generate_draft.py`
  - runs the end-to-end mock draft flow
- `tasks/run_publish_queue.py`
  - placeholder publish queue entrypoint
- `tasks/run_sync_status.py`
  - placeholder status sync entrypoint
- `data/drafts/`
  - generated mock outputs

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

These outputs confirm:

- mock record ingestion works
- the writer flow runs locally
- markdown conversion works
- review status is produced
- publish preparation is simulated without any real API call

## Git Status

This repository has already been initialized and pushed:

- branch: `main`
- initial commit: `4fcdcec init wechat-article-agent mock skeleton`
- remote: `https://github.com/munikatudu2003-oss/wechat-article-agent.git`

## Risks And Current Limits

- the default Python installation on this machine is not stable yet
- all publishing is still dry-run only
- there is no real Feishu reader yet
- there is no real WeChat draft creation yet
- the current repository is a minimal skeleton, not a full production implementation

## Next Steps

Recommended order:

1. Repair the default Python environment.
2. Replace the mock record with real Feishu task loading.
3. Swap the local `LLMService` skeleton for a real content generator.
4. Add a richer markdown/HTML formatting layer if needed.
5. Implement real WeChat draft publishing.
6. Implement real publish queue and publish status sync.
7. Expand the repository into clearer modules such as `agents/`, `services/`, `utils/`, and `config/` when the real integrations begin.
