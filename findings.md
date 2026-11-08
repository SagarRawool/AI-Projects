# Findings & Technical Research

## 1. Specification Analysis (`prompt/prompt.md`)
- **Application:** "Intelligent Test Plan Agent" — local full-stack FastAPI app with static frontend.
- **Frontend Architecture:** Dark-themed single-page app in `frontend/index.html` (zero build step, served via FastAPI `StaticFiles`).
- **Two Core Tabs:**
  1. **Generate Tab:** Fetch Jira ticket -> Render ticket summary card -> Generate test plan via LLM -> Preview in `<pre>` block -> Download Markdown (`test-plan-{KEY}.md`).
  2. **Settings Tab:** Jira connection setup (URL, email, token, auth type) -> LLM provider selection (Groq vs Ollama) -> Template management (upload PDF/TXT/MD or paste text) -> Save settings.
- **Persistence:** Local JSON file in `data/settings.json`. Secrets masked as `********` when read, preserved if not updated.

## 2. Jira REST API & ADF Handling
- **Endpoint:** `GET {base}/rest/api/3/issue/{issueKey}?fields=summary,description,comment,issuetype,priority,labels,status,assignee,reporter,fixVersions,components`
- **Authentication:**
  - Cloud: Basic Auth using `requests.auth.HTTPBasicAuth(email, api_token)`
  - Server / DC: Bearer token using `Authorization: Bearer {token}`
- **Atlassian Document Format (ADF):**
  - Cloud returns description and comments as JSON tree (`doc -> paragraph / bulletList / heading -> text / hardBreak`).
  - Required: A deterministic recursive flattener to extract clean plain text / Markdown from ADF structures, with fallback for plain text strings (Server/DC).
- **Error Mapping:**
  - 401: "Invalid Jira credentials or expired token."
  - 404: "Issue key '{issueKey}' not found in Jira."
  - 502/Network: "Unable to reach Jira server at {base_url}."

## 3. LLM Dispatch Architecture
- **Groq Cloud:**
  - SDK: `groq`
  - Model: `llama-3.3-70b-versatile` (configurable)
  - Settings: `temperature=0.4`, `max_tokens=4096`
- **Ollama Local:**
  - REST Endpoint: `POST {ollama_base_url}/api/chat`
  - Tag Discovery: `GET {ollama_base_url}/api/tags`
  - Payload: `{"model": model, "messages": [...], "stream": false, "options": {"temperature": 0.4}}`
- **System Prompt & Generation Rules:**
  - Exact adherence to 12 sections (or uploaded template).
  - Grounding in Jira ticket details (no generic placeholder text).
  - Relative milestone schedules (e.g., "Day 1–2: Test Setup & Smoke Testing").
  - Clean Markdown output with zero conversational preambles.

## 4. Dependencies & Libraries
- Python 3.14.4 detected in environment.
- Installed: `fastapi`, `uvicorn`, `pydantic`, `requests`, `python-dotenv`, `pypdf`.
- Additional requirements needed: `groq`, `pydantic-settings`, `httpx`.
