# Limits of Task-Set Reduction in SWE-bench Verified

This repository is the replication package for **Limits of Task-Set Reduction
in SWE-bench Verified: A Temporal Study of Leaderboard Ranking Reliability**.
It evaluates whether task subsets selected from an earlier submission cohort
preserve the ranking of later coding-agent systems.

The study keeps two evaluation environments separate:

- **Open-submission panel:** 2024 selection and 2025 evaluation using the
  traditional SWE-bench Verified result artifacts.
- **Standardized Bash-only panel:** 2025 selection and 2026 evaluation using
  explicit 500-task outcomes from a common mini-SWE-agent environment.

The pipeline uses public result files from the official
[`swe-bench/experiments`](https://github.com/swe-bench/experiments) repository
and the canonical 500 SWE-bench Verified instance identifiers. It does not
invoke an LLM, call a model API, require an API secret, or download execution
images.

## Contents

- `src/`: standard-library Python analysis pipeline
- `configs/`: formal experiment configuration
- `tests/`: unit and integration tests
- `docs/`: protocol, analysis history, and source documentation
- `manuscript/Online_Resource_1_secondary_metrics.csv`: complete secondary
  metrics for all 208 panel-scope-method-budget cells
- `manuscript/Online_Resource_2_reproduction_manifest.pdf`: human-readable
  reproduction manifest
- `manuscript/Online_Resource_2_reproduction_manifest.md`: machine-readable
  manifest source
- `manuscript/Limits_of_Task_Set_Reduction_EMSE_submission.md`: manuscript
  source corresponding to the release

Generated aggregate outputs are included in the archived release. Upstream
binary outcome matrices are not redistributed; immutable source URLs, commits,
filenames, exclusions, and checksums are recorded in the source and
reproduction manifests.

## Reproduce

Python 3.12 or newer is recommended. The analysis uses only the Python standard
library.

```bash
python -m unittest discover -s tests -v
python src/formal_experiment.py --config configs/formal.json --output formal-output
```

To verify the archived formal results after placing them under
`artifacts/github-run-32970788181/unpacked`:

```bash
python manuscript/scripts/sync_result_tables.py --artifact artifacts/github-run-32970788181/unpacked --check
python manuscript/scripts/verify_online_resource_2.py --artifact artifacts/github-run-32970788181/unpacked
```

## Interpretation boundary

The study evaluates public leaderboard records as a measurement system. It
does not identify causal effects of time, model scale, or agent architecture.
The two execution environments are not pooled. A common procedure budget is
not one fixed deployable task set, and task-count reduction is not interpreted
as an equal proportional reduction in runtime or monetary cost.

## Citation

Use the metadata in [`CITATION.cff`](CITATION.cff). The persistent Zenodo DOI
will be added to the release metadata and this file before journal submission.

## License

The replication code is released under the MIT License. Public source datasets
remain governed by their respective licenses and terms.
