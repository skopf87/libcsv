#!/usr/bin/env python3
"""Bounded paired experiments. Standard-library only; command adapters are language agnostic."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import random
import signal
import statistics as st
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n')
    tmp.replace(path)

def command(argv, cwd, timeout=120, logfile=None):
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', PYTHONHASHSEED='0', LC_ALL='C')
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        output, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        output, _ = p.communicate()
        if logfile:
            logfile.write_text(output + '\nTIMEOUT\n')
        raise RuntimeError(f'timeout after {timeout}s: {argv}')
    if logfile:
        logfile.write_text(output)
    if p.returncode:
        raise RuntimeError(f'command exit {p.returncode}: {argv}\n{output[-2000:]}')
    return output

def git(src, *args):
    return command(['git', '-C', str(src), *args], ROOT).strip()

def render(argv, ctx):
    return [v.format(**ctx) for v in argv]

def append_csv(path, row):
    exists = path.exists()
    with path.open('a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if not exists:
            w.writeheader()
        w.writerow(row)

def interval(log_ratios, seed=941, iterations=5000):
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(log_ratios, k=len(log_ratios))) / len(log_ratios) for _ in range(iterations))
    return [math.exp(means[int(iterations*.025)]), math.exp(means[int(iterations*.975)])]

def analyze(raw, workloads, rounds):
    result = {}
    logs = {}
    for name, split in workloads.items():
        pairs = []
        vals = {}
        for variant in ['reference', 'trial']:
            vals[variant] = [r['seconds'] for r in raw if r['workload']==name and r['variant']==variant and not r['warmup']]
        for i in range(rounds):
            a = next(r for r in raw if r['workload']==name and r['variant']=='reference' and r['round']==i and not r['warmup'])
            b = next(r for r in raw if r['workload']==name and r['variant']=='trial' and r['round']==i and not r['warmup'])
            if a['checksum'] != b['checksum']:
                raise RuntimeError(f'benchmark checksum mismatch: {name}')
            pairs.append(math.log(b['seconds']/a['seconds']))
        logs[name] = pairs
        ratio = math.exp(st.mean(pairs))
        result[name] = dict(split=split, reference_median=st.median(vals['reference']), trial_median=st.median(vals['trial']),
            reference_cv=st.stdev(vals['reference'])/st.mean(vals['reference']), trial_cv=st.stdev(vals['trial'])/st.mean(vals['trial']),
            ratio=ratio, time_reduction_pct=100*(1-ratio), ratio_ci95=interval(pairs),
            reference_rss_kb=max(r.get('peak_rss_kb',0) for r in raw if r['workload']==name and r['variant']=='reference'),
            trial_rss_kb=max(r.get('peak_rss_kb',0) for r in raw if r['workload']==name and r['variant']=='trial'))
    aggregates = {}
    # Bootstrap whole paired rounds so shared VM disturbances across workloads are retained.
    for split in ['screen', 'heldout', 'all']:
        names = [n for n,s in workloads.items() if split=='all' or s==split]
        if names:
            paired = [st.mean(logs[n][i] for n in names) for i in range(rounds)]
            aggregates[split] = dict(ratio=math.exp(st.mean(paired)), ratio_ci95=interval(paired))
    return result, aggregates

def execute(args):
    cfgpath = ROOT/'configs'/f'{args.target}.json'
    cfg = json.loads(cfgpath.read_text())
    # A frozen manifest covers harness, validation, adapter and evaluator, including imported helpers.
    manifest_path = ROOT/'configs'/f'{args.target}.v{cfg["protocol_version"]}.frozen.json'
    current = {str(p.relative_to(ROOT)):digest(p) for p in [cfgpath, Path(__file__), *[ROOT/x for x in cfg['immutable']]]}
    if args.action=='freeze':
        if manifest_path.exists():
            raise RuntimeError('already frozen; create a new protocol version rather than replacing it')
        write_json(manifest_path,current)
        print('frozen', args.target)
        return
    if json.loads(manifest_path.read_text()) != current:
        raise RuntimeError('immutable evaluation infrastructure changed')
    upstream = ROOT/'repos'/cfg['repo_dir']
    if git(upstream,'rev-parse','HEAD') != cfg['upstream_commit']:
        raise RuntimeError('upstream revision mismatch')
    statepath = ROOT/'results'/f'{args.target}.state.json'
    state = json.loads(statepath.read_text()) if statepath.exists() else {'best_commit':cfg['upstream_commit'], 'status':'not started'}
    reference = cfg['upstream_commit'] if args.action=='baseline' or args.upstream else state['best_commit']
    tag = args.id or f'{args.target}-{args.action}-{int(time.time())}'
    out = ROOT/'results'/tag
    if out.exists():
        raise RuntimeError('experiment ID already exists')
    out.mkdir(parents=True)
    patch = Path(args.patch).resolve() if args.patch else None
    if args.action=='trial' and patch is None:
        raise RuntimeError('trial requires --patch')
    contexts = {}
    trees = []
    data = dict(id=tag, target=args.target, started=now(), reference_commit=reference, upstream_commit=cfg['upstream_commit'],
        hypothesis=args.hypothesis, stage=args.stage, immutable=current, status='running', patch_sha256=digest(patch) if patch else None)
    write_json(out/'experiment.json',data)
    try:
        variants = ['reference'] if args.action=='baseline' else ['reference','trial']
        for variant in variants:
            src = ROOT/'worktrees'/tag/variant
            src.parent.mkdir(parents=True,exist_ok=True)
            git(upstream,'worktree','add','--detach',str(src),reference)
            trees.append(src)
            build = ROOT/'build'/tag/variant
            build.mkdir(parents=True)
            ctx = dict(root=str(ROOT),src=str(src),build=str(build))
            contexts[variant]=ctx
            if variant=='trial':
                git(src,'apply','--check',str(patch))
                git(src,'apply',str(patch))
                files = git(src,'diff','--name-only').splitlines()
                if not files or not set(files) <= set(cfg['editable']):
                    raise RuntimeError(f'patch touches files outside editable implementation: {files}')
                data['modified_files']=files
                (out/'implementation.patch').write_bytes(patch.read_bytes())
            for group in ['build','test']:
                for i,cmd in enumerate(cfg[group]):
                    command(render(cmd,ctx), src, cfg.get('timeout',120), out/f'{variant}-{group}-{i}.log')
        if args.action=='baseline':
            raw=[]
            for w in cfg['workloads']:
                for i in range(5):
                    cmd = render(cfg['benchmark']+[w['name']],contexts['reference'])
                    r=json.loads(command(cmd,ROOT,cfg.get('benchmark_timeout',30)))
                    if not math.isfinite(r['seconds']) or r['seconds']<=0:
                        raise RuntimeError('invalid timing')
                    raw.append(dict(r,workload=w['name'],variant='reference',round=i,warmup=False))
            data.update(status='baseline established',correctness='pass',raw=raw)
            state.update(status='baseline established', baseline_experiment=tag)
            write_json(statepath,state)
        else:
            rounds=cfg['validation_rounds'] if args.stage=='validate' else cfg['screen_rounds']
            chosen = [w for w in cfg['workloads'] if args.stage=='validate' or w['split']=='screen']
            rng = random.Random(cfg['order_seed'])
            raw=[]
            for i in range(-cfg['warmups'],rounds):
                order=list(chosen); rng.shuffle(order)
                for w in order:
                    vs=list(variants); rng.shuffle(vs)
                    for variant in vs:
                        ctx=contexts[variant]
                        r=json.loads(command(render(cfg['benchmark']+[w['name']],ctx),ROOT,cfg.get('benchmark_timeout',30)))
                        if not math.isfinite(r['seconds']) or r['seconds']<=0:
                            raise RuntimeError('invalid timing')
                        row=dict(r,workload=w['name'],variant=variant,round=i,warmup=i<0)
                        raw.append(row)
                        with (out/'raw.jsonl').open('a') as f:
                            f.write(json.dumps(row)+'\n')
            metrics,agg=analyze(raw,{w['name']:w['split'] for w in chosen},rounds)
            passes = (args.stage=='validate' and 'heldout' in agg
                and all(agg[s]['ratio_ci95'][1] < 1-cfg['minimum_gain'] for s in ['screen','heldout'])
                and all(m['ratio_ci95'][1] <= 1+cfg['regression_limit'] for m in metrics.values())
                and all(m['trial_rss_kb'] <= m['reference_rss_kb']*cfg['memory_ratio_limit']+cfg['memory_slack_kb'] for m in metrics.values()))
            data.update(status='accepted' if passes else ('screened' if args.stage=='screen' else 'rejected'),correctness='pass',metrics=metrics,aggregates=agg)
            if passes and not args.no_promote:
                src=Path(contexts['trial']['src'])
                git(src,'add','--',*data['modified_files'])
                git(src,'-c','user.name=Research Lab','-c','user.email=lab@local.invalid','commit','-m',f'{tag}: {args.hypothesis}')
                commit=git(src,'rev-parse','HEAD')
                git(upstream,'update-ref',f'refs/lab/{tag}',commit)
                # An upstream comparison of a cumulative patch is verification, not a new promotion.
                if not args.upstream:
                    state.update(best_commit=commit,status='validated',best_experiment=tag)
                    write_json(statepath,state)
                data['trial_commit']=commit
            for w,m in metrics.items():
                append_csv(ROOT/'benchmark_results.csv',dict(experiment_id=tag,candidate_id=args.target,workload=w,split=m['split'],baseline_seconds=m['reference_median'],experimental_seconds=m['trial_median'],time_reduction_pct=m['time_reduction_pct'],ratio_ci95=json.dumps(m['ratio_ci95']),rounds=rounds))
    except Exception as e:
        data.update(status='failed',correctness='failed or incomplete',error=str(e))
        print(str(e),file=sys.stderr)
    finally:
        data['finished']=now()
        write_json(out/'experiment.json',data)
        for src in trees:
            git(upstream,'worktree','remove','--force',str(src))
        git(upstream,'worktree','prune')
        ratio=data.get('aggregates',{}).get('all',{}).get('ratio')
        append_csv(ROOT/'experiments.csv',dict(experiment_id=tag,candidate_id=args.target,repository=cfg['repository'],upstream_commit=cfg['upstream_commit'],reference_commit=reference,trial_commit=data.get('trial_commit',''),hypothesis=args.hypothesis,modified_files=json.dumps(data.get('modified_files',[])),baseline_metrics=json.dumps({k:v['reference_median'] for k,v in data.get('metrics',{}).items()}),experimental_metrics=json.dumps({k:v['trial_median'] for k,v in data.get('metrics',{}).items()}),time_reduction_pct=100*(1-ratio) if ratio else '',correctness=data.get('correctness',''),confidence=json.dumps(data.get('aggregates',{})),decision=data['status'],observations=data.get('error',''),result=str(out.relative_to(ROOT))))
    print(json.dumps({k:data.get(k) for k in ['id','status','aggregates','error']},indent=2))
    if data['status']=='failed':
        raise SystemExit(1)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['freeze','baseline','trial'])
    p.add_argument('target')
    p.add_argument('--id')
    p.add_argument('--patch')
    p.add_argument('--hypothesis',default='unmodified upstream baseline')
    p.add_argument('--stage',choices=['screen','validate'],default='screen')
    p.add_argument('--upstream',action='store_true')
    p.add_argument('--no-promote',action='store_true')
    args=p.parse_args()
    # O_EXCL prevents simultaneous timing runs and state corruption. SIGKILL recovery is documented.
    lock=ROOT/'.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    os.write(fd,str(os.getpid()).encode()); os.close(fd)
    try:
        execute(args)
    finally:
        lock.unlink(missing_ok=True)

if __name__=='__main__':
    main()
