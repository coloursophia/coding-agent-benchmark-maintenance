# Formal study protocol

## Research identity and claim boundary

This is an empirical software-engineering benchmark-maintenance study. It
estimates temporal changes in the measurement behavior of SWE-bench Verified
and tests whether reduced task sets preserve rankings of later systems. It does
not claim that time causes performance changes, that public submissions are
independent model trials, or that fewer tasks automatically imply proportional
cost savings.

## Why the formal design differs from the pilot

The pilot read the legacy `evaluation/verified/*/results/results.json` format.
The official website also includes a standardized `evaluation/bash-only`
panel whose files explicitly report all 500 task outcomes. The formal study
keeps these environments separate and evaluates two temporal replications:

1. **Open-submission panel:** 2024 task selection, 2025 held-out systems.
2. **Standardized Bash-only panel:** 2025 task selection, 2026 held-out systems
   evaluated with the common mini-SWE-agent scaffold.

The second panel was absent from the pilot and is the strongest time-external
validation. No outcome is transferred between panels during fitting or
evaluation.

## Data sources and reproducibility

- Canonical 500 instance identifiers: official SWE-bench Verified dataset.
- Open-submission outcomes: official `swe-bench/experiments` repository,
  `evaluation/verified/*/results/results.json`.
- Standardized outcomes: the same repository,
  `evaluation/bash-only/*/per_instance_details.json`.
- Submission metadata and published aggregate scores: official
  `swe-bench/swe-bench.github.io` leaderboard data.

Each run resolves and records the current commit SHA of both GitHub sources,
records every requested URL, reconciles task-level outcomes against published
aggregate scores, and stores a SHA-256 digest of each panel matrix. The package
does not redistribute the upstream per-task outcome matrices.

## Inclusion and quality rules

1. Folder names must begin with a valid eight-digit date.
2. Open-submission `resolved` values must be unique canonical IDs; their
   complement is unresolved, following the source format.
3. Included Bash-only files must contain exactly the 500 canonical IDs and
   Boolean `resolved` values. Leaderboard folders without a public
   `per_instance_details.json` file are excluded and enumerated in the quality
   report rather than silently encoded as failures.
4. Recomputed aggregate scores must agree with official leaderboard scores to
   within 0.15 percentage points. This tolerance covers the documented source
   artifacts that use 499 rather than 500 as the published-score denominator;
   larger discrepancies are excluded and enumerated.
5. Every panel-period must meet its predeclared minimum system count.
6. A result folder absent from the official leaderboard metadata is excluded
   from the paper-facing panel and enumerated.
7. Exact duplicate outcome signatures are reported rather than silently
   removed.

## Selectors and baselines

- Uniform random sampling, repeated over deterministic seeds.
- Repository-stratified random sampling, repeated over deterministic seeds.
- Training-period entropy ranking.
- Frozen temporal core-set heuristic from the pilot: repository and difficulty
  strata, favoring discrimination, early/late stability, and nonredundant
  outcome signatures.

The temporal core set is treated as an exploratory selector, not a newly
blinded algorithmic contribution. Its comparison with random baselines is
reported transparently at every task budget.

## Outcomes

Primary:

- Kendall tau-b between the full 500-task ranking and reduced-set ranking on
  later systems.

Secondary:

- top-k overlap;
- pairwise ranking-direction agreement;
- calibrated score mean absolute error;
- repository coverage;
- mean task entropy, solve rate, saturation counts, outcome-signature
  redundancy, and task-difficulty transitions.

## Dependence and uncertainty controls

- Random baselines report empirical intervals across task samples.
- Deterministic selectors report cluster-bootstrap intervals: official agent
  labels for the open-submission panel and model providers for the standardized
  panel.
- Longitudinal task shifts report repository-cluster bootstrap intervals.
- A latest-entry-per-cluster sensitivity analysis reduces repeated variants of
  the same agent or provider.
- The two execution panels are never pooled for inferential claims.

## Decision rule

For each panel, the reliable random-baseline budget is the smallest budget with
mean held-out tau-b at least 0.90 and empirical 2.5th percentile at least 0.85.
For deterministic entropy and temporal-core-set selectors, the descriptive
checkpoint additionally requires a cluster-bootstrap 2.5th percentile of at
least 0.80. Cross-panel claims use the larger of the two panel-specific
budgets. The 500-task endpoint is retained as a positive control.

## Known non-removable threats

- Submission dates do not identify exact harness versions.
- Public leaderboard systems are selected, heterogeneous, and often related.
- Multi-attempt policies and unverified submissions are part of the historical
  open-submission population.
- The 2026 standardized panel is smaller and represents one common scaffold.
- The pilot already inspected the 2025 open-submission panel, so it is a
  development replication rather than a blinded confirmation.
