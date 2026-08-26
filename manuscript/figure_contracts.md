# Paper Figure Contracts

## Figure 1: Temporal changes in task outcomes

- **Question:** How did task solve rates and task entropy change from the
  training period to the held-out period in each panel?
- **Takeaway:** Later cohorts had higher mean solve rates; entropy declined clearly
  only in the standardized Bash-only panel.
- **Family/variant:** Uncertainty and benchmark; paired horizontal interval
  plots on a shared change scale.
- **Data:** Two panel-level observations for each metric, with repository-
  bootstrap 95% intervals from `longitudinal.csv`.
- **Surface:** Static PNG embedded in DOCX.
- **Scale:** Honest signed scale with a visible zero reference.
- **Palette:** Hard two-root cap: blue for solve-rate change, orange for
  entropy change; marker shape and direct labels provide non-color cues.
- **Output:** `manuscript/figures/figure1_temporal_shift.png`.

## Figure 2: Held-out ranking fidelity by budget

- **Question:** How does held-out Kendall tau-b change with task budget across
  panels, dependence scopes, and selection methods?
- **Takeaway:** Fidelity depends strongly on panel and scope; deterministic
  entropy is non-monotone, so larger subsets do not necessarily pass.
- **Family/variant:** Trend; four small-multiple line-and-interval charts
  (panel by scope).
- **Data:** 208 observations for all four methods across 13
  budgets, with task-sampling or cluster-bootstrap 95% intervals.
- **Surface:** Static PNG embedded in DOCX.
- **Scale:** Full 0-1 tau-b range plus a short extension to -0.2 so negative
  lower intervals remain visible; primary mean threshold at 0.90 and lower-
  bound thresholds are stated in the caption rather than conflated.
- **Palette:** Gray plus a three-category research palette: blue, orange, olive;
  distinct line styles and markers support grayscale reading.
- **Output:** `manuscript/figures/figure2a_open_ranking_fidelity.png` and
  `manuscript/figures/figure2b_standardized_ranking_fidelity.png`, treated as
  Fig. 2a–b in the manuscript.

## Figure 3: Exact common-budget decision

- **Question:** At each budget, how many of the four panel-scope cells pass the
  primary reliability policy for each method?
- **Takeaway:** Uniform random, repository-stratified random, and entropy first
  reach 4/4 only at 500 tasks; the temporal core procedure reaches 4/4 at 475
  under the protocol-defined pointwise policy.
- **Family/variant:** Matrix; annotated heatmap of pass counts.
- **Data:** Four methods x 13 budgets, derived from `formal_metrics.csv` using
  the primary method-specific lower-bound rules.
- **Surface:** Static PNG embedded in DOCX.
- **Scale:** Cell labels show exact pass counts from 0 to 4; no inference from
  color alone.
- **Palette:** Single-root blue shades plus neutral grid and a gold outline for
  the first exact common budget.
- **Output:** `manuscript/figures/figure3_common_budget_matrix.png`.
