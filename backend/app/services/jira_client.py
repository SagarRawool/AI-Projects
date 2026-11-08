import re
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from pydantic import BaseModel


def clean_jira_base_url(url: str) -> str:
    """
    Normalizes Jira Base URL by removing common user-pasted subpaths like /browse/, /jira/, /secure/, etc.
    """
    if not url:
        return ""
    cleaned = url.strip()
    # Remove trailing paths like /browse, /browse/, /browse/PROJ-1, /jira, /secure
    cleaned = re.sub(r"/(browse|jira|secure)(/.*)?$", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.rstrip("/")
    return cleaned


class NormalizedTicket(BaseModel):
    key: str
    summary: str
    description: str
    issuetype: str = "Story"
    priority: str = "Medium"
    status: str = "Open"
    labels: List[str] = []
    assignee: Optional[str] = "Unassigned"
    reporter: Optional[str] = "Unknown"
    fixVersions: List[str] = []
    components: List[str] = []
    comments: List[str] = []


def flatten_adf(node: Any) -> str:
    """
    Recursively flattens an Atlassian Document Format (ADF) node or string to plain text.
    """
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, (int, float, bool)):
        return str(node)

    if isinstance(node, list):
        return "".join(flatten_adf(item) for item in node)

    if isinstance(node, dict):
        node_type = node.get("type", "")
        content = node.get("content", [])

        if node_type == "text":
            return node.get("text", "")
        elif node_type == "hardBreak":
            return "\n"
        elif node_type == "paragraph":
            text = "".join(flatten_adf(child) for child in content).strip()
            return f"{text}\n\n" if text else ""
        elif node_type == "heading":
            level = node.get("attrs", {}).get("level", 2)
            prefix = "#" * level
            text = "".join(flatten_adf(child) for child in content).strip()
            return f"\n{prefix} {text}\n\n"
        elif node_type == "bulletList":
            items = []
            for item in content:
                item_text = "".join(flatten_adf(c) for c in item.get("content", [])).strip()
                if item_text:
                    items.append(f"- {item_text}")
            return "\n".join(items) + "\n\n"
        elif node_type == "orderedList":
            items = []
            for idx, item in enumerate(content, 1):
                item_text = "".join(flatten_adf(c) for c in item.get("content", [])).strip()
                if item_text:
                    items.append(f"{idx}. {item_text}")
            return "\n".join(items) + "\n\n"
        elif node_type == "codeBlock":
            lang = node.get("attrs", {}).get("language", "")
            code_text = "".join(flatten_adf(child) for child in content)
            return f"\n```{lang}\n{code_text}\n```\n\n"
        elif node_type == "blockquote":
            text = "".join(flatten_adf(child) for child in content).strip()
            return f"> {text}\n\n"
        elif content:
            return "".join(flatten_adf(child) for child in content)

    return ""


def get_mock_ticket(issue_key: str) -> NormalizedTicket:
    """Provides a realistic fallback mock ticket for testing or demo purposes (e.g. VM01)."""
    return NormalizedTicket(
        key=issue_key.upper(),
        summary=f"OAuth2 & Multi-Factor Authentication Redesign ({issue_key})",
        description=(
            "As an enterprise platform user, I want to authenticate using OAuth2.0 / OIDC and optional "
            "time-based OTP so that our organizational access meets SOC2 and ISO27001 compliance standards.\n\n"
            "Key Acceptance Criteria:\n"
            "1. User can login via Google, GitHub, or Microsoft Azure AD.\n"
            "2. Users with MFA enabled must enter a 6-digit TOTP within 30 seconds of issuance.\n"
            "3. 3 failed OTP attempts triggers a 15-minute lockout and email alert.\n"
            "4. Session tokens must be JWT with RS256 signature, 15-minute access token TTL, 7-day refresh token TTL.\n"
            "5. Rate limiting enforced: max 5 login requests per IP per minute."
        ),
        issuetype="Story",
        priority="High",
        status="In Progress",
        labels=["security", "authentication", "oauth2", "soc2"],
        assignee="Alex Taylor (Security QA Lead)",
        reporter="Samira Patel (Product Manager)",
        fixVersions=["v2.4.0-release"],
        components=["Auth-Service", "API-Gateway", "User-Management"],
        comments=[
            "Security Review (AC3 & AC5): Ensure Redis cluster handles rate limiting key expiry under load testing.",
            "PM Note: Staging environment identity provider sandbox credentials have been deployed to QA Vault.",
            "Dev Update: TOTP clock drift tolerance is set to +/- 1 window (30 seconds) per RFC 6238."
        ]
    )


def fetch_jira_ticket(issue_key: str, jira_cfg: Dict[str, Any]) -> NormalizedTicket:
    """
    Fetches ticket details from Jira REST API v3 / v2, flattens ADF,
    and returns a normalized ticket model.
    """
    issue_key = issue_key.strip().upper()
    base_url = clean_jira_base_url(jira_cfg.get("base_url") or "")
    auth_type = jira_cfg.get("auth_type", "basic").lower()
    email = (jira_cfg.get("email") or "").strip()
    api_token = (jira_cfg.get("api_token") or "").strip()

    # If Jira is not configured or user requests demo ticket (VM01 or DEMO-*), provide mock ticket
    if not base_url or issue_key.startswith("VM") or issue_key.startswith("DEMO") or not api_token:
        if not base_url and not (issue_key.startswith("VM") or issue_key.startswith("DEMO")):
            raise HTTPException(
                status_code=400,
                detail="Jira is not configured in Settings. Please set Jira Base URL and API token, or use 'VM01' for demo."
            )
        return get_mock_ticket(issue_key)

    fields_param = "summary,description,comment,issuetype,priority,labels,status,assignee,reporter,fixVersions,components"
    endpoints_to_try = [
        f"{base_url}/rest/api/3/issue/{issue_key}?fields={fields_param}",
        f"{base_url}/rest/api/2/issue/{issue_key}?fields={fields_param}"
    ]

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    auth = None
    if auth_type == "bearer":
        headers["Authorization"] = f"Bearer {api_token}"
    else:
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Jira email is required when using Basic Authentication."
            )
        auth = HTTPBasicAuth(email, api_token)

    resp = None
    last_error = None

    for endpoint in endpoints_to_try:
        try:
            resp = requests.get(endpoint, headers=headers, auth=auth, timeout=15, allow_redirects=True)
            # If redirected to a login/SSO web page
            if "text/html" in resp.headers.get("Content-Type", "").lower() or (resp.history and "/login" in resp.url):
                raise HTTPException(
                    status_code=401,
                    detail="Jira redirected to a web login page. Please check your Jira credentials and API token in Settings."
                )

            if resp.status_code == 200:
                break
            elif resp.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication failed. Please verify your Jira email and API token in Settings."
                )
            elif resp.status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access forbidden. Your account does not have permission to view Jira issue '{issue_key}'."
                )
            elif resp.status_code == 404:
                last_error = f"Jira issue '{issue_key}' was not found. Please check the issue key."
                continue
            else:
                last_error = f"Jira API returned error {resp.status_code}: {resp.text[:200]}"
        except HTTPException:
            raise
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"Unable to connect to Jira instance at {base_url}. Network error: {str(e)}"
            )

    if resp is None or resp.status_code != 200:
        raise HTTPException(
            status_code=404 if "not found" in str(last_error).lower() else 502,
            detail=last_error or f"Failed to fetch ticket {issue_key} from Jira."
        )

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=f"Jira at {base_url} returned an invalid or non-JSON response. Verify Jira Base URL and permissions."
        )

    fields = data.get("fields", {})

    # Flatten description (handles ADF or plain string)
    raw_desc = fields.get("description")
    clean_desc = flatten_adf(raw_desc).strip()

    # Flatten comments (truncate each to 500 chars)
    comments_data = fields.get("comment", {}).get("comments", [])
    clean_comments: List[str] = []
    for c in comments_data:
        body = c.get("body")
        flat_body = flatten_adf(body).strip()
        if flat_body:
            truncated = flat_body[:500]
            clean_comments.append(truncated)

    # Extract other fields
    summary = fields.get("summary", "")
    issuetype = fields.get("issuetype", {}).get("name", "Story")
    priority = fields.get("priority", {}).get("name", "Medium")
    status = fields.get("status", {}).get("name", "Open")
    labels = fields.get("labels", [])

    assignee_obj = fields.get("assignee")
    assignee = assignee_obj.get("displayName", "Unassigned") if assignee_obj else "Unassigned"

    reporter_obj = fields.get("reporter")
    reporter = reporter_obj.get("displayName", "Unknown") if reporter_obj else "Unknown"

    fix_versions = [v.get("name", "") for v in fields.get("fixVersions", []) if v.get("name")]
    components = [c.get("name", "") for c in fields.get("components", []) if c.get("name")]

    return NormalizedTicket(
        key=issue_key,
        summary=summary,
        description=clean_desc,
        issuetype=issuetype,
        priority=priority,
        status=status,
        labels=labels,
        assignee=assignee,
        reporter=reporter,
        fixVersions=fix_versions,
        components=components,
        comments=clean_comments
    )


def test_jira_connection_diagnostics(jira_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs an end-to-end diagnostic connectivity test to Jira.
    Returns structured results indicating success or exact root-cause failure explanation.
    """
    base_url = clean_jira_base_url(jira_cfg.get("base_url") or "")
    auth_type = (jira_cfg.get("auth_type") or "basic").lower()
    email = (jira_cfg.get("email") or "").strip()
    api_token = (jira_cfg.get("api_token") or "").strip()

    # 1. Parameter Validation
    if not base_url:
        return {
            "success": False,
            "error": "Missing Jira Base URL",
            "detail": "Please provide your Jira instance URL (e.g. https://your-domain.atlassian.net or https://jira.company.com)."
        }

    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        return {
            "success": False,
            "error": "Invalid URL Protocol",
            "detail": f"The URL '{base_url}' must start with https:// (or http:// for local/dev instances)."
        }

    # Detect Cloud with Bearer Auth mistake
    if ".atlassian.net" in base_url.lower() and auth_type == "bearer":
        return {
            "success": False,
            "error": "Incorrect Auth Type for Jira Cloud",
            "detail": (
                f"Your URL '{base_url}' is an Atlassian Cloud instance.\n"
                "Atlassian Cloud does NOT use Bearer Tokens (PATs are only for on-premise Jira Server / Data Center).\n\n"
                "How to fix this in Settings:\n"
                "1. Change 'Authentication Type' to 'Basic Auth (Cloud: Email + API Token)'.\n"
                "2. Enter your Jira Account Email (the email you use to login to Atlassian).\n"
                "3. Paste your Atlassian API token created at https://id.atlassian.com/manage-profile/security/api-tokens."
            )
        }

    if not api_token or api_token == "your_jira_api_token_here":
        return {
            "success": False,
            "error": "Missing Jira Token",
            "detail": "Please enter your Atlassian API token (for Cloud) or Personal Access Token (for Server/DC)."
        }

    if auth_type == "basic" and (not email or "your_email" in email):
        return {
            "success": False,
            "error": "Missing Account Email",
            "detail": "Basic Authentication (Jira Cloud) requires the email address associated with your Atlassian account."
        }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    auth = None

    if auth_type == "bearer":
        headers["Authorization"] = f"Bearer {api_token}"
    else:
        auth = HTTPBasicAuth(email, api_token)

    endpoints = [
        (f"{base_url}/rest/api/3/myself", "v3 (Cloud)", f"{base_url}/rest/api/3/serverInfo"),
        (f"{base_url}/rest/api/2/myself", "v2 (Server/DC/Cloud)", f"{base_url}/rest/api/2/serverInfo")
    ]

    last_status = None
    last_detail = None

    for myself_url, api_label, server_info_url in endpoints:
        try:
            resp = requests.get(myself_url, headers=headers, auth=auth, timeout=12, allow_redirects=True)

            # Check HTML redirect (typical when unauthenticated or SSO interception)
            content_type = resp.headers.get("Content-Type", "").lower()
            if "text/html" in content_type or (resp.history and "/login" in resp.url):
                return {
                    "success": False,
                    "status_code": resp.status_code,
                    "error": "HTML Login / SSO Interception",
                    "detail": (
                        "Jira returned an HTML login page rather than JSON API data. Possible causes:\n"
                        "1. If using Jira Cloud, confirm you chose 'Basic Auth' and entered an API Token (not your web password).\n"
                        "2. If using Jira Server/Data Center, try switching Auth Type to 'Bearer Token'.\n"
                        "3. Your corporate SSO or proxy gateway is blocking automated API requests."
                    )
                }

            if resp.status_code == 200:
                try:
                    user_data = resp.json()
                except Exception:
                    return {
                        "success": False,
                        "error": "Invalid JSON Payload",
                        "detail": f"Jira endpoint {myself_url} responded 200 OK, but returned non-JSON content."
                    }

                # Query server info
                server_meta = {"title": "Jira", "version": "Unknown"}
                try:
                    s_resp = requests.get(server_info_url, headers=headers, auth=auth, timeout=6)
                    if s_resp.status_code == 200:
                        s_data = s_resp.json()
                        server_meta["title"] = s_data.get("serverTitle", "Jira")
                        server_meta["version"] = s_data.get("version", "Cloud")
                except Exception:
                    pass

                display_name = user_data.get("displayName", user_data.get("name", "Authenticated User"))
                user_email = user_data.get("emailAddress", email or "N/A")
                account_id = user_data.get("accountId", user_data.get("key", "N/A"))

                return {
                    "success": True,
                    "api_version": api_label,
                    "user": {
                        "display_name": display_name,
                        "email": user_email,
                        "account_id": account_id,
                        "active": user_data.get("active", True)
                    },
                    "server": server_meta,
                    "message": f"Connection verified successfully! Authenticated as {display_name}."
                }

            elif resp.status_code == 401:
                return {
                    "success": False,
                    "status_code": 401,
                    "error": "401 Unauthorized (Invalid Credentials)",
                    "detail": (
                        "Jira rejected your credentials.\n"
                        "• For Jira Cloud: Generate an API token at https://id.atlassian.com/manage-profile/security/api-tokens. Do NOT use your Atlassian account password.\n"
                        "• For Jira Server/DC: Ensure your Personal Access Token is active and has not expired."
                    )
                }
            elif resp.status_code == 403:
                return {
                    "success": False,
                    "status_code": 403,
                    "error": "403 Forbidden (Access Denied)",
                    "detail": f"Jira responded 403 Forbidden: {resp.text[:200]}.\nYour account is recognized but lacks permission to access Jira REST APIs or is restricted by IP whitelisting."
                }
            elif resp.status_code == 404:
                last_status = 404
                last_detail = f"Endpoint {myself_url} was not found (404). Verify that '{base_url}' points to the root of your Jira instance without trailing subpaths."
                continue
            else:
                last_status = resp.status_code
                last_detail = f"Jira returned HTTP {resp.status_code}: {resp.text[:250]}"

        except requests.exceptions.SSLError as ssl_err:
            return {
                "success": False,
                "error": "SSL Certificate Verification Failed",
                "detail": f"Could not establish secure SSL connection to {base_url}: {ssl_err}.\nIf using an internal self-signed certificate, verify your system certificate trust store."
            }
        except requests.exceptions.ConnectionError as conn_err:
            return {
                "success": False,
                "error": "Connection Failed (Host Unreachable)",
                "detail": f"Could not connect to '{base_url}': {conn_err}.\nCheck for typos in domain name, DNS resolution, or VPN requirements."
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Connection Timed Out",
                "detail": f"Request to '{base_url}' timed out after 12 seconds. The Jira server may be experiencing downtime or network latency."
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Unexpected Handshake Error",
                "detail": str(e)
            }

    return {
        "success": False,
        "status_code": last_status or 502,
        "error": "Jira Handshake Failed",
        "detail": last_detail or f"Could not verify credentials against Jira instance at '{base_url}'."
    }


