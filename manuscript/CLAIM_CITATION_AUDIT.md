# Claim-Citation Audit for Manuscript v3.2

Audit date: 2026-08-27

This internal register distinguishes study-generated claims from external
facts, methods, interpretations, and research-object identifiers. `Support`
means that the cited source was checked for the proposition used in the
manuscript; a title or DOI match alone was not treated as support.

| Section / paragraph | Claim type | Citation needed | Source or trace | Support / action |
|---|---|---:|---|---|
| Abstract, design and sample | Study design | No external citation in abstract | Methods §§4.1–4.6 | Matched to frozen configuration and artifact |
| Abstract, 500/500/500/475 and fixed=500 | Study result | No external citation in abstract | Tables 6–9 | Retained conditional, procedure-level wording |
| Introduction ¶1, SWE-bench construction | External fact | Yes | Jimenez et al. 2024; OpenAI 2024 | Original benchmark paper and official Verified account support task construction |
| Introduction ¶2, test-suite analogy | Prior work | Yes | Harrold et al. 1993; Yoo and Harman 2012 | Sources define property-specific reduction/minimization |
| Introduction ¶2, task choice can change rankings | Prior evidence | Yes | Dehghani et al. 2021 | Paper directly reports altered relative performance under task choice |
| Introduction ¶3, temporal instability | Theory/background | Yes | Gama et al. 2014; Golmohammadi et al. 2026 | Drift survey is used only as broad framing; SE paper supports evolving tools/benchmarks |
| Introduction ¶3, benchmark variance | Prior evidence | Yes | Bouthillier et al. 2021 | Official MLSys paper supports multiple sources of benchmark variation |
| Introduction ¶4, Verified no longer frontier signal | External current fact | Yes | OpenAI 2026 | Official audit supports residual flaws, contamination, and bounded current use |
| Introduction ¶4, task correctness versus rank fidelity | Author distinction | Contextual | Aleithan et al. 2024; Yu et al. 2025 | Literature fact and manuscript inference are separated |
| Introduction contributions | Study contribution | No | RQ/method/results crosswalk | No literature priority claim beyond explicit “complementing” language |
| Introduction final maintenance paragraph | Author recommendation | Yes for precedent | Paullada et al. 2021; Raji et al. 2021 | Sources support lifecycle documentation and bounded benchmark interpretation |
| §2.1, SWE-bench and Verified counts | External fact | Yes | Jimenez et al. 2024; OpenAI 2024 | Counts checked against original/official sources |
| §2.1, task/test flaws and rank correction | Prior evidence | Yes | Aleithan et al. 2024; Yu et al. 2025; OpenAI 2026 | Each source is assigned only the defect/correction claim it reports |
| §2.1, ecosystem heterogeneity | Prior evidence + author inference | Yes | Martinez and Franch 2026 | Heterogeneity is source fact; non-interchangeability is explicitly “we therefore” |
| §2.2, minimization/selection/prioritization | Prior work | Yes | Harrold et al. 1993; Elbaum et al. 2002; Yoo and Harman 2012 | Original and survey sources support definitions and objectives |
| §2.2, microbenchmark prioritization | Prior evidence | Yes | Laaber et al. 2021 | Supports suite/parameterization-dependent effectiveness and overhead |
| §2.2, benchmark task choice | Prior evidence | Yes | Dehghani et al. 2021 | Supports ranking sensitivity to task choice |
| §2.2, direct compression work | Related work | Yes | Gusev and Zaytsev 2026; Wang et al. 2025 | Sources support rank-preservation objective and reported compression regimes |
| §2.3, benchmark variance/distributions | Methods background | Yes | Bouthillier et al. 2021; Dror et al. 2019 | Used for distributional rather than single-score comparison motivation |
| §2.3, tie-aware rank correlation | Method source | Yes | Kendall 1945 | Original tau-b source supports treatment of ties |
| §2.3, user-specific leaderboard utility | Theory/background | Yes | Ethayarajh and Jurafsky 2020 | Source supports divergence between leaderboard metric and practitioner utility |
| §2.3, benchmark quality and non-generality | Related work | Yes | Bowman and Dahl 2021; Raji et al. 2021 | Claims limited to benchmark design/construct scope |
| §2.4, concept drift | Theory/background | Yes | Gama et al. 2014 | Manuscript explicitly avoids diagnosing a specific drift model |
| §2.4, software/tool evolution | Prior evidence | Yes | Golmohammadi et al. 2026; Kaltenecker et al. 2023 | Supports periodic reassessment and rank exceptions across evolution |
| §2.4, sampling/representativeness | Reporting guidance | Yes | Baltes and Ralph 2022 | Supports explicit justification of sampling limits |
| §2.5, clustered resampling | Method source | Yes | Field and Welsh 2007; Cameron et al. 2008 | Whole-cluster logic and few-cluster caution supported; no claim of using wild bootstrap |
| §2.5, simultaneous/max-type adjustment | Method source | Yes | Westfall and Young 1993; Hothorn et al. 2008 | Background only; custom joint band not assigned their general guarantees |
| §2.5, selection changes inference | Method source | Yes | Berk et al. 2013 | General selection warning, not a direct derivation of the budget algorithm |
| §2.6, version control and automated checks | Reporting guidance | Yes | Wilson et al. 2014 | Supports version control, tests, and executable workflows |
| §2.6, software/data as research objects | Citation standard | Yes | Smith et al. 2016; Data Citation Synthesis Group 2014 | Supports distinct scholarly citations and exact-version identifiers |
| §2.6, SE empirical reporting | Reporting standard | Yes | Ralph 2021 | Used as official SIGSOFT standards context, not a statistical authority |
| RQ1–RQ3 | Study questions/operational definitions | No new citation | §§2.3–2.5 and §4.7 | Procedure budget is explicitly manuscript-specific |
| §4.1, data and repositories | External research objects | Yes | Jimenez et al. 2024; OpenAI 2024; SWE-bench Team 2026a,b | Paper/software references identify objects; Online Resource 2 identifies exact bytes |
| §4.2, inclusion counts/tolerances | Study method/result | No external citation | Table 1; data_quality.json | Reproducible from artifact |
| §4.3, panels and clusters | Study design | No external citation | frozen_system_cohorts.csv; system_cluster_mapping.csv | Panels remain non-pooled; cluster policy is author-defined |
| §4.4, four selectors | Study method | No, except established context in §2.2 | source code/config | Temporal core is labelled exploratory and non-novel |
| §4.5, tau-b | Method source | Yes | Kendall 1945 | Tie-aware top-k Jaccard is labelled manuscript diagnostic |
| §4.6, bootstrap intervals | Method source | Yes | Efron and Tibshirani 1985; Davison and Hinkley 1997; Field and Welsh 2007 | Empirical intervals/bands are not population-identification claims |
| §4.6, Wilson interval | Method source | Yes | Wilson 1927 | Restricted to conditional Monte Carlo error |
| §4.6, max-t and curve family | Method source + custom method | Yes | Westfall and Young 1993; Hothorn et al. 2008; Berk et al. 2013 | Four-cell implementation explicitly custom/post hoc |
| §4.7, threshold policy | Author governance rule | Contextual | Kendall 1945; Ethayarajh and Jurafsky 2020 | Thresholds described as normative, not natural constants |
| §4.8, analysis chronology | Study provenance | No external citation | git history; analysis_history.json | No preregistration claim; post hoc work disclosed |
| §5, all numerical results | Study result | No external citation | Tables 3–11; Figures 1–3; formal CSVs | Table sync and official artifact check required before release |
| §6.1, limitation finding | Study interpretation | No external citation | §§5.3–5.6 | 475 remains conditional and fixed selection remains 500 |
| §6.2, scan and simultaneous adjustment | Study interpretation + method background | Yes | Berk et al. 2013; Hothorn et al. 2008; Westfall and Young 1993 | No general coverage claim for custom max-t |
| §6.3, maintenance cycle | Author recommendation | Yes for precedent | Golmohammadi et al. 2026; Paullada et al. 2021; Wilson et al. 2014 | Recommendations clearly separated from observed panel results |
| §6.4, task count versus cost | Author limitation + prior framing | Yes for general utility point | Ethayarajh and Jurafsky 2020 | No measured runtime/cost claim |
| §6.5, current benchmark status | External current fact | Yes | OpenAI 2026 | No permanent subset recommendation |
| §7.1, construct limits | Threat analysis | Yes | Aleithan et al. 2024; OpenAI 2026; Yu et al. 2025; Raji et al. 2021 | Full-ranking fidelity not equated with capability |
| §7.2, cluster definition and few clusters | Threat analysis + method evidence | Yes | Field and Welsh 2007; Cameron et al. 2008 | Bias direction discussed; cluster-latest remains sensitivity |
| §7.2, Monte Carlo error | Study interpretation | Yes | Wilson 1927 | Explicitly excludes panel/cluster/model-population uncertainty |
| §7.3, multi-budget selection | Threat analysis | Yes | Berk et al. 2013; Hothorn et al. 2008 | Additional time window proposed; issue not claimed eliminated |
| §7.4, external validity | Threat analysis | Yes | Baltes and Ralph 2022; Raji et al. 2021 | Numeric generalization expressly rejected |
| §8, computational workflow | Study provenance + guidance | Yes | Wilson et al. 2014; Ralph 2021 | Run identifiers moved to Online Resource 2 |
| §8, data/software citation | Citation standard | Yes | Data Citation Synthesis Group 2014; Smith et al. 2016 | DOI remains submission-stage; not invented in writing stage |
| §8.3, AI assistance | Study disclosure | No external citation required | human confirmation pending submission | No authorship assigned to AI |
| §8.4, ethics | Study applicability statement | No external citation required | public secondary artifacts only | No human recruitment/intervention |
| Conclusion | Synthesis of study | No new citation except current status | Tables 5–9; OpenAI 2026 | No new claim; all numerical qualifiers mirror Results |

## Bidirectional consistency gate

- Every author-year citation in the manuscript has a corresponding reference
  entry.
- Every reference entry is cited in the manuscript body.
- Full Git commits, SHA-256 digests, URLs, and file inventory belong in Online
  Resource 2 or `source_manifest.json`; shortened commits may appear in prose.
- The version 1.0.0 replication package is identified by the reserved Zenodo DOI
  `10.5281/zenodo.22189000`; four-author citation metadata is recorded in
  `CITATION.cff` and `.zenodo.json`.
