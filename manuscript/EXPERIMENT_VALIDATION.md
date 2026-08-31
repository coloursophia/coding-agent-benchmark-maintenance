# V3 experiment validation and v3.3 manuscript linkage

**Assessment:** The corrected v3 formal run is internally consistent and was
independently reproduced by the successful GitHub Actions execution. Public
archival availability remains to be completed.

## Validated inputs and run

- Configuration: `configs/formal.json`.
- Local output: `artifacts/formal-v3-local-r3`.
- GitHub Actions run: `32970788181` (successful; 23 min 38 s).
- Experiment commit: `4bcbd4a2cd259f9722e1fa3eb83fa1e03b79df75`.
- Downloaded artifact: `artifacts/github-run-32970788181/unpacked`.
- Manuscript: `manuscript/Limits_of_Task_Set_Reduction_EMSE_draft_v3.3.docx`.
- Manuscript DOCX SHA-256:
  `5ef769a015c3d5a1fdd4da1eb20b721a2e22c83555ebe179befda3a2049ce334`.
- Rendered PDF: `manuscript/Limits_of_Task_Set_Reduction_EMSE_draft_v3.3.pdf`.
- Rendered PDF SHA-256:
  `4a9d06c9c46dfed6e496d737cf33d3aa3c87493bf77da36fdf6f1ace67e4f1b3`.
- Submission supplement: `manuscript/Online_Resource_1_secondary_metrics.csv`
  (byte-identical to the official artifact's
  `secondary_metrics_online_resource.csv`).
- Reproduction supplement:
  `manuscript/Online_Resource_2_reproduction_manifest.md` and its
  submission-ready PDF, `manuscript/Online_Resource_2_reproduction_manifest.pdf`.
- Reproduction supplement SHA-256 values:
  `36853eca2c741eae6261b9ae8a4c0fa6f76e696e67ed586bab0263180e796dac`
  (Markdown) and
  `b1f0425ce3d49bee194e302636aaa2fdaced189cc660c54c61d37001b66efb2f`
  (PDF).
- Claim-citation audit: `manuscript/CLAIM_CITATION_AUDIT.md`.
- Artifact ZIP SHA-256:
  `c66da9edd849c36335fb15a687331d2058cb8c900c29264d38b2d06b2070c334`.
- Experiments source commit: recorded in `source_manifest.json`.
- Website source commit: recorded in `source_manifest.json`.
- Data-quality decision: all checks passed.

The classic source contains 133 usable matrices after one unlisted submission
was excluded. The standardized Bash-only source contains 38 usable matrices
after seven missing/invalid full matrices and two score mismatches were
excluded. Both panels retain the canonical 500 task identifiers and are not
pooled.

## Structural checks

- `formal_metrics.csv`: 208 unique panel–scope–method–budget rows.
- `harmonized_metrics.csv`: 208 unique rows based on 10,000 pooled curve
  replicates (five seeds × 2,000).
- `secondary_metrics_online_resource.csv`: all 208 cells with tie-aware top-k,
  pairwise agreement, calibrated MAE, repository coverage, and top-set sizes.
- `curve_band_diagnostics.csv`: raw, cell-wise max-t, and joint max-t driver
  frequencies and critical values.
- `curve_bootstrap_stability.csv`: five-seed 475-task and common-budget checks.
- `random_curve_coupling_sensitivity.csv`: nested-prefix versus
  independent-by-budget random paths.
- Tables 3–11 reproduce from the artifact with
  `manuscript/scripts/sync_result_tables.py --check`.

The official artifact and local run have identical SHA-256 digests for
`formal_metrics.csv`, `harmonized_metrics.csv`, `harmonized_decisions.csv`,
`curve_band_diagnostics.csv`, `curve_bootstrap_stability.csv`,
`random_curve_coupling_sensitivity.csv`,
`secondary_metrics_online_resource.csv`, `selection_overlap.csv`, and
`fixed_selection_decisions.csv`.

All tau-b values lie in [-1, 1], all tie-aware top-k Jaccard values lie in
[0, 1], and all top-set size fields are populated.

## Positive control and tests

The 500-task gate expects and observes all 16 combinations of two panels, two
scopes, and four methods. Every primary endpoint has tau-b=1, top-k Jaccard=1,
and zero calibrated score error. The harmonized resampling code also fixes the
full-task endpoint at 1 inside every replicate, including degenerate cluster
draws with no comparable system pair. Twenty-one unit and integration tests
pass.

The v3.3 DOCX was rendered with LibreOffice to a 30-page PDF and every page was
inspected. No text, table, figure, caption, or reference entry was clipped or
overlapped. The DOCX accessibility audit reports zero high-, medium-, or
low-severity findings; it contains 11 tables, four inline figures, no comments,
and no tracked insertions or deletions.

Online Resource 2 was rendered to a two-page PDF and both pages were inspected.
Its inventory contains the 23 files actually present in the official artifact,
and an automated path check rejects a missing or stale filename. The corrected
table-sync option is `--artifact`; the obsolete `--artifact-dir` option is not
used. All three documented commands were then copied verbatim into a detached
clean worktree at commit `6738b61` and passed; the complete output is retained
in `manuscript/Online_Resource_2_clean_verification_v3.3.txt`.

## Decision checks

The protocol-defined mixed-source pointwise policy gives common reliable
procedure budgets of 500, 500, 500, and 475 tasks for uniform random,
repository-stratified random, entropy, and temporal core. The 10,000-replicate
harmonized pointwise analysis reproduces those budgets with a common 0.80 lower
threshold.

The intentionally conservative raw cell-wise band gives 500 for all four
procedures. Budget-standardized cell-wise and four-cell joint max-t bands give
500, 500, 500, and 475. At 475 tasks, temporal core's standardized all-system
pointwise lower bound is 0.947, its raw lower band is 0.380, and its joint
max-t lower band is 0.890. Across five seeds, the joint value ranges from 0.843
to 0.911 without crossing the 0.80 threshold.

Nested-prefix and independent-by-budget random paths both give 500-task
pointwise and joint max-t decisions for the two stochastic procedures. The
temporal-core first-pass probability at 475 is 0.517 (95% Wilson interval
0.508–0.527); the persistent-rule probability is 0.560 (0.550–0.570).

At 475 tasks, all-system versus cluster-latest task-set Jaccard overlap is
0.951 (open) and 0.927 (standardized) for temporal core. A fixed all-system
selection gives 400 tasks for entropy and 500 for temporal core. Random
fixed-draw rows are omitted because they do not estimate a random procedure.

## Remaining validation limits

- The max-t construction is a custom post hoc sensitivity; it does not
  establish population coverage for a self-selected leaderboard.
- Public leaderboard submissions are self-selected and cluster labels are
  metadata-derived approximations.
- The version 1.0.0 replication bundle uses the reserved persistent DOI
  `10.5281/zenodo.22189000`; publication of the Zenodo draft registers it.
- Author metadata, funding, competing-interest, originality, and contribution
  declarations remain submission-stage materials and were not fabricated in
  the writing-stage manuscript.
