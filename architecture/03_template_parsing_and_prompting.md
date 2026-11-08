# SOP 03: Template Parsing & Prompt Synthesis

## 1. Purpose
Define how default templates, uploaded templates (`.pdf`, `.txt`, `.md`), and ticket requirements are merged into the LLM prompt.

## 2. Template Extraction
- PDF: Processed via `pypdf.PdfReader` across all pages.
- Text/Markdown: UTF-8 decoded with Latin-1 fallback.
- Overrides: If custom template is active, its headings and numbering replace the default IEEE template.

## 3. Strict Prompting Invariants
- Grounding: Scenarios must stem directly from ticket description, ACs, and comments.
- Relative Milestones: Relative dates ("Day 1–2", "Day 3–4").
- Formatting: Output pure Markdown only, with no conversational chatter.

