# Paper positioning and rejection-risk pre-mortem

## Decision

The paper should be positioned as an **empirical benchmark-maintenance study**,
not as a new coding-agent algorithm, a new task-selection algorithm, or a
causal study of model progress.

Primary target: **Empirical Software Engineering (EMSE)**. This target is not
on the 2025 Chinese Academy of Sciences international journal warning list.
Recent EMSE articles show an actual preference for benchmark/tool evolution,
replication, experimental audits, reproducibility, and carefully bounded
empirical claims—not only papers proposing new models. Particularly close
examples are:

- [Tools and benchmarks evolve: what is their impact on parameter tuning in SBSE experiments?](https://doi.org/10.1007/s10664-025-10733-y)
- [An audit of machine learning experiments on software defect prediction](https://doi.org/10.1007/s10664-025-10797-w)

## Research traditions that directly cover parts of the idea

1. **Coding-agent benchmark construction and validity.** SWE-bench established
   repository-level issue resolution as an agent evaluation task. SWE-bench+
   and UTBoost question test adequacy and annotation correctness. UTBoost
   reports that corrected outcomes change Verified leaderboard rankings. This
   tradition covers outcome validity, not the temporal reliability of reduced
   task budgets.
2. **Leaderboard and benchmark-ecosystem audits.** The 2026 ICSE-SEIP paper
   [What's in a Benchmark? The Case of SWE-Bench in Automated Program Repair](https://doi.org/10.1145/3786583.3786904)
   analyzes 133 Verified entries, submitter types, agent products, model usage,
   and openness. A paper framed merely as an analysis of SWE-bench submissions
   would be directly covered and should be rejected before submission.
3. **Benchmark evolution and replication.** Recent EMSE work shows that tool
   and benchmark evolution can invalidate prior parameter conclusions. This is
   the closest methodological tradition and the correct home for the temporal
   two-panel design.
4. **Test-suite reduction, prioritization, and representative subset
   selection.** Entropy and stratified sampling are established ideas. The
   selector itself is not the novelty. The contribution is the time-forward,
   dependence-aware decision protocol and the negative evidence that apparent
   savings disappear under stronger validity checks.
5. **Experimental-design audits and reproducible software engineering.** The
   study belongs to this tradition because it pins upstream commits, exposes
   inclusion/exclusion rules, uses positive controls, and separates
   development from time-external evidence.

## Three candidate title–journal packages

### Candidate A — retain

**Title:** *When Smaller SWE-bench Verified Subsets Stop Preserving
Leaderboards: A Temporal Two-Panel Study*

- **Target journal:** Empirical Software Engineering.
- **Journal taste:** empirical studies, replications, benchmark/tool evolution,
  methodological audits, and reproducible evidence.
- **Research identity:** longitudinal empirical benchmark-maintenance study.
- **Publishable question:** how many earlier-period tasks preserve later-system
  rankings across two non-pooled evaluation environments and after reducing
  related-system dependence?
- **Method contribution:** a frozen time-forward task-budget protocol combining
  two panels, all-system/latest-cluster scopes, task-sampling and cluster
  uncertainty, repository bootstrap, threshold sensitivity, and a mandatory
  500-task positive control.
- **Experiment closure:** 2024→2025 open submissions plus 2025→2026
  standardized Bash-only submissions; 500 repeated random samples per budget;
  1,000 system-cluster and 2,000 repository-cluster bootstrap repetitions; 13
  budgets and four selectors/baselines.
- **Risk control:** name SWE-bench Verified in the title, say “subsets” rather
  than “cost,” and keep causal or universal claims out.
- **Decision:** retain. It states the negative result and the bounded evidence
  without pretending to contribute an algorithm.

### Candidate B — reject unless broadened with another benchmark

**Title:** *Maintaining Ranking Reliability in Evolving Coding-Agent
Benchmarks: A Longitudinal Framework and Evaluation*

- **Target journal:** Journal of Systems and Software.
- **Journal taste:** empirical studies, frameworks, tools, systems evaluation,
  and practical experience reports.
- **Research identity:** general benchmark-maintenance framework.
- **Proposed method contribution:** a general lifecycle for periodically
  refreshing representative task subsets.
- **Experiment closure:** currently only one benchmark family, despite two
  panels.
- **Rejection risk:** the plural “benchmarks” and word “framework” overstate
  external validity. One SWE-bench family cannot demonstrate a general
  lifecycle across benchmark types.
- **Decision:** reject in the current free-data design. Retaining it would
  require at least one independent coding benchmark with comparable
  time-stamped per-task outcomes.

### Candidate C — reject as an algorithm paper

**Title:** *A Dependence-Aware Protocol for Task-Budget Decisions in
Coding-Agent Benchmarks*

- **Target journal:** ACM Transactions on Software Engineering and Methodology.
- **Journal taste:** strong methodological or algorithmic novelty, substantial
  validation, and broad software-engineering implications.
- **Research identity:** new evaluation methodology.
- **Proposed method contribution:** dependence-aware temporal task selection.
- **Experiment closure:** the protocol is carefully validated, but the only
  data-driven selector with material savings is a simple entropy baseline.
- **Rejection risk:** the protocol may be judged a sound combination of known
  techniques rather than a TOSEM-level methodological invention; one benchmark
  and 11 systems in the time-external standardized test period make the claim
  too narrow.
- **Decision:** reject for TOSEM. The same evidence is better presented as a
  bounded empirical finding for EMSE.

All three journals were checked against the 2025 warning-list status; none is
listed. Journal status must be rechecked immediately before submission because
the warning list is updated over time.

## Final closed-loop package

| Element | Final decision |
|---|---|
| Target journal | Empirical Software Engineering |
| Title | *When Smaller SWE-bench Verified Subsets Stop Preserving Leaderboards: A Temporal Two-Panel Study* |
| Gap | Existing work studies benchmark construction, test adequacy, ranking corrections, ecosystem composition, and benchmark evolution, but not whether task-budget ranking fidelity transfers to later systems across execution panels under related-system dependence. |
| Method | Secondary-data temporal evaluation with frozen earlier-period selection, later-period ranking, two non-pooled panels, repeated baselines, clustered uncertainty, latest-per-cluster sensitivity, threshold sensitivity, and positive control. |
| Main experiment | 51→78 open-submission systems and 27→11 standardized systems over 500 canonical tasks; 208 budget-method-scope-panel metric rows. |
| Main result | Robust cross-panel budgets are 500 for repository-stratified random sampling, 400 for entropy selection, and 475 for the temporal core set. The apparent 450-task random-sampling saving disappears after related-system sensitivity. |
| Risk control | No causal claim, no universal benchmark claim, no cost claim without runtime measurement, no algorithm-novelty claim, no pooling of execution environments, and explicit development/time-external distinction. |

## Claims and title vocabulary

Do **not** put these words in the title: `optimal`, `universal`, `causal`,
`efficient`, `cost-effective`, `generalizable`, `novel algorithm`, `benchmark
saturation`, or `agent improvement`.

Use only in the introduction, cover letter, or limitations with qualification:
`benchmark maintenance`, `evaluation cost`, `saturation risk`, `time-external
replication`, and `practical savings`.

The paper may claim:

- the 150-task pilot conclusion did not generalize;
- related-system dependence materially changes the random-baseline decision;
- entropy selection retained a 20% task reduction under primary and strict
  reliability thresholds in the observed panels;
- the temporal core-set heuristic did not provide a practically meaningful or
  stable advantage.

The paper may not claim:

- that 400 tasks are sufficient for all coding-agent benchmarks;
- that fewer tasks reduce total evaluation cost proportionally;
- that time caused the observed solve-rate or entropy changes;
- that the entropy selector is a novel algorithm;
- that task reduction repairs incorrect SWE-bench test oracles.

## Immediate manuscript plan

1. Write Results around the negative finding first: apparent reductions weaken
   under time-external and dependence-aware evaluation.
2. Treat the entropy result as a bounded operational option, not the headline
   algorithmic contribution.
3. Position UTBoost and the ICSE-SEIP ecosystem audit as complementary validity
   threats and neighboring work, not baselines.
4. Make the 2025 open panel a development replication and the 2026 Bash-only
   panel the time-external replication.
5. Keep the repository artifact, source manifests, exclusions, and cloud run
   link in the replication package.
