**Prompt:**

Design and build a complete, locally-runnable web application called **"Intelligent Test Plan Agent"** with a FastAPI backend and a single-page HTML/CSS/JS frontend. The app converts Jira tickets into professional test plans using an LLM.

**Core Requirements:**

1. **Jira Integration** — A Settings page where the user enters: Jira Base URL (e.g. `https://your-domain.atlassian.net`), Jira account email, and an Atlassian API token. The backend must call `GET {base}/rest/api/3/issue/{issueKey}?fields=summary,description,comment,issuetype,priority,labels,status,assignee,reporter,fixVersions,components`, support both Basic auth (email + token) and Bearer token, flatten Atlassian Document Format (ADF) description/comments to plain text, and return a clean JSON ticket object with an error handled for 401/404/502 cases.

2. **LLM Providers (both must be supported, selectable in Settings)**:
   - **Groq (cloud)**: user enters their Groq API key (from console.groq.com) and model (default `llama-3.3-70b-versatile`); call via the `groq` Python SDK with temperature 0.4, max_tokens 4096.
   - **Ollama (local)**: user enters Ollama base URL (default `http://localhost:11434`) and model (default `llama3.1`); call `POST {base}/api/chat` with `stream: false`, temperature 0.4. Include a `GET /api/ollama/models` endpoint that lists installed models from `{base}/api/tags` so the user can pick from a "List" button in the UI.

3. **Test Plan Template** — Bundle a default IEEE-style 12-section template (Introduction, Test Objectives & Success Criteria, Scope [In/Out], Test Strategy [Levels, Types, Techniques], Test Environment, Test Data Requirements, Test Deliverables, Entry & Exit Criteria, Roles & Responsibilities, Schedule & Milestones, Risks & Mitigation, Approvals & Sign-off). Also allow the user to upload a `testplan.pdf` (extract text with PyPDF2) or paste template text in Settings; the uploaded template overrides the default, and the LLM must follow its exact headings and numbering.

4. **Prompting** — System prompt: "You are a senior QA engineer who writes professional, precise, and actionable software test plans…" with strict rules: follow the template structure exactly, ground every section in the Jira ticket (summary, description, labels, priority, comments), derive realistic in/out-of-scope items, propose concrete named test scenarios per level/type (no generic filler), use relative timelines (e.g. "Day 1–2: …"), use Markdown tables where useful, and output ONLY the test plan in Markdown with no preamble. User prompt includes the full template + ticket fields + description + up to 500 chars per comment.

5. **Settings Storage** — Persist all settings in a local `data/settings.json` (plain JSON, created at runtime); secrets (Jira token, Groq key) must be masked as `********` when returned by `GET /api/settings` and preserved when the client sends back the masked value on `POST /api/settings`.

6. **API Endpoints** — `GET/POST /api/settings`, `POST /api/settings/template-upload` (multipart file upload, PDF/TXT/MD), `GET /api/jira/{issue_key}`, `POST /api/generate` (fetch ticket → build prompt → call configured LLM → return `{ticket, test_plan}`), `GET /api/ollama/models`.

7. **Frontend UI** — A dark-themed single page (`index.html`, no build step) with two tabs:
   - **Generate**: input for Jira issue key (e.g. `VM01`) → "Fetch Ticket" button → rendered ticket card (key, summary, type/priority/status badges, labels, assignee, components, description excerpt) → "✨ Generate Test Plan" button → streaming-free display of the Markdown plan in a `<pre>` block → "Download .md" button that saves it as `test-plan-{KEY}.md`. Show inline success/error toast messages for every action.
   - **Settings**: sections for Jira Connection, LLM Provider (provider dropdown, active model readout, Groq key/model, Ollama URL/model + List button), and Template (file upload + textarea). A "Save Settings" button with confirmation toast.
   Serve the frontend via `app.mount("/", StaticFiles(..., html=True))` so the whole app runs on one port.

8. **Project Layout** — `requirements.txt` (fastapi, uvicorn, pydantic, pydantic-settings, httpx, python-multipart, PyPDF2, groq), `backend/app/main.py`, `backend/app/config.py` (settings load/save with defaults merge), `backend/app/routers/api.py`, `backend/app/services/jira_client.py`, `backend/app/services/llm_client.py` (unified Groq/Ollama dispatch), `backend/app/services/test_plan_prompt.py` (default template + `build_user_prompt`), `frontend/index.html`, and a `README.md` with quick start (`pip install -r requirements.txt` then `uvicorn backend.app.main:app --reload --port 8000`), a configuration table, an ASCII architecture diagram, and instructions for fully-local operation via Ollama.

All backend code must compile cleanly, all errors must surface as user-readable messages in the UI toasts, and nothing besides Jira and the selected LLM provider should ever receive user data.<!--  -->