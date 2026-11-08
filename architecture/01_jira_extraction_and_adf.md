# SOP 01: Jira API Integration & ADF Flattening

## 1. Purpose
Extract Jira ticket metadata and content accurately from Jira Cloud (v3) and Jira Server/Data Center (v2), converting complex Atlassian Document Format (ADF) structures into plain text.

## 2. API Contract
- Endpoint: `GET {base}/rest/api/3/issue/{issueKey}?fields=summary,description,comment,issuetype,priority,labels,status,assignee,reporter,fixVersions,components`
- Headers:
  - `Accept: application/json`
  - `Content-Type: application/json`
- Authentication:
  - Cloud: HTTP Basic Auth (`email` + `api_token`)
  - Server/DC: Bearer Auth (`Authorization: Bearer {token}`)

## 3. ADF Recursive Flattening Logic
Jira Cloud returns `description` and comment `body` as a JSON tree.
- `text`: Extract `node["text"]`
- `hardBreak`: Append `\n`
- `paragraph`: Append wrapped text with double newlines
- `heading`: Append `#` corresponding to level + text
- `bulletList`: Indent each `listItem` with `- `
- `orderedList`: Number each `listItem` with `1. `, `2. `
- `codeBlock`: Wrap in triple backticks with syntax label

## 4. Error Handling & Edge Cases (Learnings)
- `401 Unauthorized`: Invalid email or Atlassian API token.
- `403 Forbidden`: Account lacks read permissions for the project/issue.
- `404 Not Found`: Ticket key does not exist.
- `502 / Network Timeout`: Target Jira instance unreachable.
- **SSO/Login Redirects:** Jira instances often redirect unauthenticated API requests to an HTML login page or IdP redirect returning HTTP 200 with `text/html`. The client explicitly inspects `Content-Type` and redirect history, raising a 401 alert if HTML is received.
- **REST v3 vs v2 Dual Probing:** The client automatically probes Jira Cloud REST API v3 and falls back to Jira Server/DC REST API v2 before reporting failure.
- **JSON Decode Resilience:** `resp.json()` decoding is safeguarded to prevent unhandled 500 crashes and surface clean user-friendly toast messages.

