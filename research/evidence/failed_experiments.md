# Rejected directions and setup failures

Measurements and patches are retained even when the best implementation stayed upstream. `experiments.csv` contains 27 run records; a screening record's status is `screened`, while the final decision below or in `hypotheses.json` determines whether it advanced. No screen promoted code.

| Candidate / hypothesis | Result | Final decision and reason |
|---|---|---|
| C01-E01: weighted eight-byte Adler sums | Correct; packet/bulk faster; tiny16 ~13.4% slower in screening | Rejected after validation: small-input regression |
| C01-E02: weighted sums only on blocks >=64 bytes | Correct; bulk ~16% faster | Rejected: tiny7 +3.4% point estimate, upper ratio 1.053; inflate control upper ratio 1.047 |
| C01-E03: 16 independent prefix lanes | Correct; bulk ~8.2% faster in screen | Rejected at screen: aggregate slightly slower, tiny16 ~7.0% slower; no validation/promotion |
| C03-E01: whole unescaped string copy | Correct; validation and separate upstream confirmation passed | Accepted; not a failed direction |
| C03-E02: memcpy runs between escapes | Correct; mixed-escape workload ~7.3% slower versus verified best | Scheduler rejected at screen; eight-line E01 implementation retained |
| C04-E01: separate size-only count reduction | Correct; validation and separate upstream confirmation passed | Accepted; not a failed direction |
| C04-E02 / E02b: repeated memchr sizing | First trial failed compilation because `<string.h>` was missing; corrected retry passed correctness | Rejected at screen: sized32 ~11.1% slower versus verified best, despite strong large-field gains |
| C05-E01: safe product/divide with GCD fallback | Correct; ncr workloads ~59–71% faster | Rejected: unrelated math-control point regression ~3.0%, upper ratio 1.050 |
| C05-E02: exact double-width recurrence | Correct; substantial ncr gains | Rejected: math-control point regression ~4.9%, upper ratio 1.080 |

Nine distinct optimization hypotheses were attempted. C04-E02b is a compile repair of E02, not a tenth independent idea. C03/C04 final confirmations are measurement repeats, not new optimizations.

The miniz baseline setup also exposed adapter errors before implementation work: C99 lacked GNU/POSIX declarations for `fseeko`/`ftello`, the upstream test needed mutable C++17 `string::data`, and an initially cached C++14 Catch object was incompatible with the C++17 test translation unit. All failed builds are logged. The final v4 protocol was frozen before any miniz optimization trial and added actual source-text workloads to the passing v3 baseline. The acceptance gates were unchanged.

FastBoxBlur failed baseline correctness before any optimization or performance claim. The independently calculated REFLECT_101 result is 90, while upstream outputs 114 at width 3, radius 1, position 1. See `benchmarks/blur_validate.cpp` and `results/C18-baseline-correctness/reference-test-0.log`. C18 is blocked; its configuration is a correctness probe, not a completed timing adapter.

Additional source review deferred Sorted Containers after finding overlapping open PR #263. Textdistance PR #103 and Pillow PRs #10005/#10161 likewise caused early deferral, while the SQLite COUNT(DISTINCT) covering-index lead was already solved. These are research findings, not failed experiments.

The causes of small-input and unrelated-control regressions have not been isolated. Code layout, altered branch behavior, fixed setup overhead and shared-VM noise are possibilities, not established explanations. Large kernel wins do not override a failed fixed regression gate.
