# libcsv: Separate size-only serialization into a quote-count reduction

The implementation in `libcsv.c` exactly matches the locally verified patch against upstream `b1d5212831842ee5869d99bc208a21837e4037d5`. Original lab commit: `8b5477fe4614ae3073cecc1d8f6b0e60fe4e765e`. The publication manifest records source SHA256 and Git blob identity.

**Independent upstream confirmation: 47.7% aggregate time reduction** on this CPU workload suite (descriptive 95% interval 46.9–48.5%). Held-out aggregate: 43.7% time reduction. These are paired geometric-mean ratios, not whole-application guarantees.

The full upstream test_csv program, 27,204 exact-byte/bounded/null/custom-quote cases and 4,095 protected-page serialization assertions under ASan/UBSan passed. Strict C99 passed. Strict pedantic C89 with Werror fails for the same pre-existing declarations in both original and modified source; see evidence logs.

The source, datasets, evaluator, compiler flags and thresholds were frozen before implementation trials. Each validation/confirmation uses 15 randomized pairs per workload after an excluded warmup, with 5,000 paired-round bootstrap replicates. The gate requires >2% improvement separately on screen and held-out aggregates, every workload upper ratio <=1.03, and process RSS <=1.10x + 1 MiB. Screening cannot promote.

## Workloads and confirmation medians

| Workload | Split | Upstream median batch (ms) | Optimized median batch (ms) | Paired time reduction |
|---|---|---:|---:|---:|
| count1024 | screen | 39.623 | 10.369 | 74.07% |
| sized1024 | screen | 80.400 | 50.479 | 35.90% |
| sized32 | screen | 89.446 | 52.868 | 40.52% |
| count5553 | heldout | 39.065 | 10.724 | 73.63% |
| quoted | heldout | 96.299 | 53.270 | 45.48% |
| direct256 | heldout | 41.726 | 41.510 | 1.16% |
| metadata | heldout | 89.939 | 59.077 | 34.27% |
| custom255 | heldout | 88.735 | 52.684 | 39.39% |

Median ratios can differ from paired geometric-mean effects. Raw observations include checksums, call counts, RSS and warmup flags. Shared-VM variability is visible; intervals describe this experiment, not all hardware. The confirmation reused the fixed held-out suite on the same VM. No new algorithmic novelty or independent-team validation is claimed.

## Reproduce

Requirements: Linux with CPU 0 available, Python 3.12+, GCC, Git and taskset. The original environment used GCC 14.2.0 and an AMD EPYC virtual CPU; complete details are in `evidence/environment.json`. No third-party Python packages are required.

```sh
python3 research/reproduce.py --prepare-only
python3 research/reproduce.py --stage validate
```

The script creates an isolated temporary workspace, clones the pinned original upstream, verifies the frozen evaluator hashes, checks that the patch reconstructs the exact published implementation, and runs the original baseline and paired validation. It leaves new results in the printed workspace and does not alter this checkout. Changing affinity, compiler flags or workloads requires recording a new protocol.

## Evidence

`evidence/results/` contains all target runs, including unsuccessful follow-ups. `evidence/experiments.csv` and `evidence/benchmark_results.csv` are filtered from the original campaign without changing measurements. `evidence/final_report.md`, novelty assessment, rejected directions and candidate/backlog summaries describe the wider 21-candidate campaign; raw evidence here covers this component. The other verified component is in the corresponding `skopf87/cJSON` or `skopf87/libcsv` research branch.

The original benchmark sources/configuration/frozen manifest are preserved exactly under `benchmarks/`, `configs/`, `fixtures/` and `framework/`. `patches/` contains the cumulative upstream patch. Existing techniques are used; novelty coverage is explicitly incomplete.
