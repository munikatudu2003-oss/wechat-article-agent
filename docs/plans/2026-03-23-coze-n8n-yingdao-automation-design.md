# Coze + n8n + wechat-article-agent + Yingdao Integration Design

## Goal

Move `wechat-article-agent` from a script-first publish engine into the backend core of a larger automation system:

- `Coze` handles natural-language interaction and content generation
- `n8n` handles schedules, retries, branching, and notifications
- `wechat-article-agent` handles Feishu mapping, WeChat draft creation, publish submit, and status sync
- `Yingdao` only handles browser-only fallback steps when APIs are blocked

## Division of Responsibilities

### Coze

Use Coze for:

- user-facing command entry
- title generation
- summary generation
- markdown body generation
- review hints and notes

Do not use Coze as the source of truth for:

- publish state
- retries
- WeChat API side effects
- Feishu write-back

### n8n

Use n8n for:

- daily scheduled runs
- manual replay
- error workflow routing
- retry policy
- HTTP calls into the local API
- Feishu or email alerts

### wechat-article-agent

Use this repo as the durable publish core:

- resolve Feishu records
- write generated content back into Feishu
- create WeChat drafts
- submit publishes
- sync publish status and URL

### Yingdao

Only use Yingdao when a needed action has no stable API path, for example:

- browser-only WeChat console operations
- reading or clicking backend-only pages
- account-side fallback workflows

## API Contract Needed By Coze / n8n

The minimum external contract is:

- `POST /ingest-draft`
- `POST /create-draft`
- `POST /submit-publish`
- `POST /sync-status`
- `POST /mark-manual-publish`

`/ingest-draft` is the key bridge that allows external AI output to enter the publish engine without forcing `wechat-article-agent` to generate the content itself.

## Recommended Workflow

1. n8n selects one `pending` Feishu record.
2. n8n passes record context into Coze.
3. Coze returns:
   - `title`
   - `summary`
   - `markdown`
   - `review_status`
   - `review_notes`
4. n8n calls `/ingest-draft`.
5. n8n calls `/create-draft`.
6. If publish APIs are allowed, n8n calls `/submit-publish`.
7. n8n periodically calls `/sync-status`.
8. If API publish is blocked, n8n can trigger a Yingdao fallback flow instead.

## Why This Structure

- It keeps publish side effects inside one codebase.
- It makes Coze replaceable later.
- It keeps n8n as orchestration only.
- It prevents browser automation from becoming the primary system of record.

## Immediate Next Step

The repo should continue moving toward:

1. stable local API
2. importable n8n workflows
3. external AI ingestion
4. browser fallback only when APIs cannot complete the job
