# wechat-article-agent

Minimal local skeleton for generating WeChat article drafts with a fully offline mock pipeline.

## Current Status

This project is currently in mock mode only.

- `run_generate_draft.py` uses a local mock Feishu record.
- `WriterAgent`, `LLMService`, `ReviewAgent`, `FormatterAgent`, and `PublisherAgent` all run locally.
- No real WeChat API or Feishu API calls are made.
- Publish and sync flows are dry-run placeholders.

## Project Layout

- `mock_pipeline.py`: local mock pipeline and HTML formatting logic
- `tasks/run_generate_draft.py`: generate mock markdown, HTML, review JSON, and publish dry-run JSON
- `tasks/run_publish_queue.py`: publish queue placeholder
- `tasks/run_sync_status.py`: publish status sync placeholder
- `data/drafts/`: generated mock outputs

## Python Note

The system default `python` on this machine is currently unreliable and may fail with:

```text
No module named 'encodings'
```

Use this temporary interpreter instead:

```powershell
C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe
```

## Run The Mock Smoke Test

From the project root:

```powershell
Set-Location 'D:\Administrator\Documents\电脑b\ai视频\手机号\可视化龙虾\wechat-article-agent'
```

Generate the draft and output files:

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_generate_draft.py'
```

Run the publish queue placeholder:

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_publish_queue.py'
```

Run the status sync placeholder:

```powershell
& 'C:\Users\Administrator\AppData\Local\Temp\python-3.11.5-embed\runtime\python.exe' `
  '.\tasks\run_sync_status.py'
```

## Expected Outputs

After running `run_generate_draft.py`, these files should appear in `data/drafts/`:

- `mock_output.md`
- `mock_output.html`
- `mock_review.json`
- `mock_publish_result.json`

## What The Mock Flow Verifies

- mock record ingestion works
- writer flow calls the local `LLMService` skeleton
- review result is produced as `approved` or `needs_manual_check`
- markdown is converted into HTML
- publish flow returns a dry-run payload instead of sending anything externally

## Next Steps

- replace the mock Feishu record with real upstream data loading
- swap the local `LLMService` skeleton for a real Codex CLI or API-backed generator
- add a real markdown service if richer formatting is needed
- implement real publish queue handling
- implement real publish status sync
- repair the system Python installation so `python ...` works without the temporary interpreter
