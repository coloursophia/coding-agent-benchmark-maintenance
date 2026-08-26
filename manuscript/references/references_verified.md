# Verified Reference Register

Verified on 2026-08-27 against publisher, venue, Crossref DOI metadata, or
official paper pages. Claim support was checked against abstracts or full text;
metadata verification alone was not treated as evidence for a manuscript claim.

1. Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., and
   Narasimhan, K. (2024). *SWE-bench: Can Language Models Resolve Real-World
   GitHub Issues?* International Conference on Learning Representations.
   Official paper: https://openreview.net/pdf/c2a76eb44300a738cbd7cb95f5bc04df621f4d25.pdf
   - Establishes the repository-level issue-resolution benchmark.

2. OpenAI (2024, updated 2025). *Introducing SWE-bench Verified.*
   https://openai.com/index/introducing-swe-bench-verified/
   - Official construction account for the 500-task human-validated subset.

3. OpenAI (2026). *Why SWE-bench Verified no longer measures frontier coding
   capabilities.*
   https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
   - Current official warning about residual task flaws and contamination;
     used to delimit the manuscript's historical and methodological scope.

4. Martinez, M., and Franch, X. (2026). *What's in a Benchmark? The Case of
   SWE-Bench in Automated Program Repair.* Proceedings of the 48th IEEE/ACM
   International Conference on Software Engineering: Software Engineering in
   Practice, 647-658. https://doi.org/10.1145/3786583.3786904
   - Characterizes the SWE-bench leaderboard ecosystem and submission mix.

5. Yu, B., Zhu, Y., He, P., and Kang, D. (2025). *UTBoost: Rigorous Evaluation
   of Coding Agents on SWE-Bench.* Proceedings of the 63rd Annual Meeting of
   the Association for Computational Linguistics, 3762-3774.
   https://doi.org/10.18653/v1/2025.acl-long.189
   - Shows that test adequacy corrections can change leaderboard rankings;
     complementary to this study's task-set ranking-fidelity question.

6. Golmohammadi, A., Zhang, M., and Arcuri, A. (2026). *Tools and benchmarks
   evolve: what is their impact on parameter tuning in SBSE experiments?*
   Empirical Software Engineering, 31, 8.
   https://doi.org/10.1007/s10664-025-10733-y
   - Direct support for periodic re-evaluation under tool and benchmark
     evolution.

7. Destefanis, G., Yousefi, L., Shepperd, M., Tucker, A., Swift, S., Counsell,
   S., and Arzoky, M. (2026). *An audit of machine learning experiments on
   software defect prediction.* Empirical Software Engineering, 31, 83.
   https://doi.org/10.1007/s10664-025-10797-w
   - Supports the emphasis on out-of-sample validation, transparent analysis,
     and reproducibility in empirical software engineering.

8. Baltes, S., and Ralph, P. (2022). *Sampling in software engineering
   research: a critical review and guidelines.* Empirical Software
   Engineering, 27, 94. https://doi.org/10.1007/s10664-021-10072-8
   - Frames sampling and representativeness limitations.

9. Yoo, S., and Harman, M. (2012). *Regression testing minimization, selection
   and prioritization: a survey.* Software Testing, Verification and
   Reliability, 22(2), 67-120. https://doi.org/10.1002/stvr.430
   - Connects task-set reduction to the broader test-suite reduction tradition
     while clarifying that leaderboard fidelity is a distinct objective.

10. Kendall, M. G. (1945). *The treatment of ties in ranking problems.*
    Biometrika, 33(3), 239-251. https://doi.org/10.1093/biomet/33.3.239
    - Original tie-aware rank-correlation basis for Kendall tau-b.

11. Aleithan, R., Xue, H., Mohajer, M. M., Nnorom, E., Uddin, G., and Wang,
    S. (2024).
    *SWE-Bench+: Enhanced Coding Benchmark for LLMs.* arXiv:2410.06992.
    https://arxiv.org/abs/2410.06992
    - Neighboring work on benchmark task validity and evaluation rigor.

12. Gusev, R., and Zaytsev, A. (2026). *Benchmarking on Tasks That Matter:
    Dataset Selection for Preserving Model Rankings.* Proceedings of the 32nd
    ACM SIGKDD Conference on Knowledge Discovery and Data Mining.
    https://doi.org/10.1145/3770855.3817569
    - Direct benchmark-subset work whose objective is preserving model
      rankings; it anchors the manuscript's narrower time-forward coding-agent
      contribution.

13. Wang, S., Wang, C., Fu, W., Min, Y., Feng, M., Guan, I., Hu, X., He, C.,
    Wang, C., Yang, K., Ren, X., Huang, F., Liu, D., and Zhang, L. (2025). *Rethinking LLM
    Evaluation: Can We Evaluate LLMs with 200x Less Data?* arXiv:2510.10457.
    https://arxiv.org/abs/2510.10457
    - EssenceBench combines retrieval, clustering, and rank-preservation
      diagnostics; the manuscript distinguishes its time-forward and
      dependency-aware estimand.

14. Kaltenecker, C., Mühlbauer, S., Grebhahn, A., Siegmund, N., and Apel, S.
    (2023). *Performance
    evolution of configurable software systems: an empirical study.*
    Empirical Software Engineering, 28, 152.
    https://doi.org/10.1007/s10664-023-10338-3
    - Supports treating performance and ordering as quantities that can change
      across software evolution rather than remain time invariant.

15. Laaber, C., Gall, H. C., and Leitner, P. (2021). *Applying test case
    prioritization to software microbenchmarks.* Empirical Software
    Engineering, 26, 133. https://doi.org/10.1007/s10664-021-10037-x
    - Connects benchmark-cost reduction to prioritization while underscoring
      that the retained operational property must be explicitly validated.

16. Harrold, M. J., Gupta, R., and Soffa, M. L. (1993). *A Methodology for
    Controlling the Size of a Test Suite.* ACM TOSEM, 2(3), 270-285.
    https://doi.org/10.1145/152388.152391
    - Original reduction method retaining specified testing requirements;
      supports the property-specific framing of reduction.

17. Elbaum, S., Malishevsky, A. G., and Rothermel, G. (2002). *Test Case
    Prioritization: A Family of Empirical Studies.* IEEE TSE, 28(2), 159-182.
    https://doi.org/10.1109/32.988497
    - Supports the distinction between reducing a suite and ordering it for an
      operational objective such as earlier fault detection.

18. Dehghani, M., Tay, Y., Gritsenko, A. A., Zhao, Z., Houlsby, N., Diaz, F.,
    Metzler, D., and Vinyals, O. (2021). *The Benchmark Lottery.*
    arXiv:2107.07002. https://doi.org/10.48550/arXiv.2107.07002
    - Shows that benchmark-task choice can change relative method performance.

19. Bouthillier, X., et al. (2021). *Accounting for Variance in Machine
    Learning Benchmarks.* Proceedings of Machine Learning and Systems, 3.
    https://proceedings.mlsys.org/paper/2021/hash/0184b0cd3cfb185989f858a1d9f5c1eb-Abstract.html
    - Identifies material benchmark variation from sampling, initialization,
      and hyperparameter choices; supports multi-source uncertainty reporting.

20. Dror, R., Shlomov, S., and Reichart, R. (2019). *Deep Dominance: How to
    Properly Compare Deep Neural Models.* ACL 2019, 2773-2785.
    https://doi.org/10.18653/v1/P19-1266
    - Supports comparing performance distributions rather than isolated model
      scores; not cited as direct evidence for the paper's bootstrap bands.

21. Ethayarajh, K., and Jurafsky, D. (2020). *Utility is in the Eye of the
    User: A Critique of NLP Leaderboards.* EMNLP 2020, 4846-4853.
    https://doi.org/10.18653/v1/2020.emnlp-main.393
    - Supports the claim that leaderboard metrics need not capture operational
      attributes or user-specific utility.

22. Bowman, S. R., and Dahl, G. E. (2021). *What Will it Take to Fix
    Benchmarking in Natural Language Understanding?* NAACL-HLT, 4843-4855.
    https://doi.org/10.18653/v1/2021.naacl-main.385
    - Supports the benchmark-quality, reliability, size, and capability-design
      framing; not treated as coding-agent-specific evidence.

23. Raji, I. D., Denton, E., Bender, E. M., Hanna, A., and Paullada, A. (2021).
    *AI and the Everything in the Whole Wide World Benchmark.* NeurIPS Datasets
    and Benchmarks Track, 1.
    https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/084b6fbb10729ed4da8c3d3f5a3ae7c9-Abstract-round2.html
    - Supports limiting claims that elevate a benchmark into a general measure
      of capability.

24. Paullada, A., Raji, I. D., Bender, E. M., Denton, E., and Hanna, A. (2021).
    *Data and its (Dis)contents.* Patterns, 2(11), 100336.
    https://doi.org/10.1016/j.patter.2021.100336
    - Supports lifecycle documentation and maintenance of datasets; not cited
      as evidence for the paper's numeric results.

25. Gama, J., Zliobaite, I., Bifet, A., Pechenizkiy, M., and Bouchachia, A.
    (2014). *A Survey on Concept Drift Adaptation.* ACM Computing Surveys,
    46(4), 44. https://doi.org/10.1145/2523813
    - Supplies the broader temporal-instability framing; the manuscript
      explicitly does not classify its panels under a specific drift model.

26. Field, C. A., and Welsh, A. H. (2007). *Bootstrapping Clustered Data.*
    JRSS B, 69(3), 369-390.
    https://doi.org/10.1111/j.1467-9868.2007.00593.x
    - Supports whole-cluster resampling and the dependence of bootstrap
      properties on the clustered-data model.

27. Cameron, A. C., Gelbach, J. B., and Miller, D. L. (2008).
    *Bootstrap-Based Improvements for Inference with Clustered Errors.* Review
    of Economics and Statistics, 90(3), 414-427.
    https://doi.org/10.1162/rest.90.3.414
    - Supports explicit caution about few-cluster inference; not used to claim
      that this paper implements their wild cluster bootstrap.

28. Wilson, E. B. (1927). *Probable Inference, the Law of Succession, and
    Statistical Inference.* JASA, 22(158), 209-212.
    https://doi.org/10.1080/01621459.1927.10502953
    - Original basis for the Wilson interval used only for conditional Monte
      Carlo error in the manuscript.

29. Hothorn, T., Bretz, F., and Westfall, P. (2008). *Simultaneous Inference in
    General Parametric Models.* Biometrical Journal, 50(3), 346-363.
    https://doi.org/10.1002/bimj.200810425
    - Methodological background for simultaneous max-type adjustment; the
      manuscript labels its four-cell construction a custom application.

30. Westfall, P. H., and Young, S. S. (1993). *Resampling-Based Multiple
    Testing.* Wiley. ISBN 978-0-471-55761-6.
    - Background for resampling-based simultaneous adjustment across a family.

31. Berk, R., Brown, L., Buja, A., Zhang, K., and Zhao, L. (2013). *Valid
    Post-Selection Inference.* Annals of Statistics, 41(2), 802-837.
    https://doi.org/10.1214/12-AOS1077
    - Supports the general distinction between prespecified and data-selected
      targets; not presented as a direct derivation of the paper's budget rule.

32. Wilson, G., et al. (2014). *Best Practices for Scientific Computing.* PLoS
    Biology, 12(1), e1001745.
    https://doi.org/10.1371/journal.pbio.1001745
    - Supports version control, automated checks, and executable workflows.

33. Smith, A. M., Katz, D. S., Niemeyer, K. E., and FORCE11 Software Citation
    Working Group (2016). *Software Citation Principles.* PeerJ Computer
    Science, 2, e86. https://doi.org/10.7717/peerj-cs.86
    - Supports citing software as a research object while recording specific
      versions and persistent access.

34. Data Citation Synthesis Group (2014). *Joint Declaration of Data Citation
    Principles.* FORCE11. https://doi.org/10.25490/a97f-egyk
    - Supports treating datasets as citable research objects with persistent,
      specific identifiers.

35. Ralph, P. (2021). *ACM SIGSOFT Empirical Standards Released.* ACM SIGSOFT
    Software Engineering Notes, 46(1), 19.
    https://doi.org/10.1145/3437479.3437483
    - Official announcement of SIGSOFT empirical standards; cited for
      transparent empirical reporting rather than a specific statistical rule.

36. SWE-bench Team (2026a). *SWE-bench Experiments Repository*, commit
    `1faa91c`. GitHub software repository.
    https://github.com/swe-bench/experiments/tree/1faa91cade0562ba62b66c1c99e71f7b72d96f13
    - Frozen source of outcome matrices; full commit retained in the manifest.

37. SWE-bench Team (2026b). *SWE-bench Leaderboard Website Repository*, commit
    `f42505b`. GitHub software repository.
    https://github.com/swe-bench/swe-bench.github.io/tree/f42505b21a0eb31a9cc1204caafcbe0da6c1a259
    - Frozen source of leaderboard scores and metadata.

38. Davison, A. C., and Hinkley, D. V. (1997). *Bootstrap Methods and Their
    Application.* Cambridge University Press.
    https://doi.org/10.1017/CBO9780511802843
    - General bootstrap reference used for empirical percentile intervals and
      Monte Carlo implementation guidance.

39. Efron, B., and Tibshirani, R. (1985). *The Bootstrap Method for Assessing
    Statistical Accuracy.* Behaviormetrika, 12, 1-35.
    https://doi.org/10.2333/bhmk.12.17_1
    - Foundational bootstrap overview used for the empirical-resampling
      background, not for a claim of exact coverage.
