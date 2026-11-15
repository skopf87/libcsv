A `csv_write2(NULL, 0, ...)` sizing query currently runs the bounded-output and per-byte saturation logic used for actual writes. Separate the zero-destination-size case into a quote-count reduction and one checked, saturating size calculation. GCC can vectorize this reduction; actual writes retain the existing loop and byte output. `csv_write` benefits through its existing delegation.

The PR also extends the native writer tests to verify query lengths against expected encoded lengths, exercise non-null zero-capacity destinations without modifying their sentinel byte, and cover empty input, embedded NULs, null sources and a high-bit custom quote. Writer fixture buffers are freed so the expanded test program runs cleanly under LeakSanitizer.

### Tests

- Updated full upstream `test_csv` program: passed.
- 27,204 independent exact-byte, bounded-buffer, null and custom-quote cases: passed.
- 4,095 exact-boundary protected-page assertions under AddressSanitizer/UBSan: passed.
- Full updated `test_csv` executable under AddressSanitizer/UBSan, including leak checks: passed.
- Production source with strict C99, `-pedantic -Wall -Wextra -Werror`: passed.

Reproduce the native sanitizer suite from this branch:

```sh
gcc -std=gnu99 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    test_csv.c libcsv.c -o /tmp/test-csv-sanitized
/tmp/test-csv-sanitized
```

### Performance evidence

The implementation is byte-identical to the version independently rerun against upstream `b1d5212831842ee5869d99bc208a21837e4037d5`. The native test additions do not change the timed library. That confirmation reports **47.7% lower aggregate time** across eight fixed workloads; descriptive paired-bootstrap 95% interval **46.9–48.5%**.

| Workload | Paired time reduction |
|---|---:|
| Size query, 1,024-byte field | 74.1% |
| Size query plus write, 1,024-byte field | 35.9% |
| Size query plus write, real repository metadata | 34.3% |

The aggregate includes size-only, size-plus-write, quote-heavy and custom-quote cases, and a direct-write control. No material speedup is claimed for direct writing alone. Each case uses 15 randomized pairs after an excluded warmup, equal-weight geometric means of paired ratios and 5,000 whole-round bootstrap resamples. Per-workload regression and RSS gates passed.

Environment: Codex Cloud, AMD EPYC 9V74 virtual CPU, GCC 14.2.0, generic x86-64 `-O3`, CPU 0, one thread. Variability on the odd-length count case is high and visible in the raw observations. These measurements describe this VM and suite; branchless character counting is an established technique.

[Raw measurements and frozen benchmark/reproduction package](https://github.com/skopf87/libcsv/blob/7e4b83bf165b9fff4b4f65a52cf405d1482f59dc/research/README.md) · [Additional native PR test log and test patch](https://github.com/skopf87/libcsv/blob/7e4b83bf165b9fff4b4f65a52cf405d1482f59dc/research/pr-review/README.md).
