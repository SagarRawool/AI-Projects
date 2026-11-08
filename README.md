# Intelligent Test Plan Agent (Jira Integration)

An intelligent, deterministic web application that transforms Jira user stories and epics into comprehensive, production-grade QA Test Plans using modern LLMs (Groq Cloud or Local Ollama).

---

## 🏗️ Architecture Diagram

```
+-------------------------------------------------------------------------+
|                        Frontend Single Page App                         |
|                     (HTML5 / CSS3 / Vanilla JS)                         |
|            +-----------------------+------------------------+           |
|            |     Generate Tab      |      Settings Tab      |           |
|            +-----------------------+------------------------+           |
+------------------------------------+------------------------------------+
                                     | HTTP REST
                                     v
+-------------------------------------------------------------------------+
|                    FastAPI Application (Port 8000)                      |
|                                                                         |
|  [GET/POST /api/settings]              [POST /api/settings/template]    |
|  [GET /api/jira/{key}]                 [POST /api/generate]             |
|  [GET /api/ollama/models]              [StaticFiles / -> index.html]    |
+-------------------+--------------------------------+--------------------+
                    |                                |
         +----------v-----------+         +----------v-----------+
         |   Jira Integration   |         |   Prompt & Template   |
         |  (v3/v2 REST + ADF)  |         | (IEEE 12-Section/PDF)|
         +----------+-----------+         +----------+-----------+
                    |                                |
                    +---------------+----------------+
                                    |
                                    v
                     +------------------------------+
                     |      LLM Routing Engine      |
                     |  +------------------------+  |
                     |  |  Groq Cloud (Fast)     |  |
                     |  |  Ollama Local (Offline)|  |
                     |  +------------------------+  |
                     +------------------------------+
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Application
```bash
uvicorn backend.app.main:app --reload --port 8000
```

Open your browser at: **[http://localhost:8000](http://localhost:8000)**

---

## ⚙️ Configuration Reference

| Setting | Description | Default |
| :--- | :--- | :--- |
| `jira.base_url` | Jira instance base URL | `https://your-domain.atlassian.net` |
| `jira.auth_type` | Auth method (`basic` for Cloud, `bearer` for DC) | `basic` |
| `jira.email` | Jira account email | `""` |
| `jira.api_token` | Jira Atlassian API Token or Personal Access Token | `""` (Masked as `********`) |
| `llm.provider` | Selected LLM backend (`groq` or `ollama`) | `groq` |
| `llm.groq_api_key`| Groq API key from console.groq.com | `""` (Masked as `********`) |
| `llm.groq_model` | Groq inference model | `llama-3.3-70b-versatile` |
| `llm.ollama_base_url` | Base URL of local Ollama server | `http://localhost:11434` |
| `llm.ollama_model`| Local Ollama model name | `llama3.1` |
| `template.type` | Active template (`default` or `custom`) | `default` |

All settings persist in `data/settings.json`. Secrets are masked when returned via the UI.

---

## 🔒 100% Fully-Local Operation via Ollama

Run completely offline with zero external cloud dependencies:

1. **Install and run Ollama:**
   ```bash
   ollama serve
   ```
2. **Pull model:**
   ```bash
   ollama pull llama3.1
   ```
3. In the application **Settings Tab**:
   - Set **Active Provider** to `Ollama (Local, Private)`.
   - Click **List Models** or specify `llama3.1`.
   - Click **Save Settings**.
4. Test with demo ticket `VM01` or connect to your Jira instance.

---

## 📄 Custom Test Plan Templates

- **Default IEEE Template:** 12 industry-standard sections covering Scope, Strategy, Environment, Test Data, Entry/Exit Criteria, Milestones, and Risk Mitigation.
- **Custom Uploads:** Upload `.pdf` (e.g. `Template/TestPlan Template.pdf`), `.txt`, or `.md` in the Settings tab. The system extracts headings and strictly instructs the LLM to adhere to the custom structure.

