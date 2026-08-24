#!/usr/bin/env python3
"""Collect and analyze public SWE-bench Verified leaderboard outcomes.

The script intentionally uses only the Python standard library. It is designed
for a clean GitHub-hosted runner and never calls a model API.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import html
import json
import math
import os
import pathlib
import platform
import random
import statistics
import sys
import urllib.error
import urllib.request
from collections import defaultdict


USER_AGENT = "coding-agent-benchmark-maintenance/0.1"
CONTENTS_URL = "https://api.github.com/repos/swe-bench/experiments/contents/evaluation/verified?per_page=100"
RAW_RESULT_URL = (
    "https://raw.githubusercontent.com/swe-bench/experiments/main/"
    "evaluation/verified/{name}/results/results.json"
)
HF_ROWS_URL = (
    "https://datasets-server.huggingface.co/rows?"
    "dataset=princeton-nlp/SWE-bench_Verified&config=default&split=test"
    "&offset={offset}&length=100"
)


def http_json(url: str, timeout: int = 60):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def parse_submission_date(name: str) -> dt.date | None:
    prefix = name[:8]
    if len(prefix) != 8 or not prefix.isdigit():
        return None
    try:
        return dt.datetime.strptime(prefix, "%Y%m%d").date()
    except ValueError:
        return None


def binary_entropy(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))


def kendall_tau_b(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys):
        raise ValueError("Kendall inputs must have equal length")
    concordant = discordant = ties_x = ties_y = 0
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            dx = (xs[i] > xs[j]) - (xs[i] < xs[j])
            dy = (ys[i] > ys[j]) - (ys[i] < ys[j])
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                ties_x += 1
            elif dy == 0:
                ties_y += 1
            elif dx == dy:
                concordant += 1
            else:
                discordant += 1
    denominator = math.sqrt(
        (concordant + discordant + ties_x)
        * (concordant + discordant + ties_y)
    )
    return (concordant - discordant) / denominator if denominator else 0.0


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def proportional_allocation(groups: dict, budget: int) -> dict:
    total = sum(len(items) for items in groups.values())
    if budget < 0 or budget > total:
        raise ValueError("Budget must be between zero and population size")
    raw = {key: budget * len(items) / total for key, items in groups.items()}
    allocation = {key: min(len(groups[key]), math.floor(value)) for key, value in raw.items()}
    remaining = budget - sum(allocation.values())
    order = sorted(
        groups,
        key=lambda key: (raw[key] - math.floor(raw[key]), len(groups[key]), str(key)),
        reverse=True,
    )
    while remaining:
        progressed = False
        for key in order:
            if allocation[key] < len(groups[key]):
                allocation[key] += 1
                remaining -= 1
                progressed = True
                if remaining == 0:
                    break
        if not progressed:
            raise RuntimeError("Could not complete proportional allocation")
    return allocation


def collect_instances() -> tuple[list[str], list[str]]:
    instance_ids = []
    urls = []
    for offset in range(0, 500, 100):
        url = HF_ROWS_URL.format(offset=offset)
        payload = http_json(url)
        urls.append(url)
        instance_ids.extend(row["row"]["instance_id"] for row in payload["rows"])
    if len(instance_ids) != 500 or len(set(instance_ids)) != 500:
        raise RuntimeError(f"Expected 500 unique canonical instances, got {len(set(instance_ids))}")
    return instance_ids, urls


def collect_submissions(instance_ids: list[str]) -> tuple[list[dict], list[str]]:
    listing = http_json(CONTENTS_URL)
    names = sorted(item["name"] for item in listing if item.get("type") == "dir")

    def fetch(name: str):
        date = parse_submission_date(name)
        if date is None:
            return None
        url = RAW_RESULT_URL.format(name=name)
        try:
            result = http_json(url)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return {"name": name, "date": date.isoformat(), "url": url, "error": "unavailable"}
        resolved = result.get("resolved")
        if not isinstance(resolved, list):
            return {"name": name, "date": date.isoformat(), "url": url, "error": "missing_resolved"}
        resolved_set = set(resolved) & set(instance_ids)
        outcomes = [1 if instance_id in resolved_set else 0 for instance_id in instance_ids]
        observed = set()
        for value in result.values():
            if isinstance(value, list):
                observed.update(item for item in value if isinstance(item, str))
        return {
            "name": name,
            "date": date.isoformat(),
            "year": date.year,
            "url": url,
            "resolved": len(resolved_set),
            "reported_canonical_ids": len(observed & set(instance_ids)),
            "outcomes": outcomes,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        rows = list(executor.map(fetch, names))
    usable = [row for row in rows if row and "error" not in row]
    failed = [row for row in rows if row and "error" in row]
    if failed:
        failed_names = ", ".join(row["name"] for row in failed[:10])
        raise RuntimeError(f"Result collection failed for {len(failed)} submissions: {failed_names}")
    return sorted(usable, key=lambda row: (row["date"], row["name"])), [CONTENTS_URL] + [row["url"] for row in usable]


def task_rates(rows: list[dict], task_count: int) -> list[float]:
    if not rows:
        return [0.0] * task_count
    return [sum(row["outcomes"][i] for row in rows) / len(rows) for i in range(task_count)]


def summarize_period(rows: list[dict], task_count: int) -> dict:
    rates = task_rates(rows, task_count)
    return {
        "submissions": len(rows),
        "never_solved": sum(rate == 0 for rate in rates),
        "near_impossible_le_5pct": sum(rate <= 0.05 for rate in rates),
        "discriminative_20_80pct": sum(0.20 <= rate <= 0.80 for rate in rates),
        "near_saturated_ge_95pct": sum(rate >= 0.95 for rate in rates),
        "always_solved": sum(rate == 1 for rate in rates),
        "mean_task_solve_rate": statistics.fmean(rates),
        "mean_binary_entropy": statistics.fmean(binary_entropy(rate) for rate in rates),
    }


def uniform_random_subset(task_ids: list[str], budget: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return sorted(rng.sample(range(len(task_ids)), budget))


def repository_stratified_subset(task_ids: list[str], budget: int, seed: int) -> list[int]:
    groups = defaultdict(list)
    for index, task_id in enumerate(task_ids):
        groups[task_id.split("__", 1)[0]].append(index)
    allocation = proportional_allocation(groups, budget)
    rng = random.Random(seed)
    selected = []
    for key in sorted(groups):
        selected.extend(rng.sample(groups[key], allocation[key]))
    return sorted(selected)


def entropy_subset(task_ids: list[str], training_rows: list[dict], budget: int) -> list[int]:
    rates = task_rates(training_rows, len(task_ids))
    ranked = sorted(range(len(task_ids)), key=lambda i: (-binary_entropy(rates[i]), task_ids[i]))
    return sorted(ranked[:budget])


def temporal_coreset(task_ids: list[str], training_rows: list[dict], budget: int) -> list[int]:
    ordered = sorted(training_rows, key=lambda row: (row["date"], row["name"]))
    midpoint = max(1, len(ordered) // 2)
    early = ordered[:midpoint]
    late = ordered[midpoint:] or ordered[:midpoint]
    overall_rates = task_rates(ordered, len(task_ids))
    early_rates = task_rates(early, len(task_ids))
    late_rates = task_rates(late, len(task_ids))

    groups = defaultdict(list)
    for index, task_id in enumerate(task_ids):
        repository = task_id.split("__", 1)[0]
        difficulty_bin = min(4, int(overall_rates[index] * 5))
        groups[(repository, difficulty_bin)].append(index)
    allocation = proportional_allocation(groups, budget)

    signatures = {
        index: tuple(row["outcomes"][index] for row in ordered)
        for index in range(len(task_ids))
    }
    selected = []
    for key in sorted(groups, key=str):
        candidates = list(groups[key])
        quota = allocation[key]
        local_selected = []
        while len(local_selected) < quota:
            best = None
            best_score = None
            comparison = selected + local_selected
            for index in candidates:
                if index in local_selected:
                    continue
                p = overall_rates[index]
                discrimination = 4.0 * p * (1.0 - p)
                stability = 1.0 - abs(early_rates[index] - late_rates[index])
                base = discrimination * stability
                if comparison:
                    signature = signatures[index]
                    diversity = min(
                        sum(a != b for a, b in zip(signature, signatures[other])) / len(signature)
                        for other in comparison
                    )
                else:
                    diversity = 1.0
                score = 0.75 * base + 0.25 * diversity
                key_score = (score, task_ids[index])
                if best_score is None or key_score > best_score:
                    best = index
                    best_score = key_score
            local_selected.append(best)
        selected.extend(local_selected)
    if len(selected) != budget:
        raise RuntimeError(f"Temporal selector returned {len(selected)} tasks for budget {budget}")
    return sorted(selected)


def subset_scores(rows: list[dict], subset: list[int]) -> list[float]:
    return [sum(row["outcomes"][i] for i in subset) / len(subset) for row in rows]


def linear_calibration(xs: list[float], ys: list[float]) -> tuple[float, float]:
    mean_x = statistics.fmean(xs)
    mean_y = statistics.fmean(ys)
    variance = sum((x - mean_x) ** 2 for x in xs)
    if variance == 0:
        return mean_y, 0.0
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / variance
    return mean_y - slope * mean_x, slope


def evaluate_subset(
    task_ids: list[str], training_rows: list[dict], test_rows: list[dict], subset: list[int], top_k: int
) -> dict:
    full_indices = list(range(len(task_ids)))
    train_full = subset_scores(training_rows, full_indices)
    train_subset = subset_scores(training_rows, subset)
    test_full = subset_scores(test_rows, full_indices)
    test_subset = subset_scores(test_rows, subset)
    intercept, slope = linear_calibration(train_subset, train_full)
    calibrated = [intercept + slope * value for value in test_subset]

    full_top = {
        row["name"]
        for row, _ in sorted(zip(test_rows, test_full), key=lambda pair: (-pair[1], pair[0]["name"]))[:top_k]
    }
    subset_top = {
        row["name"]
        for row, _ in sorted(zip(test_rows, test_subset), key=lambda pair: (-pair[1], pair[0]["name"]))[:top_k]
    }

    correct = considered = 0
    for i in range(len(test_rows)):
        for j in range(i + 1, len(test_rows)):
            full_direction = (test_full[i] > test_full[j]) - (test_full[i] < test_full[j])
            if full_direction == 0:
                continue
            subset_direction = (test_subset[i] > test_subset[j]) - (test_subset[i] < test_subset[j])
            considered += 1
            correct += subset_direction == full_direction

    repositories = {task_ids[index].split("__", 1)[0] for index in subset}
    return {
        "tau_b": kendall_tau_b(test_full, test_subset),
        "top_k_overlap": len(full_top & subset_top) / max(1, top_k),
        "pairwise_direction_agreement": correct / considered if considered else 0.0,
        "calibrated_score_mae": statistics.fmean(abs(a - b) for a, b in zip(test_full, calibrated)),
        "repository_coverage": len(repositories),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
    }


def summarize_repetitions(records: list[dict]) -> dict:
    output = {}
    for key in ("tau_b", "top_k_overlap", "pairwise_direction_agreement", "calibrated_score_mae", "repository_coverage"):
        values = [record[key] for record in records]
        output[key] = statistics.fmean(values)
        output[f"{key}_q025"] = quantile(values, 0.025)
        output[f"{key}_q975"] = quantile(values, 0.975)
    return output


def svg_line_chart(rows: list[dict], width: int = 760, height: int = 300) -> str:
    budgets = sorted({row["budget"] for row in rows})
    methods = ["random", "repo_stratified_random", "entropy", "temporal_coreset"]
    colors = {"random": "#64748b", "repo_stratified_random": "#0ea5e9", "entropy": "#f59e0b", "temporal_coreset": "#7c3aed"}
    left, right, top, bottom = 55, 20, 25, 45
    plot_w, plot_h = width - left - right, height - top - bottom
    x_pos = {budget: left + i * plot_w / max(1, len(budgets) - 1) for i, budget in enumerate(budgets)}
    y = lambda value: top + (1.0 - max(0.0, min(1.0, value))) * plot_h
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Held-out Kendall tau-b by task budget">']
    for value in (0.0, 0.25, 0.5, 0.75, 1.0):
        yy = y(value)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" stroke="#e2e8f0"/>')
        parts.append(f'<text x="{left-8}" y="{yy+4:.1f}" text-anchor="end" font-size="11" fill="#475569">{value:.2f}</text>')
    row_map = {(row["method"], row["budget"]): row for row in rows}
    for method in methods:
        points = []
        for budget in budgets:
            row = row_map.get((method, budget))
            if row:
                points.append((x_pos[budget], y(row["tau_b"])))
        if points:
            point_text = " ".join(f"{x:.1f},{yy:.1f}" for x, yy in points)
            parts.append(f'<polyline points="{point_text}" fill="none" stroke="{colors[method]}" stroke-width="3"/>')
            for x, yy in points:
                parts.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="4" fill="{colors[method]}"/>')
    for budget in budgets:
        parts.append(f'<text x="{x_pos[budget]:.1f}" y="{height-20}" text-anchor="middle" font-size="12" fill="#334155">{budget}</text>')
    legend_x = left
    for method in methods:
        label = method.replace("_", " ")
        parts.append(f'<rect x="{legend_x}" y="{height-10}" width="10" height="4" fill="{colors[method]}"/>')
        parts.append(f'<text x="{legend_x+14}" y="{height-5}" font-size="10" fill="#334155">{html.escape(label)}</text>')
        legend_x += 155
    parts.append("</svg>")
    return "".join(parts)


def write_outputs(output: pathlib.Path, payload: dict, metric_rows: list[dict], matrix_digest: str):
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    fieldnames = [
        "method", "budget", "tau_b", "tau_b_q025", "tau_b_q975", "top_k_overlap",
        "pairwise_direction_agreement", "calibrated_score_mae", "repository_coverage",
    ]
    with (output / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(metric_rows)

    manifest = payload["data_quality"] | {
        "collected_at_utc": payload["generated_at_utc"],
        "matrix_sha256": matrix_digest,
        "python": sys.version,
        "platform": platform.platform(),
        "source_urls": payload["source_urls"],
    }
    (output / "data_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    gate = payload["pilot_gate"]
    longitudinal = payload["longitudinal"]
    summary = [
        "# SWE-bench discriminative-power pilot",
        "",
        f"**Overall pilot decision: {'PASS' if gate['overall_pass'] else 'FAIL'}**",
        "",
        f"- Usable submissions: {payload['data_quality']['usable_submissions']} / {payload['data_quality']['submission_directories']}",
        f"- Canonical tasks: {payload['data_quality']['canonical_tasks']}",
        f"- Training submissions ({payload['config']['train_year']}): {longitudinal[str(payload['config']['train_year'])]['submissions']}",
        f"- Held-out submissions ({payload['config']['test_year']}): {longitudinal[str(payload['config']['test_year'])]['submissions']}",
        f"- Feasibility gate: {'PASS' if gate['data_feasibility_pass'] else 'FAIL'}",
        f"- Method-viability gate at {payload['config']['primary_budget']} tasks: {'PASS' if gate['method_viability_pass'] else 'FAIL'}",
        "",
        "The year comparison is descriptive and must not be interpreted causally.",
    ]
    (output / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    def period_rows():
        result = []
        for year, stats in longitudinal.items():
            result.append(
                f"<tr><td>{year}</td><td>{stats['submissions']}</td>"
                f"<td>{stats['mean_task_solve_rate']:.3f}</td><td>{stats['mean_binary_entropy']:.3f}</td>"
                f"<td>{stats['never_solved']}</td><td>{stats['discriminative_20_80pct']}</td>"
                f"<td>{stats['near_saturated_ge_95pct']}</td></tr>"
            )
        return "".join(result)

    def metric_table_rows():
        result = []
        for row in metric_rows:
            interval = ""
            if "tau_b_q025" in row:
                interval = f" [{row['tau_b_q025']:.3f}, {row['tau_b_q975']:.3f}]"
            result.append(
                f"<tr><td>{html.escape(row['method'].replace('_', ' '))}</td><td>{row['budget']}</td>"
                f"<td>{row['tau_b']:.3f}{interval}</td><td>{row['top_k_overlap']:.3f}</td>"
                f"<td>{row['pairwise_direction_agreement']:.3f}</td>"
                f"<td>{row['calibrated_score_mae']:.4f}</td><td>{row['repository_coverage']:.1f}</td></tr>"
            )
        return "".join(result)

    decision_class = "pass" if gate["overall_pass"] else "fail"
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SWE-bench Discriminative-Power Pilot</title>
<style>
body{{margin:0;background:#f8fafc;color:#0f172a;font-family:Inter,ui-sans-serif,system-ui,sans-serif;line-height:1.55}}
main{{max-width:1100px;margin:auto;padding:42px 24px 70px}}h1{{font-size:34px;line-height:1.15;margin:0 0 8px}}h2{{margin-top:34px}}
.eyebrow{{color:#6d28d9;font-weight:700;text-transform:uppercase;letter-spacing:.08em;font-size:12px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:24px 0}}
.card{{background:white;border:1px solid #e2e8f0;border-radius:14px;padding:18px;box-shadow:0 4px 18px #0f172a0b}}
.value{{font-size:28px;font-weight:750}}.muted{{color:#64748b}}.pass{{color:#047857}}.fail{{color:#b91c1c}}
table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;font-size:14px}}
th,td{{padding:10px 12px;border-bottom:1px solid #e2e8f0;text-align:right}}th:first-child,td:first-child{{text-align:left}}th{{background:#f1f5f9}}
.note{{border-left:4px solid #7c3aed;background:#ede9fe;padding:12px 16px;border-radius:6px}}svg{{width:100%;height:auto;background:white;border-radius:12px}}
</style></head><body><main>
<div class="eyebrow">Automated GitHub Actions pilot</div>
<h1>Maintaining discriminative power in coding-agent benchmarks</h1>
<p class="muted">Longitudinal SWE-bench Verified analysis with a temporally held-out core-set evaluation.</p>
<div class="grid">
<div class="card"><div class="muted">Pilot decision</div><div class="value {decision_class}">{'PASS' if gate['overall_pass'] else 'FAIL'}</div></div>
<div class="card"><div class="muted">Usable submissions</div><div class="value">{payload['data_quality']['usable_submissions']}</div></div>
<div class="card"><div class="muted">Canonical tasks</div><div class="value">{payload['data_quality']['canonical_tasks']}</div></div>
<div class="card"><div class="muted">Binary outcomes</div><div class="value">{payload['data_quality']['binary_outcomes']:,}</div></div>
</div>
<div class="note"><strong>Interpretation boundary.</strong> Year differences are descriptive. Submission populations, models, and harnesses differ, and public outcomes generally contain one run per task.</div>
<h2>Longitudinal diagnostic</h2>
<table><thead><tr><th>Year</th><th>Submissions</th><th>Mean solve rate</th><th>Mean entropy</th><th>Never solved</th><th>20–80% solved</th><th>≥95% solved</th></tr></thead><tbody>{period_rows()}</tbody></table>
<h2>Held-out ranking preservation</h2>
{svg_line_chart(metric_rows)}
<table><thead><tr><th>Method</th><th>Tasks</th><th>Held-out τ-b</th><th>Top-10 overlap</th><th>Pairwise agreement</th><th>Calibrated MAE</th><th>Repositories</th></tr></thead><tbody>{metric_table_rows()}</tbody></table>
<h2>Predeclared decision</h2>
<div class="grid"><div class="card"><div class="muted">Data feasibility</div><div class="value {'pass' if gate['data_feasibility_pass'] else 'fail'}">{'PASS' if gate['data_feasibility_pass'] else 'FAIL'}</div></div>
<div class="card"><div class="muted">Method viability</div><div class="value {'pass' if gate['method_viability_pass'] else 'fail'}">{'PASS' if gate['method_viability_pass'] else 'FAIL'}</div></div></div>
<p class="muted">Generated {html.escape(payload['generated_at_utc'])}. Matrix SHA-256: <code>{matrix_digest}</code>.</p>
</main></body></html>"""
    (output / "report.html").write_text(document, encoding="utf-8")


def run(config_path: pathlib.Path, output: pathlib.Path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    instance_ids, instance_urls = collect_instances()
    submissions, submission_urls = collect_submissions(instance_ids)
    train_rows = [row for row in submissions if row["year"] == config["train_year"]]
    test_rows = [row for row in submissions if row["year"] == config["test_year"]]

    matrix_material = "\n".join(
        row["name"] + "," + "".join(map(str, row["outcomes"])) for row in submissions
    ).encode("utf-8")
    matrix_digest = hashlib.sha256(matrix_material).hexdigest()

    metric_rows = []
    detail = {}
    for budget in config["task_budgets"]:
        repeated = {"random": [], "repo_stratified_random": []}
        for repetition in range(config["random_repetitions"]):
            repeated["random"].append(
                evaluate_subset(instance_ids, train_rows, test_rows, uniform_random_subset(instance_ids, budget, 1000 + repetition), config["top_k_systems"])
            )
            repeated["repo_stratified_random"].append(
                evaluate_subset(instance_ids, train_rows, test_rows, repository_stratified_subset(instance_ids, budget, 2000 + repetition), config["top_k_systems"])
            )
        for method in ("random", "repo_stratified_random"):
            summary = summarize_repetitions(repeated[method])
            row = {"method": method, "budget": budget} | summary
            metric_rows.append(row)
            detail[f"{method}:{budget}"] = row

        deterministic = {
            "entropy": entropy_subset(instance_ids, train_rows, budget),
            "temporal_coreset": temporal_coreset(instance_ids, train_rows, budget),
        }
        for method, subset in deterministic.items():
            metrics = evaluate_subset(instance_ids, train_rows, test_rows, subset, config["top_k_systems"])
            row = {"method": method, "budget": budget} | metrics
            metric_rows.append(row)
            detail[f"{method}:{budget}"] = row | {"selected_instance_ids": [instance_ids[i] for i in subset]}

    primary = config["primary_budget"]
    proposed = detail[f"temporal_coreset:{primary}"]
    stratified = detail[f"repo_stratified_random:{primary}"]
    data_feasibility = (
        len(submissions) >= config["minimum_usable_submissions"]
        and len(train_rows) >= config["minimum_submissions_per_period"]
        and len(test_rows) >= config["minimum_submissions_per_period"]
    )
    train_summary = summarize_period(train_rows, len(instance_ids))
    test_summary = summarize_period(test_rows, len(instance_ids))
    longitudinal_signal = (
        abs(test_summary["mean_binary_entropy"] - train_summary["mean_binary_entropy"])
        >= config["minimum_entropy_absolute_change"]
        and abs(test_summary["near_saturated_ge_95pct"] - train_summary["near_saturated_ge_95pct"])
        >= config["minimum_near_saturated_task_increase"]
    )
    budget_viability = stratified["tau_b"] >= config["minimum_heldout_tau_b"]
    payload = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "config": config,
        "data_quality": {
            "submission_directories": len(submissions),
            "usable_submissions": len(submissions),
            "canonical_tasks": len(instance_ids),
            "binary_outcomes": len(submissions) * len(instance_ids),
            "reported_id_coverage_min": min(row["reported_canonical_ids"] for row in submissions),
            "reported_id_coverage_median": statistics.median(row["reported_canonical_ids"] for row in submissions),
            "reported_id_coverage_max": max(row["reported_canonical_ids"] for row in submissions),
        },
        "longitudinal": {
            str(config["train_year"]): train_summary,
            str(config["test_year"]): test_summary,
        },
        "metrics": detail,
        "pilot_gate": {
            "data_feasibility_pass": data_feasibility,
            "longitudinal_signal_pass": longitudinal_signal,
            "reduced_budget_viability_pass": budget_viability,
            "method_viability_pass": budget_viability,
            "overall_pass": data_feasibility and longitudinal_signal and budget_viability,
            "primary_temporal_coreset_tau_b": proposed["tau_b"],
            "primary_repo_stratified_random_mean_tau_b": stratified["tau_b"],
        },
        "source_urls": instance_urls + submission_urls,
    }
    write_outputs(output, payload, metric_rows, matrix_digest)
    print(json.dumps(payload["pilot_gate"], indent=2))
    if not data_feasibility:
        raise SystemExit("Data-feasibility gate failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    run(args.config, args.output)


if __name__ == "__main__":
    main()
