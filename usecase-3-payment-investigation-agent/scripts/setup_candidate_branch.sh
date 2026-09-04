#!/usr/bin/env bash
# Creates (or reuses) a candidate's submission branch and copies a use
# case's starter files into their submissions/ folder. Run this from the
# root of a clone/fork of this repo.
#
# Usage:
#   ./scripts/setup_candidate_branch.sh <candidate-slug> <usecase-dir>
#
# Example:
#   ./scripts/setup_candidate_branch.sh jane-doe usecase-1-streaming-topk-anomaly
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <candidate-slug> <usecase-dir>" >&2
  echo "  candidate-slug: lowercase, hyphenated, e.g. jane-doe (use your GitHub username)" >&2
  echo "  usecase-dir:    one of the usecase-*/ directories in this repo" >&2
  exit 1
fi

CANDIDATE_SLUG="$1"
USECASE_DIR="$2"
BRANCH="submission/${CANDIDATE_SLUG}"
DEST="submissions/${CANDIDATE_SLUG}/${USECASE_DIR}"

if [ ! -d "$USECASE_DIR" ]; then
  echo "No such directory: $USECASE_DIR" >&2
  echo "Available use cases:" >&2
  ls -d usecase-*/ >&2
  exit 1
fi

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH"
else
  git checkout -b "$BRANCH"
fi

mkdir -p "$DEST"
cp -n "$USECASE_DIR"/starter/* "$DEST"/ 2>/dev/null || true

echo ""
echo "Branch: $BRANCH"
echo "Submission folder: $DEST"
echo ""
echo "Next steps:"
echo "  1. Read $USECASE_DIR/README.md for the full brief"
echo "  2. pip install -r requirements.txt"
echo "  3. Implement the TODOs in $DEST/"
echo "  4. Write $DEST/README.md - design, your understanding of the problem,"
echo "     why you took the approach you did, your name, phone, and email"
echo "  5. python -m scoring.cli --usecase $USECASE_DIR --submission $DEST"
echo "  6. git add $DEST && git commit -m \"Attempt $USECASE_DIR\""
echo "  7. git push -u origin $BRANCH"
echo "  8. Open a pull request into main - this triggers autoscoring, see"
echo "     the Actions tab for your score report"
echo ""
echo "Repeat step 3 onward (with a different usecase-dir) if you're"
echo "attempting another use case too - same branch/folder, another"
echo "submissions/${CANDIDATE_SLUG}/<usecase>/ subfolder."
