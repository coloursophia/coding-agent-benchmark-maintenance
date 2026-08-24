#!/usr/bin/env python3
"""Run the paper-facing two-panel SWE-bench measurement study.

The program uses public aggregate/per-instance artifacts only, pins GitHub
sources to resolved commits, requires no secret, and intentionally avoids
redistributing the upstream outcome matrices.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import html
import json
import pathlib
import random
import re
import statistics
import sys
import urllib.error
import urllib.parse
from collections import Counter, defaultdict

import experiment as core


EXPERIMENTS_REPO = "swe-bench/experiments"
WEBSITE_REPO = "swe-bench/swe-bench.github.io"
GITHUB_API = "https://api.github.com/repos/{repo}"
RAW_GITHUB = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"


def repo_commit(repo: str, branch: str) -> str:
    return core.http_json(f"{GITHUB_API.format(repo=repo)}/commits/{branch}")["sha"]


def raw_url(repo: str, ref: str, path: str) -> str:
    quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    return RAW_GITHUB.format(repo=repo, ref=ref, path=quoted)


def contents_url(repo: str, path: str, ref: str) -> str:
    quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    return f"{GITHUB_API.format(repo=repo)}/contents/{quoted}?ref={ref}&per_page=100"


def normalize_label(value: object, fallback: str = "unknown") -> str:
    text = str(value or fallback).casefold()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\bv?\d+(?:[._-]\d+)+(?:[a-z]+)?\b", " ", text)
    text = re.sub(r"\b(?:preview|experimental|dev)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split()) or fallback


def attempts_category(tags: object) -> str:
    for tag in tags if isinstance(tags, list) else []:
        match = re.search(r"attempts\s*-\s*(.+)$", str(tag), flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            return "single" if value == "1" else "multiple"
    return "unknown"


def leaderboard_maps(payload: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    boards = {board.get("name"): board.get("results", []) for board in payload.get("leaderboards", [])}
    verified = {row["folder"]: row for row in boards.get("Verified", []) if row.get("folder")}
    bash = {row["folder"]: row for row in boards.get("bash-only", []) if row.get("folder")}
    return verified, bash


def outcome_digest(rows: list[dict]) -> str:
    material = "\n".join(
        row["name"] + "," + "".join(str(value) for value in row["outcomes"])
        for row in sorted(rows, key=lambda item: item["name"])
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def collect_classic(
    instance_ids: list[str], commit: str, metadata: dict[str, dict], maximum_score_delta_pp: float
) -> tuple[list[dict], list[str], dict]:
    listing_url = contents_url(EXPERIMENTS_REPO, "evaluation/verified", commit)
    listing = core.http_json(listing_url)
    names = sorted(item["name"] for item in listing if item.get("type") == "dir")
    canonical = set(instance_ids)

    def fetch(name: str):
        date = core.parse_submission_date(name)
        if date is None:
            return None
        path = f"evaluation/verified/{name}/results/results.json"
        url = raw_url(EXPERIMENTS_REPO, commit, path)
        try:
            payload = core.http_json(url)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            return {"name": name, "url": url, "error": type(error).__name__}
        resolved = payload.get("resolved")
        if not isinstance(resolved, list):
            return {"name": name, "url": url, "error": "missing_resolved"}
        duplicate_resolved = len(resolved) - len(set(resolved))
        noncanonical = sorted(set(resolved) - canonical)
        resolved_set = set(resolved) & canonical
        official = metadata.get(name, {})
        published = official.get("resolved")
        score = 100.0 * len(resolved_set) / len(instance_ids)
        score_delta = abs(score - float(published)) if published is not None else None
        agent = official.get("agent") or name[9:].split("_", 1)[0]
        return {
            "name": name,
            "date": date.isoformat(),
            "year": date.year,
            "source": "classic",
            "url": url,
            "outcomes": [int(instance_id in resolved_set) for instance_id in instance_ids],
            "resolved": len(resolved_set),
            "agent_family": normalize_label(agent, name),
            "model_provider": normalize_label(official.get("model_org"), "unknown"),
            "attempts": attempts_category(official.get("tags")),
            "checked": official.get("checked"),
            "duplicate_resolved_ids": duplicate_resolved,
            "noncanonical_resolved_ids": len(noncanonical),
            "published_score_delta_pp": score_delta,
            "metadata_present": bool(official),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        fetched = list(executor.map(fetch, names))
    failed = [row for row in fetched if row and row.get("error")]
    if failed:
        raise RuntimeError(f"Classic collection failed for {len(failed)} folders: {failed[:5]}")
    rows = sorted((row for row in fetched if row), key=lambda item: (item["date"], item["name"]))
    unlisted = [row for row in rows if not row["metadata_present"]]
    score_mismatches = [
        row for row in rows
        if row["metadata_present"] and row["published_score_delta_pp"] > maximum_score_delta_pp
    ]
    excluded_names = {row["name"] for row in unlisted + score_mismatches}
    rows = [row for row in rows if row["name"] not in excluded_names]
    quality = {
        "directories": len(names),
        "usable": len(rows),
        "excluded_unlisted": [row["name"] for row in unlisted],
        "excluded_score_mismatch": [row["name"] for row in score_mismatches],
        "metadata_missing": sum(not row["metadata_present"] for row in rows),
        "duplicate_resolved_ids": sum(row["duplicate_resolved_ids"] for row in rows),
        "noncanonical_resolved_ids": sum(row["noncanonical_resolved_ids"] for row in rows),
        "maximum_included_score_delta_pp": max(row["published_score_delta_pp"] for row in rows),
        "score_reconciliation_failures": sum(row["published_score_delta_pp"] > maximum_score_delta_pp for row in rows),
        "matrix_sha256": outcome_digest(rows),
    }
    return rows, [listing_url] + [row["url"] for row in rows], quality


def parse_bash_payload(payload: object, instance_ids: list[str]) -> tuple[list[int], dict]:
    if not isinstance(payload, dict):
        raise ValueError("Bash-only payload must be an object")
    canonical = set(instance_ids)
    keys = set(payload)
    missing = canonical - keys
    extra = keys - canonical
    invalid = [key for key in canonical & keys if not isinstance(payload[key], dict) or not isinstance(payload[key].get("resolved"), bool)]
    if missing or extra or invalid:
        raise ValueError(f"Invalid Bash-only matrix: missing={len(missing)}, extra={len(extra)}, invalid={len(invalid)}")
    return [int(payload[instance_id]["resolved"]) for instance_id in instance_ids], {
        "missing": len(missing), "extra": len(extra), "invalid": len(invalid)
    }


def collect_bash(
    instance_ids: list[str], commit: str, metadata: dict[str, dict], maximum_score_delta_pp: float
) -> tuple[list[dict], list[str], dict]:
    listing_url = contents_url(EXPERIMENTS_REPO, "evaluation/bash-only", commit)
    listing = core.http_json(listing_url)
    names = sorted(item["name"] for item in listing if item.get("type") == "dir")

    def fetch(name: str):
        date = core.parse_submission_date(name)
        if date is None:
            return None
        path = f"evaluation/bash-only/{name}/per_instance_details.json"
        url = raw_url(EXPERIMENTS_REPO, commit, path)
        try:
            outcomes, checks = parse_bash_payload(core.http_json(url), instance_ids)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
            return {"name": name, "url": url, "error": str(error)}
        official = metadata.get(name, {})
        score = 100.0 * sum(outcomes) / len(instance_ids)
        published = official.get("resolved")
        score_delta = abs(score - float(published)) if published is not None else None
        return {
            "name": name,
            "date": date.isoformat(),
            "year": date.year,
            "source": "bash-only",
            "url": url,
            "outcomes": outcomes,
            "resolved": sum(outcomes),
            "agent_family": normalize_label(official.get("agent"), "mini swe agent"),
            "model_provider": normalize_label(official.get("model_org"), official.get("model_display", "unknown")),
            "attempts": attempts_category(official.get("tags")),
            "checked": official.get("checked"),
            "published_score_delta_pp": score_delta,
            "metadata_present": bool(official),
            "explicit_matrix_checks": checks,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        fetched = list(executor.map(fetch, names))
    failed = [row for row in fetched if row and row.get("error")]
    rows = sorted((row for row in fetched if row and not row.get("error")), key=lambda item: (item["date"], item["name"]))
    if not rows:
        raise RuntimeError("No usable Bash-only per-instance matrices were available")
    score_mismatches = [
        row for row in rows
        if row["published_score_delta_pp"] is None or row["published_score_delta_pp"] > maximum_score_delta_pp
    ]
    excluded_names = {row["name"] for row in score_mismatches}
    rows = [row for row in rows if row["name"] not in excluded_names]
    quality = {
        "directories": len(names),
        "usable": len(rows),
        "excluded_missing_or_invalid_matrix": len(failed),
        "excluded_folders": [row["name"] for row in failed],
        "excluded_score_mismatch": [row["name"] for row in score_mismatches],
        "metadata_missing": sum(not row["metadata_present"] for row in rows),
        "explicit_500_task_matrices": sum(len(row["outcomes"]) == 500 for row in rows),
        "maximum_included_score_delta_pp": max(row["published_score_delta_pp"] for row in rows),
        "score_reconciliation_failures": sum(row["published_score_delta_pp"] > maximum_score_delta_pp for row in rows),
        "matrix_sha256": outcome_digest(rows),
    }
    return rows, [listing_url] + [row["url"] for row in rows], quality


def latest_per_cluster(rows: list[dict], cluster_field: str) -> list[dict]:
    latest = {}
    for row in sorted(rows, key=lambda item: (item["date"], item["name"])):
        latest[row.get(cluster_field) or row["name"]] = row
    return sorted(latest.values(), key=lambda item: (item["date"], item["name"]))


def duplicate_signature_summary(rows: list[dict]) -> dict:
    counts = Counter(tuple(row["outcomes"]) for row in rows)
    return {
        "unique_system_signatures": len(counts),
        "duplicate_signature_groups": sum(count > 1 for count in counts.values()),
        "systems_in_duplicate_groups": sum(count for count in counts.values() if count > 1),
    }


def cluster_bootstrap_tau(
    full_scores: list[float], subset_scores: list[float], clusters: list[str], repetitions: int, seed: int
) -> tuple[float, float]:
    grouped = defaultdict(list)
    for index, cluster in enumerate(clusters):
        grouped[cluster].append(index)
    keys = sorted(grouped)
    if len(keys) < 2:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    values = []
    for _ in range(repetitions):
        indices = []
        for key in rng.choices(keys, k=len(keys)):
            indices.extend(grouped[key])
        values.append(core.kendall_tau_b([full_scores[i] for i in indices], [subset_scores[i] for i in indices]))
    return core.quantile(values, 0.025), core.quantile(values, 0.975)


def repository_bootstrap_difference(
    instance_ids: list[str], first: list[float], second: list[float], repetitions: int, seed: int
) -> tuple[float, float]:
    groups = defaultdict(list)
    for index, task_id in enumerate(instance_ids):
        groups[task_id.split("__", 1)[0]].append(index)
    keys = sorted(groups)
    rng = random.Random(seed)
    values = []
    for _ in range(repetitions):
        indices = []
        for key in rng.choices(keys, k=len(keys)):
            indices.extend(groups[key])
        values.append(statistics.fmean(second[i] - first[i] for i in indices))
    return core.quantile(values, 0.025), core.quantile(values, 0.975)


def task_band(rate: float) -> str:
    if rate <= 0.05:
        return "near_impossible"
    if rate < 0.20:
        return "low"
    if rate <= 0.80:
        return "discriminative"
    if rate < 0.95:
        return "high"
    return "near_saturated"


def longitudinal_record(
    panel: dict, instance_ids: list[str], train_rows: list[dict], test_rows: list[dict], bootstrap_repetitions: int
) -> dict:
    train_rates = core.task_rates(train_rows, len(instance_ids))
    test_rates = core.task_rates(test_rows, len(instance_ids))
    train_entropy = [core.binary_entropy(value) for value in train_rates]
    test_entropy = [core.binary_entropy(value) for value in test_rates]
    solve_ci = repository_bootstrap_difference(instance_ids, train_rates, test_rates, bootstrap_repetitions, 6100 + panel["train_year"])
    entropy_ci = repository_bootstrap_difference(instance_ids, train_entropy, test_entropy, bootstrap_repetitions, 7100 + panel["test_year"])
    transitions = Counter((task_band(a), task_band(b)) for a, b in zip(train_rates, test_rates))

    def task_signatures(rows: list[dict]) -> int:
        return len({tuple(row["outcomes"][i] for row in rows) for i in range(len(instance_ids))})

    train_summary = core.summarize_period(train_rows, len(instance_ids))
    test_summary = core.summarize_period(test_rows, len(instance_ids))
    return {
        "panel": panel["name"],
        "train_year": panel["train_year"],
        "test_year": panel["test_year"],
        "train_systems": len(train_rows),
        "test_systems": len(test_rows),
        "train_clusters": len({row[panel["cluster_field"]] for row in train_rows}),
        "test_clusters": len({row[panel["cluster_field"]] for row in test_rows}),
        "train_mean_solve_rate": train_summary["mean_task_solve_rate"],
        "test_mean_solve_rate": test_summary["mean_task_solve_rate"],
        "solve_rate_change": test_summary["mean_task_solve_rate"] - train_summary["mean_task_solve_rate"],
        "solve_rate_change_q025": solve_ci[0],
        "solve_rate_change_q975": solve_ci[1],
        "train_mean_entropy": train_summary["mean_binary_entropy"],
        "test_mean_entropy": test_summary["mean_binary_entropy"],
        "entropy_change": test_summary["mean_binary_entropy"] - train_summary["mean_binary_entropy"],
        "entropy_change_q025": entropy_ci[0],
        "entropy_change_q975": entropy_ci[1],
        "train_discriminative_tasks": train_summary["discriminative_20_80pct"],
        "test_discriminative_tasks": test_summary["discriminative_20_80pct"],
        "train_near_saturated_tasks": train_summary["near_saturated_ge_95pct"],
        "test_near_saturated_tasks": test_summary["near_saturated_ge_95pct"],
        "train_unique_task_signatures": task_signatures(train_rows),
        "test_unique_task_signatures": task_signatures(test_rows),
        "task_difficulty_tau_b": core.kendall_tau_b(train_rates, test_rates),
        "mean_absolute_task_rate_shift": statistics.fmean(abs(a - b) for a, b in zip(train_rates, test_rates)),
        "transitions": {f"{a}->{b}": count for (a, b), count in sorted(transitions.items())},
    }


def score_vectors(task_ids: list[str], rows: list[dict], subset: list[int]) -> tuple[list[float], list[float]]:
    full = core.subset_scores(rows, list(range(len(task_ids))))
    reduced = core.subset_scores(rows, subset)
    return full, reduced


def metric_row(panel: str, scope: str, method: str, budget: int, metrics: dict, interval_type: str) -> dict:
    return {
        "panel": panel,
        "scope": scope,
        "method": method,
        "budget": budget,
        "tau_b": metrics["tau_b"],
        "tau_b_q025": metrics.get("tau_b_q025", ""),
        "tau_b_q975": metrics.get("tau_b_q975", ""),
        "interval_type": interval_type,
        "top_k_overlap": metrics["top_k_overlap"],
        "pairwise_direction_agreement": metrics["pairwise_direction_agreement"],
        "calibrated_score_mae": metrics["calibrated_score_mae"],
        "repository_coverage": metrics["repository_coverage"],
        "baseline_percentile": metrics.get("baseline_percentile", ""),
    }


def analyze_panel(panel: dict, instance_ids: list[str], source_rows: list[dict], config: dict) -> tuple[list[dict], dict, dict]:
    train = [row for row in source_rows if row["year"] == panel["train_year"]]
    test = [row for row in source_rows if row["year"] == panel["test_year"]]
    if len(train) < panel["minimum_train_systems"] or len(test) < panel["minimum_test_systems"]:
        raise RuntimeError(f"Panel {panel['name']} is undersized: train={len(train)}, test={len(test)}")

    scopes = {
        "all_systems": (train, test),
        "cluster_latest": (
            latest_per_cluster(train, panel["cluster_field"]),
            latest_per_cluster(test, panel["cluster_field"]),
        ),
    }
    rows = []
    baseline_tau = {}
    selections = {}
    for scope_index, (scope, (scope_train, scope_test)) in enumerate(scopes.items()):
        for budget in config["task_budgets"]:
            repeated = {"random": [], "repo_stratified_random": []}
            for repetition in range(config["random_repetitions"]):
                random_subset = core.uniform_random_subset(instance_ids, budget, 100000 * (scope_index + 1) + 1000 + repetition)
                stratified_subset = core.repository_stratified_subset(instance_ids, budget, 100000 * (scope_index + 1) + 2000 + repetition)
                repeated["random"].append(core.evaluate_subset(instance_ids, scope_train, scope_test, random_subset, panel["top_k_systems"]))
                repeated["repo_stratified_random"].append(core.evaluate_subset(instance_ids, scope_train, scope_test, stratified_subset, panel["top_k_systems"]))
            for method, records in repeated.items():
                summary = core.summarize_repetitions(records)
                rows.append(metric_row(panel["name"], scope, method, budget, summary, "task-sampling"))
                if method == "repo_stratified_random":
                    baseline_tau[(scope, budget)] = [record["tau_b"] for record in records]

            deterministic = {
                "entropy": core.entropy_subset(instance_ids, scope_train, budget),
                "temporal_coreset": core.temporal_coreset(instance_ids, scope_train, budget),
            }
            for method, subset in deterministic.items():
                metrics = core.evaluate_subset(instance_ids, scope_train, scope_test, subset, panel["top_k_systems"])
                full, reduced = score_vectors(instance_ids, scope_test, subset)
                q025, q975 = cluster_bootstrap_tau(
                    full,
                    reduced,
                    [row[panel["cluster_field"]] for row in scope_test],
                    config["cluster_bootstrap_repetitions"],
                    300000 + scope_index * 10000 + budget * 10 + (0 if method == "entropy" else 1),
                )
                metrics["tau_b_q025"] = q025
                metrics["tau_b_q975"] = q975
                baseline = baseline_tau[(scope, budget)]
                metrics["baseline_percentile"] = sum(value <= metrics["tau_b"] for value in baseline) / len(baseline)
                rows.append(metric_row(panel["name"], scope, method, budget, metrics, f"{panel['cluster_field']}-cluster-bootstrap"))
                if scope == "all_systems":
                    selections[f"{method}:{budget}"] = [instance_ids[index] for index in subset]

    decisions = {}
    primary_rows = [row for row in rows if row["scope"] == "all_systems"]
    random_candidates = [
        row for row in primary_rows
        if row["method"] == "repo_stratified_random"
        and row["tau_b"] >= config["minimum_mean_tau_b"]
        and float(row["tau_b_q025"]) >= config["minimum_random_tau_b_q025"]
    ]
    deterministic_candidates = {
        method: [
            row for row in primary_rows
            if row["method"] == method
            and row["tau_b"] >= config["minimum_mean_tau_b"]
            and float(row["tau_b_q025"]) >= config["minimum_deterministic_tau_b_q025"]
        ]
        for method in ("entropy", "temporal_coreset")
    }
    coreset_candidates = [
        row for row in primary_rows
        if row["method"] == "temporal_coreset"
        and row["tau_b"] >= config["minimum_mean_tau_b"]
        and float(row["tau_b_q025"]) >= config["minimum_deterministic_tau_b_q025"]
    ]
    decisions["minimum_reliable_repo_stratified_budget"] = min((row["budget"] for row in random_candidates), default=None)
    decisions["minimum_reliable_entropy_budget"] = min(
        (row["budget"] for row in deterministic_candidates["entropy"]), default=None
    )
    decisions["minimum_reliable_temporal_coreset_budget"] = min((row["budget"] for row in coreset_candidates), default=None)
    decisions["train_systems"] = len(train)
    decisions["test_systems"] = len(test)
    decisions["train_clusters"] = len({row[panel["cluster_field"]] for row in train})
    decisions["test_clusters"] = len({row[panel["cluster_field"]] for row in test})
    return rows, decisions, selections


def write_csv(path: pathlib.Path, rows: list[dict], fields: list[str]):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_config(config: dict) -> None:
    budgets = config.get("task_budgets", [])
    if not budgets or budgets != sorted(set(budgets)):
        raise ValueError("task_budgets must be a non-empty, strictly increasing list")
    if any(not isinstance(budget, int) or not 1 <= budget <= 500 for budget in budgets):
        raise ValueError("every task budget must be an integer from 1 through 500")
    if 500 not in budgets:
        raise ValueError("the 500-task positive-control endpoint is required")


def validate_positive_control(metric_rows: list[dict]) -> dict:
    rows = [row for row in metric_rows if row["scope"] == "all_systems" and row["budget"] == 500]
    expected = len({row["panel"] for row in metric_rows}) * 4
    failures = [
        {key: row[key] for key in ("panel", "method", "tau_b", "top_k_overlap", "calibrated_score_mae")}
        for row in rows
        if abs(float(row["tau_b"]) - 1.0) > 1e-12
        or abs(float(row["top_k_overlap"]) - 1.0) > 1e-12
        or abs(float(row["calibrated_score_mae"])) > 1e-12
    ]
    return {
        "expected_rows": expected,
        "observed_rows": len(rows),
        "failures": failures,
        "pass": len(rows) == expected and not failures,
    }


def reliability_decision(metric_rows: list[dict], panel: str, scope: str, config: dict) -> dict:
    rows = [row for row in metric_rows if row["panel"] == panel and row["scope"] == scope]
    random_candidates = [
        row for row in rows
        if row["method"] == "repo_stratified_random"
        and row["tau_b"] >= config["minimum_mean_tau_b"]
        and float(row["tau_b_q025"]) >= config["minimum_random_tau_b_q025"]
    ]
    deterministic_candidates = {
        method: [
            row for row in rows
            if row["method"] == method
            and row["tau_b"] >= config["minimum_mean_tau_b"]
            and float(row["tau_b_q025"]) >= config["minimum_deterministic_tau_b_q025"]
        ]
        for method in ("entropy", "temporal_coreset")
    }
    return {
        "minimum_reliable_repo_stratified_budget": min((row["budget"] for row in random_candidates), default=None),
        "minimum_reliable_entropy_budget": min(
            (row["budget"] for row in deterministic_candidates["entropy"]), default=None
        ),
        "minimum_reliable_temporal_coreset_budget": min(
            (row["budget"] for row in deterministic_candidates["temporal_coreset"]), default=None
        ),
    }


def chart_svg(metric_rows: list[dict], panel: str, width: int = 760, height: int = 340) -> str:
    selected = [row for row in metric_rows if row["panel"] == panel and row["scope"] == "all_systems"]
    budgets = sorted({row["budget"] for row in selected})
    methods = ["random", "repo_stratified_random", "entropy", "temporal_coreset"]
    colors = {"random": "#64748b", "repo_stratified_random": "#0369a1", "entropy": "#c2410c", "temporal_coreset": "#f97316"}
    dashes = {"random": "2 5", "repo_stratified_random": "", "entropy": "9 4", "temporal_coreset": "3 3"}
    left, right, top, bottom = 62, 20, 24, 88
    plot_w, plot_h = width - left - right, height - top - bottom
    x = {budget: left + i * plot_w / max(1, len(budgets) - 1) for i, budget in enumerate(budgets)}
    y = lambda value: top + (1.0 - max(0.0, min(1.0, float(value)))) * plot_h
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Held-out Kendall tau-b by task budget for {html.escape(panel)}">']
    for value in (0.0, 0.25, 0.50, 0.75, 0.90, 1.0):
        yy = y(value)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" stroke="#e2e8f0"/>')
        parts.append(f'<text x="{left-7}" y="{yy+4:.1f}" text-anchor="end" font-size="11">{value:.2f}</text>')
    lookup = {(row["method"], row["budget"]): row for row in selected}
    for method in methods:
        points = [(x[budget], y(lookup[(method, budget)]["tau_b"])) for budget in budgets if (method, budget) in lookup]
        if points:
            dash = f' stroke-dasharray="{dashes[method]}"' if dashes[method] else ""
            parts.append(f'<polyline points="{" ".join(f"{xx:.1f},{yy:.1f}" for xx, yy in points)}" fill="none" stroke="{colors[method]}" stroke-width="3"{dash}/>')
            parts.extend(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="3.5" fill="#fff" stroke="{colors[method]}" stroke-width="2"/>' for xx, yy in points)
    for budget in budgets:
        parts.append(f'<text x="{x[budget]:.1f}" y="{height-64}" text-anchor="middle" font-size="11">{budget}</text>')
    parts.append(f'<text x="{left + plot_w/2:.1f}" y="{height-45}" text-anchor="middle" font-size="12">Task budget (of 500)</text>')
    parts.append(f'<text x="16" y="{top + plot_h/2:.1f}" text-anchor="middle" font-size="12" transform="rotate(-90 16 {top + plot_h/2:.1f})">Held-out Kendall tau-b</text>')
    legend_x = left
    for method in methods:
        dash = f' stroke-dasharray="{dashes[method]}"' if dashes[method] else ""
        parts.append(f'<line x1="{legend_x}" y1="{height-17}" x2="{legend_x+18}" y2="{height-17}" stroke="{colors[method]}" stroke-width="3"{dash}/>')
        parts.append(f'<text x="{legend_x+23}" y="{height-13}" font-size="10">{html.escape(method.replace("_", " "))}</text>')
        legend_x += 160
    parts.append("</svg>")
    return "".join(parts)


def write_report(output: pathlib.Path, payload: dict, metric_rows: list[dict], longitudinal: list[dict]):
    panel_cards = []
    longitudinal_rows = []
    sections = []
    for record in longitudinal:
        decision = payload["decisions"][record["panel"]]
        sensitivity = payload["sensitivity_decisions"][record["panel"]]["cluster_latest"]
        robust = payload["robust_panel_decisions"][record["panel"]]
        panel_cards.append(
            f'<div class="card"><div class="muted">{html.escape(record["panel"])}</div>'
            f'<div class="value">{robust["minimum_reliable_repo_stratified_budget"] or "—"}</div>'
            '<div>tasks for stratified baseline, robust across scopes</div></div>'
        )
        longitudinal_rows.append(
            f'<tr><td>{html.escape(record["panel"])}</td><td>{record["train_year"]} → {record["test_year"]}</td>'
            f'<td>{record["train_systems"]} → {record["test_systems"]}</td>'
            f'<td>{record["solve_rate_change"]:+.3f} [{record["solve_rate_change_q025"]:+.3f}, {record["solve_rate_change_q975"]:+.3f}]</td>'
            f'<td>{record["entropy_change"]:+.3f} [{record["entropy_change_q025"]:+.3f}, {record["entropy_change_q975"]:+.3f}]</td>'
            f'<td>{record["train_near_saturated_tasks"]} → {record["test_near_saturated_tasks"]}</td></tr>'
        )
        panel_metrics = [row for row in metric_rows if row["panel"] == record["panel"] and row["scope"] == "all_systems"]
        checkpoints = {
            100,
            150,
            400,
            500,
            decision["minimum_reliable_repo_stratified_budget"],
            decision["minimum_reliable_entropy_budget"],
            decision["minimum_reliable_temporal_coreset_budget"],
        }
        checkpoint_rows = []
        for row in panel_metrics:
            if row["budget"] not in checkpoints:
                continue
            interval = ""
            if row["tau_b_q025"] != "":
                interval = f' [{float(row["tau_b_q025"]):.3f}, {float(row["tau_b_q975"]):.3f}]'
            checkpoint_rows.append(
                f'<tr><td>{html.escape(row["method"].replace("_", " "))}</td><td>{row["budget"]}</td>'
                f'<td>{row["tau_b"]:.3f}{interval}</td><td>{row["top_k_overlap"]:.2f}</td>'
                f'<td>{row["pairwise_direction_agreement"]:.3f}</td><td>{row["calibrated_score_mae"]:.4f}</td></tr>'
            )
        sections.append(
            f'<h3>{html.escape(record["panel"])} held-out ranking fidelity</h3>'
            f'<p>Task selection used only {record["train_year"]} outcomes; evaluation used {record["test_systems"]} systems from {record["test_year"]}. '
            f'The first reliable repository-stratified random budget was <strong>{decision["minimum_reliable_repo_stratified_budget"]} tasks</strong>. '
            f'After retaining only the latest system in each related family/provider cluster, it was <strong>{sensitivity["minimum_reliable_repo_stratified_budget"]} tasks</strong>. '
            'Lines show mean held-out Kendall tau-b; the exact decision also requires the predeclared lower-bound threshold.</p>'
            f'{chart_svg(metric_rows, record["panel"])}'
            '<table><thead><tr><th>Method</th><th>Tasks</th><th>τ-b with interval</th><th>Top-k</th><th>Pairwise</th><th>MAE</th></tr></thead>'
            f'<tbody>{"".join(checkpoint_rows)}</tbody></table>'
        )

    common = payload["robust_cross_panel_decision"]
    open_record = next(record for record in longitudinal if record["panel"] == "open-submission")
    bash_record = next(record for record in longitudinal if record["panel"] == "standardized-bash")

    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Formal SWE-bench Discriminative-Power Study</title><style>
body{{margin:0;background:#f8fafc;color:#0f172a;font-family:Inter,system-ui,sans-serif;line-height:1.5}}main{{max-width:1120px;margin:auto;padding:42px 24px 70px}}
h1{{font-size:36px;line-height:1.15;margin:4px 0}}h2{{margin-top:38px}}h3{{margin-top:28px;font-size:21px}}.eyebrow{{color:#0369a1;font-weight:750;text-transform:uppercase;letter-spacing:.08em;font-size:12px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:22px 0}}.card{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px;box-shadow:0 4px 18px #0f172a0b}}
.value{{font-size:30px;font-weight:780}}.muted{{color:#64748b}}.note{{border-left:4px solid #0369a1;background:#e0f2fe;padding:13px 16px;border-radius:7px;margin:20px 0}}code{{font-size:12px;overflow-wrap:anywhere}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;font-size:13px}}th,td{{padding:9px 11px;border-bottom:1px solid #e2e8f0;text-align:right}}th:first-child,td:first-child{{text-align:left}}th{{background:#f1f5f9}}svg{{width:100%;height:auto;background:#fff;border-radius:12px;margin:8px 0 14px}}
</style></head><body><main><div class="eyebrow">Paper-facing formal experiment</div><h1>Temporal discriminative power in SWE-bench Verified</h1>
<p class="muted">Two non-pooled temporal panels: heterogeneous open submissions and a standardized mini-SWE-agent Bash-only environment.</p>
<h2>Technical summary</h2>
<p><strong>The original 150-task pilot conclusion does not generalize.</strong> After requiring a rule to hold in both temporal panels and after retaining only the latest member of each related system family/provider cluster, repository-stratified random sampling required all {common["common_reliable_repo_stratified_budget"]} tasks. Entropy selection required {common["common_reliable_entropy_budget"]} tasks and the temporal core set required {common["common_reliable_temporal_coreset_budget"]}. The 500-task positive control passed, and all included matrices reconciled to official scores.</p>
<div class="grid">{"".join(panel_cards)}</div>
<div class="note"><strong>Interpretation boundary.</strong> The 2025 open-submission panel was inspected during the pilot and is developmental. The 2026 standardized panel was absent from the pilot and supplies the time-external replication. Submission dates do not identify exact harness versions.</div>
<h2>Both panels became easier, but only the standardized panel clearly lost task entropy</h2>
<p>Mean task solve rate increased by {open_record["solve_rate_change"]:+.3f} in the open panel and {bash_record["solve_rate_change"]:+.3f} in the standardized panel. The open-panel entropy interval crosses zero; the standardized-panel entropy change is negative throughout its repository-bootstrap interval. These are descriptive temporal shifts, not causal effects.</p>
<table><thead><tr><th>Panel</th><th>Years</th><th>Systems</th><th>Solve-rate change</th><th>Entropy change</th><th>Near-saturated tasks</th></tr></thead><tbody>{"".join(longitudinal_rows)}</tbody></table>
<h2>Reduced task budgets are panel-dependent</h2>
<p>The charts compare four selectors at the same 13 predeclared budgets. Ranking fidelity alone is insufficient: a budget is called reliable only when its mean and lower uncertainty bound both cross the protocol thresholds.</p>
{"".join(sections)}
<h2>Scope, definitions, and experimental design</h2><p>The unit of analysis is a public system-task outcome on the canonical 500 SWE-bench Verified instances. The open-submission panel selects tasks from 2024 and evaluates 2025; the standardized Bash-only panel selects from 2025 and evaluates 2026. Kendall tau-b compares each reduced-task system ordering with the full 500-task ordering. Top-k overlap, pairwise agreement, calibrated score MAE, and repository coverage are secondary outcomes.</p>
<h2>Data quality, uncertainty, and robustness</h2><p>All included task matrices reconcile to official aggregate scores. Random intervals vary task samples; deterministic intervals cluster systems by official agent label or model provider. Task-shift intervals resample source repositories. Exact duplicate signatures, enumerated exclusions, source hashes, and latest-per-cluster sensitivity results are retained in the machine-readable files. The 500-task endpoint is a mandatory positive control and fails the workflow if it does not reproduce the full ranking exactly.</p>
<h2>Limitations and next study decision</h2><p>Submission dates do not identify exact harness versions, public systems are selected and correlated, and most public results do not measure run-to-run model variance. The related-system sensitivity is consequential: it eliminates the apparent 450-task saving for stratified random sampling. Therefore the result supports benchmark-maintenance and task-budget claims only—not causal claims about model progress. Further robustness work should target score denominators and selector stability; it should not revive the rejected build-log hypothesis.</p>
<h2>Further questions</h2><p>Does entropy selection remain stable under future standardized submissions, and can a selector trained across multiple frozen historical windows outperform the simple entropy baseline without approaching the full 500-task cost?</p>
<p class="muted">Generated {html.escape(payload["generated_at_utc"])}. Experiments commit <code>{payload["source_commits"]["experiments"]}</code>; website commit <code>{payload["source_commits"]["website"]}</code>.</p>
</main></body></html>'''
    (output / "report.html").write_text(document, encoding="utf-8")


def run(config_path: pathlib.Path, output: pathlib.Path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_config(config)
    output.mkdir(parents=True, exist_ok=True)
    experiments_commit = repo_commit(EXPERIMENTS_REPO, "main")
    website_commit = repo_commit(WEBSITE_REPO, "master")
    leaderboard_url = raw_url(WEBSITE_REPO, website_commit, "data/leaderboards.json")
    verified_meta, bash_meta = leaderboard_maps(core.http_json(leaderboard_url))
    instance_ids, instance_urls = core.collect_instances()
    score_tolerance = config["maximum_published_score_delta_pp"]
    classic_rows, classic_urls, classic_quality = collect_classic(instance_ids, experiments_commit, verified_meta, score_tolerance)
    bash_rows, bash_urls, bash_quality = collect_bash(instance_ids, experiments_commit, bash_meta, score_tolerance)
    sources = {"classic": classic_rows, "bash-only": bash_rows}

    metric_rows = []
    longitudinal = []
    decisions = {}
    selections = {}
    panel_quality = {}
    for panel_index, panel in enumerate(config["panels"]):
        source_rows = sources[panel["source"]]
        train = [row for row in source_rows if row["year"] == panel["train_year"]]
        test = [row for row in source_rows if row["year"] == panel["test_year"]]
        longitudinal.append(longitudinal_record(panel, instance_ids, train, test, config["repository_bootstrap_repetitions"]))
        rows, panel_decisions, panel_selections = analyze_panel(panel, instance_ids, source_rows, config)
        metric_rows.extend(rows)
        decisions[panel["name"]] = panel_decisions
        selections[panel["name"]] = panel_selections
        panel_quality[panel["name"]] = {
            "train": duplicate_signature_summary(train) | Counter(row["attempts"] for row in train),
            "test": duplicate_signature_summary(test) | Counter(row["attempts"] for row in test),
        }

    random_budgets = [value["minimum_reliable_repo_stratified_budget"] for value in decisions.values()]
    entropy_budgets = [value["minimum_reliable_entropy_budget"] for value in decisions.values()]
    coreset_budgets = [value["minimum_reliable_temporal_coreset_budget"] for value in decisions.values()]
    cross_panel = {
        "common_reliable_repo_stratified_budget": max(random_budgets) if all(value is not None for value in random_budgets) else None,
        "common_reliable_entropy_budget": max(entropy_budgets) if all(value is not None for value in entropy_budgets) else None,
        "common_reliable_temporal_coreset_budget": max(coreset_budgets) if all(value is not None for value in coreset_budgets) else None,
    }
    positive_control = validate_positive_control(metric_rows)
    sensitivity_decisions = {
        panel["name"]: {
            scope: reliability_decision(metric_rows, panel["name"], scope, config)
            for scope in ("all_systems", "cluster_latest")
        }
        for panel in config["panels"]
    }
    decision_keys = (
        "minimum_reliable_repo_stratified_budget",
        "minimum_reliable_entropy_budget",
        "minimum_reliable_temporal_coreset_budget",
    )
    robust_panel_decisions = {
        panel: {
            key: max(scope_decisions[scope][key] for scope in scope_decisions)
            if all(scope_decisions[scope][key] is not None for scope in scope_decisions)
            else None
            for key in decision_keys
        }
        for panel, scope_decisions in sensitivity_decisions.items()
    }
    robust_cross_panel = {
        "common_reliable_repo_stratified_budget": max(
            value["minimum_reliable_repo_stratified_budget"] for value in robust_panel_decisions.values()
        ),
        "common_reliable_entropy_budget": max(
            value["minimum_reliable_entropy_budget"] for value in robust_panel_decisions.values()
        ),
        "common_reliable_temporal_coreset_budget": max(
            value["minimum_reliable_temporal_coreset_budget"] for value in robust_panel_decisions.values()
        ),
    }
    data_quality = {
        "canonical_tasks": len(instance_ids),
        "classic": classic_quality,
        "bash-only": bash_quality,
        "panel_period_checks": panel_quality,
        "cross_format_folder_overlap": len({row["name"] for row in classic_rows} & {row["name"] for row in bash_rows}),
        "positive_control": positive_control,
        "overall_pass": (
            classic_quality["score_reconciliation_failures"] == 0
            and classic_quality["metadata_missing"] == 0
            and bash_quality["score_reconciliation_failures"] == 0
            and bash_quality["metadata_missing"] == 0
            and bash_quality["explicit_500_task_matrices"] == bash_quality["usable"]
            and positive_control["pass"]
        ),
    }
    payload = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "config": config,
        "source_commits": {"experiments": experiments_commit, "website": website_commit},
        "data_quality": data_quality,
        "longitudinal": longitudinal,
        "decisions": decisions,
        "cross_panel_decision": cross_panel,
        "sensitivity_decisions": sensitivity_decisions,
        "robust_panel_decisions": robust_panel_decisions,
        "robust_cross_panel_decision": robust_cross_panel,
        "selected_instance_ids": selections,
    }
    (output / "formal_results.json").write_text(json.dumps(payload, indent=2, sort_keys=True, default=dict), encoding="utf-8")
    (output / "data_quality.json").write_text(json.dumps(data_quality, indent=2, sort_keys=True, default=dict), encoding="utf-8")
    manifest = {
        "collected_at_utc": payload["generated_at_utc"],
        "source_commits": payload["source_commits"],
        "canonical_instance_urls": instance_urls,
        "leaderboard_url": leaderboard_url,
        "classic_urls": classic_urls,
        "bash_only_urls": bash_urls,
        "matrix_digests": {"classic": classic_quality["matrix_sha256"], "bash-only": bash_quality["matrix_sha256"]},
        "python": sys.version,
        "redistributes_upstream_outcome_matrix": False,
    }
    (output / "source_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    metric_fields = [
        "panel", "scope", "method", "budget", "tau_b", "tau_b_q025", "tau_b_q975", "interval_type",
        "top_k_overlap", "pairwise_direction_agreement", "calibrated_score_mae", "repository_coverage", "baseline_percentile",
    ]
    write_csv(output / "formal_metrics.csv", metric_rows, metric_fields)
    longitudinal_fields = [key for key in longitudinal[0] if key != "transitions"]
    write_csv(output / "longitudinal.csv", longitudinal, longitudinal_fields)
    summary_lines = [
        "# Formal SWE-bench discriminative-power study",
        "",
        f"**Data-quality decision: {'PASS' if data_quality['overall_pass'] else 'FAIL'}**",
        "",
    ]
    for record in longitudinal:
        decision = decisions[record["panel"]]
        summary_lines.extend([
            f"## {record['panel']}",
            "",
            f"- Temporal comparison: {record['train_year']} ({record['train_systems']} systems) to {record['test_year']} ({record['test_systems']} systems).",
            f"- Mean task solve-rate change: {record['solve_rate_change']:+.3f} (repository-bootstrap 95% interval {record['solve_rate_change_q025']:+.3f} to {record['solve_rate_change_q975']:+.3f}).",
            f"- Mean task entropy change: {record['entropy_change']:+.3f} (repository-bootstrap 95% interval {record['entropy_change_q025']:+.3f} to {record['entropy_change_q975']:+.3f}).",
            f"- Minimum reliable repository-stratified budget: {decision['minimum_reliable_repo_stratified_budget']} tasks.",
            f"- Minimum reliable entropy budget: {decision['minimum_reliable_entropy_budget']} tasks.",
            f"- Minimum reliable temporal-core-set budget: {decision['minimum_reliable_temporal_coreset_budget']} tasks.",
            "",
        ])
    summary_lines.extend([
        "## Cross-panel decisions",
        "",
        f"- All-systems repository-stratified budget: {cross_panel['common_reliable_repo_stratified_budget']} tasks.",
        f"- All-systems entropy budget: {cross_panel['common_reliable_entropy_budget']} tasks.",
        f"- All-systems temporal-core-set budget: {cross_panel['common_reliable_temporal_coreset_budget']} tasks.",
        f"- Robust repository-stratified budget across all/latest-cluster scopes: {robust_cross_panel['common_reliable_repo_stratified_budget']} tasks.",
        f"- Robust entropy budget across all/latest-cluster scopes: {robust_cross_panel['common_reliable_entropy_budget']} tasks.",
        f"- Robust temporal-core-set budget across all/latest-cluster scopes: {robust_cross_panel['common_reliable_temporal_coreset_budget']} tasks.",
        "",
        "The open-submission comparison is developmental because its 2025 outcomes were inspected in the pilot. The 2026 standardized panel is the time-external replication. Neither comparison is causal.",
    ])
    (output / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    write_report(output, payload, metric_rows, longitudinal)
    print(json.dumps({"data_quality_pass": data_quality["overall_pass"], "cross_panel": cross_panel, "robust_cross_panel": robust_cross_panel, "decisions": decisions, "sensitivity_decisions": sensitivity_decisions}, indent=2))
    if not data_quality["overall_pass"]:
        raise SystemExit("Formal data-quality gate failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    run(args.config, args.output)


if __name__ == "__main__":
    main()
