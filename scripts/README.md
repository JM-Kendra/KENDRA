# Scripts

Reviewed, reproducible developer and operational scripts belong here. Scripts must not embed secrets or depend on committed runtime data.

Validate the tracked Milestone 5 dataset mechanically and bind it to the ignored, owner-approved source manifest with:

```bash
python3 scripts/validate_gold_cases.py evaluation/gold_cases.json \
  --manifest document-repository/approved-samples/APPROVAL_MANIFEST.json
```

Passing this command does not constitute expert review or adjudication. It checks structure, counts, page ranges, hashes, manifest alignment, and the recorded v2 page correction only.

Create hash-bound, independent Reviewer A and Reviewer B worksheets plus an adjudication log under the ignored run area with:

```bash
python3 scripts/prepare_m5_adjudication.py evaluation/gold_cases.json \
  evaluation/runs/M5-adjudication/<run-id>
```

The generator is frozen to the exact v2 candidate hash and refuses to overwrite a non-empty packet directory.
