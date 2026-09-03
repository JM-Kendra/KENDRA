#!/usr/bin/env bash
# Mechanical ADR-014 one-commit check: a release tag is only cut when the
# candidate commit (HEAD), the drill's report.json source_revision, the
# drill's pipeline_revision (all documents, from the drill's own database
# snapshot written to <drill-run-dir>/pipeline_revision.txt before teardown
# -- docs/DOST_DEMO.md Section 10, step 8a), and the release evaluation's
# report.json source_revision all equal the same commit. This replaces a
# prose argument that they are "close enough" -- demo-dost-v1.3's mistake
# (docs/DOST_DEMO.md Section 6.4).
#
# Usage: scripts/tag_evidence.sh <tag> <drill-run-dir> <release-run-dir>
set -euo pipefail

TAG="${1:?usage: tag_evidence.sh <tag> <drill-run-dir> <release-run-dir>}"
DRILL="${2:?usage: tag_evidence.sh <tag> <drill-run-dir> <release-run-dir>}"
RELEASE="${3:?usage: tag_evidence.sh <tag> <drill-run-dir> <release-run-dir>}"

read_source_revision() {
	python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['source_revision'])" "$1/report.json"
}

candidate="$(git rev-parse HEAD)"
drill_source="$(read_source_revision "$DRILL")"
release_source="$(read_source_revision "$RELEASE")"

pr_file="$DRILL/pipeline_revision.txt"
pipeline_ok=0
if [[ -f "$pr_file" ]]; then
	# One distinct value, non-empty, equal to the candidate.
	values="$(grep -v '^[[:space:]]*$' "$pr_file" || true)"
	count="$(printf '%s\n' "$values" | grep -c . || true)"
	if [[ "$count" -eq 1 && "$values" == "$candidate" ]]; then
		drill_pipeline="$values"
		pipeline_ok=1
	else
		drill_pipeline="$(printf '%s' "$values" | tr '\n' ',' | sed 's/,$//')"
		[[ -z "$drill_pipeline" ]] && drill_pipeline="<empty>"
	fi
else
	drill_pipeline="<absent>"
fi

echo "candidate:            $candidate"
echo "drill  source_revision:   $drill_source"
echo "drill  pipeline_revision: $drill_pipeline"
echo "release source_revision:  $release_source"

if [[ "$drill_source" == "$candidate" && "$pipeline_ok" -eq 1 && "$release_source" == "$candidate" ]]; then
	echo "EQUAL"
	exit 0
else
	echo "NOT EQUAL"
	exit 1
fi
