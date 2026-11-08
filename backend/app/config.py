import json
import os
from pathlib import Path
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# Locate data directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
MASK = "********"


class JiraSettings(BaseModel):
    base_url: str = Field(default="", description="Base URL of Jira instance")
    auth_type: Literal["basic", "bearer"] = Field(default="basic", description="Auth type")
    email: str = Field(default="", description="Account email for basic auth")
    api_token: str = Field(default="", description="Atlassian API token or Bearer PAT")


class LLMSettings(BaseModel):
    provider: Literal["groq", "ollama"] = Field(default="groq", description="Active LLM provider")
    groq_api_key: str = Field(default="", description="Groq API Key")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq Model")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama Base URL")
    ollama_model: str = Field(default="llama3.1", description="Ollama Model")


class TemplateSettings(BaseModel):
    type: Literal["default", "custom"] = Field(default="default", description="Template source type")
    source_filename: Optional[str] = Field(default=None, description="Uploaded file name")
    content: str = Field(default="", description="Custom template text")


class AppSettings(BaseModel):
    jira: JiraSettings = Field(default_factory=JiraSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    template: TemplateSettings = Field(default_factory=TemplateSettings)


def get_default_settings() -> AppSettings:
    return AppSettings()


def load_settings() -> AppSettings:
    """Loads settings from data/settings.json, merging with defaults."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        defaults = get_default_settings()
        save_settings(defaults.model_dump())
        return defaults

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppSettings.model_validate(data)
    except Exception:
        # Fallback to default if file is corrupted
        defaults = get_default_settings()
        return defaults


def get_masked_settings() -> Dict[str, Any]:
    """Returns settings with sensitive credentials masked."""
    settings = load_settings()
    data = settings.model_dump()

    # Mask Jira API token
    if data["jira"].get("api_token"):
        data["jira"]["api_token"] = MASK

    # Mask Groq API key
    if data["llm"].get("groq_api_key"):
        data["llm"]["groq_api_key"] = MASK

    return data


def save_settings(incoming: Dict[str, Any]) -> AppSettings:
    """
    Saves incoming settings.
    If masked values ('********') are provided for secrets, preserves existing stored secrets.
    """
    current = load_settings().model_dump()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Preserve Jira secret if incoming is masked
    if "jira" in incoming:
        incoming_jira_token = incoming["jira"].get("api_token")
        if incoming_jira_token == MASK:
            incoming["jira"]["api_token"] = current["jira"].get("api_token", "")

    # Preserve Groq secret if incoming is masked
    if "llm" in incoming:
        incoming_groq_key = incoming["llm"].get("groq_api_key")
        if incoming_groq_key == MASK:
            incoming["llm"]["groq_api_key"] = current["llm"].get("groq_api_key", "")

    # Validate against AppSettings model
    validated = AppSettings.model_validate(incoming)

    # Write to file
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(validated.model_dump(), f, indent=2)

    return validated

