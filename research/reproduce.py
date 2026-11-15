#!/usr/bin/env python3
"""Recreate the original frozen evaluator in an isolated workspace."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

RESEARCH=Path(__file__).resolve().parent

def run(args,cwd=None,timeout=240):
    subprocess.run(list(map(str,args)),cwd=cwd,check=True,timeout=timeout)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['screen','validate'],default='validate')
    p.add_argument('--work-dir',type=Path)
    p.add_argument('--prepare-only',action='store_true')
    args=p.parse_args()
    meta=json.loads((RESEARCH/'publication.json').read_text());target=meta['candidate_id']
    if hasattr(os,'sched_getaffinity') and 0 not in os.sched_getaffinity(0):
        raise SystemExit('The frozen protocol pins CPU 0, which is unavailable here. Record a new protocol before changing affinity.')
    for command in ['git','gcc','taskset']:
        if not shutil.which(command):raise SystemExit('Required executable missing: '+command)
    if args.work_dir:
        work=args.work_dir.resolve()
        if work.exists() and any(work.iterdir()):raise SystemExit('Work directory must be empty; existing files are preserved.')
        work.mkdir(parents=True,exist_ok=True)
    else:work=Path(tempfile.mkdtemp(prefix=target.lower()+'-autoresearch-'))
    for name in ['framework','configs','benchmarks','fixtures','patches']:
        if (RESEARCH/name).exists():shutil.copytree(RESEARCH/name,work/name,dirs_exist_ok=True)
    cfg=json.loads((work/'configs'/f'{target}.json').read_text())
    manifest=json.loads((work/'configs'/f'{target}.v{cfg["protocol_version"]}.frozen.json').read_text())
    for name,expected in manifest.items():
        if hashlib.sha256((work/name).read_bytes()).hexdigest()!=expected:raise SystemExit('Frozen evaluator mismatch: '+name)
    src=work/'repos'/cfg['repo_dir'];src.parent.mkdir(parents=True)
    run(['git','clone','--depth','1',cfg['repository'],src],timeout=120)
    head=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
    if head!=cfg['upstream_commit']:
        run(['git','-C',src,'fetch','--depth','1','origin',cfg['upstream_commit']],timeout=120)
        run(['git','-C',src,'checkout','--detach',cfg['upstream_commit']])
    optimized=RESEARCH.parent/meta['implementation_file']
    if hashlib.sha256(optimized.read_bytes()).hexdigest()!=meta['implementation_sha256']:
        raise SystemExit('Optimized implementation differs from the uploaded verified source.')
    # Prove the saved patch reconstructs exactly that implementation without altering the oracle checkout.
    patch=work/'patches'/f'{target}-best-upstream.patch'
    run(['git','-C',src,'apply','--check',patch])
    run(['git','-C',src,'apply',patch])
    if hashlib.sha256((src/meta['implementation_file']).read_bytes()).hexdigest()!=meta['implementation_sha256']:
        raise SystemExit('Patch does not reconstruct the verified implementation.')
    run(['git','-C',src,'apply','--reverse',patch])
    print('Pinned upstream, immutable evaluator and implementation hashes verified:',work,flush=True)
    if args.prepare_only:return
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run([sys.executable,work/'framework/lab.py','baseline',target,'--id',f'{target}-repro-baseline-{stamp}'],cwd=work)
    run([sys.executable,work/'framework/lab.py','trial',target,'--id',f'{target}-repro-{args.stage}-{stamp}',
         '--patch',patch,'--hypothesis','Reproduce the published verified implementation against original upstream',
         '--stage',args.stage,'--upstream','--no-promote'],cwd=work)
    print('Fresh measurements and full logs:',work/'results',flush=True)

if __name__=='__main__':main()
