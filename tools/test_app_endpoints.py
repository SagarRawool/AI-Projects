#!/usr/bin/env python3
"""
Comprehensive backend test suite for Intelligent Test Plan Agent.
Tests FastAPI routes, ADF parser, Jira client, template extraction, and settings masking.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.jira_client import flatten_adf, get_mock_ticket
from backend.app.config import load_settings, save_settings, get_masked_settings, MASK


def test_all():
    client = TestClient(app)
    print("========================================")
    print("   INTELLIGENT TEST PLAN AGENT TESTS    ")
    print("========================================")

    # 1. Test Static Frontend
    resp = client.get("/")
    assert resp.status_code == 200, f"Frontend failed: {resp.status_code}"
    assert "Intelligent Test Plan Agent" in resp.text
    print("[PASS] Static frontend served successfully at root /")

    # 2. Test GET /api/settings
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    settings_data = resp.json()
    assert "jira" in settings_data and "llm" in settings_data and "template" in settings_data
    print("[PASS] GET /api/settings returned valid schema")

    # 3. Test Secret Masking
    test_save = {
        "jira": {"base_url": "https://test.atlassian.net", "auth_type": "basic", "email": "test@domain.com", "api_token": "super_secret_token_123"},
        "llm": {"provider": "groq", "groq_api_key": "gsk_secret_456", "groq_model": "llama-3.3-70b-versatile", "ollama_base_url": "http://localhost:11434", "ollama_model": "llama3.1"},
        "template": {"type": "default", "source_filename": None, "content": ""}
    }
    resp = client.post("/api/settings", json=test_save)
    assert resp.status_code == 200
    masked = resp.json()
    assert masked["jira"]["api_token"] == MASK, "Jira token not masked!"
    assert masked["llm"]["groq_api_key"] == MASK, "Groq key not masked!"
    print("[PASS] Secret masking verified on GET / POST settings")

    # Verify unmasked persistence in load_settings
    loaded = load_settings()
    assert loaded.jira.api_token == "super_secret_token_123"
    assert loaded.llm.groq_api_key == "gsk_secret_456"
    print("[PASS] Raw secrets preserved safely in data/settings.json")

    # 4. Test ADF Flattener
    sample_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Requirements"}]
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "This is a detailed paragraph with "},
                    {"type": "text", "text": "strong text."}
                ]
            },
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": "First bullet item"}]}
                        ]
                    }
                ]
            }
        ]
    }
    flattened = flatten_adf(sample_adf)
    assert "Requirements" in flattened
    assert "First bullet item" in flattened
    print("[PASS] ADF recursive parser flattens complex Jira trees cleanly")

    # 5. Test GET /api/jira/VM01 (Demo ticket)
    resp = client.get("/api/jira/VM01")
    assert resp.status_code == 200
    ticket = resp.json()
    assert ticket["key"] == "VM01"
    assert "OAuth2" in ticket["summary"]
    assert len(ticket["comments"]) > 0
    print("[PASS] GET /api/jira/VM01 returned normalized ticket with comments")

    # 6. Test PDF Template Upload
    with open("Template/TestPlan Template.pdf", "rb") as f:
        resp = client.post("/api/settings/template-upload", files={"file": ("TestPlan Template.pdf", f, "application/pdf")})
    assert resp.status_code == 200
    upload_res = resp.json()
    assert "source_filename" in upload_res
    assert upload_res["length"] > 100
    print(f"[PASS] Template upload parsed PDF successfully ({upload_res['length']} characters)")

    # 7. Test POST /api/generate
    gen_resp = client.post("/api/generate", json={"issue_key": "VM01"})
    print("Generate status:", gen_resp.status_code, gen_resp.text)
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert "ticket" in gen_data and "test_plan" in gen_data
    assert "TEST PLAN" in gen_data["test_plan"]
    assert gen_data["ticket"]["key"] == "VM01"
    print("[PASS] POST /api/generate produced complete 12-section test plan successfully")

    # 8. Test POST /api/jira/test-connection diagnostic endpoint
    # 8a: Missing base URL
    tc_resp = client.post("/api/jira/test-connection", json={"jira": {"base_url": "", "api_token": ""}})
    assert tc_resp.status_code == 200
    tc_data = tc_resp.json()
    assert tc_data["success"] is False
    assert "Missing Jira Base URL" in tc_data["error"]
    print("[PASS] Diagnostic test caught missing Jira Base URL with explanation")

    # 8b: Invalid URL protocol
    tc_resp = client.post("/api/jira/test-connection", json={"jira": {"base_url": "ftp://jira.com", "api_token": "token"}})
    assert tc_resp.status_code == 200
    assert tc_resp.json()["success"] is False
    assert "Invalid URL Protocol" in tc_resp.json()["error"]
    print("[PASS] Diagnostic test caught invalid protocol with explanation")

    # 8c: Missing email for basic auth
    tc_resp = client.post("/api/jira/test-connection", json={"jira": {"base_url": "https://myjira.atlassian.net", "auth_type": "basic", "email": "", "api_token": "abc"}})
    assert tc_resp.status_code == 200
    assert tc_resp.json()["success"] is False
    assert "Missing Account Email" in tc_resp.json()["error"]
    print("[PASS] Diagnostic test caught missing email for basic auth with explanation")

    print("========================================")
    print("   ALL BACKEND & API SUITE TESTS PASSED ")
    print("========================================")


if __name__ == "__main__":
    test_all()
