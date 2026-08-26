# V2 experiment validation

**Assessment:** The local v2 formal run is internally consistent and suitable
for manuscript revision. Public archival availability remains unresolved.

The authoritative GitHub Actions execution is run `32962316617` at commit
`eb3119b65cfb48ce758a5d9faea44c1cc6843cd2`. It completed successfully in
8m45s. The downloaded artifact SHA-256 is
`15338bb2fd7292f3e89959f3dcc672748702b99c04197757e07acbedfad37dcd`, exactly
matching the digest reported by GitHub Actions.

## Validated inputs and run

- Experiments source commit: `1faa91cade0562ba62b66c1c99e71f7b72d96f13`.
- Website source commit: `f42505b21a0eb31a9cc1204caafcbe0da6c1a259`.
- Configuration: `configs/formal.json`.
- Local output: `formal-output-v2-local`.
- Data-quality decision: all checks passed.

The classic source contains 133 usable matrices after one unlisted submission
was excluded. The standardized Bash-only source contains 38 usable matrices
after seven missing/invalid full matrices and two score mismatches were
excluded. Both panels retain the canonical 500 task identifiers and are not
pooled.

## Structural checks

- `formal_metrics.csv`: 208 rows and 208 unique
  panel–scope–method–budget keys.
- `harmonized_metrics.csv`: 208 rows and 208 unique keys.
- `fixed_selection_sensitivity.csv`: 208 rows.
- `budget_stability.csv`: 56 rows.
- `selection_overlap.csv`: 52 rows.
- `cluster_mapping.csv`: 167 system records.
- `cluster_sensitivity.csv`: 312 rows.
- `bootstrap_stability.csv`: 52 rows.
- All τ_b values lie in [-1, 1]; all tie-aware top-k Jaccard values lie in
  [0, 1]; top-set size fields are populated.
- Tables 3–9 in the manuscript reproduce from the formal artifact with
  `manuscript/scripts/sync_result_tables.py --check`.

## Positive control and tests

The 500-task gate expects and observes all 16 combinations of two panels, two
scopes, and four methods. Every endpoint has τ_b=1, top-k Jaccard=1, and zero
calibrated score error. Eighteen unit tests pass, including the inclusive
boundary-tie definition and a missing-cell failure for the positive control.

## Decision checks

The predeclared mixed-source pointwise policy gives common reliable procedure
budgets of 500, 500, 500, and 475 tasks for uniform random,
repository-stratified random, entropy, and temporal core, respectively. The
harmonized pointwise analysis reproduces those budgets with a common 0.80 lower
threshold. The simultaneous curve band changes temporal core from 475 to 500;
all four procedures then require 500 tasks.

At 475 tasks, all-system versus cluster-latest task-set Jaccard overlap is
0.951 (open) and 0.927 (standardized) for temporal core. The fixed all-system
selection sensitivity yields procedure budgets 300, 475, 400, and 500, but the
two random rows omit task-selection uncertainty and are diagnostic only.

The RQ1 two-way intervals preserve the directional interpretation. Alternative
cluster definitions materially change several first-passing budgets and the
standardized agent-lineage definition collapses to one cluster. Across five
seeds, the seven-cluster lower-bound range can reach 0.256 at low budgets;
temporal core at 475 in the standardized cluster-latest scope remains exactly
1.0 at both 1,000 and 5,000 bootstrap repetitions.

## Remaining validation limits

- The 300-replicate simultaneous curve analysis has finite Monte Carlo error.
- Public leaderboard submissions are self-selected and cluster labels are
  metadata-derived approximations.
- The replication bundle has no public immutable release or DOI yet.
- Author metadata, funding, competing-interest, and contribution declarations
  require author confirmation before journal submission.
