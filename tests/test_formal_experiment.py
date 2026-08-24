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
            "threshold_policies": [{
                "name": "primary",
                "minimum_mean_tau_b": 0.90,
                "minimum_random_tau_b_q025": 0.85,
                "minimum_deterministic_tau_b_q025": 0.80,
            }],
        })

    def test_positive_control_is_exact_and_complete(self):
        rows = []
        for panel in ("a", "b"):
            for method in ("random", "repo_stratified_random", "entropy", "temporal_coreset"):
                rows.append({
                    "panel": panel,
                    "scope": "all_systems",
                    "method": method,
                    "budget": 500,
                    "tau_b": 1.0,
                    "top_k_overlap": 1.0,
                    "calibrated_score_mae": 0.0,
                })
        self.assertTrue(formal.validate_positive_control(rows)["pass"])
        rows[0]["tau_b"] = 0.99
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
                for method in ("repo_stratified_random", "entropy", "temporal_coreset"):
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
