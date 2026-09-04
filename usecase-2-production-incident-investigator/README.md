# 🔎 Use Case 4 — Production Incident Investigator

**Track**: Retrieval + evidence correlation (RAG-shaped, no LLM required)
**Estimated time**: ~1 hour
**No banking/domain knowledge needed** beyond reading application logs. **No API keys, no GPU, no LLM calls** — see "A note on what 'RAG' means here" below.

---

## 📋 The brief

You're an on-call engineer's investigation assistant. You're given a
corpus of documents for one production incident — application logs, an
architecture overview, API specs, deployment history, previous incidents,
runbooks, and a known-issues catalog — plus a plain-English question
describing the symptom. Your job is to correlate evidence *across* those
documents and produce a structured incident report: probable root cause,
supporting evidence, impacted systems, mean time to recover, recommended
remediation, and a calibrated confidence score.

Not every document is markdown prose: `known_issues.csv` is a flat CSV
catalog with one row per known issue (`issue_id,title,signature,
affected_component,notes`) — several rows, most of them irrelevant to any
given incident, same as a real issue tracker export would look. Your
retrieval/correlation has to work over raw text regardless of which
file it came from, not assume everything is a markdown document.

There are **two incidents** in `data/`, and they're deliberately
different in kind:

- **`incident_a_pool_exhaustion/`** — "Payments are intermittently
  failing after yesterday's deployment...". The evidence is there, spread
  across five different documents, and a correct investigation finds all
  of it.
- **`incident_b_ambiguous_delay/`** — "Order confirmation emails are
  arriving late...". The evidence is genuinely thin: one unconfirmed
  warning, no matching known issue, no correlated deployment, no
  precedent. **The correct answer is low confidence, not a confident
  guess.**

### Exact spec

Implement:

```python
def investigate(query: str, corpus: dict) -> dict:
    """corpus: filename -> full document text (all the files in one
    incident's data/ folder)."""
```

Return a dict with exactly these keys:

- **`root_cause`** — non-empty string, even for the low-confidence incident
- **`supporting_evidence`** — `list[dict]`, each `{"source": <filename>, "excerpt": <str>}`
- **`impacted_systems`** — `list[str]`
- **`mttr_minutes`** — `int | None`
- **`remediation`** — string
- **`confidence_score`** — `float`, 0-100
- **`needs_human_review`** — `bool`, must equal `confidence_score < 50` exactly

No exact wording is required anywhere the tests don't say so explicitly.
Free-text fields are checked for key terms, not exact phrasing.

---

## 🧠 A note on what "RAG" means here

A real production version of this tool would hand retrieved evidence to
an LLM to write the narrative. That needs an API key, and every other use
case in this repo deliberately doesn't — so this one doesn't either. What
you're building is the two halves that *are* fully autogradable:

1. **Retrieval** — rank the corpus against the query (the starter scaffolds
   this with TF-IDF cosine similarity; that's genuinely representative of
   how retrieval works, just without a vector database behind it).
2. **Structured correlation and confidence calibration** — the actual
   graded difficulty. Do independent sources agree with each other, and
   does your confidence score honestly reflect that?

If you want to wire in a real LLM anyway to turn your structured report
into better prose, go ahead — it's not graded either way, and CI never
calls it (no API key available there). It won't move your score up or
down.

---

## 🧠 Why this is harder than it looks

- **Retrieval alone isn't the answer.** The top-ranked document for
  incident A's query might just be the architecture overview (it
  literally contains the word "payment" the most). The actual root cause
  only becomes clear when you notice that *logs*, *deployment history*,
  *known issues*, *the runbook*, and *a previous incident* are all
  independently telling you the same thing.
- **Not every log line is about this incident.** Both logs files carry a
  handful of entries from other, unrelated known issues (checkout
  latency, search indexing, email templating, and so on) alongside the
  ones that actually matter — real logs are not pre-filtered to just the
  incident you're investigating, and neither is this one.
- **Calibration, not confidence theater.** It's easy to always emit a
  plausible-sounding root cause with a high confidence number attached —
  that's what a fluent AI assistant will hand you if you don't push back.
  It's much harder to build something that correctly recognizes when the
  evidence is actually too thin, and says so.
- **The two incidents use the same document *types* on purpose.** If your
  approach only works for incident A because you hardcoded something
  specific to it (a filename, a magic string), it'll misbehave on
  incident B — the tests check both.

---

## 🎯 What you're building

In your `submissions/<your-name>/usecase-4-production-incident-investigator/` folder:

- **`solution.py`** — your `investigate()`. Copy `starter/solution.py` in
  as your starting point; it has working retrieval and a stubbed-out
  correlation step.
- **`README.md`** — see the root [README.md](../README.md)'s "Submission
  requirements" for what this needs to contain.

---

## ✅ How this is graded

`tests/test_solution.py` (trusted, don't edit) runs `investigate()`
against both incidents and checks: the report is well-formed and
internally consistent (`needs_human_review` must exactly match the
confidence threshold); incident A scores confidence ≥ 50, correctly names
`payment-gateway-adapter`, extracts an MTTR close to the runbook's stated
20 minutes, and cites at least 3 distinct source documents; incident B
scores confidence < 50 and is flagged for review. `benchmark/perf_bench.py`
separately times retrieval over a much larger synthetic corpus.

| Component | Weight | What it measures |
|---|---|---|
| Correctness | 30% | Well-formed output, incident A's high-confidence identification (component, MTTR, multi-source evidence), incident B's correctly-low confidence |
| Performance | 20% | Wall-clock time and peak memory on a padded, much larger corpus |
| Reusability | 15% | Function/method complexity, length, docstrings + type hints (see root README) |
| Code quality | 15% | `ruff` findings per line |
| Maintainability | 10% | `radon` maintainability index |
| Completion | 10% | `solution.py` and a real `README.md` present |

Run it yourself before pushing:
```bash
# from the repo root
python -m scoring.cli --usecase usecase-4-production-incident-investigator \
  --submission submissions/<your-name>/usecase-4-production-incident-investigator
```

## 💡 Using Claude (or any AI assistant) here

Useful for: explaining TF-IDF/cosine similarity if retrieval is new to
you, reviewing whether your evidence-correlation logic actually checks
independent sources or just restates the top search hit, brainstorming
what "confidence" should mean here before you write the formula. Less
useful for: an assistant asked to "investigate this incident" with no
further steering will very readily produce a confident-sounding answer
for incident B too, regardless of how thin the evidence actually is —
check your own output against both incidents before you trust it.
