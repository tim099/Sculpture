# 階段二十一 下 CLI（TASK-0690）：裝飾（deco=1）—— 讀 verify_decor_models.json（draft_decor_models.py 產）
#   步驟：skel_create｜skel_stamp｜models
#   · 格的那一步只跑一次（讀回 placed）；模型 overwrite=1。⛔ 失敗那一行整段印出來
# 用法：python -I -X utf8 -B apply_stage21.py <design> <步驟>
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_decor_models.json'), encoding='utf-8'))
PRE = 'summit-stormkaap-01m'
ok = bad = 0


def cli(args, quiet_fail=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        if not quiet_fail:
            bad += 1; print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


def xyz(p):
    return ','.join('%g' % v for v in p)


K = V['skeleton']
if step == 'skel_create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + K['work']], quiet_fail=True)
    if rc == 0: print('已有', K['work'])
    else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + K['work'], 'title=' + K['title'], 'size=' + xyz(K['size']), 'parent_work=' + PRE, 'tags=sub']); print('建立', K['work'])
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + K['work'], 'meters_per_voxel=0.05'])
elif step == 'skel_stamp':
    rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + K['work'], 'voxels=' + os.path.join(D, K['file']).replace('\\', '/'), 'at=0,0,0',
                   'expect_pixels=%d' % K['cells'], 'draft=0'])
    m = re.search(r'🔢 placed = (\d+)', out); print('stampvox', K['work'], K['cells'], '讀回', m.group(0) if m else '?')
elif step == 'models':
    for r in V['rows']:
        if not r.get('at'):
            continue
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + r['host_work'], 'name=' + r['model'], 'source_work=' + r['work'], 'at=' + xyz(r['at']),
             'pivot=' + xyz(r['pivot']), 'rotate=0,0,%g' % r['rotate'], 'scale=%g' % r['scale'], 'overwrite=1',
             'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True), 'note=階段二十一 裝飾（verify_decor_models.json）'])
        print('model', r['path'], xyz(r['at']), 'rot', r['rotate'])
else:
    raise SystemExit('步驟？ skel_create｜skel_stamp｜models')
print(step, 'ok', ok, 'bad', bad)
