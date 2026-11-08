# Task Plan: Intelligent Test Plan Agent

## Phase 1: B - Blueprint (Vision & Logic)
- [x] Synthesize requirements from `prompt/prompt.md` into the 5 Discovery Dimensions.
- [x] Formulate and lock JSON Data Schemas in `gemini.md` (`SettingsConfig`, `JiraTicket`, `GeneratePayload`, `OllamaModels`).
- [x] Conduct technical research (ADF recursive parsing, Groq client, Ollama REST, PDF text extraction).
- [x] User review & approval of Phase 1 Blueprint.

## Phase 2: L - Link (Connectivity & Environment)
- [x] Created `requirements.txt` and verified package dependencies (`groq`, `httpx`, `pydantic-settings`, `pypdf`, `fastapi`, `uvicorn`).
- [x] Created `data/settings.json` store with default configs and secret masking logic.
- [x] Verified Jira connection handshake with `tools/verify_jira_link.py`.

## Phase 3: A - Architect (The 3-Layer Build)
- [x] Layer 1: Architecture SOPs written in `architecture/`:
  - `01_jira_extraction_and_adf.md`
  - `02_llm_dispatch_and_routing.md`
  - `03_template_parsing_and_prompting.md`
- [x] Layer 3: Core backend services implemented:
  - `backend/app/config.py`: Settings manager with bidirectional secret masking.
  - `backend/app/services/jira_client.py`: Jira REST API client + recursive ADF flattener.
  - `backend/app/services/llm_client.py`: Unified Groq SDK & Ollama local client with fallback synthesizer.
  - `backend/app/services/test_plan_prompt.py`: 12-section IEEE template and prompt builder.
  - `backend/app/services/template_parser.py`: PDF/text custom template parser.
- [x] Layer 2: FastAPI routing and static file mounting:
  - `backend/app/routers/api.py`: All endpoints (`/api/settings`, `/api/jira/{key}`, `/api/generate`, `/api/ollama/models`).
  - `backend/app/main.py`: FastAPI server mounting static frontend on single port 8000.

## Phase 4: S - Stylize (Frontend Refinement & UI)
- [x] Built dark-themed single-page application in `frontend/index.html`:
  - Generate Tab: Jira ticket key fetch, ticket metadata badges, description, comment display, test plan generation, `<pre>` Markdown rendering, one-click copy, and `.md` file download.
  - Settings Tab: Jira connection options (Basic/Bearer), LLM provider (Groq vs Ollama with live model discovery), custom template upload (PDF/TXT/MD), and save with toast notifications.

## Phase 5: T - Trigger (Deployment & Verification)
- [x] Built and ran backend test suite `tools/test_app_endpoints.py` (all tests passed).
- [x] Added `POST /api/jira/test-connection` diagnostic test with root-cause explanations (HTTP 401, 403, 404, SSL, SSO HTML interception, Host unreachable).
- [x] Added interactive "🔌 Test Jira Connection" button and live diagnostic status panel to Settings tab.
- [x] Wrote `README.md` with ASCII architecture diagram, quick start guide, and Ollama offline instructions.
- [x] Started production FastAPI daemon server on `http://127.0.0.1:8000`.
- [x] Launched browser for immediate user interaction.
