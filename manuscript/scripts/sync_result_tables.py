import argparse
import csv
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_MANUSCRIPT = ROOT / "manuscript" / "Limits_of_Task_Set_Reduction_manuscript.md"
METHODS = (
    ("random", "Uniform random"),
    ("repo_stratified_random", "Repository-stratified random"),
    ("entropy", "Training-period entropy"),
    ("temporal_coreset", "Temporal core set"),
)
PANELS = (("open-submission", "Open"), ("standardized-bash", "Standardized"))
SCOPES = (("all_systems", "all systems"), ("cluster_latest", "cluster latest"))


def read_csv(path: pathlib.Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def passes(row: dict, method: str, policy: dict) -> bool:
    lower = (
        policy["minimum_random_tau_b_q025"]
        if method in {"random", "repo_stratified_random"}
        else policy["minimum_deterministic_tau_b_q025"]
    )
    return float(row["tau_b"]) >= policy["minimum_mean_tau_b"] and float(row["tau_b_q025"]) >= lower


def exact_common_budget(rows: list[dict], cells: list[tuple[str, str]], method: str, policy: dict):
    lookup = {
        (row["panel"], row["scope"], row["method"], int(row["budget"])): row
        for row in rows
    }
    budgets = sorted({int(row["budget"]) for row in rows if row["method"] == method})
    for budget in budgets:
        candidates = [lookup.get((panel, scope, method, budget)) for panel, scope in cells]
        if all(row is not None and passes(row, method, policy) for row in candidates):
            return budget
    return None


def first_budget(rows: list[dict], panel: str, scope: str, method: str, policy: dict):
    candidates = [
        row for row in rows
        if row["panel"] == panel and row["scope"] == scope and row["method"] == method
        and passes(row, method, policy)
    ]
    return min((int(row["budget"]) for row in candidates), default=None)


def fmt_budget(value):
    return "—" if value is None else str(value)


def table3(payload: dict) -> str:
    lookup = {row["panel"]: row for row in payload["longitudinal"]}
    lines = [
        "| Panel | Systems (earlier → later) | Solve-rate change [95% interval] | Entropy change [95% interval] | Task-difficulty τ_b |",
        "|---|---:|---:|---:|---:|",
    ]
    for panel, label in PANELS:
        row = lookup[panel]
        lines.append(
            f"| {label} | {row['train_systems']} → {row['test_systems']} | "
            f"{row['solve_rate_change']:+.3f} [{row['solve_rate_change_q025']:+.3f}, {row['solve_rate_change_q975']:+.3f}] | "
            f"{row['entropy_change']:+.3f} [{row['entropy_change_q025']:+.3f}, {row['entropy_change_q975']:+.3f}] | "
            f"{row['task_difficulty_tau_b']:.3f} |"
        )
    return "\n".join(lines)


def table4(rows: list[dict], policy: dict) -> str:
    lines = [
        "| Panel and scope | Uniform random | Repository-stratified random | Entropy | Temporal core set |",
        "|---|---:|---:|---:|---:|",
    ]
    for panel, panel_label in PANELS:
        for scope, scope_label in SCOPES:
            values = [fmt_budget(first_budget(rows, panel, scope, method, policy)) for method, _ in METHODS]
            lines.append(f"| {panel_label}, {scope_label} | " + " | ".join(values) + " |")
    return "\n".join(lines)


def table5(rows: list[dict], policy: dict) -> str:
    all_system_cells = [(panel, "all_systems") for panel, _ in PANELS]
    all_cells = [(panel, scope) for panel, _ in PANELS for scope, _ in SCOPES]
    lines = [
        "| Selection procedure | All-system cross-panel budget | Four-cell common reliable budget | Reduction from 500 |",
        "|---|---:|---:|---:|",
    ]
    for method, label in METHODS:
        all_system = exact_common_budget(rows, all_system_cells, method, policy)
        common = exact_common_budget(rows, all_cells, method, policy)
        reduction = "—" if common is None else f"{100 * (500 - common) / 500:.0f}%"
        lines.append(f"| {label} | {fmt_budget(all_system)} | **{fmt_budget(common)}** | **{reduction}** |")
    return "\n".join(lines)


def table6(rows: list[dict], policies: list[dict]) -> str:
    cells = [(panel, scope) for panel, _ in PANELS for scope, _ in SCOPES]
    lines = [
        "| Policy | " + " | ".join(label for _, label in METHODS) + " |",
        "|---|" + "---:|" * len(METHODS),
    ]
    for policy in policies:
        values = []
        for method, _ in METHODS:
            budget = exact_common_budget(rows, cells, method, policy)
            reduction = "—" if budget is None else f"{100 * (500 - budget) / 500:.0f}%"
            values.append(f"{fmt_budget(budget)} ({reduction})")
        lines.append(f"| {policy['name'].title()} | " + " | ".join(values) + " |")
    return "\n".join(lines)


def table7(artifact: pathlib.Path) -> str:
    rows = read_csv(artifact / "harmonized_decisions.csv")
    lookup = {row["method"]: row for row in rows}
    lines = [
        "| Selection procedure | Pointwise common budget | Simultaneous-band common budget |",
        "|---|---:|---:|",
    ]
    for method, label in METHODS:
        row = lookup[method]
        lines.append(
            f"| {label} | {fmt_budget(row['pointwise_common_reliable_budget'] or None)} | "
            f"**{fmt_budget(row['simultaneous_band_common_reliable_budget'] or None)}** |"
        )
    return "\n".join(lines)


def table8(artifact: pathlib.Path) -> str:
    rows = [row for row in read_csv(artifact / "selection_overlap.csv") if int(row["budget"]) == 475]
    lines = [
        "| Panel | Deterministic procedure | Jaccard overlap | Shared tasks |",
        "|---|---|---:|---:|",
    ]
    labels = dict(METHODS)
    panels = dict(PANELS)
    for row in rows:
        lines.append(
            f"| {panels[row['panel']]} | {labels[row['method']]} | "
            f"{float(row['jaccard_all_vs_cluster_latest']):.3f} | {row['intersection_tasks']} |"
        )
    return "\n".join(lines)


def table9(artifact: pathlib.Path) -> str:
    rows = read_csv(artifact / "fixed_selection_decisions.csv")
    lookup = {row["method"]: row for row in rows}
    lines = [
        "| Selection procedure | Fixed all-system selection: common budget | Random task uncertainty included? |",
        "|---|---:|---:|",
    ]
    for method, label in METHODS:
        row = lookup[method]
        value = row["fixed_all_system_selection_common_budget"] or None
        included = "Yes" if row["random_task_uncertainty"].casefold() == "true" else "No"
        lines.append(f"| {label} | {fmt_budget(value)} | {included} |")
    return "\n".join(lines)


def replace_block(text: str, number: int, content: str) -> str:
    start = f"<!-- BEGIN GENERATED TABLE {number} -->"
    end = f"<!-- END GENERATED TABLE {number} -->"
    if start not in text or end not in text:
        raise ValueError(f"Missing generated-table markers for Table {number}")
    before, remainder = text.split(start, 1)
    _, after = remainder.split(end, 1)
    return before + start + "\n" + content.rstrip() + "\n" + end + after


def render(artifact: pathlib.Path, manuscript: pathlib.Path) -> str:
    payload = json.loads((artifact / "formal_results.json").read_text(encoding="utf-8"))
    rows = read_csv(artifact / "formal_metrics.csv")
    policies = payload["config"]["threshold_policies"]
    primary = next(policy for policy in policies if policy["name"] == "primary")
    text = manuscript.read_text(encoding="utf-8")
    for number, content in (
        (3, table3(payload)),
        (4, table4(rows, primary)),
        (5, table5(rows, primary)),
        (6, table6(rows, policies)),
        (7, table7(artifact)),
        (8, table8(artifact)),
        (9, table9(artifact)),
    ):
        text = replace_block(text, number, content)
    return text


def main():
    parser = argparse.ArgumentParser(description="Synchronize manuscript result tables with a formal artifact")
    parser.add_argument("--artifact", required=True, type=pathlib.Path)
    parser.add_argument("--manuscript", type=pathlib.Path, default=DEFAULT_MANUSCRIPT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render(args.artifact, args.manuscript)
    current = args.manuscript.read_text(encoding="utf-8")
    if args.check:
        if rendered != current:
            print("Manuscript result tables are not synchronized with the formal artifact", file=sys.stderr)
            raise SystemExit(1)
        print("Manuscript Tables 3–9 match the formal artifact")
    else:
        args.manuscript.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
