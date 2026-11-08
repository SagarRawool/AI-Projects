#!/usr/bin/env python3
"""
Jira Link Handshake Verifier (Phase 2: Link)
Deterministic verification tool for Jira Cloud and Jira Server/DC connectivity.
Supports both live API handshakes and deterministic mock validation.
"""

import os
import sys
import argparse
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment configuration
load_dotenv()


def mock_handshake() -> bool:
    """Deterministic offline handshake simulation for testing and local dev."""
    print("========================================")
    print("   JIRA LINK HANDSHAKE (MOCK MODE)      ")
    print("========================================")
    print("[INFO] Simulating Jira Connectivity Handshake...")
    print("[INFO] Base URL: https://mock-jira.atlassian.net")
    print("[INFO] Auth Protocol: Basic Auth (API Token) / Bearer PAT")
    print("[PASS] Endpoint /rest/api/3/serverInfo responded status 200")
    print("       - Server Title: Jira Cloud Mock Instance")
    print("       - Version: 1001.0.0-SNAPSHOT")
    print("[PASS] Endpoint /rest/api/3/myself responded status 200")
    print("       - Authenticated User: QA Automation Engineer (qa-bot)")
    print("       - Email: qa-bot@company.com")
    print("       - Active: True")
    print("========================================")
    print("[SUCCESS] Mock Link Handshake SUCCESSFUL. Environment ready.")
    print("========================================")
    return True


def verify_jira_connection(force_live: bool = False, force_mock: bool = False) -> bool:
    """Verifies live or mock Jira API connection."""
    mock_mode_env = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")

    if force_mock or (mock_mode_env and not force_live):
        return mock_handshake()

    base_url = os.getenv("JIRA_BASE_URL", "").strip().rstrip("/")
    auth_type = os.getenv("JIRA_AUTH_TYPE", "basic").strip().lower()
    email = os.getenv("JIRA_EMAIL", "").strip()
    api_token = os.getenv("JIRA_API_TOKEN", "").strip()
    pat = os.getenv("JIRA_PAT", "").strip()

    print("========================================")
    print("   JIRA CONNECTIVITY HANDSHAKE (LIVE)   ")
    print("========================================")

    # Validate configuration
    if not base_url or "your-domain" in base_url or "yourcompany" in base_url:
        print("[ERROR] JIRA_BASE_URL is not properly configured in .env.")
        print("        Expected a valid Jira URL (e.g. https://your-org.atlassian.net)")
        print("        Tip: Use --mock to run in mock/offline mode.")
        return False

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    auth = None

    if auth_type == "bearer" or pat:
        token = pat or api_token
        if not token or "your_" in token:
            print("[ERROR] JIRA_PAT is missing or contains placeholder values.")
            return False
        headers["Authorization"] = f"Bearer {token}"
    else:
        if not email or "your_email" in email or not api_token or "your_" in api_token:
            print("[ERROR] JIRA_EMAIL or JIRA_API_TOKEN is missing or contains placeholders.")
            print("        Tip: Provide real credentials in .env or run with --mock.")
            return False
        auth = HTTPBasicAuth(email, api_token)

    # Endpoints to check
    # Try Jira Cloud v3 first, fallback to v2
    endpoints_to_test = [
        f"{base_url}/rest/api/3/myself",
        f"{base_url}/rest/api/2/myself"
    ]

    print(f"Connecting to: {base_url} ...")
    authenticated = False
    user_data = None

    for endpoint in endpoints_to_test:
        try:
            resp = requests.get(endpoint, headers=headers, auth=auth, timeout=10)
            if resp.status_code == 200:
                user_data = resp.json()
                authenticated = True
                break
            elif resp.status_code in (401, 403):
                print(f"[FAIL] Authentication failed ({resp.status_code}): Invalid credentials or insufficient permissions.")
                print(f"       Response: {resp.text[:200]}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"[WARN] Connection to {endpoint} failed: {e}")

    if not authenticated:
        print("[FAIL] Unable to reach Jira REST API myself endpoint.")
        return False

    display_name = user_data.get("displayName", "N/A")
    user_email = user_data.get("emailAddress", email or "N/A")
    account_id = user_data.get("accountId", user_data.get("name", "N/A"))

    print("[PASS] Authentication Successful:")
    print(f"       - Authenticated User: {display_name} ({account_id})")
    print(f"       - Email: {user_email}")
    print("========================================")
    print("[SUCCESS] Link Handshake SUCCESSFUL. Ready for Phase 3: Architect.")
    print("========================================")
    return True


def main():
    parser = argparse.ArgumentParser(description="Verify Jira Link Handshake")
    parser.add_argument("--mock", action="store_true", help="Force mock verification mode")
    parser.add_argument("--live", action="store_true", help="Force live verification mode against .env")
    args = parser.parse_args()

    success = verify_jira_connection(force_live=args.live, force_mock=args.mock)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

