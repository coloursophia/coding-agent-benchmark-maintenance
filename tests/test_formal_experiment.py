import importlib.util
import pathlib
import sys
import unittest


SRC_DIR = pathlib.Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))
MODULE_PATH = SRC_DIR / "formal_experiment.py"
SPEC = importlib.util.spec_from_file_location("formal_experiment", MODULE_PATH)
formal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(formal)


class FormalStudyTests(unittest.TestCase):
    def test_normalize_label_removes_version_but_preserves_family(self):
        self.assertEqual(formal.normalize_label("Prometheus-v1.2.1 (OpenHands)"), "prometheus")

    def test_attempts_category(self):
        self.assertEqual(formal.attempts_category(["System: Attempts - 1"]), "single")
        self.assertEqual(formal.attempts_category(["System: Attempts - 2+"]), "multiple")
        self.assertEqual(formal.attempts_category([]), "unknown")

    def test_parse_bash_payload_requires_exact_boolean_matrix(self):
        ids = ["a__a-1", "b__b-2"]
        outcomes, checks = formal.parse_bash_payload(
            {"a__a-1": {"resolved": True}, "b__b-2": {"resolved": False}}, ids
        )
        self.assertEqual(outcomes, [1, 0])
        self.assertEqual(checks, {"missing": 0, "extra": 0, "invalid": 0})
        with self.assertRaises(ValueError):
            formal.parse_bash_payload({"a__a-1": {"resolved": 1}}, ids)

    def test_latest_per_cluster(self):
        rows = [
            {"name": "old", "date": "2025-01-01", "family": "a"},
            {"name": "new", "date": "2025-02-01", "family": "a"},
            {"name": "other", "date": "2025-01-15", "family": "b"},
        ]
        selected = formal.latest_per_cluster(rows, "family")
        self.assertEqual({row["name"] for row in selected}, {"new", "other"})

    def test_cluster_bootstrap_tau_bounds(self):
        q025, q975 = formal.cluster_bootstrap_tau(
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            ["a", "a", "b", "b", "c", "c"],
            50,
            7,
        )
        self.assertAlmostEqual(q025, 1.0)
        self.assertAlmostEqual(q975, 1.0)

    def test_task_band_boundaries(self):
        self.assertEqual(formal.task_band(0.05), "near_impossible")
        self.assertEqual(formal.task_band(0.20), "discriminative")
        self.assertEqual(formal.task_band(0.95), "near_saturated")

    def test_config_requires_full_benchmark_positive_control(self):
        with self.assertRaises(ValueError):
            formal.validate_config({"task_budgets": [25, 100, 250]})
        formal.validate_config({
            "task_budgets": [25, 100, 500],
            "random_repetitions": 10,
            "cluster_bootstrap_repetitions": 10,
            "repository_bootstrap_repetitions": 10,
            "two_way_bootstrap_repetitions": 10,
            "harmonized_bootstrap_repetitions": 10,
            "harmonized_bootstrap_seeds": [11, 29],
            "independent_budget_coupling_repetitions": 10,
            "minimum_harmonized_tau_b_q025": 0.80,
            "threshold_policies": [{
                "name": "primary",
                "minimum_mean_tau_b": 0.90,
                "minimum_random_tau_b_q025": 0.85,
                "minimum_deterministic_tau_b_q025": 0.80,
            }],
        })

    def test_nested_random_paths_are_exact_and_nested(self):
        task_ids = [f"repo{index % 4}__task-{index}" for index in range(20)]
        budgets = [3, 7, 13, 20]
        uniform = formal.nested_uniform_subsets(20, budgets, formal.random.Random(17))
        stratified = formal.nested_repository_subsets(task_ids, budgets, formal.random.Random(17))
        for path in (uniform, stratified):
            for budget in budgets:
                self.assertEqual(len(path[budget]), budget)
            for smaller, larger in zip(budgets, budgets[1:]):
                self.assertTrue(set(path[smaller]) < set(path[larger]))
            self.assertEqual(set(path[20]), set(range(20)))

    def test_wilson_interval_contains_observed_proportion(self):
        lower, upper = formal.wilson_interval(60, 100)
        self.assertLess(lower, 0.60)
        self.assertGreater(upper, 0.60)

    def test_harmonized_curve_bootstrap_integrates_four_cells(self):
        instance_ids = [f"repo{index % 2}__task-{index}" for index in range(6)]
        panels = []
        sources = {}
        for panel_index, panel_name in enumerate(("p1", "p2")):
            source_name = f"source-{panel_name}"
            cluster_field = "family"
            panels.append({
                "name": panel_name,
                "source": source_name,
                "train_year": 2024,
                "test_year": 2025,
                "cluster_field": cluster_field,
            })
            rows = []
            for year in (2024, 2025):
                for system_index in range(4):
                    rows.append({
                        "name": f"{panel_name}-{year}-{system_index}",
                        "date": f"{year}-0{1 + system_index}-01",
                        "year": year,
                        cluster_field: f"c{system_index % 2}",
                        "outcomes": [
                            int((task_index + system_index + year + panel_index) % 3 != 0)
                            for task_index in range(6)
                        ],
                    })
            sources[source_name] = rows
        budgets = [2, 6]
        metric_rows = []
        for panel in panels:
            for scope in ("all_systems", "cluster_latest"):
                for method in ("random", "repo_stratified_random", "entropy", "temporal_coreset"):
                    for budget in budgets:
                        metric_rows.append({
                            "panel": panel["name"], "scope": scope, "method": method,
                            "budget": budget, "tau_b": 1.0 if budget == 6 else 0.5,
                        })
        config = {
            "task_budgets": budgets,
            "harmonized_bootstrap_repetitions": 3,
            "harmonized_bootstrap_seeds": [11, 29],
            "independent_budget_coupling_repetitions": 3,
            "minimum_mean_tau_b": 0.90,
            "minimum_harmonized_tau_b_q025": 0.80,
        }
        rows, decisions, stability, drivers, seed_rows, coupling = formal.harmonized_curve_bootstrap(
            panels, sources, instance_ids, metric_rows, config
        )
        self.assertEqual(len(rows), 2 * 2 * 4 * 2)
        self.assertEqual(len(decisions), 4)
        self.assertTrue(all(row["joint_max_t_common_reliable_budget"] == 6 for row in decisions))
        self.assertTrue(stability and seed_rows and coupling)
        self.assertIsInstance(drivers, list)
        endpoints = [row for row in rows if row["budget"] == 6]
        self.assertTrue(all(row["joint_max_t_lower_band"] == 1.0 for row in endpoints))
        self.assertTrue(all(row["raw_cellwise_lower_band"] == 1.0 for row in endpoints))
        self.assertTrue(all(row["tau_b_q025"] == 1.0 for row in endpoints))

    def test_positive_control_is_exact_and_complete(self):
        rows = []
        for panel in ("a", "b"):
            for scope in ("all_systems", "cluster_latest"):
                for method in ("random", "repo_stratified_random", "entropy", "temporal_coreset"):
                    rows.append({
                        "panel": panel,
                        "scope": scope,
                        "method": method,
                        "budget": 500,
                        "tau_b": 1.0,
                        "top_k_overlap": 1.0,
                        "calibrated_score_mae": 0.0,
                    })
        self.assertTrue(formal.validate_positive_control(rows)["pass"])
        rows[0]["tau_b"] = 0.99
        self.assertFalse(formal.validate_positive_control(rows)["pass"])

    def test_metric_matrix_requires_every_unique_cell(self):
        panels = [{"name": "a"}, {"name": "b"}]
        budgets = [100, 500]
        rows = []
        for panel in ("a", "b"):
            for scope in ("all_systems", "cluster_latest"):
                for method in ("random", "repo_stratified_random", "entropy", "temporal_coreset"):
                    for budget in budgets:
                        rows.append({
                            "panel": panel, "scope": scope, "method": method, "budget": budget,
                            "tau_b": 1.0, "tau_b_q025": 1.0, "tau_b_q975": 1.0,
                            "top_k_overlap": 1.0, "calibrated_score_mae": 0.0,
                        })
        self.assertTrue(formal.validate_metric_matrix(rows, panels, budgets)["pass"])
        rows.pop()
        self.assertFalse(formal.validate_metric_matrix(rows, panels, budgets)["pass"])
        rows[0]["tau_b"] = 1.0
        rows.pop()
        self.assertFalse(formal.validate_positive_control(rows)["pass"])

    def test_reliability_decision_uses_scope_and_lower_bound(self):
        config = {
            "minimum_mean_tau_b": 0.90,
            "minimum_random_tau_b_q025": 0.85,
            "minimum_deterministic_tau_b_q025": 0.80,
        }
        rows = []
        for method, budget, tau, lower in (
            ("repo_stratified_random", 100, 0.95, 0.84),
            ("repo_stratified_random", 150, 0.91, 0.86),
            ("entropy", 100, 0.91, 0.81),
            ("temporal_coreset", 100, 0.89, 0.90),
            ("temporal_coreset", 150, 0.92, 0.82),
        ):
            rows.append({"panel": "p", "scope": "cluster_latest", "method": method, "budget": budget, "tau_b": tau, "tau_b_q025": lower})
        decision = formal.reliability_decision(rows, "p", "cluster_latest", config)
        self.assertEqual(decision["minimum_reliable_repo_stratified_budget"], 150)
        self.assertEqual(decision["minimum_reliable_entropy_budget"], 100)
        self.assertEqual(decision["minimum_reliable_temporal_coreset_budget"], 150)

    def test_threshold_sensitivity_requires_one_budget_to_pass_every_cell(self):
        policies = [{
            "name": "primary",
            "minimum_mean_tau_b": 0.90,
            "minimum_random_tau_b_q025": 0.85,
            "minimum_deterministic_tau_b_q025": 0.80,
        }]
        rows = []
        for panel in ("a", "b"):
            for scope in ("all_systems", "cluster_latest"):
                for method in ("random", "repo_stratified_random", "entropy", "temporal_coreset"):
                    for budget in (100, 500):
                        passes = budget == 500 or (panel == "a" and scope == "all_systems")
                        rows.append({"panel": panel, "scope": scope, "method": method, "budget": budget, "tau_b": 0.95 if passes else 0.5, "tau_b_q025": 0.90 if passes else 0.4})
        result = formal.threshold_sensitivity(rows, [{"name": "a"}, {"name": "b"}], policies)
        self.assertEqual({row["robust_budget"] for row in result}, {500})

    def test_common_budget_does_not_assume_monotone_fidelity(self):
        policy = {
            "minimum_mean_tau_b": 0.90,
            "minimum_random_tau_b_q025": 0.85,
            "minimum_deterministic_tau_b_q025": 0.80,
        }
        rows = []
        cells = [("a", "all_systems"), ("b", "cluster_latest")]
        for panel, scope in cells:
            for budget in (100, 400, 500):
                passes = budget == 500 or (
                    panel == "a" and scope == "all_systems" and budget == 400
                ) or (
                    panel == "b" and scope == "cluster_latest" and budget == 100
                )
                rows.append({
                    "panel": panel,
                    "scope": scope,
                    "method": "entropy",
                    "budget": budget,
                    "tau_b": 0.95 if passes else 0.70,
                    "tau_b_q025": 0.90 if passes else 0.60,
                })

        individual = [
            formal.reliability_decision(rows, panel, scope, policy)["minimum_reliable_entropy_budget"]
            for panel, scope in cells
        ]
        self.assertEqual(individual, [400, 100])
        self.assertEqual(max(individual), 400)
        self.assertEqual(
            formal.minimum_common_budget(rows, cells, "entropy", policy),
            500,
        )


if __name__ == "__main__":
    unittest.main()
