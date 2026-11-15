# Ranked research backlog

Initial weighted scores are preserved. Later evidence determines resource allocation.

| Initial rank | ID | Project | Score | Current status | Next action |
|---:|---|---|---:|---|---|
| 1 | C01 | miniz | 7.90 | Completed, no promotion | Requires a distinct explanation for tiny/control regressions |
| 2 | C03 | cJSON | 7.80 | Completed, validated | Cross-machine/compiler/application validation remains |
| 3 | C04 | libcsv | 7.60 | Completed, validated | Cross-machine/compiler/application validation remains |
| 4 | C05 | tinyexpr | 7.40 | Completed, no promotion | Isolate math-control regression before further tuning |
| 5 | C08 | Sorted Containers | 7.05 | Deferred | Open PR #263 overlaps block-range deletion |
| 6 | C06 | NetworkX | 6.65 | Not started | Highest-priority unfinished target: verify build and a distinct gap |
| 7 | C07 | Bottleneck | 6.45 | Not started | Profile median heap and review active fixes |
| 8 | C09 | pocketfft | 6.30 | Not started | Verify cache settings and profile uncached plans |
| 9 | C18 | FastBoxBlur | 6.25 | Blocked | Upstream reflected-border oracle failure; no optimization |
| 10 | C10 | CRoaring | 6.20 | Not started | Inspect helpers before proposing another SIMD/skew optimization |

Next-session queue: **C06 → C07 → C09 → C10**. Recheck recent source/PR work before allocating experiments. C08 is deferred, C18 correctness-blocked, and failed C01/C05 directions are closed for this campaign.

Initial budget: a 90-minute ceiling for active campaign work, <=18 minutes discovery/framework target, at least 15 minutes reserved for final validation and checkpoints. The campaign closes at its current reproducible checkpoint instead of starting builds that would displace final review/packaging. This ceiling is not a promise of unattended execution. Child commands have timeouts; measurements are serialized, single-threaded and pinned to CPU 0.

Scoring weights: practical impact 20%, remaining potential 20%, automated feasibility 20%, reproducibility 15%, underexplored 15%, low complexity/risk 10%. Full component scores and evidence are in candidates.csv and candidate_analysis.md. Initial source reviews were updated with the ncr, CSV sizing, PR #263 and blur correctness findings.

Promotion protocol: 15 randomized pairs, 95% paired-round bootstrap interval, >2% improvement independently in screen and held-out aggregates, every workload upper ratio <=1.03, RSS <=1.10x + 1 MiB and correctness pass. No gate was relaxed. Fast screening never promotes. Hypotheses are agent-authored; the portfolio scheduler selects eligible queued patches and automates evaluation/rollback.
