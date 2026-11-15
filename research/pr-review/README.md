# libcsv PR regression checks

The PR retains the exact previously verified libcsv.c implementation and adds native tests for size-only queries, null/zero-capacity destinations, empty input, embedded NULs and a high-bit custom quote. Test fixture allocations are freed so the complete test_csv executable runs cleanly under ASan/UBSan.

The updated full upstream test_csv, 27,204 independent exact-byte/buffer/null/custom-quote cases, 4,095 protected-page assertions, strict C99 compilation, and the full test_csv program under ASan/UBSan pass. See native-validation.log. The implementation bytes are unchanged, so the original paired benchmark and independent confirmation evidence in ../evidence remain applicable.

The added native cases are available in tests.patch and on the perf/size-query-quote-count branch.
