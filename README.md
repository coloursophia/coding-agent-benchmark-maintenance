# Maintaining Discriminative Power in Coding-Agent Benchmarks

Manuscript writers should start from [`WRITING_BASELINE.md`](WRITING_BASELINE.md),
which locks the final title, paper direction, experiment protocol, numerical
results, claim boundaries, and reproducibility links.

This repository contains a fully automated, zero-API-cost empirical study of
how the discriminative power of SWE-bench Verified changes over time and how
many tasks are required to preserve the ordering of later systems.

The workflow uses only public result files from the official
[`swe-bench/experiments`](https://github.com/swe-bench/experiments) repository
and the canonical 500 SWE-bench Verified instance identifiers. It does **not**
invoke an LLM, use a model API, require a secret, download execution images, or
depend on a local computer after the GitHub Actions job has started.

## Research questions

1. How did task-level difficulty and discrimination change across later
   SWE-bench Verified submission cohorts?
2. Can task subsets selected only from an earlier period preserve the ranking
   of later systems in both open and standardized evaluation panels?
3. Which reduced task budget reliably preserves held-out rankings, and do
   data-driven selectors outperform simple sampling baselines?

## Formal design

The paper-facing experiment keeps two evaluation environments separate:

- **Open-submission panel:** 2024 selection and 2025 evaluation, using the
  traditional Verified result artifacts.
- **Standardized Bash-only panel:** 2025 selection and 2026 evaluation, using
  explicit 500-task outcomes from the common mini-SWE-agent environment.

The 2026 panel was not read by the pilot and therefore supplies the strongest
time-external replication. See [`docs/formal_protocol.md`](docs/formal_protocol.md)
for inclusion rules, dependence controls, uncertainty estimators, and claim
boundaries. The rejected alternatives, target-journal fit, title vocabulary,
and paper-facing claim limits are documented in
[`docs/paper_positioning.md`](docs/paper_positioning.md).

## Evaluation design

- Unit of observation: one public submission-task outcome.
- Temporal split: tasks are selected from the earlier period of each panel and
  evaluated only on its later systems.
- Task budgets: 25, 50, 75, 100, 125, 150, 200, 250, 300, 400, 450,
  475, and the 500-task positive control.
- Primary metric: Kendall's tau-b between full-benchmark and subset rankings on
  held-out submissions.
- Secondary metrics: top-10 overlap, pairwise direction agreement, calibrated
  score MAE, repository coverage, and bootstrap/random-baseline intervals.

The temporal split is deliberate: a random submission split would leak later
system behavior into task selection and would not test whether a core set
generalizes to future systems.

## Run remotely

Open **Actions → Formal Study - Benchmark Discriminative Power → Run
workflow**. The job collects both panels, validates every included outcome
matrix against the official leaderboard, runs the full analysis, and uploads
`swe-bench-formal-discriminative-power-study` with CSV, JSON, Markdown, and
HTML results. Paper-facing task-budget claims must hold in both temporal panels
and in both the all-systems and latest-entry-per-related-cluster scopes. The
pilot workflow remains available as a design-history check.

## Reproduce locally (optional)

```bash
python -m unittest discover -s tests -v
python src/formal_experiment.py --config configs/formal.json --output formal-output
```

Only the Python standard library is required.

## Interpretation boundary

This study evaluates the public leaderboard as a measurement system. A change
between submission years is not interpreted as a causal effect of time, model
scale, or agent architecture. Public submissions are correlated system
variants and usually expose one outcome per task, so the analysis cannot
estimate run-to-run model variance. Submission dates also do not identify the
exact harness version; the formal design therefore does not pool its two
execution environments.

## License

MIT. Public source datasets remain governed by their respective licenses and
terms.
