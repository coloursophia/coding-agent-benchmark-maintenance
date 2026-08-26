# Corrected Formal Experiment Validation

**Assessment:** Ready for manuscript use, with the stated construct and
external-validity limitations.

**Validated run:** GitHub Actions run 32747736415, completed successfully on
2026-08-24 at commit `5d012416189c888948c99b3544e4f8cf4175b165`.

**Artifact:** `artifacts/github-run-32747736415.zip`

**Artifact SHA-256:**
`deb302cb6b41eeddbc17e066a6535e485e7c7a1be9a98b58115bd3df4c26793b`

## Validation scope

- Confirmed that the downloaded ZIP digest matches the digest reported by
  GitHub Actions.
- Confirmed 208 unique metric rows: 2 panels x 2 dependence scopes x 4
  methods x 13 budgets.
- Found no duplicate panel-scope-method-budget cells and no missing primary
  rank metrics.
- Independently recomputed all nine threshold-sensitivity decisions directly
  from `formal_metrics.csv`.
- Confirmed the 500-task positive control: 8 expected rows, 8 observed rows,
  no failures.
- Confirmed source commits and matrix digests against the source manifest and
  data-quality report.
- Ran all 16 unit tests, including the non-monotone common-budget regression;
  all passed.

## Corrected primary results

| Method | Exact common budget | Task reduction |
|---|---:|---:|
| Repository-stratified random | 500 | 0% |
| Training-period entropy | 500 | 0% |
| Temporal core set | 475 | 5% |

The common budget is the smallest single budget that passes every panel and
dependence scope at that exact budget. It is not the maximum of cell-specific
minimum passing budgets.

## Threshold sensitivity

| Policy | Repository-stratified random | Entropy | Temporal core set |
|---|---:|---:|---:|
| Lenient | 500 | 250 | 475 |
| Primary | 500 | 500 | 475 |
| Strict | 500 | 500 | 475 |

## Material correction

The prior aggregation treated pass/fail status as monotone in task budget.
That assumption is empirically false for deterministic selectors. In the
standardized Bash-only panel's cluster-latest scope, entropy passes the primary
cell rule at 150, 200, 250, and 300 tasks; fails at 400, 450, and 475 tasks;
and passes again at the 500-task positive control. At 400 tasks, tau-b is
approximately 0.878 and the cluster-bootstrap 2.5th percentile is
approximately 0.471. Therefore, the former 400-task robust entropy decision
was invalid. The corrected exact-common-budget decision is 500 tasks.

## Provenance

| Item | Value |
|---|---|
| SWE-bench experiments commit | `1faa91cade0562ba62b66c1c99e71f7b72d96f13` |
| SWE-bench website commit | `f42505b21a0eb31a9cc1204caafcbe0da6c1a259` |
| Classic outcome-matrix SHA-256 | `e477915c5dd68a132995f692da67b0105743f34bd868f636d3b5fec43c1b11e0` |
| Bash-only outcome-matrix SHA-256 | `0f5fda63360d75604589e4916057ffc294dd3b4ef6d9cca9552adf651806357d` |
| Canonical tasks | 500 |
| Usable classic submissions | 133 |
| Usable Bash-only submissions | 38 |

## Remaining limitations

- The public leaderboard is an observational submission ecosystem, not a
  randomized sample of systems.
- Related systems are only approximately controlled through declared family
  or provider clusters.
- Public matrices expose one outcome per task and cannot estimate run-to-run
  agent variance.
- Submission dates do not identify exact harness versions.
- The two execution formats are intentionally not pooled.
- The study evaluates ranking preservation within SWE-bench Verified and does
  not establish task correctness, contamination freedom, proportional runtime
  savings, or generalization to other benchmarks.
