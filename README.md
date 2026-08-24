# Maintaining Discriminative Power in Coding-Agent Benchmarks

This repository contains a fully automated, zero-API-cost pilot study of how
the discriminative power of SWE-bench Verified changes over time and how many
tasks are required to preserve the ordering of later, unseen submissions.

The workflow uses only public result files from the official
[`swe-bench/experiments`](https://github.com/swe-bench/experiments) repository
and the canonical 500 SWE-bench Verified instance identifiers. It does **not**
invoke an LLM, use a model API, require a secret, download execution images, or
depend on a local computer after the GitHub Actions job has started.

## Research questions

1. How did task-level difficulty and discrimination change between the 2024
   and 2025 SWE-bench Verified submissions?
2. Can task subsets selected only from 2024 outcomes preserve the ranking of
   unseen 2025 submissions?
3. Which reduced task budget reliably preserves held-out rankings, and do
   data-driven selectors outperform simple sampling baselines?

## Pilot design

- Unit of observation: one public submission-task outcome.
- Training period: submissions whose directory names begin with `2024`.
- Held-out period: submissions whose directory names begin with `2025`.
- Task budgets: 25, 50, 100, 150, 200, and 250 of the 500 canonical instances.
- Primary metric: Kendall's tau-b between full-benchmark and subset rankings on
  held-out submissions.
- Secondary metrics: top-10 overlap, pairwise direction agreement, calibrated
  score MAE, repository coverage, and bootstrap/random-baseline intervals.

The temporal split is deliberate: a random submission split would leak later
system behavior into task selection and would not test whether a core set
generalizes to future systems.

## Run remotely

Open **Actions → SWE-bench Discriminative Power Pilot → Run workflow**. The job
collects data, validates it, runs the analysis, and uploads a compact artifact
named `swe-bench-discriminative-power-pilot` containing CSV, JSON, Markdown,
and HTML results.

## Reproduce locally (optional)

```bash
python -m unittest discover -s tests -v
python src/experiment.py --config configs/pilot.json --output results
```

Only the Python standard library is required.

## Interpretation boundary

This study evaluates the public leaderboard as a measurement system. A change
between submission years is not interpreted as a causal effect of time, model
scale, or agent architecture. Public submissions are correlated system
variants and usually expose one outcome per task, so the analysis cannot
estimate run-to-run model variance.

## License

MIT. Public source datasets remain governed by their respective licenses and
terms.
