import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "src" / "experiment.py"
SPEC = importlib.util.spec_from_file_location("experiment", MODULE_PATH)
experiment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(experiment)


class MetricTests(unittest.TestCase):
    def test_kendall_tau_perfect(self):
        self.assertAlmostEqual(experiment.kendall_tau_b([1, 2, 3], [10, 20, 30]), 1.0)

    def test_kendall_tau_reverse(self):
        self.assertAlmostEqual(experiment.kendall_tau_b([1, 2, 3], [30, 20, 10]), -1.0)

    def test_binary_entropy_boundaries(self):
        self.assertEqual(experiment.binary_entropy(0.0), 0.0)
        self.assertEqual(experiment.binary_entropy(1.0), 0.0)
        self.assertAlmostEqual(experiment.binary_entropy(0.5), 1.0)

    def test_proportional_allocation_exact(self):
        groups = {"a": list(range(7)), "b": list(range(3)), "c": list(range(2))}
        allocation = experiment.proportional_allocation(groups, 8)
        self.assertEqual(sum(allocation.values()), 8)
        self.assertTrue(all(allocation[k] <= len(groups[k]) for k in groups))

    def test_temporal_selector_is_deterministic_and_exact(self):
        task_ids = ["a__a-1", "a__a-2", "b__b-1", "b__b-2"]
        rows = [
            {"name": "20240101_x", "date": "2024-01-01", "outcomes": [0, 0, 1, 1]},
            {"name": "20240201_y", "date": "2024-02-01", "outcomes": [0, 1, 0, 1]},
            {"name": "20240901_z", "date": "2024-09-01", "outcomes": [1, 0, 1, 0]},
            {"name": "20241001_w", "date": "2024-10-01", "outcomes": [1, 1, 0, 0]},
        ]
        first = experiment.temporal_coreset(task_ids, rows, 3)
        second = experiment.temporal_coreset(task_ids, rows, 3)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)

    def test_top_k_overlap_includes_boundary_ties_without_name_breaking(self):
        task_ids = ["r__1", "r__2"]
        training = [
            {"name": "train-a", "outcomes": [1, 0]},
            {"name": "train-b", "outcomes": [0, 1]},
        ]
        test = [
            {"name": "z-system", "outcomes": [1, 0]},
            {"name": "a-system", "outcomes": [1, 0]},
            {"name": "m-system", "outcomes": [0, 1]},
        ]
        metrics = experiment.evaluate_subset(task_ids, training, test, [0], 1)
        self.assertEqual(metrics["full_top_k_set_size"], 3)
        self.assertEqual(metrics["subset_top_k_set_size"], 2)
        self.assertAlmostEqual(metrics["top_k_overlap"], 2 / 3)


if __name__ == "__main__":
    unittest.main()
