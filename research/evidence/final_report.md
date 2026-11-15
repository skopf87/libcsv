# CPU optimization research campaign

**Result: 21 candidate opportunities investigated, 10 selected, 4 targets correctly benchmarked, 9 distinct optimization hypotheses attempted, and 2 implementations validated and rerun against original upstream.** One additional target built but failed baseline correctness. There are 27 run records (including setup failures and confirmation reruns) and 2,392 raw paired timing observations including warmups. Repeats are not counted as new improvements.

**The two confirmed results are cJSON string parsing and libcsv serialization sizing.** Improvements are time reductions in fixed local workload suites, not whole-application guarantees. No scientific algorithmic novelty is claimed. No upstream pull requests were submitted.

# Ranked portfolio

Ranks and weighted scores are the initial research priorities. Later evidence closes or defers targets without hiding unsuccessful work. See `research_backlog.md` for the next-session queue.

| Rank | Project | Algorithm/Kernel | Existing Work | Optimization | Improvement | Validation | Novelty Assessment |
|---:|---|---|---|---|---|---|---|
| 1 | [miniz](https://github.com/richgel999/miniz) (7.90) | mz_adler32; miniz.c | Scalar unroll; SIMD/weighted sums known in zlib | Weighted8, short fallback, 16 lanes | Up to ~16% on bulk; no promotion | Correctness passed; tiny/control regression gates failed | Known technique; no novel claim |
| 2 | [cJSON](https://github.com/DaveGamble/cJSON) (7.80) | parse_string; cJSON.c | Two-pass scan/copy; bulk copy known elsewhere | Memcpy when existing escape count is zero | 16.0% aggregate time reduction | 15-pair validation + separate 15-pair upstream rerun | Existing technique in pinned revision; novelty uncertain |
| 3 | [libcsv](https://github.com/rgamble/libcsv) (7.60) | csv_write2 sizing; libcsv.c | Per-byte sizing and bounded writes; SIMD classification known | Separate size queries into branchless quote count | 47.7% aggregate time reduction | 15-pair validation + separate 15-pair upstream rerun | Existing technique in pinned revision; novelty uncertain |
| 4 | [tinyexpr](https://github.com/codeplea/tinyexpr) (7.40) | ncr exact combinatorics; tinyexpr.c | Exact GCD cancellation; recent overflow fix | Safe multiply/divide and widened recurrence | Large ncr gains; no promotion | Exact oracles passed; unrelated control failed | Established combinatorics methods |
| 5 | [Sorted Containers](https://github.com/grantjenks/python-sortedcontainers) (7.05) | SortedList index/slice operations; sortedlist.py | Lazy segment-tree index; active PR #263 block deletion | Deferred overlapping range deletion | Not measured | Source and PR reviewed; no baseline | Currently being developed |
| 6 | [NetworkX](https://github.com/networkx/networkx) (6.65) | weakly_connected._plain_bfs | Current BFS already has early exit and len hoisting | Profile distinct adjacency overhead next | Not measured | Not started | Uncertain; generic early-exit idea already solved |
| 7 | [Bottleneck](https://github.com/pydata/bottleneck) (6.45) | move_median heaps; move_median.c | Existing dual heaps; active correctness fixes | Profile contiguous/indexed heap layout | Not measured | Not started | Known methods; distinct gap uncertain |
| 8 | [pocketfft](https://github.com/mreineck/pocketfft) (6.30) | pocketfft_c / pocketfft_r plan choice | Codelets, SIMD, Bluestein heuristic and cache support | Investigate uncached prime planning crossover | Not measured | Not started | Known FFT planning techniques; uncertain gap |
| 9 | [FastBoxBlur](https://github.com/michelerenzullo/FastBoxBlur) (6.25) | separable sliding accumulator blur | Sliding sums and blocked transpose already implemented | Blocked before implementation | No performance result | Upstream fails independent reflected-border oracle | Correctness blocker; no novelty claim |
| 10 | [CRoaring](https://github.com/RoaringBitmap/CRoaring) (6.20) | array_container_intersection_cardinality | AVX2, scalar and skew-aware galloping already implemented | Inspect a distinct short/cardinality-only crossover | Not measured | Not started | Main opportunity thoroughly explored |

# Experimental controls and limits

The selected Cloud VM reports 3 AMD EPYC 9V74 vCPUs but has a **2-CPU cgroup quota and 8 GiB memory cap**. Benchmark processes use virtual CPU 0, one thread, GCC 14.2.0, generic x86-64 `-O3`, and Python 3.12.14 for orchestration. No GPU is exposed. Builds are sequential and all child commands have timeouts. `environment.json` records the observed environment.

Each promising implementation received 15 randomized paired rounds per workload after one excluded warmup. Two successful implementations were later built and measured again against their original upstream commits. The effect estimate is the geometric mean of paired latency ratios, with equal weight per workload. Descriptive 95% intervals come from 5,000 bootstrap resamples of entire paired rounds. Median batch latencies and coefficients of variation are retained; median ratios need not equal paired geometric mean effects.

Promotion requires correctness, >2% improvement separately on development and held-out aggregates, every workload upper ratio bound <=1.03, and process RSS <=1.10x reference + 1 MiB. Fixed thresholds were never loosened. Screens use 3 pairs and cannot promote. More than one hypothesis was tested per experimentally explored target. Rejected patches leave the best implementation and pristine upstream intact.

The CPU is shared and timing variability is visible: the libcsv odd-length count control has approximately 40–46% CV in the confirmation run. Its large gain repeats, but the interval is not a universal hardware claim. Some unchanged controls show apparent small gains or regressions; these are not promoted as separate discoveries. RSS has a startup floor and does not precisely resolve small stack changes. No energy, cache-miss or cycle claims are made.

Held-out workloads are separate from fast screens. Once inspected after a failed validation they are no longer pristine for later hypotheses. Final confirmation is an independent measurement run on the same suite and VM, not a new unseen corpus or an independent research team. Cross-machine/compiler and production-application validation remain unfinished. The hypothesis search is adaptive and its intervals are descriptive, without multiplicity-adjusted discovery claims.

# Verified optimization: cJSON

The original `parse_string` scans to the closing quote while counting escapes, allocates output, then copies ordinary bytes through another scalar loop. The accepted eight-line patch uses the existing escape count to copy an entirely unescaped string with `memcpy`, then shares the original termination and metadata path. Escaped strings retain the original decoder, allocation behavior and error offsets. The implementation has no additional allocation.

Profiling the original long-text parse/delete workload attributes about 98% of sampled self time to `parse_string`. Initial short profiling runs were expanded separately from frozen timing harnesses. `logs/C03-upstream-gprof.txt` and `framework/profile.py` preserve this evidence.

Correctness: all 21 upstream Unity test programs finish with zero failures (one upstream test is ignored), along with 3,891 independently checked JSON/differential/bounded-input cases and 1,530 exact-boundary protected-page cases under AddressSanitizer/UBSan. The oracle compares decoded values against Python json and compares permissive/error-offset behavior against a separately built unmodified cJSON. Strict C89 compilation with warnings as errors also passes.

Applications include parsing text-heavy API responses, configuration documents and JSON payloads. This gain depends strongly on string length and escaping: short-key and number-only workloads receive little benefit. Parsing and deletion are timed together, so allocation and tree management are included.

Initial validation: **17.0%** aggregate time reduction. Separate upstream confirmation: **16.0%** (descriptive 95% interval **14.9–17.2%**), corresponding to 1.19x aggregate speedup. Held-out confirmation: **12.2%**.

| Workload | Split | Upstream median batch (ms) | Optimized median batch (ms) | Paired geometric-mean time reduction |
|---|---|---:|---:|---:|
| short-keys | screen | 176.413 | 175.149 | 1.20% |
| long-text | screen | 30.855 | 16.879 | 44.82% |
| mixed-escapes | screen | 65.667 | 56.427 | 13.02% |
| unicode | heldout | 49.579 | 35.503 | 28.32% |
| numbers | heldout | 469.655 | 471.137 | 1.73% |
| upstream-test1 | heldout | 58.709 | 55.210 | 5.29% |
| upstream-test4 | heldout | 64.028 | 57.864 | 9.15% |
| github-repo | heldout | 58.290 | 49.172 | 14.05% |

Upstream commit: `6d9f2443ab071f86e5d9b43025a40929ec41c46c`. Raw paired measurements, output checksums, process RSS, per-workload intervals and variability: `results/C03-confirm-upstream/`. Batch sizes/call counts are fixed in the immutable harness and included in every raw observation. Tiny apparent changes on controls are not separately claimed as improvements.

The follow-up bulk copy of runs between escapes passed correctness but slowed the mixed-escape screening workload by 7.3% against the verified best and was discarded. The accepted source commit is `553c85d470fcf652d7b589580ba8fa765aac5235`; the cumulative upstream patch is `patches/C03-best-upstream.patch`.

Novelty: bulk copying unescaped strings is established. The pinned cJSON revision already uses a related bulk copy in printing, and SIMD/string-specialization is common in other JSON parsers. Searches of current PRs and an inspected older cJSON fork did not establish an equivalent current parsing patch; that limited absence does not prove novelty. Classification: **known technique applied in this pinned implementation; global novelty uncertain**.

# Verified optimization: libcsv

The original `csv_write2` executes bounded-output and saturating per-byte logic even for a size-only query with no destination. The accepted patch separates that query into a quote-count reduction and one checked saturated size calculation. Actual writes retain the upstream byte loop, preserving truncated buffers, arbitrary quote bytes, source null handling and alias behavior. Buffer-growth API and parser code are unchanged.

Original-source profiling attributes the size-only workload to `csv_write2`. GCC reports the new count loop vectorized with 16-byte vectors (`logs/C04-vectorization.txt`). No ISA-specific compiler flags or manual intrinsics were added. Counting characters with a branchless reduction is a known technique.

Correctness: full upstream `test_csv` passes; 27,204 independent exact-byte, bounded-buffer, null and custom-quote cases pass; 4,095 protected-page serialization assertions pass under AddressSanitizer/UBSan. Both original and modified source pass strict C99. Both fail strict C89-with-pedantic-Werror due to the same pre-existing mixed declarations in unrelated functions; this is recorded instead of claiming an unsupported compatibility check passed.

Applications are serializers that first query encoded size and then write a field. The benchmark includes that complete two-call operation, high quote density, a custom 0xff quote, a direct-write control, and metadata from 20 real public repository records converted to CSV. Direct writing alone has no demonstrated material improvement. No allocation was introduced.

Initial validation: **48.8%** aggregate time reduction. Separate upstream confirmation: **47.7%** (descriptive 95% interval **46.9–48.5%**), corresponding to 1.91x aggregate speedup. Held-out confirmation: **43.7%**.

| Workload | Split | Upstream median batch (ms) | Optimized median batch (ms) | Paired geometric-mean time reduction |
|---|---|---:|---:|---:|
| count1024 | screen | 39.623 | 10.369 | 74.07% |
| sized1024 | screen | 80.400 | 50.479 | 35.90% |
| sized32 | screen | 89.446 | 52.868 | 40.52% |
| count5553 | heldout | 39.065 | 10.724 | 73.63% |
| quoted | heldout | 96.299 | 53.270 | 45.48% |
| direct256 | heldout | 41.726 | 41.510 | 1.16% |
| metadata | heldout | 89.939 | 59.077 | 34.27% |
| custom255 | heldout | 88.735 | 52.684 | 39.39% |

Upstream commit: `b1d5212831842ee5869d99bc208a21837e4037d5`. Raw paired measurements, output checksums, process RSS, per-workload intervals and variability: `results/C04-confirm-upstream/`. Batch sizes/call counts are fixed in the immutable harness and included in every raw observation. Tiny apparent changes on controls are not separately claimed as improvements.

A second hypothesis used repeated `memchr` for sparse quotes. Its initial compile omitted `<string.h>`; the corrected retry passed correctness and improved large-field sizing, but short-field screening slowed by 11.1%, so the scheduler discarded it. The accepted source commit is `8b5477fe4614ae3073cecc1d8f6b0e60fe4e765e`; the cumulative patch is `patches/C04-best-upstream.patch`.

Novelty: SIMD character classification/counting and query-specific fast paths are established, including related CSV systems and PostgreSQL discussions. The exact proposal was absent from inspected pinned source and targeted PR search, while one requested fork endpoint could not be read. Classification: **existing technique newly applied to this pinned size-query path; novelty uncertain**.

# Observed improvements that were not promoted

**Miniz:** weighted eight-byte sums passed 131,389 upstream assertions, 5,721 independent checksum/streaming/null cases, and exact-end checks with sanitizers. Bulk Adler-32 improved about 16%, but tiny calls regressed. A short-block fallback still failed the tiny-7/control upper bounds; independent 16-lane prefix accumulation then failed screening. The best verified commit remains upstream. No compression-ratio change or checksum weakening was allowed.

**Tinyexpr:** bypassing GCD cancellation when the unreduced integer product fits reduced some ncr workload times about 59–71%; a double-width integer alternative also helped combinatorics. Both preserved exact reference results in 14,907 oracle/compatibility cases and 11,327 sanitizer cases, plus both upstream smoke configurations (10,125 and 10,135 assertions). The unrelated math control nevertheless regressed about 3.0% and 4.9%, with upper ratio bounds above 1.03. The causes (layout effects, scheduling or another interaction) were not isolated. Both were rejected; reported ncr gains are observations, not accepted improvements.

**FastBoxBlur:** the unmodified C++ header built, but width 3, radius 1, pixel 1 produced 114 where an independent REFLECT_101 oracle requires 90. This radius is inside the stated range. Baseline correctness therefore blocked performance work. The reproducer and failing log are retained. The source already includes a blocked transpose, so proposing an initial transpose would also duplicate existing work.

**Sorted Containers:** a follow-up PR search found [open PR #263](https://github.com/grantjenks/python-sortedcontainers/pull/263), including a block-range deletion implementation inside SortedList. It substantially overlaps the proposed area. No benchmark or optimization was performed. This is a useful negative discovery, not a blocked build or a measured improvement.

# Reproducibility and remaining work

Start with `RESUME.md`. `framework/bootstrap.py` restores exact source archives without overwriting existing checkouts; `framework/inspect_state.py` verifies upstream revisions, clean source, retained best objects and frozen evaluator hashes. Use the saved patches with `framework/lab.py` for reruns. `framework/portfolio.py` selects a bounded queue of agent-authored hypotheses and automates screening, validation and rollback. The research agent supplies hypotheses; the scheduler does not pretend to invent algorithms by itself.

Artifacts include candidate scoring and analysis, all 27 run records, CSV summaries, raw paired observations, test/build logs, original-source profiles, frozen configurations, known-good patches and local Git commits. The baseline sources are archived with their Git histories and retained lab refs. Root workspace checkpoints are also committed. No background experiment is left running.

The source archive was restored into a separate directory, all frozen hashes and saved revisions were audited there, and both accepted source commits were rebuilt and passed their correctness suites from the restored archive. This verifies archive recovery on the same machine; it is not cross-machine validation. Logs are in `logs/archive-restore.log` and `logs/archive-correctness-replay.log`. `verified/` contains direct review copies generated from the accepted Git commits.

Next candidates are NetworkX, Bottleneck, pocketfft and CRoaring, subject to renewed gap/source checks. These four are researched but unbenchmarked. Sorted Containers is deferred for active overlapping work; FastBoxBlur is blocked for correctness. Miniz and tinyexpr should receive further resources only after a distinct explanation/hypothesis addresses their regression failures.

Discovery is a bounded initial survey, not a systematic literature review: initial GitHub issue/PR queries return at most five matches, additional targeted searches have limits, two repository source endpoints were unresolved, and some papers were inspected only through abstracts/official descriptions. Competing implementations, forks, papers and current PRs constrain novelty assessments, but coverage remains incomplete. Ten targets were researched; ten successful optimizations were never assumed.
