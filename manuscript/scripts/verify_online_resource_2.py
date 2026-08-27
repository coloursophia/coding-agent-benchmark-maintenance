#!/usr/bin/env python3
"""Verify the Online Resource 2 inventory against an experiment artifact."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


EXPECTED_FILES = (
    "analysis_history.md",
    "bootstrap_stability.csv",
    "budget_stability.csv",
    "cluster_mapping.csv",
    "cluster_sensitivity_decisions.csv",
    "cluster_sensitivity.csv",
    "curve_band_diagnostics.csv",
    "curve_bootstrap_stability.csv",
    "data_quality.json",
    "fixed_selection_decisions.csv",
    "fixed_selection_sensitivity.csv",
    "formal_metrics.csv",
    "formal_results.json",
    "harmonized_decisions.csv",
    "harmonized_metrics.csv",
    "longitudinal.csv",
    "random_curve_coupling_sensitivity.csv",
    "report.html",
    "secondary_metrics_online_resource.csv",
    "selection_overlap.csv",
    "source_manifest.json",
    "summary.md",
    "threshold_sensitivity.csv",
)

METRIC_FILES = (
    "formal_metrics.csv",
    "harmonized_metrics.csv",
    "secondary_metrics_online_resource.csv",
)

KEY_FIELDS = ("panel", "scope", "method", "budget")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("manuscript/Online_Resource_2_reproduction_manifest.md"),
    )
    args = parser.parse_args()

    artifact = args.artifact.resolve()
    if not artifact.is_dir():
        raise SystemExit(f"Artifact directory does not exist: {artifact}")
    if not args.manifest.is_file():
        raise SystemExit(f"Manifest does not exist: {args.manifest}")

    manifest_text = args.manifest.read_text(encoding="utf-8")
    forbidden = (
        "--artifact-dir",
        "harmonized_curve_metrics.csv",
        "data_quality_report.json",
    )
    present_forbidden = [token for token in forbidden if token in manifest_text]
    if present_forbidden:
        raise SystemExit(f"Obsolete manifest tokens: {present_forbidden}")

    required_command = (
        "python manuscript/scripts/sync_result_tables.py --artifact "
        "artifacts/github-run-32970788181/unpacked --check"
    )
    if required_command not in manifest_text:
        raise SystemExit("Correct table-verification command is absent from manifest")

    missing_mentions = [name for name in EXPECTED_FILES if f"`{name}`" not in manifest_text]
    if missing_mentions:
        raise SystemExit(f"Artifact files absent from manifest inventory: {missing_mentions}")

    missing_files = [name for name in EXPECTED_FILES if not (artifact / name).is_file()]
    if missing_files:
        raise SystemExit(f"Artifact files do not exist: {missing_files}")

    for name in METRIC_FILES:
        rows = read_rows(artifact / name)
        if len(rows) != 208:
            raise SystemExit(f"{name}: expected 208 rows, found {len(rows)}")
        keys = {tuple(row[field] for field in KEY_FIELDS) for row in rows}
        if len(keys) != 208:
            raise SystemExit(f"{name}: expected 208 unique keys, found {len(keys)}")
        if any(row.get("tau_b", "") == "" for row in rows):
            raise SystemExit(f"{name}: missing tau_b values")
        controls = [row for row in rows if row["budget"] == "500"]
        if len(controls) != 16 or any(float(row["tau_b"]) != 1.0 for row in controls):
            raise SystemExit(f"{name}: full-budget positive control is not exact and complete")

    print(
        "Online Resource 2 verification passed: "
        f"{len(EXPECTED_FILES)} files exist; "
        "three metric tables each contain 208 unique cells and 16 exact controls."
    )


if __name__ == "__main__":
    main()
