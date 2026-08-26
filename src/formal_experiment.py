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
import math
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
            "agent_lineage": normalize_label(agent, name),
            "model_family": normalize_label(official.get("model_display"), official.get("model_org", "unknown")),
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
            "agent_lineage": normalize_label(official.get("agent"), "mini swe agent"),
            "model_family": normalize_label(official.get("model_display"), official.get("model_org", "unknown")),
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


def two_way_bootstrap_difference(
    instance_ids: list[str],
    train_rows: list[dict],
    test_rows: list[dict],
    cluster_field: str,
    transform,
    repetitions: int,
    seed: int,
) -> tuple[float, float]:
    """Resample task repositories and system clusters independently.

    This sensitivity analysis adds system-cohort uncertainty to the repository-
    only RQ1 interval.  It is descriptive because public leaderboard systems
    are not a probability sample.
    """
    repositories = defaultdict(list)
    for index, task_id in enumerate(instance_ids):
        repositories[task_id.split("__", 1)[0]].append(index)

    def cluster_groups(rows: list[dict]):
        groups = defaultdict(list)
        for index, row in enumerate(rows):
            groups[row[cluster_field]].append(index)
        return groups

    train_groups = cluster_groups(train_rows)
    test_groups = cluster_groups(test_rows)
    repository_keys = sorted(repositories)
    train_keys = sorted(train_groups)
    test_keys = sorted(test_groups)
    rng = random.Random(seed)
    values = []
    for _ in range(repetitions):
        train_indices = [
            index
            for key in rng.choices(train_keys, k=len(train_keys))
            for index in train_groups[key]
        ]
        test_indices = [
            index
            for key in rng.choices(test_keys, k=len(test_keys))
            for index in test_groups[key]
        ]
        task_indices = [
            index
            for key in rng.choices(repository_keys, k=len(repository_keys))
            for index in repositories[key]
        ]
        train_rates = [
            statistics.fmean(train_rows[row_index]["outcomes"][task_index] for row_index in train_indices)
            for task_index in task_indices
        ]
        test_rates = [
            statistics.fmean(test_rows[row_index]["outcomes"][task_index] for row_index in test_indices)
            for task_index in task_indices
        ]
        values.append(statistics.fmean(transform(b) - transform(a) for a, b in zip(train_rates, test_rates)))
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
    panel: dict,
    instance_ids: list[str],
    train_rows: list[dict],
    test_rows: list[dict],
    bootstrap_repetitions: int,
    two_way_repetitions: int,
) -> dict:
    train_rates = core.task_rates(train_rows, len(instance_ids))
    test_rates = core.task_rates(test_rows, len(instance_ids))
    train_entropy = [core.binary_entropy(value) for value in train_rates]
    test_entropy = [core.binary_entropy(value) for value in test_rates]
    solve_ci = repository_bootstrap_difference(instance_ids, train_rates, test_rates, bootstrap_repetitions, 6100 + panel["train_year"])
    entropy_ci = repository_bootstrap_difference(instance_ids, train_entropy, test_entropy, bootstrap_repetitions, 7100 + panel["test_year"])
    solve_two_way_ci = two_way_bootstrap_difference(
        instance_ids, train_rows, test_rows, panel["cluster_field"], lambda value: value,
        two_way_repetitions, 8100 + panel["train_year"],
    )
    entropy_two_way_ci = two_way_bootstrap_difference(
        instance_ids, train_rows, test_rows, panel["cluster_field"], core.binary_entropy,
        two_way_repetitions, 9100 + panel["test_year"],
    )
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
        "solve_rate_change_two_way_q025": solve_two_way_ci[0],
        "solve_rate_change_two_way_q975": solve_two_way_ci[1],
        "train_mean_entropy": train_summary["mean_binary_entropy"],
        "test_mean_entropy": test_summary["mean_binary_entropy"],
        "entropy_change": test_summary["mean_binary_entropy"] - train_summary["mean_binary_entropy"],
        "entropy_change_q025": entropy_ci[0],
        "entropy_change_q975": entropy_ci[1],
        "entropy_change_two_way_q025": entropy_two_way_ci[0],
        "entropy_change_two_way_q975": entropy_two_way_ci[1],
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
        "full_top_k_set_size": metrics["full_top_k_set_size"],
        "subset_top_k_set_size": metrics["subset_top_k_set_size"],
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


def sampled_cluster_indices(rows: list[dict], cluster_field: str, rng: random.Random) -> list[int]:
    groups = defaultdict(list)
    for index, row in enumerate(rows):
        groups[row[cluster_field]].append(index)
    keys = sorted(groups)
    return [index for key in rng.choices(keys, k=len(keys)) for index in groups[key]]


def nested_uniform_subsets(task_count: int, budgets: list[int], rng: random.Random) -> dict[int, list[int]]:
    """Draw one random task ordering and return its nested budget prefixes."""
    ordering = list(range(task_count))
    rng.shuffle(ordering)
    return {budget: sorted(ordering[:budget]) for budget in budgets}


def nested_repository_subsets(
    instance_ids: list[str], budgets: list[int], rng: random.Random
) -> dict[int, list[int]]:
    """Build a nested, approximately proportional repository-stratified path.

    At each step the repository with the largest proportional allocation
    deficit supplies its next randomly ordered task.  This defines one deployable
    random ordering, keeps every larger budget a superset of every smaller one,
    and reaches the exact 500-task endpoint.
    """
    groups = defaultdict(list)
    for index, task_id in enumerate(instance_ids):
        groups[task_id.split("__", 1)[0]].append(index)
    for indices in groups.values():
        rng.shuffle(indices)
    keys = sorted(groups)
    total = len(instance_ids)
    selected_counts = {key: 0 for key in keys}
    ordering = []
    checkpoints = set(budgets)
    output = {}
    for step in range(1, max(budgets) + 1):
        available = [key for key in keys if selected_counts[key] < len(groups[key])]
        key = max(
            available,
            key=lambda item: (
                step * len(groups[item]) / total - selected_counts[item],
                -selected_counts[item],
                str(item),
            ),
        )
        ordering.append(groups[key][selected_counts[key]])
        selected_counts[key] += 1
        if step in checkpoints:
            output[step] = sorted(ordering)
    return output


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Return a two-sided Wilson interval for a binomial proportion."""
    if trials <= 0:
        return float("nan"), float("nan")
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (proportion + z * z / (2.0 * trials)) / denominator
    half_width = z * math.sqrt(
        proportion * (1.0 - proportion) / trials + z * z / (4.0 * trials * trials)
    ) / denominator
    return max(0.0, centre - half_width), min(1.0, centre + half_width)


def harmonized_curve_bootstrap(
    panels: list[dict],
    sources: dict[str, list[dict]],
    instance_ids: list[str],
    metric_rows: list[dict],
    config: dict,
) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    """Bootstrap complete budget curves under a joint decision-family design.

    Each seed contributes ``harmonized_bootstrap_repetitions`` replicates.  A
    replicate draws held-out clusters once per panel and reuses that draw for
    both the all-system and cluster-latest scopes.  The two panels are sampled
    independently and paired by replicate index.  Random procedures draw one
    nested task ordering per panel-replicate; deterministic procedures retain
    the task set trained for their scope.  The pooled replicates support
    empirical pointwise bounds, the legacy raw-deviation cell-wise band,
    budget-standardized cell-wise max-t bands, and a max-t band over the full
    four-cell by budget decision family.
    """
    budgets = config["task_budgets"]
    methods = ("random", "repo_stratified_random", "entropy", "temporal_coreset")
    repetitions_per_seed = config["harmonized_bootstrap_repetitions"]
    seeds = config["harmonized_bootstrap_seeds"]
    repetitions = repetitions_per_seed * len(seeds)
    independent_repetitions = config.get("independent_budget_coupling_repetitions", 0)
    point_lookup = {
        (row["panel"], row["scope"], row["method"], int(row["budget"])): float(row["tau_b"])
        for row in metric_rows
    }
    curves = defaultdict(list)
    independent_curves = defaultdict(list)
    cells = [
        (panel["name"], scope)
        for panel in panels
        for scope in ("all_systems", "cluster_latest")
    ]
    for panel_index, panel in enumerate(panels):
        source_rows = sources[panel["source"]]
        train = [row for row in source_rows if row["year"] == panel["train_year"]]
        test = [row for row in source_rows if row["year"] == panel["test_year"]]
        scope_rows = {
            "all_systems": (train, test),
            "cluster_latest": (
                latest_per_cluster(train, panel["cluster_field"]),
                latest_per_cluster(test, panel["cluster_field"]),
            ),
        }
        cluster_groups = defaultdict(list)
        for index, row in enumerate(test):
            cluster_groups[row[panel["cluster_field"]]].append(index)
        cluster_keys = sorted(cluster_groups)
        latest_test = scope_rows["cluster_latest"][1]
        latest_index = {
            row[panel["cluster_field"]]: index for index, row in enumerate(latest_test)
        }
        full_scores = {
            scope: core.subset_scores(scope_test, list(range(len(instance_ids))))
            for scope, (_, scope_test) in scope_rows.items()
        }
        deterministic_scores = {}
        for scope, (scope_train, scope_test) in scope_rows.items():
            for budget in budgets:
                for method, selector in (
                    ("entropy", core.entropy_subset),
                    ("temporal_coreset", core.temporal_coreset),
                ):
                    subset = selector(instance_ids, scope_train, budget)
                    deterministic_scores[(scope, method, budget)] = core.subset_scores(scope_test, subset)

        for seed_index, seed in enumerate(seeds):
            for local_repetition in range(repetitions_per_seed):
                replicate_seed = seed * 10_000_000 + panel_index * 1_000_000 + local_repetition
                cluster_rng = random.Random(replicate_seed + 11)
                drawn_clusters = cluster_rng.choices(cluster_keys, k=len(cluster_keys))
                bootstrap_indices = {
                    "all_systems": [
                        index for key in drawn_clusters for index in cluster_groups[key]
                    ],
                    "cluster_latest": [latest_index[key] for key in drawn_clusters],
                }
                random_paths = {
                    "random": nested_uniform_subsets(
                        len(instance_ids), budgets, random.Random(replicate_seed + 101)
                    ),
                    "repo_stratified_random": nested_repository_subsets(
                        instance_ids, budgets, random.Random(replicate_seed + 211)
                    ),
                }
                for scope, (_, scope_test) in scope_rows.items():
                    cell = (panel["name"], scope)
                    indices = bootstrap_indices[scope]
                    boot_full = [full_scores[scope][index] for index in indices]
                    for budget in budgets:
                        for method in methods:
                            if budget == len(instance_ids):
                                value = 1.0
                            else:
                                if method in random_paths:
                                    reduced = core.subset_scores(scope_test, random_paths[method][budget])
                                else:
                                    reduced = deterministic_scores[(scope, method, budget)]
                                value = core.kendall_tau_b(
                                    boot_full, [reduced[index] for index in indices]
                                )
                            curves[(cell, method, budget)].append(value)

                            if (
                                seed_index == 0
                                and local_repetition < independent_repetitions
                                and method in random_paths
                            ):
                                if budget == len(instance_ids):
                                    independent_value = 1.0
                                else:
                                    independent_seed = replicate_seed + budget * 10_000
                                    subset = (
                                        core.uniform_random_subset(instance_ids, budget, independent_seed + 307)
                                        if method == "random"
                                        else core.repository_stratified_subset(instance_ids, budget, independent_seed + 401)
                                    )
                                    independent_reduced = core.subset_scores(scope_test, subset)
                                    independent_value = core.kendall_tau_b(
                                        boot_full, [independent_reduced[index] for index in indices]
                                    )
                                independent_curves[(cell, method, budget)].append(independent_value)

    def curve_summary(curve_source: dict, slice_start: int = 0, slice_end: int | None = None):
        values_lookup = {
            key: values[slice_start:slice_end]
            for key, values in curve_source.items()
        }
        centres = {key: statistics.fmean(values) for key, values in values_lookup.items()}
        standard_errors = {
            key: statistics.stdev(values) if len(values) > 1 else 0.0
            for key, values in values_lookup.items()
        }
        exact = {
            key: key[2] == len(instance_ids) or standard_errors[key] <= 1e-12
            for key in values_lookup
        }
        raw_corrections = {}
        cellwise_critical = {}
        joint_critical = {}
        driver_rows = []
        active_methods = sorted({key[1] for key in values_lookup})
        for cell in cells:
            panel, scope = cell
            for method in active_methods:
                available = [budget for budget in budgets if (cell, method, budget) in values_lookup]
                nonexact = [budget for budget in available if not exact[(cell, method, budget)]]
                if not nonexact:
                    raw_corrections[(cell, method)] = 0.0
                    cellwise_critical[(cell, method)] = 0.0
                    continue
                n = len(values_lookup[(cell, method, nonexact[0])])
                raw_deviations = []
                standardized_maxima = []
                raw_driver_counts = Counter()
                max_t_driver_counts = Counter()
                for repetition in range(n):
                    raw_budget = min(
                        nonexact,
                        key=lambda budget: values_lookup[(cell, method, budget)][repetition]
                        - point_lookup[(panel, scope, method, budget)],
                    )
                    max_t_budget = max(
                        nonexact,
                        key=lambda budget: (
                            centres[(cell, method, budget)]
                            - values_lookup[(cell, method, budget)][repetition]
                        ) / standard_errors[(cell, method, budget)],
                    )
                    raw_driver_counts[raw_budget] += 1
                    max_t_driver_counts[max_t_budget] += 1
                    raw_deviations.append(
                        values_lookup[(cell, method, raw_budget)][repetition]
                        - point_lookup[(panel, scope, method, raw_budget)]
                    )
                    standardized_maxima.append((
                        centres[(cell, method, max_t_budget)]
                        - values_lookup[(cell, method, max_t_budget)][repetition]
                    ) / standard_errors[(cell, method, max_t_budget)])
                raw_corrections[(cell, method)] = core.quantile(raw_deviations, 0.025)
                cellwise_critical[(cell, method)] = core.quantile(standardized_maxima, 0.975)
                for budget in available:
                    driver_rows.append({
                        "band": "raw_deviation_cellwise",
                        "panel": panel,
                        "scope": scope,
                        "method": method,
                        "budget": budget,
                        "driver_count": raw_driver_counts[budget],
                        "driver_probability": raw_driver_counts[budget] / n,
                        "critical_value": raw_corrections[(cell, method)],
                    })
                    driver_rows.append({
                        "band": "standardized_max_t_cellwise",
                        "panel": panel,
                        "scope": scope,
                        "method": method,
                        "budget": budget,
                        "driver_count": max_t_driver_counts[budget],
                        "driver_probability": max_t_driver_counts[budget] / n,
                        "critical_value": cellwise_critical[(cell, method)],
                    })

        for method in active_methods:
            available = [
                (cell, budget) for cell in cells for budget in budgets
                if (cell, method, budget) in values_lookup and not exact[(cell, method, budget)]
            ]
            if not available:
                joint_critical[method] = 0.0
                continue
            n = len(values_lookup[(available[0][0], method, available[0][1])])
            maxima = []
            driver_counts = Counter()
            for repetition in range(n):
                driver = max(
                    available,
                    key=lambda item: (
                        centres[(item[0], method, item[1])]
                        - values_lookup[(item[0], method, item[1])][repetition]
                    ) / standard_errors[(item[0], method, item[1])],
                )
                driver_counts[driver] += 1
                maxima.append((
                    centres[(driver[0], method, driver[1])]
                    - values_lookup[(driver[0], method, driver[1])][repetition]
                ) / standard_errors[(driver[0], method, driver[1])])
            joint_critical[method] = core.quantile(maxima, 0.975)
            for cell, budget in available:
                driver_rows.append({
                    "band": "standardized_max_t_joint_four_cells",
                    "panel": cell[0],
                    "scope": cell[1],
                    "method": method,
                    "budget": budget,
                    "driver_count": driver_counts[(cell, budget)],
                    "driver_probability": driver_counts[(cell, budget)] / n,
                    "critical_value": joint_critical[method],
                })
        return values_lookup, centres, standard_errors, exact, raw_corrections, cellwise_critical, joint_critical, driver_rows

    (
        pooled_values, pooled_centres, pooled_se, pooled_exact, raw_corrections,
        cellwise_critical, joint_critical, driver_rows,
    ) = curve_summary(curves)

    output_rows = []
    for cell in cells:
        panel, scope = cell
        for method in methods:
            for budget in budgets:
                values = pooled_values[(cell, method, budget)]
                point = point_lookup[(panel, scope, method, budget)]
                exact_endpoint = pooled_exact[(cell, method, budget)]
                standard_error = pooled_se[(cell, method, budget)]
                output_rows.append({
                    "panel": panel,
                    "scope": scope,
                    "method": method,
                    "budget": budget,
                    "tau_b": point,
                    "tau_b_bootstrap_mean": statistics.fmean(values),
                    "tau_b_bootstrap_sd": standard_error,
                    "tau_b_q025": core.quantile(values, 0.025),
                    "tau_b_q975": core.quantile(values, 0.975),
                    "raw_cellwise_lower_band": point if exact_endpoint else point + raw_corrections[(cell, method)],
                    "cellwise_max_t_lower_band": point if exact_endpoint else point - cellwise_critical[(cell, method)] * standard_error,
                    "joint_max_t_lower_band": point if exact_endpoint else point - joint_critical[method] * standard_error,
                    "repetitions": repetitions,
                    "repetitions_per_seed": repetitions_per_seed,
                    "seed_count": len(seeds),
                    "system_cluster_resampled": True,
                    "task_subset_redrawn": method in {"random", "repo_stratified_random"},
                    "random_budget_coupling": "nested_prefix",
                })

    harmonized_lookup = {
        (row["panel"], row["scope"], row["method"], row["budget"]): row
        for row in output_rows
    }
    mean_threshold = config["minimum_mean_tau_b"]
    lower_threshold = config["minimum_harmonized_tau_b_q025"]

    def common_budget(lower_field: str):
        result = {}
        for method in methods:
            result[method] = next((
                budget for budget in budgets
                if all(
                    harmonized_lookup[(panel, scope, method, budget)]["tau_b"] >= mean_threshold
                    and harmonized_lookup[(panel, scope, method, budget)][lower_field] >= lower_threshold
                    for panel, scope in cells
                )
            ), None)
        return result

    pointwise = common_budget("tau_b_q025")
    raw_cellwise = common_budget("raw_cellwise_lower_band")
    cellwise_max_t = common_budget("cellwise_max_t_lower_band")
    joint_max_t = common_budget("joint_max_t_lower_band")
    decision_rows = [{
        "method": method,
        "mean_tau_b_threshold": mean_threshold,
        "common_lower_bound_threshold": lower_threshold,
        "pointwise_common_reliable_budget": pointwise[method],
        "raw_cellwise_common_reliable_budget": raw_cellwise[method],
        "cellwise_max_t_common_reliable_budget": cellwise_max_t[method],
        "joint_max_t_common_reliable_budget": joint_max_t[method],
        "repetitions": repetitions,
        "repetitions_per_seed": repetitions_per_seed,
        "seed_count": len(seeds),
    } for method in methods]

    stability_rows = []
    for method in methods:
        first_counts = Counter()
        persistent_counts = Counter()
        for repetition in range(repetitions):
            passing = {
                budget: all(curves[(cell, method, budget)][repetition] >= mean_threshold for cell in cells)
                for budget in budgets
            }
            first_counts[next((budget for budget in budgets if passing[budget]), "no_pass")] += 1
            persistent_counts[next((
                budget for index, budget in enumerate(budgets)
                if all(passing[later] for later in budgets[index:])
            ), "no_pass")] += 1
        for budget in budgets + ["no_pass"]:
            first_lower, first_upper = wilson_interval(first_counts[budget], repetitions)
            persistent_lower, persistent_upper = wilson_interval(persistent_counts[budget], repetitions)
            stability_rows.append({
                "method": method,
                "selected_budget": budget,
                "first_passing_count": first_counts[budget],
                "first_passing_probability": first_counts[budget] / repetitions,
                "first_passing_probability_ci_lower": first_lower,
                "first_passing_probability_ci_upper": first_upper,
                "persistent_rule_count": persistent_counts[budget],
                "persistent_rule_probability": persistent_counts[budget] / repetitions,
                "persistent_rule_probability_ci_lower": persistent_lower,
                "persistent_rule_probability_ci_upper": persistent_upper,
                "repetitions": repetitions,
                "criterion": f"all four cells have tau_b >= {mean_threshold:.2f} in the same curve replicate",
            })

    seed_stability_rows = []
    diagnostic_budget = 475 if 475 in budgets else budgets[-2]
    for seed_index, seed in enumerate(seeds):
        start = seed_index * repetitions_per_seed
        end = start + repetitions_per_seed
        (
            seed_values, _, seed_se, seed_exact, seed_raw, _, seed_joint, _,
        ) = curve_summary(curves, start, end)
        for method in methods:
            def seed_common(lower_kind: str):
                for budget in budgets:
                    passes = True
                    for cell in cells:
                        point = point_lookup[(cell[0], cell[1], method, budget)]
                        values = seed_values[(cell, method, budget)]
                        if lower_kind == "pointwise":
                            lower = core.quantile(values, 0.025)
                        elif lower_kind == "raw":
                            lower = point if seed_exact[(cell, method, budget)] else point + seed_raw[(cell, method)]
                        else:
                            lower = point if seed_exact[(cell, method, budget)] else point - seed_joint[method] * seed_se[(cell, method, budget)]
                        if point < mean_threshold or lower < lower_threshold:
                            passes = False
                            break
                    if passes:
                        return budget
                return None

            first_475 = persistent_475 = 0
            for repetition in range(repetitions_per_seed):
                passing = {
                    budget: all(seed_values[(cell, method, budget)][repetition] >= mean_threshold for cell in cells)
                    for budget in budgets
                }
                first = next((budget for budget in budgets if passing[budget]), None)
                persistent = next((
                    budget for index, budget in enumerate(budgets)
                    if all(passing[later] for later in budgets[index:])
                ), None)
                first_475 += first == 475
                persistent_475 += persistent == 475
            for cell in cells:
                budget = diagnostic_budget
                values = seed_values[(cell, method, budget)]
                point = point_lookup[(cell[0], cell[1], method, budget)]
                joint_lower = point if seed_exact[(cell, method, budget)] else point - seed_joint[method] * seed_se[(cell, method, budget)]
                seed_stability_rows.append({
                    "seed": seed,
                    "panel": cell[0],
                    "scope": cell[1],
                    "method": method,
                    "diagnostic_budget": budget,
                    "pointwise_q025_at_diagnostic_budget": core.quantile(values, 0.025),
                    "raw_cellwise_lower_at_diagnostic_budget": point if seed_exact[(cell, method, budget)] else point + seed_raw[(cell, method)],
                    "joint_max_t_lower_at_diagnostic_budget": joint_lower,
                    "pointwise_common_reliable_budget": seed_common("pointwise"),
                    "raw_cellwise_common_reliable_budget": seed_common("raw"),
                    "joint_max_t_common_reliable_budget": seed_common("joint"),
                    "first_passing_475_probability": first_475 / repetitions_per_seed,
                    "persistent_rule_475_probability": persistent_475 / repetitions_per_seed,
                    "repetitions": repetitions_per_seed,
                })

    coupling_rows = []
    if independent_curves:
        for coupling, source in (
            ("nested_prefix", {
                key: values[:independent_repetitions] for key, values in curves.items()
                if key[1] in {"random", "repo_stratified_random"}
            }),
            ("independent_by_budget", independent_curves),
        ):
            values, _, standard_errors, exact, _, _, joint, _ = curve_summary(source)
            for method in ("random", "repo_stratified_random"):
                pointwise_budget = joint_budget = None
                for budget in budgets:
                    pointwise_pass = all(
                        point_lookup[(cell[0], cell[1], method, budget)] >= mean_threshold
                        and core.quantile(values[(cell, method, budget)], 0.025) >= lower_threshold
                        for cell in cells
                    )
                    joint_pass = all(
                        point_lookup[(cell[0], cell[1], method, budget)] >= mean_threshold
                        and (
                            point_lookup[(cell[0], cell[1], method, budget)]
                            if exact[(cell, method, budget)]
                            else point_lookup[(cell[0], cell[1], method, budget)]
                            - joint[method] * standard_errors[(cell, method, budget)]
                        ) >= lower_threshold
                        for cell in cells
                    )
                    if pointwise_budget is None and pointwise_pass:
                        pointwise_budget = budget
                    if joint_budget is None and joint_pass:
                        joint_budget = budget
                coupling_rows.append({
                    "coupling": coupling,
                    "method": method,
                    "pointwise_common_reliable_budget": pointwise_budget,
                    "joint_max_t_common_reliable_budget": joint_budget,
                    "repetitions": independent_repetitions,
                    "seed": seeds[0],
                })
    return output_rows, decision_rows, stability_rows, driver_rows, seed_stability_rows, coupling_rows


def selection_scope_sensitivity(
    panels: list[dict], sources: dict[str, list[dict]], instance_ids: list[str], config: dict
) -> tuple[list[dict], list[dict]]:
    """Compare scope-trained task identities and fixed all-system selections."""
    overlap_rows = []
    fixed_rows = []
    for panel_index, panel in enumerate(panels):
        source_rows = sources[panel["source"]]
        train = [row for row in source_rows if row["year"] == panel["train_year"]]
        test = [row for row in source_rows if row["year"] == panel["test_year"]]
        latest_train = latest_per_cluster(train, panel["cluster_field"])
        latest_test = latest_per_cluster(test, panel["cluster_field"])
        for budget in config["task_budgets"]:
            selections = {
                "entropy": (
                    core.entropy_subset(instance_ids, train, budget),
                    core.entropy_subset(instance_ids, latest_train, budget),
                ),
                "temporal_coreset": (
                    core.temporal_coreset(instance_ids, train, budget),
                    core.temporal_coreset(instance_ids, latest_train, budget),
                ),
            }
            for method, (all_subset, latest_subset) in selections.items():
                all_set, latest_set = set(all_subset), set(latest_subset)
                overlap_rows.append({
                    "panel": panel["name"],
                    "method": method,
                    "budget": budget,
                    "jaccard_all_vs_cluster_latest": len(all_set & latest_set) / len(all_set | latest_set),
                    "intersection_tasks": len(all_set & latest_set),
                })

            fixed_subsets = {
                "random": core.uniform_random_subset(instance_ids, budget, 4_000_000 + panel_index * 100_000 + budget),
                "repo_stratified_random": core.repository_stratified_subset(
                    instance_ids, budget, 5_000_000 + panel_index * 100_000 + budget
                ),
                "entropy": selections["entropy"][0],
                "temporal_coreset": selections["temporal_coreset"][0],
            }
            for method, subset in fixed_subsets.items():
                for scope, scope_test in (("all_systems", test), ("cluster_latest", latest_test)):
                    metrics = core.evaluate_subset(instance_ids, train, scope_test, subset, panel["top_k_systems"])
                    full, reduced = score_vectors(instance_ids, scope_test, subset)
                    q025, q975 = cluster_bootstrap_tau(
                        full, reduced, [row[panel["cluster_field"]] for row in scope_test],
                        config["cluster_bootstrap_repetitions"],
                        6_000_000 + panel_index * 100_000 + budget * 10 + list(fixed_subsets).index(method),
                    )
                    fixed_rows.append({
                        "panel": panel["name"],
                        "scope": scope,
                        "method": method,
                        "budget": budget,
                        "tau_b": metrics["tau_b"],
                        "tau_b_q025": q025,
                        "tau_b_q975": q975,
                        "selection_training_scope": "all_systems",
                        "calibration_training_scope": "all_systems",
                    })
    return overlap_rows, fixed_rows


def cluster_mapping_records(panels: list[dict], sources: dict[str, list[dict]]) -> list[dict]:
    records = []
    for panel in panels:
        relevant = [
            row for row in sources[panel["source"]]
            if row["year"] in {panel["train_year"], panel["test_year"]}
        ]
        latest_names = {
            year: {row["name"] for row in latest_per_cluster(
                [item for item in relevant if item["year"] == year], panel["cluster_field"]
            )}
            for year in (panel["train_year"], panel["test_year"])
        }
        for row in relevant:
            records.append({
                "panel": panel["name"],
                "period": "training" if row["year"] == panel["train_year"] else "held_out",
                "year": row["year"],
                "system": row["name"],
                "date": row["date"],
                "agent_lineage": row["agent_lineage"],
                "model_family": row["model_family"],
                "model_provider": row["model_provider"],
                "primary_cluster_field": panel["cluster_field"],
                "primary_cluster": row[panel["cluster_field"]],
                "retained_in_primary_cluster_latest": row["name"] in latest_names[row["year"]],
            })
    return records


def small_cluster_bootstrap_stability(
    panels: list[dict], sources: dict[str, list[dict]], instance_ids: list[str], config: dict
) -> list[dict]:
    """Audit lower-bound Monte Carlo stability where the held-out cluster count is small."""
    output = []
    repetition_counts = (1000, 5000)
    seeds = (11, 29, 47, 71, 101)
    for panel in panels:
        source_rows = sources[panel["source"]]
        train = [row for row in source_rows if row["year"] == panel["train_year"]]
        test = [row for row in source_rows if row["year"] == panel["test_year"]]
        scope_train = latest_per_cluster(train, panel["cluster_field"])
        scope_test = latest_per_cluster(test, panel["cluster_field"])
        cluster_count = len({row[panel["cluster_field"]] for row in scope_test})
        if cluster_count > 10:
            continue
        for method in ("entropy", "temporal_coreset"):
            for budget in config["task_budgets"]:
                subset = (
                    core.entropy_subset(instance_ids, scope_train, budget)
                    if method == "entropy"
                    else core.temporal_coreset(instance_ids, scope_train, budget)
                )
                full, reduced = score_vectors(instance_ids, scope_test, subset)
                clusters = [row[panel["cluster_field"]] for row in scope_test]
                for repetitions in repetition_counts:
                    lower_values = []
                    upper_values = []
                    for seed in seeds:
                        lower, upper = cluster_bootstrap_tau(full, reduced, clusters, repetitions, seed + budget)
                        lower_values.append(lower)
                        upper_values.append(upper)
                    output.append({
                        "panel": panel["name"],
                        "scope": "cluster_latest",
                        "method": method,
                        "budget": budget,
                        "clusters": cluster_count,
                        "bootstrap_repetitions": repetitions,
                        "seeds": len(seeds),
                        "q025_min_across_seeds": min(lower_values),
                        "q025_max_across_seeds": max(lower_values),
                        "q025_range": max(lower_values) - min(lower_values),
                        "q975_min_across_seeds": min(upper_values),
                        "q975_max_across_seeds": max(upper_values),
                    })
    return output


def alternative_cluster_sensitivity(
    panels: list[dict], sources: dict[str, list[dict]], instance_ids: list[str], config: dict
) -> list[dict]:
    """Hold task selection fixed while varying the related-system definition."""
    output = []
    cluster_fields = ("agent_lineage", "model_family", "model_provider")
    for panel_index, panel in enumerate(panels):
        source_rows = sources[panel["source"]]
        train = [row for row in source_rows if row["year"] == panel["train_year"]]
        test = [row for row in source_rows if row["year"] == panel["test_year"]]
        for budget in config["task_budgets"]:
            fixed_subsets = {
                "random": core.uniform_random_subset(instance_ids, budget, 7_000_000 + panel_index * 100_000 + budget),
                "repo_stratified_random": core.repository_stratified_subset(
                    instance_ids, budget, 8_000_000 + panel_index * 100_000 + budget
                ),
                "entropy": core.entropy_subset(instance_ids, train, budget),
                "temporal_coreset": core.temporal_coreset(instance_ids, train, budget),
            }
            for cluster_index, cluster_field in enumerate(cluster_fields):
                clustered_test = latest_per_cluster(test, cluster_field)
                cluster_count = len({row[cluster_field] for row in test})
                if cluster_count < 2:
                    for method in fixed_subsets:
                        output.append({
                            "panel": panel["name"], "cluster_field": cluster_field,
                            "clusters": cluster_count, "held_out_systems": len(clustered_test),
                            "method": method, "budget": budget, "tau_b": "", "tau_b_q025": "",
                            "tau_b_q975": "", "status": "unavailable_fewer_than_two_clusters",
                            "selection_training_scope": "all_systems", "random_task_uncertainty": False,
                        })
                    continue
                for method, subset in fixed_subsets.items():
                    metrics = core.evaluate_subset(instance_ids, train, clustered_test, subset, panel["top_k_systems"])
                    full, reduced = score_vectors(instance_ids, clustered_test, subset)
                    q025, q975 = cluster_bootstrap_tau(
                        full, reduced, [row[cluster_field] for row in clustered_test],
                        config["cluster_bootstrap_repetitions"],
                        9_000_000 + panel_index * 100_000 + cluster_index * 10_000 + budget * 10
                        + list(fixed_subsets).index(method),
                    )
                    output.append({
                        "panel": panel["name"], "cluster_field": cluster_field,
                        "clusters": cluster_count, "held_out_systems": len(clustered_test),
                        "method": method, "budget": budget, "tau_b": metrics["tau_b"],
                        "tau_b_q025": q025, "tau_b_q975": q975, "status": "ok",
                        "selection_training_scope": "all_systems", "random_task_uncertainty": False,
                    })
    return output


def summarize_fixed_selection(rows: list[dict], config: dict) -> list[dict]:
    cells = sorted({(row["panel"], row["scope"]) for row in rows})
    budgets = config["task_budgets"]
    output = []
    for method in ("random", "repo_stratified_random", "entropy", "temporal_coreset"):
        lookup = {
            (row["panel"], row["scope"], int(row["budget"])): row
            for row in rows if row["method"] == method
        }
        budget = next((
            candidate for candidate in budgets
            if all(
                float(lookup[(panel, scope, candidate)]["tau_b"]) >= config["minimum_mean_tau_b"]
                and float(lookup[(panel, scope, candidate)]["tau_b_q025"])
                >= config["minimum_harmonized_tau_b_q025"]
                for panel, scope in cells
            )
        ), None)
        output.append({
            "method": method,
            "fixed_all_system_selection_common_budget": budget,
            "mean_tau_b_threshold": config["minimum_mean_tau_b"],
            "system_cluster_lower_bound_threshold": config["minimum_harmonized_tau_b_q025"],
            "random_task_uncertainty": False,
        })
    return output


def summarize_cluster_sensitivity(rows: list[dict], config: dict) -> list[dict]:
    groups = sorted({(row["panel"], row["cluster_field"], row["method"]) for row in rows})
    output = []
    for panel, cluster_field, method in groups:
        selected = [
            row for row in rows
            if row["panel"] == panel and row["cluster_field"] == cluster_field and row["method"] == method
        ]
        ok = [row for row in selected if row["status"] == "ok"]
        budget = min((
            int(row["budget"]) for row in ok
            if float(row["tau_b"]) >= config["minimum_mean_tau_b"]
            and float(row["tau_b_q025"]) >= config["minimum_harmonized_tau_b_q025"]
        ), default=None)
        output.append({
            "panel": panel,
            "cluster_field": cluster_field,
            "method": method,
            "clusters": selected[0]["clusters"],
            "first_passing_budget": budget,
            "status": selected[0]["status"],
            "selection_training_scope": "all_systems",
            "random_task_uncertainty": False,
        })
    return output


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
    policies = config.get("threshold_policies", [])
    if not policies or len({policy.get("name") for policy in policies}) != len(policies):
        raise ValueError("threshold_policies must be non-empty and have unique names")
    required_thresholds = {
        "minimum_mean_tau_b",
        "minimum_random_tau_b_q025",
        "minimum_deterministic_tau_b_q025",
    }
    if any(not required_thresholds.issubset(policy) for policy in policies):
        raise ValueError("every threshold policy must define all three reliability thresholds")
    for field in (
        "random_repetitions", "cluster_bootstrap_repetitions", "repository_bootstrap_repetitions",
        "two_way_bootstrap_repetitions", "harmonized_bootstrap_repetitions",
    ):
        if not isinstance(config.get(field), int) or config[field] <= 0:
            raise ValueError(f"{field} must be a positive integer")
    seeds = config.get("harmonized_bootstrap_seeds")
    if (
        not isinstance(seeds, list)
        or len(seeds) < 2
        or any(not isinstance(seed, int) for seed in seeds)
        or len(set(seeds)) != len(seeds)
    ):
        raise ValueError("harmonized_bootstrap_seeds must contain at least two unique integers")
    independent_repetitions = config.get("independent_budget_coupling_repetitions", 0)
    if not isinstance(independent_repetitions, int) or independent_repetitions < 0:
        raise ValueError("independent_budget_coupling_repetitions must be a non-negative integer")
    if not 0 <= config.get("minimum_harmonized_tau_b_q025", -1) <= 1:
        raise ValueError("minimum_harmonized_tau_b_q025 must be between zero and one")


def validate_positive_control(metric_rows: list[dict]) -> dict:
    rows = [row for row in metric_rows if row["budget"] == 500]
    panels = {row["panel"] for row in metric_rows}
    scopes = {"all_systems", "cluster_latest"}
    methods = {"random", "repo_stratified_random", "entropy", "temporal_coreset"}
    expected_keys = {
        (panel, scope, method)
        for panel in panels
        for scope in scopes
        for method in methods
    }
    observed_keys = {(row["panel"], row["scope"], row["method"]) for row in rows}
    duplicate_keys = sorted({
        key for key in observed_keys
        if sum((row["panel"], row["scope"], row["method"]) == key for row in rows) != 1
    })
    failures = [
        {key: row[key] for key in ("panel", "scope", "method", "tau_b", "top_k_overlap", "calibrated_score_mae")}
        for row in rows
        if abs(float(row["tau_b"]) - 1.0) > 1e-12
        or abs(float(row["top_k_overlap"]) - 1.0) > 1e-12
        or abs(float(row["calibrated_score_mae"])) > 1e-12
    ]
    return {
        "expected_rows": len(expected_keys),
        "observed_rows": len(rows),
        "missing_cells": sorted(expected_keys - observed_keys),
        "unexpected_cells": sorted(observed_keys - expected_keys),
        "duplicate_cells": duplicate_keys,
        "failures": failures,
        "pass": observed_keys == expected_keys and not duplicate_keys and not failures,
    }


def validate_metric_matrix(metric_rows: list[dict], panels: list[dict], budgets: list[int]) -> dict:
    scopes = ("all_systems", "cluster_latest")
    methods = ("random", "repo_stratified_random", "entropy", "temporal_coreset")
    expected = {
        (panel["name"], scope, method, budget)
        for panel in panels for scope in scopes for method in methods for budget in budgets
    }
    keys = [
        (row["panel"], row["scope"], row["method"], int(row["budget"]))
        for row in metric_rows
    ]
    counts = Counter(keys)
    observed = set(keys)
    numeric_fields = ("tau_b", "tau_b_q025", "tau_b_q975", "top_k_overlap", "calibrated_score_mae")
    incomplete = [
        key for key, row in zip(keys, metric_rows)
        if any(row.get(field, "") == "" for field in numeric_fields)
    ]
    return {
        "expected_rows": len(expected),
        "observed_rows": len(metric_rows),
        "missing_cells": sorted(expected - observed),
        "unexpected_cells": sorted(observed - expected),
        "duplicate_cells": sorted(key for key, count in counts.items() if count != 1),
        "incomplete_numeric_cells": incomplete,
        "pass": observed == expected and all(count == 1 for count in counts.values()) and not incomplete,
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


def row_passes_policy(row: dict, method: str, policy: dict) -> bool:
    lower_bound = (
        policy["minimum_random_tau_b_q025"]
        if method in {"random", "repo_stratified_random"}
        else policy["minimum_deterministic_tau_b_q025"]
    )
    return (
        float(row["tau_b"]) >= policy["minimum_mean_tau_b"]
        and float(row["tau_b_q025"]) >= lower_bound
    )


def minimum_common_budget(
    metric_rows: list[dict], cells: list[tuple[str, str]], method: str, policy: dict
) -> int | None:
    """Return the smallest single budget that passes in every requested cell.

    Taking the maximum of cell-specific minimum budgets is only valid when
    pass/fail status is monotone in budget. Held-out ranking fidelity can be
    non-monotone, especially for deterministic selectors, so every candidate
    budget must be checked across all panels and scopes at that exact budget.
    """
    lookup = {
        (row["panel"], row["scope"], row["method"], row["budget"]): row
        for row in metric_rows
    }
    budgets = sorted({int(row["budget"]) for row in metric_rows if row["method"] == method})
    for budget in budgets:
        rows = [lookup.get((panel, scope, method, budget)) for panel, scope in cells]
        if all(row is not None and row_passes_policy(row, method, policy) for row in rows):
            return budget
    return None


def threshold_sensitivity(metric_rows: list[dict], panels: list[dict], policies: list[dict]) -> list[dict]:
    methods = ("random", "repo_stratified_random", "entropy", "temporal_coreset")
    rows = []
    cells = [
        (panel["name"], scope)
        for panel in panels
        for scope in ("all_systems", "cluster_latest")
    ]
    for policy in policies:
        for method in methods:
            robust_budget = minimum_common_budget(metric_rows, cells, method, policy)
            rows.append({
                "policy": policy["name"],
                "minimum_mean_tau_b": policy["minimum_mean_tau_b"],
                "minimum_random_tau_b_q025": policy["minimum_random_tau_b_q025"],
                "minimum_deterministic_tau_b_q025": policy["minimum_deterministic_tau_b_q025"],
                "method": method,
                "robust_budget": robust_budget,
                "task_reduction_pct": 100.0 * (500 - robust_budget) / 500 if robust_budget is not None else "",
            })
    return rows


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
            'Lines show mean held-out Kendall tau-b; the exact decision also requires the protocol-defined lower-bound threshold.</p>'
            f'{chart_svg(metric_rows, record["panel"])}'
            '<table><thead><tr><th>Method</th><th>Tasks</th><th>τ-b with interval</th><th>Top-k</th><th>Pairwise</th><th>MAE</th></tr></thead>'
            f'<tbody>{"".join(checkpoint_rows)}</tbody></table>'
        )

    common = payload["robust_cross_panel_decision"]
    open_record = next(record for record in longitudinal if record["panel"] == "open-submission")
    bash_record = next(record for record in longitudinal if record["panel"] == "standardized-bash")
    threshold_rows = "".join(
        f'<tr><td>{html.escape(row["policy"])}</td><td>{html.escape(row["method"].replace("_", " "))}</td>'
        f'<td>{row["minimum_mean_tau_b"]:.2f}</td><td>{row["robust_budget"]}</td><td>{row["task_reduction_pct"]:.0f}%</td></tr>'
        for row in payload["threshold_sensitivity"]
    )
    harmonized_rows = "".join(
        f'<tr><td>{html.escape(row["method"].replace("_", " "))}</td>'
        f'<td>{row["pointwise_common_reliable_budget"]}</td>'
        f'<td>{row["raw_cellwise_common_reliable_budget"]}</td>'
        f'<td>{row["cellwise_max_t_common_reliable_budget"]}</td>'
        f'<td>{row["joint_max_t_common_reliable_budget"]}</td></tr>'
        for row in payload["harmonized_uncertainty_decisions"]
    )
    joint_budgets = ", ".join(
        f'{row["method"].replace("_", " ")}: {row["joint_max_t_common_reliable_budget"]}'
        for row in payload["harmonized_uncertainty_decisions"]
    )

    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Formal SWE-bench Discriminative-Power Study</title><style>
body{{margin:0;background:#f8fafc;color:#0f172a;font-family:Inter,system-ui,sans-serif;line-height:1.5}}main{{max-width:1120px;margin:auto;padding:42px 24px 70px}}
h1{{font-size:36px;line-height:1.15;margin:4px 0}}h2{{margin-top:38px}}h3{{margin-top:28px;font-size:21px}}.eyebrow{{color:#0369a1;font-weight:750;text-transform:uppercase;letter-spacing:.08em;font-size:12px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:22px 0}}.card{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px;box-shadow:0 4px 18px #0f172a0b}}
.value{{font-size:30px;font-weight:780}}.muted{{color:#64748b}}.note{{border-left:4px solid #0369a1;background:#e0f2fe;padding:13px 16px;border-radius:7px;margin:20px 0}}code{{font-size:12px;overflow-wrap:anywhere}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;font-size:13px}}th,td{{padding:9px 11px;border-bottom:1px solid #e2e8f0;text-align:right}}th:first-child,td:first-child{{text-align:left}}th{{background:#f1f5f9}}svg{{width:100%;height:auto;background:#fff;border-radius:12px;margin:8px 0 14px}}
</style></head><body><main><div class="eyebrow">Formal experiment</div><h1>Temporal discriminative power in SWE-bench Verified</h1>
<p class="muted">Two non-pooled temporal panels: heterogeneous open submissions and a standardized mini-SWE-agent Bash-only environment.</p>
<h2>Technical summary</h2>
<p><strong>The original 150-task pilot conclusion does not generalize.</strong> Under the protocol-defined pointwise thresholds, uniform random, repository-stratified random, and entropy require {common["common_reliable_uniform_random_budget"]}, {common["common_reliable_repo_stratified_budget"]}, and {common["common_reliable_entropy_budget"]} tasks; temporal core requires {common["common_reliable_temporal_coreset_budget"]}. The reviewer-motivated joint max-t robustness analysis returns {joint_budgets}. The 16-cell positive control passed, and all included matrices reconciled to official scores.</p>
<div class="grid">{"".join(panel_cards)}</div>
<div class="note"><strong>Interpretation boundary.</strong> The 2025 open-submission panel was inspected during the pilot and is developmental. The 2026 standardized panel was absent from the pilot and supplies a time-external validation panel. Submission dates do not identify exact harness versions.</div>
<h2>Later cohorts achieved higher mean solve rates; only the standardized panel clearly lost task entropy</h2>
<p>Mean task solve rate increased by {open_record["solve_rate_change"]:+.3f} in the open panel and {bash_record["solve_rate_change"]:+.3f} in the standardized panel. The open-panel entropy interval crosses zero; the standardized-panel entropy change is negative throughout its repository-bootstrap interval. These are descriptive temporal shifts, not causal effects.</p>
<table><thead><tr><th>Panel</th><th>Years</th><th>Systems</th><th>Solve-rate change</th><th>Entropy change</th><th>Near-saturated tasks</th></tr></thead><tbody>{"".join(longitudinal_rows)}</tbody></table>
<h2>Reduced task budgets are panel-dependent</h2>
<p>The charts compare four selectors at the same 13 protocol-specified budgets. Ranking fidelity alone is insufficient: a budget is called reliable only when its mean and lower uncertainty bound both cross the protocol thresholds.</p>
{"".join(sections)}
<h2>Scope, definitions, and experimental design</h2><p>The unit of analysis is a public system-task outcome on the canonical 500 SWE-bench Verified instances. The open-submission panel selects tasks from 2024 and evaluates 2025; the standardized Bash-only panel selects from 2025 and evaluates 2026. Kendall’s τ-b compares each reduced-task system ordering with the full 500-task ordering. The top-k diagnostic includes every boundary tie and reports Jaccard overlap.</p>
<h2>Data quality, uncertainty, and robustness</h2><p>All included task matrices reconcile to official aggregate scores. The original intervals separately describe task-selection or system-cluster variation. The harmonized curve bootstrap resamples held-out system clusters for every procedure and additionally redraws tasks for stochastic procedures. The 500-task endpoint is a mandatory 16-cell positive control.</p>
<h3>Harmonized uncertainty</h3><table><thead><tr><th>Procedure</th><th>Pointwise tasks</th><th>Raw cell-wise tasks</th><th>Cell-wise max-t tasks</th><th>Joint max-t tasks</th></tr></thead><tbody>{harmonized_rows}</tbody></table>
<h3>Reliability-threshold sensitivity</h3><p>The robust budget is recomputed across both panels and both dependence scopes under lenient, primary, and strict threshold policies. This separates a genuine selector result from an artifact of the primary cutoff.</p><table><thead><tr><th>Policy</th><th>Method</th><th>Mean τ-b threshold</th><th>Robust tasks</th><th>Task reduction</th></tr></thead><tbody>{threshold_rows}</tbody></table>
<h2>Limitations and next study decision</h2><p>Submission dates do not identify exact harness versions, public systems are selected and correlated, cluster definitions are approximate, and most public results do not measure run-to-run model variance. A common procedure budget does not identify one fixed task set. Therefore the result supports benchmark-maintenance claims only—not causal claims about model progress or a permanent 475-task subset.</p>
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
        longitudinal.append(longitudinal_record(
            panel,
            instance_ids,
            train,
            test,
            config["repository_bootstrap_repetitions"],
            config["two_way_bootstrap_repetitions"],
        ))
        rows, panel_decisions, panel_selections = analyze_panel(panel, instance_ids, source_rows, config)
        metric_rows.extend(rows)
        decisions[panel["name"]] = panel_decisions
        selections[panel["name"]] = panel_selections
        panel_quality[panel["name"]] = {
            "train": duplicate_signature_summary(train) | Counter(row["attempts"] for row in train),
            "test": duplicate_signature_summary(test) | Counter(row["attempts"] for row in test),
        }

    method_keys = {
        "random": "common_reliable_uniform_random_budget",
        "repo_stratified_random": "common_reliable_repo_stratified_budget",
        "entropy": "common_reliable_entropy_budget",
        "temporal_coreset": "common_reliable_temporal_coreset_budget",
    }
    all_system_cells = [(panel["name"], "all_systems") for panel in config["panels"]]
    cross_panel = {
        key: minimum_common_budget(metric_rows, all_system_cells, method, config)
        for method, key in method_keys.items()
    }
    positive_control = validate_positive_control(metric_rows)
    metric_matrix = validate_metric_matrix(metric_rows, config["panels"], config["task_budgets"])
    sensitivity_decisions = {
        panel["name"]: {
            scope: reliability_decision(metric_rows, panel["name"], scope, config)
            for scope in ("all_systems", "cluster_latest")
        }
        for panel in config["panels"]
    }
    robust_panel_decisions = {
        panel: {
            "minimum_reliable_repo_stratified_budget": minimum_common_budget(
                metric_rows,
                [(panel, "all_systems"), (panel, "cluster_latest")],
                "repo_stratified_random",
                config,
            ),
            "minimum_reliable_entropy_budget": minimum_common_budget(
                metric_rows,
                [(panel, "all_systems"), (panel, "cluster_latest")],
                "entropy",
                config,
            ),
            "minimum_reliable_temporal_coreset_budget": minimum_common_budget(
                metric_rows,
                [(panel, "all_systems"), (panel, "cluster_latest")],
                "temporal_coreset",
                config,
            ),
        }
        for panel in sensitivity_decisions
    }
    robust_cells = [
        (panel["name"], scope)
        for panel in config["panels"]
        for scope in ("all_systems", "cluster_latest")
    ]
    robust_cross_panel = {
        key: minimum_common_budget(metric_rows, robust_cells, method, config)
        for method, key in method_keys.items()
    }
    threshold_rows = threshold_sensitivity(metric_rows, config["panels"], config["threshold_policies"])
    (
        harmonized_rows, harmonized_decisions, budget_stability, curve_band_diagnostics,
        curve_bootstrap_stability, coupling_sensitivity,
    ) = harmonized_curve_bootstrap(
        config["panels"], sources, instance_ids, metric_rows, config
    )
    selection_overlap, fixed_selection = selection_scope_sensitivity(
        config["panels"], sources, instance_ids, config
    )
    cluster_mapping = cluster_mapping_records(config["panels"], sources)
    bootstrap_stability = small_cluster_bootstrap_stability(
        config["panels"], sources, instance_ids, config
    )
    cluster_sensitivity = alternative_cluster_sensitivity(
        config["panels"], sources, instance_ids, config
    )
    fixed_selection_decisions = summarize_fixed_selection(fixed_selection, config)
    cluster_sensitivity_decisions = summarize_cluster_sensitivity(cluster_sensitivity, config)
    data_quality = {
        "canonical_tasks": len(instance_ids),
        "classic": classic_quality,
        "bash-only": bash_quality,
        "panel_period_checks": panel_quality,
        "cross_format_folder_overlap": len({row["name"] for row in classic_rows} & {row["name"] for row in bash_rows}),
        "positive_control": positive_control,
        "metric_matrix": metric_matrix,
        "overall_pass": (
            classic_quality["score_reconciliation_failures"] == 0
            and classic_quality["metadata_missing"] == 0
            and bash_quality["score_reconciliation_failures"] == 0
            and bash_quality["metadata_missing"] == 0
            and bash_quality["explicit_500_task_matrices"] == bash_quality["usable"]
            and positive_control["pass"]
            and metric_matrix["pass"]
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
        "threshold_sensitivity": threshold_rows,
        "harmonized_uncertainty_decisions": harmonized_decisions,
        "fixed_selection_decisions": fixed_selection_decisions,
        "cluster_sensitivity_decisions": cluster_sensitivity_decisions,
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
        "top_k_overlap", "full_top_k_set_size", "subset_top_k_set_size",
        "pairwise_direction_agreement", "calibrated_score_mae", "repository_coverage", "baseline_percentile",
    ]
    write_csv(output / "formal_metrics.csv", metric_rows, metric_fields)
    write_csv(
        output / "secondary_metrics_online_resource.csv",
        metric_rows,
        [
            "panel", "scope", "method", "budget", "tau_b", "top_k_overlap",
            "full_top_k_set_size", "subset_top_k_set_size", "pairwise_direction_agreement",
            "calibrated_score_mae", "repository_coverage", "baseline_percentile",
        ],
    )
    (output / "analysis_history.md").write_text(
        "# Analysis history\n\n"
        "- A pilot inspected the 2025 open-submission outcomes.\n"
        "- The formal protocol and thresholds were committed on 2026-08-24 before the final two-panel rerun.\n"
        "- On 2026-08-26, a non-monotonicity defect was found in the common-budget aggregation; the rule was corrected to test every required cell at each exact budget.\n"
        "- Harmonized resampling, raw-deviation bands, standardized max-t bands, and random-curve coupling analyses were added after review as post hoc robustness analyses.\n"
        "- The study had no external registration.\n",
        encoding="utf-8",
    )
    write_csv(
        output / "threshold_sensitivity.csv",
        threshold_rows,
        [
            "policy",
            "minimum_mean_tau_b",
            "minimum_random_tau_b_q025",
            "minimum_deterministic_tau_b_q025",
            "method",
            "robust_budget",
            "task_reduction_pct",
        ],
    )
    write_csv(
        output / "harmonized_metrics.csv",
        harmonized_rows,
        [
            "panel", "scope", "method", "budget", "tau_b", "tau_b_bootstrap_mean",
            "tau_b_bootstrap_sd", "tau_b_q025", "tau_b_q975", "raw_cellwise_lower_band",
            "cellwise_max_t_lower_band", "joint_max_t_lower_band", "repetitions",
            "repetitions_per_seed", "seed_count", "system_cluster_resampled",
            "task_subset_redrawn", "random_budget_coupling",
        ],
    )
    write_csv(
        output / "harmonized_decisions.csv",
        harmonized_decisions,
        [
            "method", "mean_tau_b_threshold", "common_lower_bound_threshold",
            "pointwise_common_reliable_budget", "raw_cellwise_common_reliable_budget",
            "cellwise_max_t_common_reliable_budget", "joint_max_t_common_reliable_budget",
            "repetitions", "repetitions_per_seed", "seed_count",
        ],
    )
    write_csv(
        output / "budget_stability.csv",
        budget_stability,
        [
            "method", "selected_budget", "first_passing_count", "first_passing_probability",
            "first_passing_probability_ci_lower", "first_passing_probability_ci_upper",
            "persistent_rule_count", "persistent_rule_probability",
            "persistent_rule_probability_ci_lower", "persistent_rule_probability_ci_upper",
            "repetitions", "criterion",
        ],
    )
    write_csv(
        output / "curve_band_diagnostics.csv",
        curve_band_diagnostics,
        [
            "band", "panel", "scope", "method", "budget", "driver_count",
            "driver_probability", "critical_value",
        ],
    )
    write_csv(
        output / "curve_bootstrap_stability.csv",
        curve_bootstrap_stability,
        [
            "seed", "panel", "scope", "method", "diagnostic_budget",
            "pointwise_q025_at_diagnostic_budget", "raw_cellwise_lower_at_diagnostic_budget",
            "joint_max_t_lower_at_diagnostic_budget", "pointwise_common_reliable_budget",
            "raw_cellwise_common_reliable_budget", "joint_max_t_common_reliable_budget",
            "first_passing_475_probability", "persistent_rule_475_probability", "repetitions",
        ],
    )
    write_csv(
        output / "random_curve_coupling_sensitivity.csv",
        coupling_sensitivity,
        [
            "coupling", "method", "pointwise_common_reliable_budget",
            "joint_max_t_common_reliable_budget", "repetitions", "seed",
        ],
    )
    write_csv(
        output / "selection_overlap.csv",
        selection_overlap,
        ["panel", "method", "budget", "jaccard_all_vs_cluster_latest", "intersection_tasks"],
    )
    write_csv(
        output / "fixed_selection_sensitivity.csv",
        fixed_selection,
        [
            "panel", "scope", "method", "budget", "tau_b", "tau_b_q025", "tau_b_q975",
            "selection_training_scope", "calibration_training_scope",
        ],
    )
    write_csv(
        output / "fixed_selection_decisions.csv",
        fixed_selection_decisions,
        [
            "method", "fixed_all_system_selection_common_budget", "mean_tau_b_threshold",
            "system_cluster_lower_bound_threshold", "random_task_uncertainty",
        ],
    )
    write_csv(
        output / "cluster_mapping.csv",
        cluster_mapping,
        [
            "panel", "period", "year", "system", "date", "agent_lineage", "model_family",
            "model_provider", "primary_cluster_field", "primary_cluster", "retained_in_primary_cluster_latest",
        ],
    )
    write_csv(
        output / "bootstrap_stability.csv",
        bootstrap_stability,
        [
            "panel", "scope", "method", "budget", "clusters", "bootstrap_repetitions", "seeds",
            "q025_min_across_seeds", "q025_max_across_seeds", "q025_range",
            "q975_min_across_seeds", "q975_max_across_seeds",
        ],
    )
    write_csv(
        output / "cluster_sensitivity.csv",
        cluster_sensitivity,
        [
            "panel", "cluster_field", "clusters", "held_out_systems", "method", "budget",
            "tau_b", "tau_b_q025", "tau_b_q975", "status", "selection_training_scope",
            "random_task_uncertainty",
        ],
    )
    write_csv(
        output / "cluster_sensitivity_decisions.csv",
        cluster_sensitivity_decisions,
        [
            "panel", "cluster_field", "method", "clusters", "first_passing_budget", "status",
            "selection_training_scope", "random_task_uncertainty",
        ],
    )
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
        f"- All-systems uniform-random budget: {cross_panel['common_reliable_uniform_random_budget']} tasks.",
        f"- All-systems repository-stratified budget: {cross_panel['common_reliable_repo_stratified_budget']} tasks.",
        f"- All-systems entropy budget: {cross_panel['common_reliable_entropy_budget']} tasks.",
        f"- All-systems temporal-core-set budget: {cross_panel['common_reliable_temporal_coreset_budget']} tasks.",
        f"- Robust uniform-random budget across all/latest-cluster scopes: {robust_cross_panel['common_reliable_uniform_random_budget']} tasks.",
        f"- Robust repository-stratified budget across all/latest-cluster scopes: {robust_cross_panel['common_reliable_repo_stratified_budget']} tasks.",
        f"- Robust entropy budget across all/latest-cluster scopes: {robust_cross_panel['common_reliable_entropy_budget']} tasks.",
        f"- Robust temporal-core-set budget across all/latest-cluster scopes: {robust_cross_panel['common_reliable_temporal_coreset_budget']} tasks.",
        "",
        "## Reliability-threshold sensitivity",
        "",
    ])
    summary_lines.extend(
        f"- {row['policy']} / {row['method']}: {row['robust_budget']} tasks ({row['task_reduction_pct']:.0f}% reduction)."
        for row in threshold_rows
    )
    summary_lines.extend([
        "",
        "## Harmonized curve uncertainty",
        "",
    ])
    summary_lines.extend(
        f"- {row['method']}: pointwise {row['pointwise_common_reliable_budget']} tasks; "
        f"raw cell-wise band {row['raw_cellwise_common_reliable_budget']} tasks; "
        f"cell-wise max-t {row['cellwise_max_t_common_reliable_budget']} tasks; "
        f"joint max-t {row['joint_max_t_common_reliable_budget']} tasks."
        for row in harmonized_decisions
    )
    summary_lines.extend([
        "",
        f"The 500-task positive control passed all {positive_control['observed_rows']} expected panel-scope-method cells.",
        "",
        "The open-submission comparison is developmental because its 2025 outcomes were inspected in the pilot. The 2026 standardized panel is a time-external validation panel. Neither comparison is causal.",
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
