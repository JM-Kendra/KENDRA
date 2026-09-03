#!/usr/bin/env bash
# Runs the three demo-script questions (docs/DOST_DEMO.md Section 2:
# KND-M5-DF-009, KND-M5-DF-020, KND-M5-UN-007) against the loopback api and
# records the responses, so an "online" pass and an "offline" pass (network
# uplink disconnected -- see docs/DOST_DEMO.md Section 8, "Offline
# verification procedure") can be diffed to confirm answering behaves
# identically without internet access. No network beyond loopback: talks
# only to 127.0.0.1:8000 and the api's own container over the compose
# network (via `make verify-chain`).
#
# Usage:
#   scripts/offline_check.sh <phase>       # e.g. online, offline
#   scripts/offline_check.sh diff <YYYYMMDD>
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_BASE="http://127.0.0.1:8000"
OUT_ROOT="$REPO_ROOT/evaluation/offline-checks"

CASE_IDS=(DF-009 DF-020 UN-007)

question_for() {
	case "$1" in
	DF-009) printf '%s' "Within how many days from the EOPT Act's effectivity were implementing rules and regulations to be promulgated, according to RMC No. 3-2024?" ;;
	DF-020) printf '%s' "When did the invoicing provisions of RR No. 7-2024 become effective according to RMC No. 77-2024?" ;;
	UN-007) printf '%s' "What exact email address should a taxpayer use to submit Annex C or Annex D reports?" ;;
	*) echo "unknown case id: $1" >&2; exit 1 ;;
	esac
}

run_phase() {
	local phase="$1"
	local date_dir out_dir
	date_dir="$(date +%Y%m%d)"
	out_dir="$OUT_ROOT/$date_dir"
	mkdir -p "$out_dir"
	echo "Writing to $out_dir"

	for case_id in "${CASE_IDS[@]}"; do
		local question payload response out_file status
		question="$(question_for "$case_id")"
		payload="$(python3 -c 'import json,sys; print(json.dumps({"question": sys.argv[1], "collection_id": "default"}))' "$question")"
		response="$(curl -sf --max-time 30 -X POST "$API_BASE/api/v1/questions" \
			-H "Content-Type: application/json" \
			-d "$payload")"
		out_file="$out_dir/${phase}-${case_id}.json"
		printf '%s' "$response" | python3 -m json.tool > "$out_file"
		status="$(printf '%s' "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
		echo "$case_id: $status"
	done

	make -C "$REPO_ROOT" verify-chain
}

diff_phase() {
	local date_dir="$1"
	local dir="$OUT_ROOT/$date_dir"
	if [[ ! -d "$dir" ]]; then
		echo "no such run directory: $dir" >&2
		exit 1
	fi

	for case_id in "${CASE_IDS[@]}"; do
		local online_file="$dir/online-${case_id}.json"
		local offline_file="$dir/offline-${case_id}.json"
		if [[ ! -f "$online_file" || ! -f "$offline_file" ]]; then
			echo "$case_id: MISSING (expected $online_file and $offline_file)"
			continue
		fi
		if diff -q "$online_file" "$offline_file" > /dev/null 2>&1; then
			echo "$case_id: identical"
		else
			echo "$case_id: DIFFERS"
			diff "$online_file" "$offline_file" || true
		fi
	done
}

if [[ "${1:-}" == "diff" ]]; then
	diff_phase "${2:?usage: offline_check.sh diff <YYYYMMDD>}"
else
	run_phase "${1:?usage: offline_check.sh <phase>}"
fi
