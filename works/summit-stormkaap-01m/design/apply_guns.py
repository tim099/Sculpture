# 階段十二：照 verify_guns.json 下 CLI —— 三種砲的子作品、墊木、固定點、42 門外部模型
# 用法：python -I -X utf8 -B apply_guns.py <design 資料夾> <步驟> [模型名 regex]
#   步驟：create（已有就略過；0.05 m）｜stamp（砲＋墊木，每刀讀回 placed；只跑一次）｜anchors（overwrite=1）｜models（overwrite=1）
#   · ⛔ 失敗那一行整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
V = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
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


xyz = lambda v: ','.join('%g' % c for c in v)
fwd = lambda p: os.path.join(D, p).replace(chr(92), '/')
if step == 'create':
    for k, T in sorted(V['types'].items()):
        rc, _ = cli(['op=work', 'sub=show', 'work=' + T['work']], quiet_fail=True)
        if rc == 0: print('已有', T['work'])
        else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + T['work'], 'title=' + T['title'], 'size=' + xyz(T['size']), 'parent_work=' + PRE, 'tags=sub']); print('建立', T['work'])
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + T['work'], 'meters_per_voxel=%g' % T['mpv']])
elif step == 'stamp':
    jobs = [(T['work'], T['file'], T['cells'], k) for k, T in sorted(V['types'].items())] + [(hw, P['file'], P['voxels'], 'pads') for hw, P in sorted(V['pads'].items())]
    for work, f, n, nm in jobs:
        rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + work, 'voxels=' + fwd(f), 'at=0,0,0', 'expect_pixels=%d' % n, 'draft=0'])
        m = re.search(r'🔢 placed = (\d+)', out)
        print(nm, work, 'voxels', n, 'placed', m.group(1) if m else '?')
elif step == 'anchors':
    for k, T in sorted(V['types'].items()):
        for name, at in sorted(T['anchors'].items()):
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + T['work'], 'name=' + name, 'at=' + xyz(at), 'overwrite=1',
                 'note=%s（階段十二 draft_guns.py）；子作品座標 x 寬、y 砲身（砲口 +y）、z 0 甲板面' % T['title']])
        print('anchors', T['work'], len(T['anchors']))
elif step == 'models':
    for r in V['rows']:
        if not flt.search(r['host_link'] + '/' + r['model']): continue
        T = V['types'][r['type']]
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + r['host_work'], 'name=' + r['model'], 'source_work=' + T['work'],
             'at=' + xyz(r['at']), 'pivot=' + xyz(T['pivot']), 'rotate=' + xyz(r['rotate']), 'scale=%g' % V['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
             'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True),
             'note=%s（階段十二：退到零碰撞；pivot ＝ 砲架前緣中間、甲板面）' % T['title']])
        print('model', r['host_link'] + '/' + r['model'], xyz(r['at']), r['rotate'], r['mirror'])
else:
    raise SystemExit('步驟？ create|stamp|anchors|models')
print(step, 'ok', ok, 'bad', bad)
