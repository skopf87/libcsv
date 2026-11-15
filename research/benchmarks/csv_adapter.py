from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1];src=Path(sys.argv[2]);build=Path(sys.argv[3])
def run(args):subprocess.run(list(map(str,args)),check=True,timeout=110)
if sys.argv[1]=='build':
    run(['gcc','-std=c99','-O3','-g','-fPIC','-shared',src/'libcsv.c','-o',build/'libcsv.so'])
    run(['gcc','-std=c99','-O3','-fPIC','-shared',root/'repos/libcsv/libcsv.c','-o',build/'upstream.so'])
    run(['gcc','-std=c99','-O3','-g','-I',src,f'-DCORPUS_PATH="{root}/fixtures/csv/github-repos.csv"',root/'benchmarks/csv_bench.c','-L',build,'-lcsv',f'-Wl,-rpath,{build}','-o',build/'csv_bench'])
    run(['gcc','-std=c99','-O2','-I',src,src/'test_csv.c','-L',build,'-lcsv',f'-Wl,-rpath,{build}','-o',build/'test_csv'])
    run(['gcc','-std=c99','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',src,src/'libcsv.c',root/'benchmarks/csv_bounds.c','-o',build/'sanitizer-bounds'])
elif sys.argv[1]=='test':
    run([build/'test_csv'])
    run([sys.executable,root/'benchmarks/csv_validate.py',build/'libcsv.so',build/'upstream.so'])
    run([build/'sanitizer-bounds'])
else:raise ValueError(sys.argv[1])
