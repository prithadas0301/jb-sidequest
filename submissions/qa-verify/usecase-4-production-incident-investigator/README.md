# Submission — usecase-4-production-incident-investigator

**Name**: QA Verify
**Email**: qa-verify@example.com
**Phone**: +65 8000 0000

## Design

Pipeline verification submission, not a real candidate attempt — pushed
to confirm autoscoring still works after converting `known_issues.md` to
a multi-row `known_issues.csv` catalog. Reuses the same
retrieval-then-correlation design as before, unchanged: `rank_documents`
(TF-IDF cosine similarity) feeds a correlation stage anchored on the
log's dominant error signature, checked against every corpus document
regardless of format (markdown or CSV), since correlation here is plain
substring matching over raw text either way.

## My understanding of the problem

Same as any real submission: retrieval relevance and evidentiary
corroboration are different signals, and the correlation step shouldn't
care what file format a piece of evidence happened to arrive in.

## Why I took this approach

Reused the previously-verified implementation unchanged — the goal here
is confirming the corpus format change (CSV alongside markdown) doesn't
break anything, not re-deriving a new solution.

## What I'd try next with more time

N/A for a verification submission.
