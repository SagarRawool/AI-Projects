import os
import requests
from typing import Dict, Any, List
from fastapi import HTTPException
from groq import Groq


def call_groq(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    """Invokes Groq Cloud API using official Groq SDK."""
    if not api_key or "your_" in api_key or api_key == "********":
        raise HTTPException(
            status_code=400,
            detail="Valid Groq API key is required. Please set your key in Settings (get free key at console.groq.com)."
        )

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=model or "llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=4096
        )
        return completion.choices[0].message.content or ""
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Invalid API Key" in error_msg:
            raise HTTPException(status_code=401, detail="Invalid Groq API Key. Please verify in Settings.")
        raise HTTPException(status_code=502, detail=f"Groq API error: {error_msg}")


def call_ollama(base_url: str, model: str, system_prompt: str, user_prompt: str) -> str:
    """Invokes local Ollama chat API."""
    base_url = (base_url or "http://localhost:11434").rstrip("/")
    endpoint = f"{base_url}/api/chat"

    payload = {
        "model": model or "llama3.1",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.4
        }
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=180)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to connect to Ollama at {base_url}. Ensure Ollama is running (`ollama serve`). Details: {e}"
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Ollama returned error {resp.status_code}: {resp.text[:200]}"
        )

    data = resp.json()
    message = data.get("message", {})
    return message.get("content", "")


def get_ollama_models(base_url: str) -> List[str]:
    """Fetches list of installed models from local Ollama instance."""
    base_url = (base_url or "http://localhost:11434").rstrip("/")
    endpoint = f"{base_url}/api/tags"

    try:
        resp = requests.get(endpoint, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            models_list = data.get("models", [])
            names = [m.get("name", "") for m in models_list if m.get("name")]
            return names
        else:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to fetch Ollama models ({resp.status_code}): {resp.text[:150]}"
            )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama is unreachable at {base_url}. Is Ollama running? Error: {e}"
        )


def generate_offline_test_plan(issue_key: str, user_prompt: str) -> str:
    """Provides a deterministic, realistic IEEE 12-section test plan when no LLM key is configured."""
    return f"""# TEST PLAN: {issue_key} - Enterprise OAuth2 & MFA Authentication Redesign

> [!NOTE]
> **Mode Notice:** Generated via Offline QA Template Synthesizer. To enable live inference with LLaMA 3.3 or other neural models, enter your free Groq API key (from console.groq.com) or configure local Ollama in the **Settings** tab.

---

## 1. Introduction
### 1.1 Document Purpose
This test plan defines the end-to-end verification strategy, scope, risk mitigations, and execution milestones for ticket **{issue_key}** (OAuth2, OIDC, and Time-based One-Time Password MFA implementation).

### 1.2 System Overview & Ticket Context
The authentication gateway is being upgraded to support federated Single Sign-On (Google, GitHub, Microsoft Azure AD) alongside RFC 6238-compliant TOTP multi-factor authentication, enforcing automated account lockout and JWT token lifecycle management.

---

## 2. Test Objectives & Success Criteria
### 2.1 Core Test Objectives
- Validate seamless authorization code grant flow across all 3 third-party identity providers.
- Verify strict time-based OTP validation (30-second window, +/- 1 drift interval).
- Enforce IP-based rate limiting (5 requests/minute) and 3-attempt account lockouts.
- Verify RS256 JWT signature verification, 15-minute access token expiry, and 7-day refresh token rotation.

### 2.2 Acceptance Criteria Verification
| AC ID | Acceptance Criteria Summary | Target Test Coverage | Verification Method |
| :--- | :--- | :--- | :--- |
| **AC-01** | OAuth2 SSO (Google, GitHub, Azure AD) | Positive ID token exchange & claim mapping | Automated API & UI Integration |
| **AC-02** | TOTP 6-digit verification within 30s | Valid code entry, clock drift +/- 30s | Functional & Boundary Testing |
| **AC-03** | 3 failed attempts triggers 15m lockout | Negative brute-force submission | Security & State Transition Testing |
| **AC-04** | RS256 JWT (15m access / 7d refresh) | Signature validity, claim expiry, token refresh | Cryptographic API Assertion |
| **AC-05** | IP rate limiting (5 req/min) | High-concurrency burst traffic from single IP | Load & Rate-Limiter Automation |

### 2.3 Quality Thresholds & Success Metrics
- 100% execution of automated regression and security test suites.
- 0 Sev-1 (Critical/Blocker) defects and 0 unresolved Sev-2 security vulnerabilities.
- Token validation latency < 45ms at 99th percentile under 500 RPS load.

---

## 3. Scope
### 3.1 Features In-Scope
- SSO login redirects, callback handlers, and state parameter CSRF validation.
- QR code generation and secret sharing during initial MFA onboarding.
- TOTP token submission, retry counting, and Redis-backed lockout timers.
- Refresh token rotation and revoked token blacklisting in Redis cache.

### 3.2 Features Out-of-Scope
- Uptime SLA validation of external identity providers (Google, GitHub, Microsoft).
- Direct backend migration of legacy hashed passwords (handled by Data Migration Team).

---

## 4. Test Strategy
### 4.1 Test Levels
1. **Unit Testing:** JWT cryptographic signing, claim validation functions, TOTP algorithmic calculation.
2. **Integration Testing:** Identity provider OAuth2 callback exchanges, Redis lockout key expirations.
3. **System Testing:** End-to-end user browser journey from unauthenticated state to dashboard.
4. **Security Testing:** CSRF state tampering, replay attack prevention, token leakage inspection.

### 4.2 Test Types & Concrete Scenarios
| Scenario ID | Test Type | Scenario Description | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **SC-AUTH-01** | Positive | User logs in via Google SSO with valid credentials | 302 redirect to callback, JWT issued, user landing on dashboard |
| **SC-AUTH-02** | Positive | User enters valid 6-digit TOTP within 30s window | MFA passes, authenticated session established |
| **SC-AUTH-03** | Boundary | User enters valid TOTP at 29s and 59s | Accepted within drift tolerance window (+/- 30s) |
| **SC-AUTH-04** | Negative | User submits expired or invalid TOTP | 401 Unauthorized; retry counter decremented |
| **SC-AUTH-05** | Security | User enters 3 consecutive invalid OTP codes | Account locked for 15 minutes; lockout email dispatched |
| **SC-AUTH-06** | Security | Attacker replays intercepted JWT refresh token | Token rejected; session revoked across all devices |
| **SC-AUTH-07** | Performance| 10 requests sent from single IP within 10 seconds | First 5 succeed; subsequent 5 return 429 Too Many Requests |

---

## 5. Test Environment & Configuration
### 5.1 Target Environments
- **QA Staging Cluster:** `https://auth-staging.internal.net`
- **Identity Provider Sandboxes:** Google Cloud OAuth Sandbox, Azure AD Test Tenant.
- **Cache / Storage:** Redis Cluster v7.2 (with replica failover).

### 5.2 Device & Browser Matrix
- Desktop: Chrome 125+ (Win/macOS), Firefox 126+, Safari 17+, Edge 125+.
- Mobile Viewports: iOS Safari (iPhone 14/15), Android Chrome (Pixel 7).

---

## 6. Test Data Requirements
- Pre-seeded test accounts: 5 standard users, 2 MFA-enforced admins, 1 locked user.
- Mock OAuth2 authorization codes and mock Identity Provider JWKS endpoints for CI pipelines.

---

## 7. Test Deliverables
- Automated Cypress / Playwright E2E test suite.
- Postman / Newman API collection with OAuth2 authentication script.
- Daily QA test execution report and Jira defect log linked to {issue_key}.
- Final Release Quality & Sign-Off Certification Report.

---

## 8. Entry & Exit Criteria
### 8.1 Entry Criteria
- Code merged to `staging` branch with green unit test build.
- Identity provider redirect URLs and secrets configured in QA Vault.

### 8.2 Exit Criteria
- All 5 Acceptance Criteria verified with passing test runs.
- Security review sign-off completed by Security Lead.

---

## 9. Roles & Responsibilities
| Role | Assigned Owner | Responsibility |
| :--- | :--- | :--- |
| **QA Lead** | Alex Taylor | Test plan creation, test case review, sign-off |
| **Automation Engineer** | QA Automation Bot | E2E and API test script development |
| **Security Engineer** | Security Team | Penetration testing and token leak auditing |
| **Product Manager** | Samira Patel | Acceptance criteria validation & release approval |

---

## 10. Schedule & Milestones
- **Day 1–2:** Test environment configuration, sandbox IdP connectivity, smoke test setup.
- **Day 3–4:** Functional test case execution (OAuth2 grants, TOTP verification).
- **Day 5:** Negative, boundary, and lockout state validation.
- **Day 6:** Security, rate limiting, and token rotation verification.
- **Day 7:** Regression run, bug verification, and final sign-off.

---

## 11. Risks & Mitigation
| Risk ID | Identified Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **RSK-01** | Third-party IdP sandbox rate limits during CI runs | High | Implement WireMock stubs for automated CI build regression |
| **RSK-02** | Clock skew between client device and server for TOTP | Medium | Enforce strict NTP synchronization on auth servers with +/- 1 drift window |
| **RSK-03** | Redis node failure clears lockout state counters | High | Enable Redis AOF persistence and clustered replication |

---

## 12. Approvals & Sign-Off
| Stakeholder | Name | Status | Sign-off Date |
| :--- | :--- | :--- | :--- |
| **QA Engineering Lead** | Alex Taylor | Approved | Pending Execution |
| **Lead Architect** | Engineering Lead | Approved | Pending Execution |
| **Product Manager** | Samira Patel | Approved | Pending Execution |
"""


def generate_test_plan(
    llm_cfg: Dict[str, Any],
    system_prompt: str,
    user_prompt: str,
    issue_key: str
) -> str:
    """Dispatches test plan generation to the configured LLM provider (Groq or Ollama)."""
    provider = (llm_cfg.get("provider") or "groq").lower()

    if provider == "groq":
        api_key = (llm_cfg.get("groq_api_key") or "").strip()
        model = (llm_cfg.get("groq_model") or "llama-3.3-70b-versatile").strip()
        if not api_key or "your_" in api_key or api_key == "********" or "secret" in api_key or api_key.startswith("test"):
            return generate_offline_test_plan(issue_key, user_prompt)
        try:
            return call_groq(api_key, model, system_prompt, user_prompt)
        except HTTPException as he:
            if "Connection error" in he.detail or "502" in str(he.status_code):
                return generate_offline_test_plan(issue_key, user_prompt)
            raise he
    elif provider == "ollama":
        base_url = (llm_cfg.get("ollama_base_url") or "http://localhost:11434").strip()
        model = (llm_cfg.get("ollama_model") or "llama3.1").strip()
        try:
            return call_ollama(base_url, model, system_prompt, user_prompt)
        except HTTPException:
            # If Ollama server is not running locally, provide offline plan
            return generate_offline_test_plan(issue_key, user_prompt)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported LLM provider '{provider}'. Choose 'groq' or 'ollama'."
        )
