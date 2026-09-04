# Julius Baer AI Hackathon — jb-sidequest

## Overview

Two use cases, each with a different evaluation model. Read each use
case's own `README.md` before starting — full spec, starter code, exact
scoring breakdown. Attempt as many as you like; one done well beats two
done halfway.

| # | Directory | Track | LLM required? | How it's scored |
|---|---|---|---|---|
| 1 | [`usecase-1-payment-investigation-agent/`](usecase-1-payment-investigation-agent/) | AI agent: tools + RAG + LLM orchestration | **Yes** — any LLM provider with tool-calling support | Manual evaluation against a private answer key (see `EVALUATION_CRITERIA.md`) |
| 2 | [`usecase-2-production-incident-investigator/`](usecase-2-production-incident-investigator/) | Retrieval + evidence correlation (RAG-shaped, no LLM) | No | Hybrid: correctness judged manually against a private answer key, other components autoscored via GitHub Actions (6 weighted components) |

**Use case 1** asks you to build a payment-investigation AI assistant
that answers 10 natural-language questions by combining structured data,
policy documents (via RAG), deterministic tools, and an LLM agent. It
requires an LLM API key (any provider — see `.env.example`). The
organizer runs your code and evaluates the output against a private
answer key.

**Use case 2** asks you to build an incident-investigation function that
correlates evidence across a document corpus and produces a structured
report with a calibrated confidence score. No LLM, no API key — it's
purely retrieval + correlation. You run your own code against both
incidents and submit the resulting `answers.json` alongside your
`solution.py`; correctness is judged manually against a private answer
key, while performance/code-quality/reusability/maintainability/completion
still run automatically via the autoscoring pipeline on your PR.

---

## Project structure

```
jb-sidequest/
├── README.md                     you are here — participant-facing overview
├── LICENSE
├── requirements.txt                shared deps for scoring/ + use case 2
├── .gitignore
│
├── docs/
│   └── HIRING_GUIDE.md             for organizers/admins, not participants
│
├── scripts/
│   ├── setup_candidate_branch.sh   creates your branch + starter files (use case 2)
│   └── generate_protected_manifest.py   admin-only, regenerates the integrity manifest
│
├── scoring/                        shared autoscoring engine (use case 2 only, do not edit)
│   ├── cli.py                        entry point: `python -m scoring.cli --usecase ... --submission ...`
│   ├── integrity.py                  anti-tamper check, runs first in CI
│   ├── detect_submission.py          figures out who/what a PR is scoring
│   ├── submission_loader.py          dynamically imports your solution.py
│   ├── correctness.py                runs a use case's pytest suite -> score
│   ├── performance.py                runs a use case's benchmark -> score
│   ├── reusability.py                complexity + length + docstring/type-hint coverage -> score
│   ├── code_quality.py               ruff findings -> score
│   ├── maintainability.py            radon maintainability index -> score
│   ├── completion.py                 required files + README content -> score
│   ├── report.py                     combines the above into score_report.{md,json}
│   └── PROTECTED_MANIFEST.json       sha256 of every protected file (see below)
│
├── .github/workflows/
│   └── score-submission.yml        the autoscoring pipeline (triggers on PR)
│
├── usecase-1-payment-investigation-agent/
│   ├── README.md                     the brief + quick start
│   ├── main.py                        entry point (do not modify)
│   ├── requirements.txt               use-case-specific deps (pandas, numpy)
│   ├── .env.example                   LLM configuration template
│   ├── sample_submission.json         example output format
│   ├── PROBLEM_STATEMENT.md           what you are building
│   ├── PARTICIPANT_INSTRUCTIONS.md    your three tasks and schedule
│   ├── DATA_NOTES.md                  important data clarifications
│   ├── AI_ARCHITECTURE_REQUIREMENTS.md  required components
│   ├── EVALUATION_CRITERIA.md         how submissions are scored
│   ├── SUBMISSION_GUIDE.md            required output format
│   ├── ARCHITECTURE_HINTS.md          architecture guidance (optional)
│   ├── WHY_METHODS_ONLY.md            why interfaces are empty
│   ├── QUICKSTART.md                  setup + run guide
│   ├── data/
│   │   ├── clients.csv                50 synthetic clients
│   │   ├── payments.csv               184 synthetic payments
│   │   ├── data_dictionary.csv        field descriptions
│   │   └── policies/                  9 policy docs (5 relevant, 4 decoys)
│   ├── questions/
│   │   └── questions.json             10 evaluation questions
│   ├── tools/                         data-access tools (implement these)
│   │   ├── client_tools.py
│   │   ├── payment_tools.py
│   │   └── policy_tools.py
│   ├── rag/                           RAG pipeline (implement this)
│   │   └── pipeline.py
│   └── agent/                         AI agent (implement this)
│       └── agent.py
│
├── usecase-2-production-incident-investigator/
│   ├── README.md                     the brief, spec, and scoring table
│   ├── scoring_hooks.py              this use case's weights + performance thresholds
│   ├── data/
│   │   ├── incident_a_pool_exhaustion/   7 documents + query.txt (high-confidence scenario)
│   │   ├── incident_b_ambiguous_delay/   7 documents + query.txt (low-confidence scenario)
│   │   └── loader.py                       loads one incident's query + document corpus
│   ├── benchmark/perf_bench.py       what scoring_hooks.run_benchmark() calls
│   └── starter/solution.py           copy this into your submission folder
│
└── submissions/                    your work goes here
    └── <your-github-username>/
        └── usecase-2-production-incident-investigator/
            ├── solution.py
            ├── answers.json
            └── README.md
```

**Use case 1** provides method-only interfaces — function signatures and
contracts with no implementations. You implement the tools, RAG pipeline,
and AI agent, then run `python main.py` to produce `submission.json`.

**Use case 2** pairs a still-autoscored code component with a manually
judged output component: `README.md` (the brief), `scoring_hooks.py`
(weights + thresholds), `benchmark/perf_bench.py` (performance harness),
`starter/solution.py` (what you copy into your submission and fill in).
There's no trusted pytest suite here anymore — correctness comes from
reading your submitted `answers.json` against a private key, not from
running your code in CI. Everything under `usecase-*/` other than what
you create in `submissions/` is protected — see below.

---

## Getting started

### Use case 1 — Payment Investigation Agent

```bash
cd usecase-1-payment-investigation-agent
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Add your LLM API key
# Install your chosen LLM SDK, e.g.: pip install openai

python main.py --questions questions/questions.json --output submission.json
```

Follow the reading order in `PARTICIPANT_INSTRUCTIONS.md` → "Before you
start". Key documents: `PROBLEM_STATEMENT.md`, `DATA_NOTES.md`,
`AI_ARCHITECTURE_REQUIREMENTS.md`, `EVALUATION_CRITERIA.md`,
`SUBMISSION_GUIDE.md`.

### Use case 2 — Production Incident Investigator

```bash
pip install -r requirements.txt

./scripts/setup_candidate_branch.sh <your-github-username> usecase-2-production-incident-investigator

cd usecase-2-production-incident-investigator
# implement solution.py, then run it against both incidents yourself -
# there's no trusted test suite to run instead. e.g.:
python -c "
from data.loader import load_incident
import json, sys
sys.path.insert(0, 'submissions/<your-github-username>/usecase-2-production-incident-investigator')
import solution
answers = {}
for name in ['incident_a_pool_exhaustion', 'incident_b_ambiguous_delay']:
    query, corpus = load_incident(name)
    answers[name] = solution.investigate(query, corpus)
print(json.dumps(answers, indent=2))
"
```

---

## Submission requirements

### Use case 1 (manual evaluation)

Run the official command and submit the resulting `submission.json` along
with your source code:

```bash
python main.py --questions questions/questions.json --output submission.json
```

Your output must contain exactly 10 JSON objects (one per question), each
with the required fields: `question_id`, `payment_id`, `answer`,
`citations`, `facts`, `tools_used`. See `SUBMISSION_GUIDE.md` for the
full schema and `sample_submission.json` for a worked example.

### Use case 2 (submit via PR; correctness judged manually)

```
submissions/
└── <your-github-username>/
    └── usecase-2-production-incident-investigator/
        ├── solution.py
        ├── answers.json
        └── README.md
```

`answers.json` is your `investigate()`'s output for both incidents (see
that use case's README, "What you submit") — this, not a live run of
your code, is what correctness is judged against.

Your `README.md` **must** cover, in your own words:

- **Design** — how your solution is structured and why
- **Your understanding of the problem** — what the actual difficulty
  was, in your assessment
- **Why you took the approach you did** — including anything you tried
  and abandoned, and tradeoffs made under the time limit
- **Your name, phone number, and email**

This is graded (Completion, below) and it's what a reviewer reads first.

#### Submitting (use case 2)

```bash
git add submissions/<your-github-username>/
git commit -m "Attempt usecase-2-production-incident-investigator"
git push -u origin submission/<your-github-username>
```

Open a pull request into `main`. This triggers the automated portion
(performance/reusability/code-quality/maintainability/completion)
immediately — check the PR's **Checks** tab (or **Actions** on the repo)
for that report. Correctness is added separately once the organizer
reviews your `answers.json` against the private answer key.

**One participant per PR.** Attempting both use cases? Use case 1 is
submitted as `submission.json` + source code (fully manual evaluation);
use case 2 goes under `submissions/<your-github-username>/` and is
submitted via PR (automated components + manually judged correctness).
Don't mix submissions from different people in one PR.

---

## How grading works (use case 2 only)

Use case 2 is scored on 6 weighted components — weights and thresholds
live in `scoring_hooks.py`. Five of them are still autoscored straight
off your `solution.py`; Correctness is judged manually, by comparing
your submitted `answers.json` against a private answer key (that review
may itself use an LLM as judge — the judging logic isn't part of this
repo, only the submission format is).

| Component | What it measures |
|---|---|
| **Correctness** | Manual: your `answers.json` vs. the private answer key, for both incidents |
| **Performance** | A timed benchmark against declared thresholds — where a wrong-complexity solution loses points correctness alone can't catch |
| **Reusability** | Cyclomatic complexity, function length, and docstring+type-hint coverage on public functions, averaged |
| **Code quality** | `ruff` findings per line, submission files only |
| **Maintainability** | `radon` maintainability index, submission files only |
| **Completion** | Required files present and non-trivial, README actually contains what's asked for above |

Run the automated five yourself before pushing (Correctness will print
as 0 — there's no test suite left for it to run, ignore that number):
```bash
python -m scoring.cli --usecase usecase-2-production-incident-investigator \
  --submission submissions/<your-github-username>/usecase-2-production-incident-investigator
```

**The automated components run the moment your PR is opened against
`main` with a change under `submissions/**`** — the workflow trigger is
path-filtered to that folder specifically so pushing to your branch or
opening the PR is all it takes, no manual step. Correctness itself is
added separately by the organizer's manual review.

Use case 1 is **fully** manual — the organizer runs your code and
evaluates the output manually, with no autoscored components at all.
See `EVALUATION_CRITERIA.md` in that use case's directory for the
scoring rubric.

---

## Protecting the autoscoring engine (use case 2)

**You may only add new files under `submissions/<your-username>/`.**
Everything else — `scoring/`, use case 2's `scoring_hooks.py`,
`benchmark/`, the workflow files, docs, this README — is hashed and
checked on every PR, *before* anything else runs:

```yaml
# .github/workflows/score-submission.yml, first real step
- name: Verify protected files were not modified
  run: python -m scoring.integrity
```

If your PR changes, deletes, or adds anything outside your own
`submissions/` folder, this step fails immediately and your PR is
disqualified — the scoring engine never runs. If you think starter code
has an actual bug, say so in your PR description instead of editing it.

This protection applies to use case 2's autoscoring pipeline. Use case 1
does not use the autoscoring engine — its files are still protected by
the integrity check, but its evaluation is manual.

---

## Using AI assistants well

You're welcome to use AI tools here — that's realistic, not a shortcut.
It's genuinely useful for explaining a concept you're rusty on, reviewing
a solution once you've already spotted a specific concern, and handling
boilerplate. What it won't reliably do: a fluent, obvious-looking first
draft from an assistant tends to look plausible and fail somewhere that
actually matters — read each use case's README carefully and check your
own output against the actual source material (the incident corpus, for
use case 2) before trusting a first pass.

---

Good luck!
