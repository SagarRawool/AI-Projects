from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from backend.app.config import (
    load_settings,
    save_settings,
    get_masked_settings,
    AppSettings,
    MASK
)
from backend.app.services.jira_client import (
    fetch_jira_ticket,
    NormalizedTicket,
    test_jira_connection_diagnostics
)
from backend.app.services.llm_client import generate_test_plan, get_ollama_models
from backend.app.services.template_parser import parse_template_upload
from backend.app.services.test_plan_prompt import SYSTEM_PROMPT, build_user_prompt

router = APIRouter(prefix="/api", tags=["API"])


class GenerateRequest(BaseModel):
    issue_key: str
    template_override: Optional[str] = None


class GenerateResponse(BaseModel):
    ticket: NormalizedTicket
    test_plan: str


@router.get("/settings")
def get_settings():
    """Retrieve current application configuration with secrets masked."""
    return get_masked_settings()


@router.post("/settings")
def update_settings(payload: Dict[str, Any]):
    """Update application configuration while safely preserving masked secrets."""
    try:
        updated = save_settings(payload)
        return get_masked_settings()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save settings: {str(e)}")


@router.post("/settings/template-upload")
async def upload_template(file: UploadFile = File(...)):
    """Upload custom test plan template (PDF, TXT, or MD), extract text, and save to settings."""
    extracted_text = await parse_template_upload(file)

    current_settings = load_settings().model_dump()
    current_settings["template"] = {
        "type": "custom",
        "source_filename": file.filename,
        "content": extracted_text
    }
    save_settings(current_settings)

    return {
        "message": f"Successfully extracted template from '{file.filename}'",
        "source_filename": file.filename,
        "length": len(extracted_text),
        "content": extracted_text
    }


@router.post("/jira/test-connection")
def test_connection(payload: Optional[Dict[str, Any]] = None):
    """
    Test connectivity to Jira using provided or saved credentials.
    Returns diagnostic details explaining connection success or specific failure reason.
    """
    settings = load_settings()
    jira_cfg = settings.jira.model_dump()

    # If parameters were sent in request body, merge them
    if payload:
        incoming_jira = payload.get("jira") or payload
        for key in ("base_url", "auth_type", "email", "api_token"):
            if key in incoming_jira and incoming_jira[key] is not None:
                val = str(incoming_jira[key]).strip()
                if key == "api_token" and val == MASK:
                    # Keep stored raw secret
                    continue
                jira_cfg[key] = val

    return test_jira_connection_diagnostics(jira_cfg)


@router.get("/jira/{issue_key}", response_model=NormalizedTicket)
def get_jira_ticket(issue_key: str):
    """Fetch and normalize Jira ticket details with ADF flattened to plain text."""
    settings = load_settings()
    return fetch_jira_ticket(issue_key, settings.jira.model_dump())


@router.post("/generate", response_model=GenerateResponse)
def generate_plan(payload: GenerateRequest):
    """
    Orchestrates the full generation pipeline:
    1. Fetch Jira ticket details.
    2. Build context-grounded prompt using active template.
    3. Invoke configured LLM (Groq Cloud or Ollama Local).
    4. Return ticket and test plan.
    """
    settings = load_settings()

    # 1. Fetch Ticket
    ticket = fetch_jira_ticket(payload.issue_key, settings.jira.model_dump())

    # 2. Determine Template
    active_template = payload.template_override
    if not active_template and settings.template.type == "custom":
        active_template = settings.template.content

    # 3. Build Prompt
    user_prompt = build_user_prompt(ticket, active_template)

    # 4. Generate with LLM
    test_plan = generate_test_plan(
        settings.llm.model_dump(),
        SYSTEM_PROMPT,
        user_prompt,
        ticket.key
    )

    return GenerateResponse(ticket=ticket, test_plan=test_plan)


@router.get("/ollama/models")
def list_models():
    """Query local Ollama server for installed models."""
    settings = load_settings()
    base_url = settings.llm.ollama_base_url
    models = get_ollama_models(base_url)
    return {"models": models}

