# BudgetSync – Generative AI (Local-First) Design & Implementation Notes

> **Goal:** Add resume-ready GenAI features to BudgetSync’s Flask backend **without recurring cloud costs** and **without changing core money math**. AI enhances UX (summaries, NL queries), while all calculations remain deterministic and testable.

---

## 1) Scope & Principles

- **Use case, not hype:** Add small, high-impact features: monthly insights, natural-language queries, optional receipt OCR → category suggestion.
- **Local-first & $0 run-cost:** Prefer local/open-source models (e.g., Ollama on your machine) and classic NLP. Cloud providers are **off by default** behind a feature flag.
- **Deterministic core:** Balances, taxes, and budget math stay non-AI. AI outputs are advisory/explanatory only.
- **Production-ish hygiene:** Feature flags, timeouts, fallbacks, caching, redaction, basic metrics.

**Non-Goals**
- Training custom LLMs or building agents.
- Replacing tax/budget logic with AI.
- Complex orchestration or vendor lock-in.

---

## 2) Features (User-Facing)

### 2.1 Monthly Insights (LLM-Assisted, with Fallback)
**What users get:** A 4–6 sentence summary of the selected month (top categories, changes vs. last month, one simple tip).

- **Endpoint:** `POST /ai/insights/monthly`
- **Request (JSON):**
  ```json
  { "user_id": 42, "month": "July", "year": 2025 }
  ```
- **Response (JSON):**
  ```json
  {
    "summary": "string",
    "stats": { "...": "deterministic monthly stats payload" },
    "source": "llm|fallback|deterministic"
  }
  ```
- **Notes:** If AI is disabled/unavailable, return a deterministic template summary using the same `stats`.

---

### 2.2 Natural-Language Query → Safe SQL (Bounded)
**What users get:** Ask “What did I spend on groceries in July?” → mapped to a **whitelisted** intent + parameterized SQL, then optional AI rephrasing.

- **Endpoint:** `POST /ai/query?phrased=true|false`
- **Request (JSON):**
  ```json
  { "q": "What did I spend on groceries in July 2025?" }
  ```
- **Response (JSON):**
  ```json
  {
    "results": [{ "category": "Groceries", "amount": 345.67, "month": "July", "year": 2025 }],
    "explanation": "optional llm phrasing if phrased=true",
    "source": "sql|llm+sql"
  }
  ```
- **Safety:** Only support a handful of intents (e.g., `spend_by_category_month`, `top_merchants_month`). Unknown → helpful error with examples.

---

### 2.3 (Optional) Receipt OCR → Category Suggestion
**What users get:** Upload a receipt image → extract text → suggest a category with a confidence score. **User must confirm** before saving.

- **Endpoint:** `POST /ai/ocr/receipt` (multipart)
- **Response (JSON):**
  ```json
  { "text": "...", "suggested_category": "Groceries", "confidence": 0.82 }
  ```
- **Notes:** Keep a simple classical model (TF-IDF/logistic regression) or rules; AI is not required here.

---

## 3) Configuration & Feature Flags

**Environment variables (example):**
```text
AI_ENABLED=true                # master on/off
AI_MODE=local                  # local|mock|cloud (cloud disabled by default)
AI_MODEL=qwen2.5:3b-instruct   # Ollama model tag, or similar small instruct model
AI_MAX_TOKENS=400              # cap output size
AI_TIMEOUT_MS=8000             # per-request timeout
AI_CACHE_DIR=.ai_cache         # file cache for responses
AI_LOG_REDACT=true             # mask PII in logs/responses
AI_EMBED_MODEL=all-MiniLM-L6-v2
```

**Behavior:**
- `AI_ENABLED=false` → All `/ai/*` routes return deterministic or SQL-only results.
- `AI_MODE=mock` → Deterministic stubbed strings for demos/tests.
- `AI_MODE=local` → Calls a local runtime (e.g., Ollama at `http://localhost:11434`) for summaries/phrasing.

---

## 4) Data Flow (Narrative)

- **Monthly Insights:**  
  (a) Compute **deterministic stats** (totals, top categories, deltas vs. last month).  
  (b) If AI enabled, build a short prompt from stats → local LLM → redact PII → return.  
  (c) On failure/timeout, return deterministic template summary.
  
- **NL Query:**  
  (a) Parse the question into **intent + entities** using simple rules + embeddings (MiniLM) for robustness.  
  (b) Map to **whitelisted parameterized SQL** and execute.  
  (c) If `phrased=true` and AI enabled, pass results into a short “explain” prompt; else return raw results.

- **OCR Suggestion (optional):**  
  (a) OCR the image (local OCR).  
  (b) Extract merchant/keywords → rules or small classifier → category + confidence.  
  (c) Do **not** auto-save—require user confirmation.

---

## 5) Pseudocode (Illustrative Only)

**5.1 Monthly Insights**
```text
function monthly_insights(user_id, month, year):
    stats = compute_monthly_stats(user_id, month, year)   # deterministic
    if not AI_ENABLED:
        return { summary: summarize_deterministically(stats),
                 stats: stats, source: "deterministic" }

    prompt = render_monthly_prompt(stats)                  # short, versioned
    try:
        text = AI.generate(prompt, max_tokens=AI_MAX_TOKENS, timeout=AI_TIMEOUT_MS)
        return { summary: redact_pii(text), stats: stats, source: "llm" }
    except TimeoutOrError:
        return { summary: summarize_deterministically(stats),
                 stats: stats, source: "fallback" }
```

**5.2 NL Query → Safe SQL**
```text
function nl_query(q, phrased=false):
    intent = classify_intent(q)            # rules + embeddings; limited set
    if intent == UNKNOWN:
        return { error: "Unsupported query. Try: 'What did I spend on groceries in July 2025?'" }

    params = extract_entities(q, intent)   # month/year/category, with defaults
    results = run_parameterized_sql(intent, params)

    if phrased and AI_ENABLED:
        try:
            explanation = AI.generate(prompt_explain(q, results), max_tokens=220)
            return { results: results, explanation: redact_pii(explanation), source: "llm+sql" }
        except TimeoutOrError:
            pass
    return { results: results, source: "sql" }
```

**5.3 OCR → Category Suggestion (Optional)**
```text
function receipt_ocr_suggest(file):
    text = OCR.read(file)
    features = extract_keywords(text)
    (category, confidence) = classify_category(features)  # rules or simple model
    return { text: text, suggested_category: category, confidence: confidence }
```

---

## 6) Prompting Guidelines (Keep Them Tiny)

- **Monthly summary prompt** should be ≤ 1200 characters and include only:
  - Month/year, total spend, top categories list, notable deltas vs. last month.
  - Instruction: 4–6 concise sentences; one low-risk tip; **no financial advice**.
- **Explain-results prompt** (for NL queries): pass the SQL results and user question; ask for 2–3 sentences tops.
- **Version prompts** in comments (e.g., `v1.0`, `v1.1`) and keep a small **golden test set** to catch regressions when you tweak wording.

---

## 7) Privacy & Safety

- **PII redaction** in logs and AI responses (names, emails, SSNs, addresses).  
- **Strict SQL allow-list:** Only predefined queries; all parameters sanitized.  
- **AI is advisory only:** No balances/taxes are computed by AI.  
- **Input limits:** Max payload sizes for prompts and files; fail fast on oversized requests.

---

## 8) Cost Control & Reliability

- **Local-first:** Use a small local instruct model; no API fees.  
- **Timeouts & caps:** `AI_TIMEOUT_MS`, `AI_MAX_TOKENS`.  
- **Response cache:** Hash `(model, prompt)` → cached JSON to avoid recomputation.  
- **Circuit breaker:** After N failures in M minutes, auto-serve fallbacks and log a warning.

---

## 9) Observability

- Log: request id, route, latency, `source` (`llm|sql|fallback|deterministic`), and cache hit/miss.  
- Counters: #calls, timeouts, failures, cache hit-rate.  
- Optional: a small admin page or CLI to dump recent AI metrics.

---

## 10) Testing & Quality

- **Golden tests:** 15–20 fixed inputs → assert output contains key phrases/patterns (regex), independent of model quirks.
- **Unit tests:**
  - Fallback path returns a deterministic summary.
  - Intent classifier picks the correct intent for canonical queries.
  - PII redactor masks emails/SSNs reliably.
- **E2E smoke:** With local model running, hit `/ai/insights/monthly` and assert non-empty `summary` within timeout.

---

## 11) Documentation Snippets (Copy into README)

- “**Local-first GenAI** via a small instruct model; core budget math remains deterministic.”
- “**Feature flags & fallbacks:** AI can be toggled off; users still get deterministic summaries.”
- “**Safe NL → SQL:** Queries map to whitelisted intents and parameterized SQL only.”
- “**Privacy:** PII redaction in logs; no AI used for financial calculations.”

---

## 12) Roadmap

- **v1.0 (current):** Monthly insights + bounded NL query; optional receipt OCR suggestion; flags, fallbacks, cache.  
- **v1.1:** Expand intents (date ranges, merchants); add simple admin toggles and usage chart.  
- **v1.2:** Add RAG over user notes/attachments with local embeddings + citations (optional).  
- **v1.3:** Lightweight evaluation harness (golden tests + latency histograms).

---

## 13) Risks & Mitigations

- **Model latency on CPU:** Keep prompts short; set conservative timeouts; cache results.  
- **Hallucinations in summaries:** Provide stats alongside `summary`; keep prompts narrow; allow easy user feedback.  
- **Scope creep:** Limit intents; document “unsupported” queries clearly.  
- **Privacy:** Enforce redaction; never send raw PII to any external provider.

---

## 14) Success Criteria (Resume-Ready)

- Screenshots/GIF:  
  - Insights panel with “source: llm” and the same panel with “source: deterministic”.  
  - NL query with results + one-line explanation.  
- Docs show flags, fallback behavior, and guardrails.  
- Short bullets for resume/LinkedIn highlighting **local-first GenAI**, **safe NL→SQL**, **fallbacks**, and **privacy**.

---
