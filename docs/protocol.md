# Pilot protocol

## Research identity

This is an empirical software-engineering measurement study with a method
component. It is not an evaluation of a newly run coding model and does not
make causal claims about model or agent improvements.

## Sources

- Canonical instance IDs: Hugging Face datasets server for
  `princeton-nlp/SWE-bench_Verified`, test split.
- Submission directories and outcomes: official `swe-bench/experiments`
  repository, `evaluation/verified/*/results/results.json`.

Every downloaded payload is represented in a manifest with its source URL.
The workflow records collection time, Python version, runner platform, and a
SHA-256 digest of the outcome matrix.

## Inclusion rules

1. The directory name must begin with an eight-digit date.
2. `results/results.json` must be valid JSON and contain a list-valued
   `resolved` field.
3. Only canonical Verified instance IDs are counted.
4. A canonical instance absent from `resolved` is treated as not resolved,
   matching the leaderboard's aggregate scoring convention.

## Temporal design

The 2024 submissions form the task-selection period. The 2025 submissions are
never used to choose tasks or tune the proposed selector. They are used once
as the held-out evaluation period. Sensitivity analyses use early/late splits
inside 2024 only.

## Methods

- Random: uniform task sampling, repeated across deterministic seeds.
- Repository-stratified random: proportional allocation by source repository,
  repeated across deterministic seeds.
- Entropy: highest binary entropy on 2024 outcomes.
- Temporal core set: proportional allocation across repository and 2024
  difficulty strata. Within each stratum, tasks are preferred when they have
  high discrimination, stable early/late-2024 solve rates, and non-redundant
  submission outcome signatures.

## Metrics

- Kendall tau-b of held-out full vs subset rankings (primary).
- Top-10 system overlap.
- Pairwise direction agreement.
- Mean absolute error after fitting a linear calibration on 2024 submissions.
- Repository coverage.

Random baselines are summarized by mean and empirical 2.5/97.5 percentiles.

## Pilot decision rule after design review

The first exploratory selector did not reach the original 100-task tau-b
threshold and was therefore not promoted as the paper's contribution. The
revised study treats temporal benchmark discrimination and the empirically
required task budget as the primary questions.

The pilot is feasible when data retrieval is complete, at least 100 result
files are usable, and both temporal periods contain at least 30 submissions.
A longitudinal signal is present when mean task entropy changes by at least
0.03 and the number of near-saturated tasks changes by at least 50. A reduced
budget is considered viable when repository-stratified random sampling reaches
mean held-out tau-b of at least 0.90. The pilot examines budgets through 250
tasks and uses 200 as its primary feasibility checkpoint. Passing this pilot
does not establish publication-level superiority; the formal study must add
lineage-blocked validation and uncertainty analyses.

## Threat controls

- Submission variants are not assumed independent.
- Year comparisons are descriptive, not causal.
- Task-count reduction is not equated with monetary or wall-clock savings.
- Results apply directly only to SWE-bench Verified and its public submissions.
- The formal study must reconstruct system-family lineages from metadata before
  inferential comparisons.
