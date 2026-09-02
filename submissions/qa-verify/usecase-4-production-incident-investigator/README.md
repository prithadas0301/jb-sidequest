# Submission — usecase-4-production-incident-investigator

**Name**: QA Verify
**Email**: qa-verify@example.com
**Phone**: +65 8000 0000

## Design

This is a pipeline verification submission, not a real candidate attempt
— pushed specifically to reconfirm autoscoring still works end-to-end
after recent changes to the repo (README wording trims, the earlier
candidate-cleanup work). It reuses the same retrieval-then-correlation
design as before: `rank_documents` (TF-IDF cosine similarity) feeds a
correlation stage that anchors on the log's dominant error signature,
checks how many other document types corroborate it, and derives
`confidence_score` directly from that corroboration count.

## My understanding of the problem

Same as any real submission: retrieval relevance and evidentiary
corroboration are different signals, and a trustworthy investigator has
to be able to report low confidence honestly when the evidence is thin,
not just when it's convenient.

## Why I took this approach

Reused the previously-verified implementation unchanged, since the goal
here is confirming the *pipeline* (integrity check, scoring, PR
reporting) behaves correctly after the recent repo changes — not
re-deriving a new solution.

## What I'd try next with more time

N/A for a verification submission.
