# Online Resource 2: Reproduction Manifest

Version: manuscript v3.2 source manifest, 2026-08-27

This manifest separates scholarly identification of research objects from the
exact identifiers needed to reproduce the reported analysis. The manuscript
cites the SWE-bench paper, Verified construction account, and versioned
software repositories. The full identifiers below pin the exact materials.

## Frozen upstream sources

| Resource | Scholarly/software citation | Exact version | Retrieval location |
|---|---|---|---|
| SWE-bench Verified canonical task identifiers | Jimenez et al. (2024); OpenAI (2024) | 500-task `princeton-nlp/SWE-bench_Verified` test split | URLs enumerated in `source_manifest.json` |
| Outcome matrices | SWE-bench Team (2026a) | experiments commit `1faa91cade0562ba62b66c1c99e71f7b72d96f13` | https://github.com/swe-bench/experiments/tree/1faa91cade0562ba62b66c1c99e71f7b72d96f13 |
| Leaderboard scores and metadata | SWE-bench Team (2026b) | website commit `f42505b21a0eb31a9cc1204caafcbe0da6c1a259` | https://github.com/swe-bench/swe-bench.github.io/tree/f42505b21a0eb31a9cc1204caafcbe0da6c1a259 |

Collection timestamp recorded by the authoritative run:
`2026-08-26T13:14:23.499910+00:00`.

## Source matrix digests

| Matrix | SHA-256 |
|---|---|
| Open/classic binary outcome matrix | `e477915c5dd68a132995f692da67b0105743f34bd868f636d3b5fec43c1b11e0` |
| Standardized Bash-only binary outcome matrix | `0f5fda63360d75604589e4916057ffc294dd3b4ef6d9cca9552adf651806357d` |

The binary matrices are not redistributed. `source_manifest.json` lists every
immutable API/raw URL required to recollect them and records
`redistributes_upstream_outcome_matrix: false`.

## Authoritative experiment execution

| Field | Value |
|---|---|
| Git repository | https://github.com/coloursophia/coding-agent-benchmark-maintenance |
| Experiment commit | `4bcbd4a2cd259f9722e1fa3eb83fa1e03b79df75` |
| GitHub Actions run | `32970788181` |
| Workflow URL | https://github.com/coloursophia/coding-agent-benchmark-maintenance/actions/runs/32970788181 |
| Completion date | 2026-08-26 |
| Workflow duration | 23 min 38 s |
| Downloaded artifact SHA-256 | `c66da9edd849c36335fb15a687331d2058cb8c900c29264d38b2d06b2070c334` |
| Formal configuration | `configs/formal.json` |
| Python recorded by source manifest | 3.12.14 |

## Required result files

The authoritative artifact contains, at minimum:

- `formal_metrics.csv` (208 panel-scope-method-budget rows);
- `harmonized_curve_metrics.csv` (208 corresponding harmonized rows);
- `secondary_metrics_online_resource.csv` (208 complete secondary-metric rows);
- procedure-budget, budget-selection, fixed-selection, task-overlap,
  alternative-cluster, curve-driver, bootstrap-stability, and coupling
  sensitivity tables;
- `source_manifest.json`, `data_quality_report.json`, cluster mappings, frozen
  cohort files, and the HTML diagnostic report.

Online Resource 1 is `Online_Resource_1_secondary_metrics.csv`, SHA-256
`1f7603e22c4469a39a19459ea63f6c4593301da50bb5c178ae9a7dc979854b26`.

## Verification commands

From the repository root:

```text
python -m unittest discover -s tests -v
python manuscript/scripts/sync_result_tables.py --artifact-dir artifacts/github-run-32970788181/unpacked --check
```

The v3.2 writing workflow must additionally render the final DOCX to PDF/PNG,
inspect every page, audit accessibility and styles, and confirm that all
author-year citations and reference entries are bidirectionally matched.

## Persistent archive status

A public tagged release and persistent archive DOI are required before journal
submission. No DOI is invented here. When assigned, the final DOI will replace
the provisional repository-only citation in the Data and Code Availability
statements and in `CITATION.cff`; this manifest will continue to supply the
exact commits and checksums.
