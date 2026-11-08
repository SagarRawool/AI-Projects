from typing import Optional
from backend.app.services.jira_client import NormalizedTicket

DEFAULT_IEEE_TEMPLATE = """
# 1. Introduction
## 1.1 Document Purpose
## 1.2 System Overview & Ticket Context

# 2. Test Objectives & Success Criteria
## 2.1 Core Test Objectives
## 2.2 Acceptance Criteria Verification
## 2.3 Quality Thresholds & Success Metrics

# 3. Scope
## 3.1 Features In-Scope
## 3.2 Features Out-of-Scope

# 4. Test Strategy
## 4.1 Test Levels (Unit, Integration, System, User Acceptance)
## 4.2 Test Types (Functional, Security, Regression, Negative & Boundary, Performance)
## 4.3 Test Design Techniques & Concrete Test Scenarios

# 5. Test Environment & Configuration
## 5.1 Target Test Environments (QA/Staging)
## 5.2 Browser, OS, and Client Device Matrix
## 5.3 Infrastructure, Database & Third-Party Service Dependencies

# 6. Test Data Requirements
## 6.1 User Personas, Roles & Access Credentials
## 6.2 Test Payloads, Seed Data & Boundary Datasets

# 7. Test Deliverables
## 7.1 Test Artifacts (Test Cases, Execution Matrix)
## 7.2 Defect Tracking, Daily Status Reports & Final Sign-off Summary

# 8. Entry & Exit Criteria
## 8.1 Entry Criteria
## 8.2 Suspension & Resumption Criteria
## 8.3 Exit Criteria

# 9. Roles & Responsibilities
## 9.1 QA and Engineering Responsibility Matrix

# 10. Schedule & Milestones
## 10.1 Relative Timeline (Day 1-2, Day 3-4, etc.)
## 10.2 Milestone Checkpoints

# 11. Risks & Mitigation
## 11.1 Identified Technical & Schedule Risks Table

# 12. Approvals & Sign-off
## 12.1 Stakeholder Sign-off Matrix
""".strip()

SYSTEM_PROMPT = """You are a senior QA engineer who writes professional, precise, and actionable software test plans.
Strict rules:
1. Follow the template structure and numbering exactly without skipping, renaming, or creating unrequested sections.
2. Ground every section in the Jira ticket details (summary, description, acceptance criteria, comments, labels, priority). Never invent unrelated features or include generic placeholder text like "TBD" or "Lorem Ipsum".
3. Derive realistic in-scope and out-of-scope boundaries directly from ticket constraints.
4. Propose concrete, named, testable scenarios for each test level and type (positive, negative, boundary, security/auth).
5. Use relative timelines for the schedule (e.g., "Day 1–2: Test Environment Setup & Smoke Tests", "Day 3–4: Execution").
6. Use Markdown tables where structured information is clearer (e.g., Environments, Roles, Test Scenarios, Risks, Approvals).
7. Output ONLY the test plan in Markdown format. Do NOT include any conversational preamble, intro sentences ("Here is your test plan..."), or postscript comments.
""".strip()


def build_user_prompt(ticket: NormalizedTicket, template_override: Optional[str] = None) -> str:
    """
    Constructs the detailed prompt for the LLM using the active template and ticket fields.
    """
    template_text = template_override.strip() if template_override and template_override.strip() else DEFAULT_IEEE_TEMPLATE

    comments_block = ""
    if ticket.comments:
        formatted_comments = [f"- Comment {i+1}: {c[:500]}" for i, c in enumerate(ticket.comments)]
        comments_block = "\n".join(formatted_comments)
    else:
        comments_block = "None"

    labels_str = ", ".join(ticket.labels) if ticket.labels else "None"
    components_str = ", ".join(ticket.components) if ticket.components else "None"
    fix_versions_str = ", ".join(ticket.fixVersions) if ticket.fixVersions else "None"

    user_prompt = f"""Generate a comprehensive, actionable QA Software Test Plan for the following Jira Ticket by strictly adhering to the provided Template.

==================================================
TARGET TEMPLATE STRUCTURE
==================================================
{template_text}

==================================================
JIRA TICKET SPECIFICATION
==================================================
- Issue Key: {ticket.key}
- Summary: {ticket.summary}
- Issue Type: {ticket.issuetype}
- Priority: {ticket.priority}
- Status: {ticket.status}
- Assignee: {ticket.assignee}
- Reporter: {ticket.reporter}
- Labels: {labels_str}
- Components: {components_str}
- Fix Versions: {fix_versions_str}

--------------------------------------------------
Ticket Description & Acceptance Criteria:
--------------------------------------------------
{ticket.description if ticket.description else "No description provided."}

--------------------------------------------------
Ticket Comments & Implementation Notes:
--------------------------------------------------
{comments_block}

==================================================
INSTRUCTIONS:
Output the complete Test Plan following the Template headings and numbering. Ensure every scenario is tailored to {ticket.key} and its requirements. Output ONLY the Markdown document.
"""
    return user_prompt.strip()

