# Project Constitution: Intelligent Test Plan Agent (JIRA Integration)

## 1. Project Map & Identity
- **Project Name:** Intelligent Test Plan Agent
- **Specification Source:** `prompt/prompt.md`
- **Protocol:** B.L.A.S.T. (Blueprint, Link, Architect, Stylize, Trigger)
- **Architecture:** A.N.T. 3-Layer System
  - **Layer 1: Architecture (`architecture/`):** Technical SOPs for Jira parsing, LLM routing, template extraction, and API contracts.
  - **Layer 2: Navigation (`backend/app/routers/` & `backend/app/main.py`):** FastAPI orchestration routing between endpoints and business engines.
  - **Layer 3: Tools & Services (`backend/app/services/` & `tools/`):** Atomic, deterministic Python engines (`jira_client.py`, `llm_client.py`, `test_plan_prompt.py`, `config.py`).

---

## 2. Phase 1 Discovery Blueprint (The 5 Dimensions)

### 1. North Star
A complete, locally-runnable web application ("Intelligent Test Plan Agent") powered by a FastAPI backend and a dark-themed single-page frontend. It connects to Jira, extracts ticket details (including ADF flattening), accepts default or custom templates (PDF/text), prompts configured LLM providers (Groq Cloud or Ollama Local), and generates professional, actionable Markdown test plans without generic filler.

### 2. Integrations
- **Jira REST API (v3 / v2):** Cloud Basic auth (email + Atlassian token) and Server/DC Bearer token.
- **Groq Cloud API:** via `groq` Python SDK (default model: `llama-3.3-70b-versatile`, temperature 0.4, max_tokens 4096).
- **Ollama Local API:** via HTTP `POST {base}/api/chat` (default model: `llama3.1`, temperature 0.4) and `GET {base}/api/tags` for installed models.
- **PDF Extraction:** `pypdf` / `PyPDF2` for custom template parsing.

### 3. Source of Truth
- Primary ticket data: Jira REST API endpoint `GET /rest/api/3/issue/{issueKey}?fields=summary,description,comment,issuetype,priority,labels,status,assignee,reporter,fixVersions,components`.
- Local app configuration: `data/settings.json` (persisted locally, secrets masked).
- Template source: Default IEEE-style 12-section template or user-uploaded `testplan.pdf` / pasted text.

### 4. Delivery Payload
- Interactive single-page UI: Live rendered ticket card + rendered Markdown test plan in `<pre>` block.
- Downloadable deliverable: `test-plan-{KEY}.md` triggered directly from browser.
- Backend API response: Structured JSON `{ "ticket": {...}, "test_plan": "..." }`.

### 5. Behavioral Rules
- **Template Fidelity:** Follow template headings and numbering strictly without skipping or adding unrequested sections.
- **Ticket Grounding:** Ground every test scenario in actual ticket data (summary, description, comments, labels, priority). No generic filler.
- **Zero Leakage:** Never send user credentials or ticket data anywhere other than the configured Jira instance and configured LLM provider.
- **Secret Masking:** Jira token and Groq API key must always be returned as `********` by `GET /api/settings` and preserved if not modified.
- **Deterministic ADF Handling:** Convert Jira Atlassian Document Format (ADF) nodes recursively into clean, readable plain text.

---

## 3. Data Schemas (Locked Contracts)

### 3.1 Settings Configuration Schema (`data/settings.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SettingsConfig",
  "type": "object",
  "properties": {
    "jira": {
      "type": "object",
      "properties": {
        "base_url": { "type": "string" },
        "auth_type": { "type": "string", "enum": ["basic", "bearer"], "default": "basic" },
        "email": { "type": "string" },
        "api_token": { "type": "string" }
      },
      "required": ["base_url"]
    },
    "llm": {
      "type": "object",
      "properties": {
        "provider": { "type": "string", "enum": ["groq", "ollama"], "default": "groq" },
        "groq_api_key": { "type": "string" },
        "groq_model": { "type": "string", "default": "llama-3.3-70b-versatile" },
        "ollama_base_url": { "type": "string", "default": "http://localhost:11434" },
        "ollama_model": { "type": "string", "default": "llama3.1" }
      },
      "required": ["provider"]
    },
    "template": {
      "type": "object",
      "properties": {
        "type": { "type": "string", "enum": ["default", "custom"], "default": "default" },
        "source_filename": { "type": ["string", "null"] },
        "content": { "type": "string" }
      },
      "required": ["type"]
    }
  },
  "required": ["jira", "llm", "template"]
}
```

### 3.2 Normalized Jira Ticket Schema
```json
{
  "key": "PROJ-101",
  "summary": "User Authentication via OAuth2 and Passwordless OTP",
  "description": "As a user, I want to authenticate using OAuth2 or OTP so that my account remains secure.",
  "issuetype": "Story",
  "priority": "High",
  "status": "In Progress",
  "labels": ["auth", "security", "sprint-4"],
  "assignee": "Jane Doe",
  "reporter": "John Smith",
  "fixVersions": ["v1.4.0"],
  "components": ["Authentication", "Security"],
  "comments": [
    "AC1: OTP must expire within 5 minutes.",
    "AC2: Lock account after 3 invalid attempts."
  ]
}
```

### 3.3 Generation Request & Response Schema
```json
// POST /api/generate Request
{
  "issue_key": "PROJ-101",
  "template_override": null
}

// POST /api/generate Response
{
  "ticket": { /* Normalized Jira Ticket */ },
  "test_plan": "# TEST PLAN: PROJ-101\n\n## 1. Introduction\n..."
}
```

### 3.4 Ollama Models Schema
```json
// GET /api/ollama/models Response
{
  "models": ["llama3.1", "qwen2.5-coder", "mistral"]
}
```

---

## 4. Architectural Invariants
- Single port operation: FastAPI serves both `/api/...` endpoints and static frontend assets via `StaticFiles(..., html=True)`.
- Ephemeral workspace: All temporary uploaded files or intermediate testing artifacts belong in `.tmp/`.
- Local persistence: All settings persist in `data/settings.json`.
- Fail-safe Error Handling: Surface all Jira and LLM errors as clean HTTP JSON errors with friendly user messages for UI toast display.

## 5. Maintenance Log
- **2026-11-07:** Phase 1 Blueprint locked from `prompt/prompt.md`. Schemas and 5 discovery dimensions defined.
- **2026-11-08:** Phase 2 Link, Phase 3 Architect, Phase 4 Stylize, and Phase 5 Trigger completed. Full-stack application running on port 8000. All test suites verified.
- **2026-11-08:** Added Jira connection test endpoint (`POST /api/jira/test-connection`) and interactive diagnostics panel in Settings tab with root-cause explanations (HTTP 401, 403, 404, SSO HTML interception, SSL errors).
- **2026-11-08:** Verified live end-to-end Jira Cloud integration with ticket `SCRUM-5` and custom PDF template (`TestPlan Template.pdf`). Test plan generated successfully.
