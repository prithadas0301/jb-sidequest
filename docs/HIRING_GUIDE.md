# Hiring Guide (for reviewers, not candidates)

`jb-sidequest` is a 3-use-case, ~1-hour-each hiring sidequest for
graduates and 1–3 YOE candidates. Use case 1 is pure Python/data-structures;
use case 2 is traditional ML with a deliberate leakage trap and class
imbalance; use case 3 is a payment-webhook-themed data-structures problem
(order independence, deduplication, exact money math) that doesn't
require prior payments experience to solve. Everything is autoscored by
GitHub Actions on pull request. This doc covers the parts candidates
don't need.

## One-time repo setup (do this before sending candidates the repo)

1. **Regenerate the protected-files manifest** after any change you make
   outside `submissions/`:
   ```bash
   python scripts/generate_protected_manifest.py
   git add scoring/PROTECTED_MANIFEST.json
   git commit -m "Regenerate protected manifest"
   ```
   Copy the sha256 it prints into the **`PROTECTED_MANIFEST_SHA256`
   repository variable** (Settings → Secrets and variables → Actions →
   **Variables** tab). This variable is **not set** in a fresh checkout —
   set it before the first real candidate run. It's what makes the
   manifest file itself tamper-evident: the expected hash lives outside
   the git tree, so a PR can't edit both the manifest and the value it's
   checked against.

2. **Set the `ML_HOLDOUT_SEED` repository secret** (Settings → Secrets
   and variables → Actions → **Secrets** tab) — any integer, kept
   private. Without it, use case 2 grades against the public fallback
   seed baked into `data/generate_data.py`, which candidates can also see
   and iterate against locally.

3. **Require branch protection on `main`**: require the `score` status
   check to pass, and require pull requests before merging.

4. **Require approval to run workflows from outside/first-time
   contributors** (Settings → Actions → General). **Not optional.**
   `scoring/integrity.py` stops a candidate from scoring higher by
   editing protected files, but only a human approving the workflow run
   stops a PR that edits `.github/workflows/score-submission.yml` itself
   from running its own modified copy — GitHub's `pull_request` trigger
   uses the workflow file as it exists on the PR branch. Actually look at
   the "Files changed" tab for `.github/workflows/**` diffs before
   approving a run.

5. Decide how candidates get access - a shared fork, or invite each as a
   collaborator. Either way, `scripts/setup_candidate_branch.sh` gets
   them a `submission/<name>` branch with their folder started.

## Calibration you should sanity-check before a real run

All three use cases' `PERFORMANCE_THRESHOLDS` (in each `scoring_hooks.py`)
are first-pass estimates, not independently benchmarked on your actual CI
runner:

- **Use case 1**: `wall_clock_seconds` / `peak_memory_kb` for a
  200,000-event stream, window_size=1000, k=10.
- **Use case 2**: `wall_clock_seconds` / `peak_memory_kb` for
  `top_risk_customers` over 3,000,000 rows selecting the top 20.
- **Use case 3**: `wall_clock_seconds` / `peak_memory_kb` for a
  20,000-charge payment ledger (~30k events including refunds/orphans/
  duplicates). Deliberately kept small enough that even an O(n²)
  per-refund-scan reference solution finishes within the workflow's
  20-minute timeout instead of hanging it - don't scale this up without
  also raising the timeout, or a genuinely bad submission could exhaust
  the whole CI job rather than just scoring 0 on this component.

Write a quick correct reference solution for each (an O(log window)
sliding-window tracker for use case 1; a `heapq.nlargest`-based selection
for use case 2; a `charge_id -> amount` index for use case 3), run
`python -m scoring.cli` against it, and adjust `floor`/`target` in the
relevant `scoring_hooks.py` if your CI runner's numbers land somewhere
you didn't expect. Same for use case 2's `AP_FLOOR`/`AP_TARGET` constants
in `tests/test_solution.py` — the synthetic data is calibrated for
roughly a 10% churn rate and a non-trivial-but-learnable signal, but
"non-trivial" was designed, not measured against a real trained model.

## How scoring actually works

Each `usecase-*/scoring_hooks.py` defines 6 weighted components
(`correctness`, `performance`, `reusability`, `code_quality`,
`maintainability`, `completion` — see `scoring/cli.py` for orchestration).
By default `scoring/cli.py` never hard-fails CI purely for a low score —
it produces a report either way. Tampering (see below) is the one thing
that hard-fails unconditionally. If you want a hard minimum, pass
`--fail-under <score>` in the workflow's scoring step.

## Protecting the autoscoring engine (the mechanism)

Candidates may only add new files under `submissions/<their-name>/`.
Everything else is hashed into `scoring/PROTECTED_MANIFEST.json`.
`.github/workflows/score-submission.yml` runs `python -m scoring.integrity`
as its very first step, before installing any dependency or touching a
submission - a PR that changed, deleted, or added a file outside
`submissions/` fails immediately, before the scoring engine ever runs.

Two known, deliberately-accepted limitations (proportionate to a hiring
sidequest, not a paid competition):

- **Cross-candidate protection is best-effort.** The manifest is a
  snapshot from when you last ran `scripts/generate_protected_manifest.py`
  - a previous candidate's merged submission files aren't automatically
  re-protected until you regenerate again. Regenerate + commit after
  each merge if this matters for your process.
- **Use case 2's held-out seed isn't hardened against a same-process
  read.** `tests/test_solution.py` pops `ML_HOLDOUT_SEED` out of
  `os.environ` before a submission's `solution.py` ever runs, which stops
  casual/accidental leakage. It does not stop code that deliberately
  walks `sys.modules` looking for it - true isolation needs a separate
  process/container. Not built here; flag it if you scale this beyond an
  internal hiring exercise.

## Local dry run before sending this to anyone

```bash
pip install -r requirements.txt
python -m scoring.integrity                     # should print "Integrity OK"

./scripts/setup_candidate_branch.sh test-candidate usecase-1-streaming-topk-anomaly
# ... fill in the TODOs in submissions/test-candidate/usecase-1-streaming-topk-anomaly/ ...
python -m scoring.cli --usecase usecase-1-streaming-topk-anomaly \
  --submission submissions/test-candidate/usecase-1-streaming-topk-anomaly
```
