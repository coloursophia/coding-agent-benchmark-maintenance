# Writing Baseline: Temporal Reliability of Reduced SWE-bench Verified Task Sets

**Baseline status:** locked for manuscript drafting  
**Experiment status:** complete and independently reproduced in GitHub Actions  
**Last substantive experiment commit:** `538cc40c402ed538849935555a3cc9c60a427d84`  
**Final cloud run:** [Formal Study - Benchmark Discriminative Power #3](https://github.com/coloursophia/coding-agent-benchmark-maintenance/actions/runs/32740664311)  
**Final artifact:** [swe-bench-formal-discriminative-power-study](https://github.com/coloursophia/coding-agent-benchmark-maintenance/actions/runs/32740664311/artifacts/9525182781)

This file is the authoritative handoff to a writing AI. Numerical results,
claim boundaries, terminology, and study identity below must not be changed
without checking the replication package. Do not return to the rejected
build-failure-log topic.

## 1. Locked paper identity

### English title

**Limits of Task-Set Reduction in SWE-bench Verified: A Temporal Study of
Leaderboard Ranking Reliability**

### Chinese working title

**SWE-bench Verified任务集缩减的局限：排行榜排序可靠性的时间性研究**

### Target journal

**Empirical Software Engineering (EMSE)**

- Manuscript type: empirical study / benchmark-maintenance study.
- The journal's recent publication pattern includes benchmark and tool
  evolution studies, replications, methodological audits, and reproducibility
  studies.
- EMSE was not on the 2025 Chinese Academy of Sciences international journal
  warning list. Recheck the current list immediately before submission.

### Research identity

This is a **secondary-data longitudinal empirical software-engineering study**
of benchmark measurement reliability. It is not:

- an LLM or coding-agent performance paper;
- a new coding-agent framework;
- a new task-selection algorithm paper;
- a causal study of model progress;
- a test-oracle correction study;
- a continuation of the rejected build-log-structure experiment.

## 2. Direction change and status of the old topic

### Rejected direction

The original direction asked whether build-failure log structure changes an
LLM coding agent's self-repair performance. Its pilot did not provide evidence
for the expected effect. That direction is closed and must not appear as the
paper's motivation, method, result, or future experiment.

### Current publishable direction

The paper studies whether smaller subsets of an evolving coding-agent
benchmark preserve the full benchmark's ordering of later systems. It treats
SWE-bench Verified as a measurement instrument whose discriminative behavior
and task-budget requirements may change as submitted systems improve and the
evaluation environment evolves.

### Original idea, publishable question, contribution, and application

| Layer | Locked formulation |
|---|---|
| Original idea | Large coding-agent benchmarks may contain redundant tasks and may be reducible. |
| Publishable question | Do task subsets selected from earlier outcomes preserve the full 500-task ranking of later systems across two evaluation panels and after controlling related-system dependence? |
| Method contribution | A frozen time-forward, two-panel, dependence-aware protocol for making task-budget decisions with explicit uncertainty, threshold sensitivity, and a full-benchmark positive control. |
| Empirical contribution | The apparent large task reduction from the pilot does not generalize; related-system dependence eliminates the apparent saving of random sampling. |
| Engineering application | Periodic benchmark-maintenance audits can test whether a reduced evaluation set still preserves rankings before it is operationally adopted. |
| Overclaim to avoid | The study does not establish a universal 400-task benchmark, proportional cost savings, a new selection algorithm, or causal model progress. |

## 3. Research gap and closest research traditions

The paper sits at the intersection of five established traditions:

1. coding-agent benchmark construction and validity;
2. SWE-bench leaderboard and ecosystem audits;
3. test adequacy and result-label correction;
4. benchmark/tool evolution and replication;
5. test-suite reduction, prioritization, and representative subset selection.

Existing research already covers important neighboring questions:

- [SWE-bench](https://arxiv.org/abs/2310.06770) established repository-level
  issue resolution as an evaluation task.
- [What's in a Benchmark? The Case of SWE-Bench in Automated Program Repair](https://doi.org/10.1145/3786583.3786904)
  analyzes the SWE-bench leaderboard ecosystem, including 133 Verified
  entries. Therefore, this manuscript must not claim to be the first general
  analysis of SWE-bench submissions.
- [UTBoost: Rigorous Evaluation of Coding Agents on SWE-Bench](https://arxiv.org/abs/2506.09289)
  studies test inadequacy and parser/annotation errors and reports resulting
  ranking changes. This manuscript does not correct test oracles or labels.
- [Tools and benchmarks evolve: what is their impact on parameter tuning in
  SBSE experiments?](https://doi.org/10.1007/s10664-025-10733-y) establishes
  benchmark/tool evolution and replication as a current EMSE research concern.
- [An audit of machine learning experiments on software defect prediction](https://doi.org/10.1007/s10664-025-10797-w)
  demonstrates EMSE's interest in experimental validity, out-of-sample design,
  and reproducibility.

### Precise gap

Existing work does not answer whether a task budget learned from earlier
coding-agent outcomes preserves rankings of later systems across distinct
evaluation panels, nor whether such a decision survives removal of related
system variants. The present study addresses that bounded gap.

Do not write that no prior work studies benchmark reliability, benchmark
evolution, subset selection, or leaderboard validity. The novelty lies in the
specific temporal and dependence-aware task-budget evaluation, not in those
general concepts.

## 4. Research questions

Use three research questions.

**RQ1 — Temporal measurement shift.** How do task solve rates and task-level
discrimination change between earlier and later SWE-bench Verified submission
cohorts in open and standardized evaluation panels?

**RQ2 — Time-forward ranking fidelity.** To what extent do task subsets
selected exclusively from earlier-period outcomes preserve the full 500-task
ranking of later systems?

**RQ3 — Reliable task budgets.** What is the smallest task budget that meets
predeclared ranking-reliability thresholds across panels, and how do decisions
change under related-system and threshold sensitivity analyses?

Do not formulate a hypothesis that entropy selection must win. The temporal
core-set selector is exploratory and its weak result must be reported.

## 5. Data sources and frozen provenance

### Official sources

- Canonical task identifiers: official SWE-bench Verified dataset, 500 tasks.
- Per-system outcomes: official
  [`swe-bench/experiments`](https://github.com/swe-bench/experiments)
  repository.
- Published scores and metadata: official
  [`swe-bench/swe-bench.github.io`](https://github.com/swe-bench/swe-bench.github.io)
  repository.

### Source commits used in the final verified run

- `swe-bench/experiments`: `1faa91cade0562ba62b66c1c99e71f7b72d96f13`
- `swe-bench/swe-bench.github.io`: `f42505b21a0eb31a9cc1204caafcbe0da6c1a259`

### Outcome-matrix digests

- Open/classic matrix SHA-256:
  `e477915c5dd68a132995f692da67b0105743f34bd868f636d3b5fec43c1b11e0`
- Standardized Bash-only matrix SHA-256:
  `0f5fda63360d75604589e4916057ffc294dd3b4ef6d9cca9552adf651806357d`

The replication package records every requested URL and does not redistribute
the upstream outcome matrices.

## 6. Study panels

The two panels are analyzed separately and are never pooled for inferential
claims.

| Panel | Selection period | Held-out period | Selection systems | Held-out systems | Cluster variable | Top-k |
|---|---:|---:|---:|---:|---|---:|
| Open-submission | 2024 | 2025 | 51 | 78 | Official agent family | 10 |
| Standardized Bash-only | 2025 | 2026 | 27 | 11 | Model provider | 5 |

Interpretation rule:

- The open-submission 2024→2025 comparison is a **development replication**
  because its 2025 outcomes were inspected during the pilot.
- The standardized Bash-only 2025→2026 comparison is the
  **time-external replication** because its 2026 outcomes were absent from the
  pilot.
- Submission dates do not identify exact evaluation-harness versions. The
  study therefore does not interpret year as a causal treatment and does not
  pool the two environments.

## 7. Inclusion and data-quality rules

### Open/classic source

- Directories discovered: 134.
- Usable systems: 133.
- Excluded because absent from official leaderboard metadata:
  `20251127_openhands_claude-opus-4-5`.
- Duplicate resolved IDs: 0.
- Noncanonical resolved IDs: 0.
- Included score-reconciliation failures: 0.
- Maximum included published-score difference: 0.00 percentage points.

### Standardized Bash-only source

- Directories discovered: 47.
- Usable explicit 500-task matrices: 38.
- Excluded for missing or invalid per-instance matrices: 7.
- Excluded for a published-score mismatch above tolerance: 2:
  `20250720_mini-v0.0.0-claude-3-7-sonnet-20250219` and
  `20260226_mini-v2.0.0_gemini-3-pro-high`.
- Included score-reconciliation failures: 0.
- Maximum included published-score difference: 0.13 percentage points.

The allowed reconciliation tolerance is 0.15 percentage points. It covers two
source artifacts whose published scores use a 499- rather than 500-task
denominator. Larger mismatches are excluded and enumerated, never silently
converted to failures.

### Additional quality checks

- Canonical tasks: 500.
- Exact duplicate outcome-signature groups in every panel-period: 0.
- Cross-format folder overlap: 0.
- Positive-control rows expected/observed: 8/8.
- Positive-control failures: 0.
- Overall data-quality decision: **PASS**.

## 8. Experimental design

### Task budgets

`25, 50, 75, 100, 125, 150, 200, 250, 300, 400, 450, 475, 500`

The 500-task endpoint is a mandatory positive control.

### Selection methods and baselines

1. uniform random sampling;
2. repository-stratified random sampling;
3. training-period entropy ranking;
4. frozen temporal core-set heuristic from the pilot.

The temporal core set combines repository and difficulty strata with
discrimination, early/late stability, and outcome-signature nonredundancy. It
must be described as an exploratory heuristic, not a novel algorithmic
contribution.

### Evaluation scopes

1. **All systems:** all included systems in the selection and held-out periods.
2. **Latest per cluster:** in both periods, retain only the latest system in
   each official agent-family cluster (open panel) or model-provider cluster
   (standardized panel), then reselect tasks and reevaluate held-out rankings.

The second scope is not merely a post-hoc deletion from the final table; it
changes both task selection and held-out evaluation.

### Repetitions and uncertainty

- Random task samples: 500 deterministic-seed repetitions for every random
  method, budget, panel, and scope.
- Deterministic-selector system-cluster bootstrap: 1,000 repetitions.
- Longitudinal repository-cluster bootstrap: 2,000 repetitions.
- Random-baseline intervals vary task samples.
- Deterministic-selector intervals resample official agent-family or
  model-provider clusters.
- Temporal task-shift intervals resample source repositories.

### Outcomes

Primary outcome:

- Kendall tau-b between the full 500-task system ranking and the reduced-task
  ranking in the later period.

Secondary outcomes:

- top-k overlap;
- pairwise ranking-direction agreement;
- calibrated score mean absolute error;
- repository coverage;
- mean task solve rate and binary entropy;
- discriminative and near-saturated task counts;
- task-difficulty transitions and outcome-signature redundancy.

### Primary decision thresholds

- Mean held-out Kendall tau-b at least 0.90.
- Repository-stratified random empirical 2.5th percentile at least 0.85.
- Deterministic selector cluster-bootstrap 2.5th percentile at least 0.80.
- A paper-facing budget must pass in both panels and in both the all-system and
  latest-per-cluster scopes at the same exact budget. The reported robust
  budget is the smallest scanned budget that passes all four cells
  simultaneously; it is not obtained by aggregating cell-specific minima.

### Threshold-sensitivity policies

| Policy | Mean tau-b | Random lower bound | Deterministic lower bound |
|---|---:|---:|---:|
| Lenient | 0.85 | 0.80 | 0.75 |
| Primary | 0.90 | 0.85 | 0.80 |
| Strict | 0.95 | 0.90 | 0.85 |

## 9. Locked numerical results

### RQ1 — Temporal measurement shift

| Panel | Years | Systems | Mean solve-rate change | Repository-bootstrap 95% interval | Mean entropy change | Repository-bootstrap 95% interval |
|---|---|---|---:|---|---:|---|
| Open-submission | 2024→2025 | 51→78 | +0.236 | [+0.213, +0.261] | -0.049 | [-0.096, +0.029] |
| Standardized Bash-only | 2025→2026 | 27→11 | +0.158 | [+0.125, +0.175] | -0.292 | [-0.332, -0.203] |

Interpretation:

- Both later cohorts have higher mean task solve rates.
- The open-panel entropy interval crosses zero; do not call its entropy change
  statistically clear or definitive.
- The standardized-panel entropy change is negative throughout the interval,
  providing evidence that task-level discrimination decreased in that panel.
- These are descriptive temporal changes, not causal effects of time, model
  scale, or agent architecture.

### RQ2/RQ3 — All-system minimum reliable budgets

| Panel | Repository-stratified random | Entropy | Temporal core set |
|---|---:|---:|---:|
| Open-submission | 150 | 400 | 150 |
| Standardized Bash-only | 450 | 100 | 475 |
| Cross-panel all-system decision | 450 | 400 | 475 |

These are not the final paper-facing budgets because they do not yet apply the
latest-per-cluster dependence sensitivity.

### Related-system sensitivity: latest per cluster

| Panel | Repository-stratified random | Entropy | Temporal core set |
|---|---:|---:|---:|
| Open-submission | 150 | 400 | 150 |
| Standardized Bash-only | 500 | 300 | 475 |

The standardized-panel repository-stratified result changes from 450 to 500.
This is substantively important: related system variants make the all-system
random-sampling result too optimistic.

### Final robust cross-panel decisions

| Method | Robust task budget | Reduction from 500 | Paper interpretation |
|---|---:|---:|---|
| Repository-stratified random | **500** | **0%** | No reliable task reduction survives both panels and dependence sensitivity. |
| Entropy | **500** | **0%** | No primary-policy reduction passes every panel and dependence scope at one exact budget. |
| Temporal core set | **475** | **5%** | Only marginal reduction; it is not a successful method contribution. |

These three numbers—**500 / 500 / 475**—are the principal paper-facing task-
budget result. Do not substitute the all-system-only values 450 / 400 / 475 or
aggregate cell-specific minima. A common budget must pass every requested
panel-scope cell at that same exact budget because fidelity is not monotone in
budget for deterministic selectors.

### Reliability-threshold sensitivity

| Policy | Repository-stratified random | Entropy | Temporal core set |
|---|---:|---:|---:|
| Lenient | 500 (0%) | 250 (50%) | 475 (5%) |
| Primary | 500 (0%) | 500 (0%) | 475 (5%) |
| Strict | 500 (0%) | 500 (0%) | 475 (5%) |

Interpretation:

- The negative random-sampling result is unchanged under all three policies.
- Entropy permits a 250-task budget only under the lenient rule. Under the
  primary and strict policies it requires the full 500 tasks.
- The temporal core-set conclusion is unchanged and weak under every policy.
- Entropy fidelity is visibly non-monotone in the standardized cluster-latest
  scope: budgets 150–300 pass the primary cell rule, budgets 400–475 fail, and
  the 500-task positive control passes. This invalidates any aggregation based
  on monotone pass/fail assumptions.

### Pilot correction

The pilot suggested that approximately 150 tasks might be sufficient. The
formal experiment rejects that as a general paper-facing conclusion. It holds
only in the developmental open panel for selected methods and fails the
time-external standardized panel and/or the related-system sensitivity.

## 10. Main findings to write

The Results and Discussion must center the following findings in this order:

1. **The pilot's large task-reduction result does not generalize.** A
   time-external standardized panel requires far larger budgets.
2. **Related-system dependence changes the conclusion.** The apparent
   450-task random-sampling saving disappears when retaining the latest system
   in each related cluster.
3. **Simple entropy selection is not robust under the primary policy.** It
   permits a 50% reduction only under the lenient sensitivity rule and requires
   the full benchmark under the primary and strict rules.
4. **The exploratory temporal core set is not successful as a method
   contribution.** Its robust budget is 475 tasks and it does not justify an
   algorithm paper.
5. **Benchmark maintenance is periodic, not one-time.** A task budget supported
   by an earlier cohort should be revalidated against later systems before
   operational adoption.

The negative result is publishable evidence. Do not try to hide it or turn the
paper into an entropy-algorithm success story.

## 11. Permitted and prohibited claims

### Permitted

- The 150-task pilot conclusion did not generalize to the time-external panel.
- Related-system dependence materially changed the random-baseline budget.
- In the observed panels, entropy selection required all 500 tasks under the
  primary and strict reliability thresholds.
- Under the lenient sensitivity rule, entropy selection admitted a 250-task
  common budget, but this does not replace the primary conclusion.
- Repository-stratified random sampling required all 500 tasks under the
  robust decision rule.
- The temporal core-set heuristic offered only a 5% robust reduction.
- The study provides a reproducible time-forward protocol for evaluating task-
  budget reliability.

### Prohibited

- “Four hundred tasks are sufficient for all coding-agent benchmarks.”
- “The method reduces total evaluation cost by 20%.” Runtime, setup, caching,
  and fixed costs were not measured.
- “Benchmark performance improved because of time/model scale/agent design.”
- “Entropy selection is a novel algorithm.”
- “The study repairs SWE-bench test-oracle or annotation errors.”
- “The two panels are interchangeable or statistically pooled.”
- “The 2025 open panel is blinded confirmation.”
- “The temporal core set outperforms all baselines.”
- “This is the first study of the SWE-bench leaderboard or benchmark
  reliability.”

## 12. Title and terminology controls

### Final title

Use:

> **Limits of Task-Set Reduction in SWE-bench Verified: A Temporal Study of
> Leaderboard Ranking Reliability**

### Do not place in the title

`optimal`, `universal`, `causal`, `efficient`, `cost-effective`,
`generalizable`, `novel algorithm`, `benchmark saturation`, `agent
improvement`, or `framework`.

### Use only with qualification in the body or cover letter

`benchmark maintenance`, `evaluation cost`, `saturation risk`, `time-external
replication`, `practical savings`, and `robust`.

Preferred technical terms:

- task-set reduction;
- task budget;
- ranking fidelity;
- leaderboard ranking reliability;
- earlier-period selection;
- later-period or held-out systems;
- development replication;
- time-external replication;
- related-system dependence;
- latest-per-cluster sensitivity.

## 13. Recommended manuscript structure

### 1. Introduction

1. Coding-agent leaderboards increasingly function as measurement
   infrastructure.
2. Full benchmark execution motivates interest in smaller task sets, but a
   subset selected from current systems may not preserve future rankings.
3. Existing benchmark-validity work focuses on construction, test adequacy,
   labeling, or ecosystem composition rather than time-forward task-budget
   reliability under system dependence.
4. State the three RQs.
5. Contributions should be listed as: protocol, two-panel temporal evidence,
   dependence/threshold sensitivity, and replication package.

Do not open with a claim that SWE-bench is simply too expensive unless a source
supports the statement and the manuscript avoids converting task reduction
directly into measured monetary savings.

### 2. Related Work

Use four subsections:

1. repository-level coding-agent benchmarks;
2. SWE-bench validity, test adequacy, and leaderboard audits;
3. benchmark evolution and longitudinal evaluation;
4. test-suite reduction and ranking-preserving subset selection.

The related-work synthesis must distinguish outcome correctness from ranking
fidelity. UTBoost addresses whether outcomes are correct; this study asks
whether a reduced observed outcome matrix preserves later system ordering.

### 3. Study Design

Suggested order:

1. study identity and noncausal claim boundary;
2. official sources and pinned provenance;
3. panel construction and inclusion rules;
4. earlier/later temporal split;
5. selectors and random baselines;
6. outcomes and reliability thresholds;
7. dependence and uncertainty controls;
8. positive control and reproducibility.

### 4. Results

Suggested order:

1. RQ1 temporal solve-rate and entropy shifts;
2. RQ2 ranking-fidelity curves by budget and panel;
3. RQ3 all-system decisions;
4. related-system sensitivity and correction from 450 to 500;
5. threshold sensitivity;
6. concise answer to each RQ.

### 5. Discussion

Suggested themes:

- why the open panel made 150 tasks look sufficient;
- why later standardized systems expose a harder ranking-preservation problem;
- why correlated system variants create optimistic precision;
- why entropy is a useful baseline but not an algorithmic contribution;
- periodic revalidation as a benchmark-maintenance practice;
- complementarity with test-adequacy and leaderboard-audit research.

### 6. Threats to Validity

Required threats:

- construct validity: leaderboard ranking is not complete software quality;
- internal validity: no causal identification and unknown exact harness
  versions;
- conclusion validity: small 2026 standardized held-out sample, system
  dependence, and public-result selection;
- external validity: one benchmark family, Python repositories, one
  standardized scaffold;
- researcher degrees of freedom: pilot inspected 2025 open outcomes;
- measurement validity: public outcomes can contain test or annotation errors;
- reproducibility: upstream sources evolve, mitigated by pinned commits,
  digests, manifests, and cloud workflow.

### 7. Conclusion

The conclusion should state that aggressive task reduction was not supported
by the time-external and dependence-aware evidence. Both repository-stratified
random sampling and entropy selection required the complete benchmark under
the primary and strict policies; the temporal core set retained only a 5%
reduction. End with periodic revalidation, not a universal subset
recommendation.

## 14. Tables and figures required

Minimum paper-facing exhibits:

1. **Study-design table:** panels, periods, system counts, cluster variables,
   and top-k definitions.
2. **Data-quality table:** discovered, usable, excluded, and reconciliation
   counts by source format.
3. **Temporal-shift table:** solve-rate and entropy changes with repository-
   bootstrap intervals.
4. **Ranking-fidelity figure:** held-out Kendall tau-b against task budget,
   separated by panel and method. Do not pool panels.
5. **Budget-decision table:** all-system, latest-per-cluster, and final robust
   decisions.
6. **Threshold-sensitivity table:** lenient, primary, and strict robust budgets.

Avoid a chart that shows only means without uncertainty or decision thresholds.
Use full 0–1 scales for Kendall tau-b comparisons unless a focused scale is
explicitly labeled and the full-scale context is also available.

## 15. Abstract evidence skeleton

The writing AI may draft the abstract from this evidence sequence:

1. **Context:** coding-agent benchmarks evolve, and reduced task sets selected
   from current systems may not preserve rankings of later systems.
2. **Objective:** evaluate temporal ranking fidelity and reliable task budgets
   in SWE-bench Verified.
3. **Method:** two non-pooled temporal panels; 500 tasks; 13 budgets; four
   selectors/baselines; repeated task sampling; system- and repository-cluster
   uncertainty; related-system and threshold sensitivity.
4. **Results:** the developmental open panel suggests some 150-task decisions,
   but the 2026 time-external standardized panel requires 450–475 tasks before
   dependence sensitivity; after requiring one exact budget to pass every
   panel-scope cell, robust budgets are 500 for repository-stratified random,
   500 for entropy, and 475 for the temporal core set. Entropy admits 250 tasks
   only under the lenient sensitivity policy.
5. **Conclusion:** aggressive task reduction is not temporally reliable;
   periodic, dependence-aware revalidation is necessary, and neither random
   nor entropy selection supports a primary-policy reduction in the observed
   panels.

Do not insert claims of statistical significance unless a reported interval or
predeclared decision rule directly supports them.

## 16. Reproduction package

Repository:

- [coding-agent-benchmark-maintenance](https://github.com/coloursophia/coding-agent-benchmark-maintenance)

Core files:

- `configs/formal.json` — frozen formal configuration;
- `src/formal_experiment.py` — collection, validation, analysis, and reporting;
- `tests/test_formal_experiment.py` — formal-study unit checks;
- `.github/workflows/formal.yml` — secret-free cloud workflow;
- `docs/formal_protocol.md` — formal design and claim boundaries;
- `docs/paper_positioning.md` — title, journal fit, alternatives, and rejection
  risks.

Final artifact contents:

- `report.html`;
- `summary.md`;
- `formal_metrics.csv` — 208 primary metric rows;
- `threshold_sensitivity.csv` — 9 policy-method rows;
- `longitudinal.csv`;
- `formal_results.json`;
- `data_quality.json`;
- `source_manifest.json`.

Final cloud artifact SHA-256 reported by GitHub:
`8936abfd669484ca890bd79a30a6b6091312ca916e9508837bc59bc0bd4119a2`.

The workflow uses only public data and the Python standard library. It requires
no model API, secret, GPU, local dataset, or local computer after dispatch.

## 17. Instructions to the writing AI

1. Treat this baseline as factual input, not as a request to invent additional
   results.
2. Do not alter numerical values without checking the final GitHub artifact.
3. Do not revive the build-log-structure topic.
4. Do not present the temporal core set as successful or novel.
5. Always distinguish the all-system result from the final robust result.
6. Always distinguish the developmental open panel from the time-external
   standardized panel.
7. Do not pool the two panels or call year a causal treatment.
8. Verify every bibliographic record from the publisher, DOI, or official
   paper before adding it to the reference list.
9. Use citations for benchmark cost, benchmark evolution, test adequacy, and
   leaderboard claims; do not infer them from the experiment alone.
10. Write the negative result directly. Do not manufacture a positive
    algorithm narrative for perceived publishability.
11. Keep exact exclusions and source provenance in Methodology or an appendix.
12. Report the primary and sensitivity rules as predeclared analytical
    policies, not as thresholds selected to obtain a particular budget.
13. State that the planned experiment package is complete. New experiments
    are not required for the present bounded EMSE manuscript unless peer review
    requests an extension.

## 18. Handoff decision

**The experimental evidence is complete and supports formal manuscript
writing.** It supports the new temporal benchmark-maintenance paper described
here; it does not support the former build-log-effect paper.

The manuscript's defensible headline is a limitation finding: task-set
reductions that appear adequate in a developmental panel can fail under later
systems and dependence-aware analysis. In the observed evidence, both simple
entropy selection and random sampling require the full 500-task benchmark
under the primary and strict policies.
# Historical writing baseline (superseded)

This file records the pre-v3 design and writing state. It is retained for
analysis-history transparency and must not be used as the source of current
numerical claims. The artifact-backed manuscript and formal configuration are
authoritative.
