# Submission — usecase-4-production-incident-investigator

**Name**: John Smith
**Email**: john.smith@example.com
**Phone**: +65 8123 4567

## Design

Two stages, kept strictly separate: `rank_documents` (TF-IDF cosine
similarity retrieval — this is genuinely the "R" in RAG, no shortcuts)
and evidence correlation. Correlation itself is a small pipeline of
single-purpose functions: pull an exception signature and the components
it appears against out of the logs (`identify_error_signature`), fall
back to the top-ranked document's components when there's no error
signal at all (`resolve_impacted_components`), check how many other
*document types* independently corroborate that signature
(`correlate_evidence` — this is also where `confidence_score` comes
from), then extract MTTR/remediation from whichever runbook section
actually mentions the relevant keywords rather than just the first one in
the file.

## My understanding of the problem

The retrieval half is the easy part and mostly a solved problem —
TF-IDF against a handful of documents. The actual difficulty is that
"most relevant document" and "root cause" aren't the same thing: the
architecture overview will often rank highly just because it mentions the
right words a lot, without being evidence of anything. What actually
distinguishes a real finding from a plausible-sounding guess is whether
independent sources — logs, deployment history, a runbook, a known
issue, a past incident — agree with each other. And the honest answer
sometimes really is "I don't have enough to go on" — a system that always
reports a confident root cause regardless of how thin the evidence is
isn't more useful than one that occasionally says so.

## Why I took this approach

I anchor everything on the log evidence specifically (which exception
recurs, which components it appears against) rather than on the
retrieval ranking, because retrieval relevance and evidentiary weight
aren't the same signal — a document can be topically relevant without
corroborating anything. `confidence_score` is a direct, simple function
of how many *other* document types mention the same exception/component
(`20 + 15 × corroborating_count`, capped at 100) rather than anything
derived from retrieval scores — I wanted it to be legible and auditable,
not a black box.

I deliberately did **not** try to make this incident-specific. Nothing in
`solution.py` mentions "payment", "pool", or "notification" by name — the
same logic runs unmodified against both incidents, and it happens to
produce a low-confidence result for incident B because that incident
genuinely doesn't have a recurring error signature in its logs, not
because I special-cased it.

One limitation I'm aware of: the component-name regex is a plain
kebab-case pattern match, so it can't distinguish a real service name
from any other hyphenated token that happens to look like one. I
tightened it once already (excluding numeric IDs like `ord-88350`) but a
more robust version would cross-check candidate names against the
architecture document's declared component list.

## What I'd try next with more time

Weight corroboration by document type rather than treating all five
non-log sources equally — a matching known-issue entry (an explicit,
curated signature match) is stronger evidence than a passing mention in
the architecture doc, and the current formula doesn't distinguish them.
