# V3 experiment validation

**Assessment:** The corrected local v3 formal run is internally consistent and
suitable for manuscript revision. The GitHub Actions execution and public
archival availability remain to be completed.

## Validated inputs and run

- Configuration: `configs/formal.json`.
- Local output: `artifacts/formal-v3-local-r3`.
- Experiments source commit: recorded in `source_manifest.json`.
- Website source commit: recorded in `source_manifest.json`.
- Data-quality decision: all checks passed.

The classic source contains 133 usable matrices after one unlisted submission
was excluded. The standardized Bash-only source contains 38 usable matrices
after seven missing/invalid full matrices and two score mismatches were
excluded. Both panels retain the canonical 500 task identifiers and are not
pooled.

## Structural checks

- `formal_metrics.csv`: 208 unique panel–scope–method–budget rows.
- `harmonized_metrics.csv`: 208 unique rows based on 10,000 pooled curve
  replicates (five seeds × 2,000).
- `secondary_metrics_online_resource.csv`: all 208 cells with tie-aware top-k,
  pairwise agreement, calibrated MAE, repository coverage, and top-set sizes.
- `curve_band_diagnostics.csv`: raw, cell-wise max-t, and joint max-t driver
  frequencies and critical values.
- `curve_bootstrap_stability.csv`: five-seed 475-task and common-budget checks.
- `random_curve_coupling_sensitivity.csv`: nested-prefix versus
  independent-by-budget random paths.
- Tables 3–11 reproduce from the artifact with
  `manuscript/scripts/sync_result_tables.py --check`.

All tau-b values lie in [-1, 1], all tie-aware top-k Jaccard values lie in
[0, 1], and all top-set size fields are populated.

## Positive control and tests

The 500-task gate expects and observes all 16 combinations of two panels, two
scopes, and four methods. Every primary endpoint has tau-b=1, top-k Jaccard=1,
and zero calibrated score error. The harmonized resampling code also fixes the
full-task endpoint at 1 inside every replicate, including degenerate cluster
draws with no comparable system pair. Twenty-one unit and integration tests
pass.

## Decision checks

The protocol-defined mixed-source pointwise policy gives common reliable
procedure budgets of 500, 500, 500, and 475 tasks for uniform random,
repository-stratified random, entropy, and temporal core. The 10,000-replicate
harmonized pointwise analysis reproduces those budgets with a common 0.80 lower
threshold.

The intentionally conservative raw cell-wise band gives 500 for all four
procedures. Budget-standardized cell-wise and four-cell joint max-t bands give
500, 500, 500, and 475. At 475 tasks, temporal core's standardized all-system
pointwise lower bound is 0.947, its raw lower band is 0.380, and its joint
max-t lower band is 0.890. Across five seeds, the joint value ranges from 0.843
to 0.911 without crossing the 0.80 threshold.

Nested-prefix and independent-by-budget random paths both give 500-task
pointwise and joint max-t decisions for the two stochastic procedures. The
temporal-core first-pass probability at 475 is 0.517 (95% Wilson interval
0.508–0.527); the persistent-rule probability is 0.560 (0.550–0.570).

At 475 tasks, all-system versus cluster-latest task-set Jaccard overlap is
0.951 (open) and 0.927 (standardized) for temporal core. A fixed all-system
selection gives 400 tasks for entropy and 500 for temporal core. Random
fixed-draw rows are omitted because they do not estimate a random procedure.

## Remaining validation limits

- The max-t construction is a custom post hoc sensitivity; it does not
  establish population coverage for a self-selected leaderboard.
- Public leaderboard submissions are self-selected and cluster labels are
  metadata-derived approximations.
- The replication bundle has no public immutable release or DOI yet.
- Author metadata, funding, competing-interest, originality, and contribution
  declarations require author confirmation before journal submission.
