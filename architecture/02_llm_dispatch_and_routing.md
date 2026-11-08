# SOP 02: Unified LLM Dispatch (Groq Cloud & Ollama Local)

## 1. Purpose
Provide unified dispatch across cloud-hosted fast inference (Groq) and local air-gapped private models (Ollama).

## 2. Groq Cloud Engine
- SDK: `groq.Groq`
- Model: `llama-3.3-70b-versatile` (configurable)
- Parameters: `temperature=0.4`, `max_tokens=4096`
- Error mapping: 401 on bad key; 429 on rate limit.

## 3. Ollama Local Engine
- Endpoint: `POST {base_url}/api/chat`
- Model: `llama3.1` (configurable)
- Payload:
  ```json
  {
    "model": "llama3.1",
    "messages": [
      { "role": "system", "content": "..." },
      { "role": "user", "content": "..." }
    ],
    "stream": false,
    "options": { "temperature": 0.4 }
  }
  ```
- Model Tag Discovery: `GET {base_url}/api/tags`

