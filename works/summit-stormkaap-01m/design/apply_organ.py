# 階段十八：照 verify_organ.json 下 CLI —— 子作品 -organ（0.05 m）＋ 甲板-後 的外部模型 `管風琴`
# 用法：python -I -X utf8 -B apply_organ.py <design 資料夾> <步驟>
#   步驟：create（已存在 ⇒ 略過）｜restamp（匯出子作品現在的格、跟清單比：多的 carvevox 帶原色守門、少的或色不同的 stampvox overwrite）｜model
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_organ.json'), encoding='utf-8'))
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


def rd(p):
    return {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}


def dump(path, cells):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for k, c in sorted(cells.items()):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c))


xyz = lambda v: ','.join('%g' % c for c in v)
if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + V['work']], quiet_fail=True)
    if rc == 0:
        print('已有', V['work'])
    else:
        cli(['op=work', 'sub=create', 'persona=summit', 'id=' + V['work'], 'title=' + V['title'], 'size=' + xyz(V['size']), 'parent_work=summit-stormkaap-01m', 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + V['work'], 'meters_per_voxel=%g' % V['mpv']])
elif step == 'restamp':
    tmp = os.path.join(os.path.dirname(D), 'exports', 'restamp'); os.makedirs(tmp, exist_ok=True)
    cp = os.path.join(tmp, V['work'] + '.list.txt').replace('\\', '/')
    cli(['op=export', 'format=list', 'work=' + V['work'], 'out=' + cp])
    cur, want = rd(cp), rd(os.path.join(D, V['file']))
    carve = {k: c for k, c in cur.items() if k not in want}
    add = {k: c for k, c in want.items() if cur.get(k) != c}
    for nm, cells, args in (('carve', carve, ['op=carvevox']), ('stamp', add, ['op=stampvox', 'overwrite=1'])):
        if not cells:
            continue
        p = os.path.join(tmp, '%s.%s.vox.txt' % (V['work'], nm)); dump(p, cells)
        rc, out = cli(args + ['persona=summit', 'work=' + V['work'], 'voxels=' + p.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(cells), 'draft=0'])
        print(nm, len(cells), 'rc', rc)
    print('現況 %d → 清單 %d｜刻 %d、補／換色 %d' % (len(cur), len(want), len(carve), len(add)))
elif step == 'model':
    cli(['op=work', 'sub=model', 'persona=summit', 'work=' + V['host_work'], 'name=' + V['model'], 'source_work=' + V['work'], 'at=' + xyz(V['at']),
         'pivot=' + xyz(V['pivot']), 'rotate=0,0,0', 'scale=%g' % V['scale'], 'overwrite=1', 'note=階段十八 管風琴（verify_organ.json）'])
else:
    raise SystemExit('步驟？ create|restamp|model')
print(step, 'ok', ok, 'bad', bad)
