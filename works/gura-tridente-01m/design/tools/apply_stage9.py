# 階段九落格（TASK-0562）：照 magazines_placement.json／verify_fittings.json 下 CLI
#   magazines：每間一件子作品（0.1 m、parent 船殼、tags sub；已在且格數對 ⇒ 不重落）→ 固定點 blast／door → 子作品裡掛火藥桶模型（憲法號 -powder-barrel、
#              scale 0.2、meta kind=powder／powder_lb=100）→ 組裝件關聯 彈藥庫-前／後（meta kind=magazine、pos、powder_lb ＝ 桶數 × 100）
#   fittings：甲板-spar 掛舵輪、羅經櫃、主絞盤、小艇（meta 照造船規格 §9）；組裝件掛舵索 2 條（組 steering）
#   用法：python -I -X utf8 tools/apply_stage9.py <design> magazines|fittings
#   · 改自餘燼號 magazine_mid_apply.py、wheel_apply.py（basecamp）；IOException 中英文訊息都重試
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
HULL, ASM = 'gura-tridente-01m', 'gura-tridente-01m-assembly'
ok = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, retried
    for k in range(5):
        r = run(args)
        out = r.stdout + r.stderr
        if r.returncode and any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 4:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        print('✗ rc=%d' % r.returncode, ' '.join(args[:6]))
        print(out[-1200:])
        raise SystemExit(1)
    ok += 1
    return r.stdout


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


if step == 'magazines':
    PL = json.load(open(os.path.join(D, 'magazines_placement.json'), encoding='utf-8'))
    for key, R in sorted(PL['rooms'].items()):
        W = R['work']
        vox = os.path.join(D, 'masks', 'magazines', key + '.vox.txt').replace('\\', '/')
        if run(['op=work', 'sub=show', 'work=' + W]).returncode != 0:
            cli(['op=work', 'sub=create', 'persona=gura', 'id=' + W, 'title=' + R['title'], 'size=' + xyz(R['size']), 'parent_work=' + HULL, 'tags=sub'])
            cli(['op=work', 'sub=update', 'persona=gura', 'work=' + W, 'meters_per_voxel=0.1'])
        have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
        if have == 0:
            out = cli(['op=stampvox', 'persona=gura', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % R['cells'], 'share=0'])
            n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
            if n != R['cells']:
                raise SystemExit('✗ %s placed %d ≠ %d' % (W, n, R['cells']))
        elif have != R['cells']:
            raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (W, have, R['cells']))
        for name, p in sorted(R['anchors'].items()):
            cli(['op=work', 'sub=anchor', 'persona=gura', 'work=' + W, 'name=' + name, 'at=' + xyz(p), 'overwrite=1',
                 'note=' + ('爆心：房間內空氣重心最近的一格' if name == 'blast' else '門洞地板中線（朝船中那道艙壁）')])
        s = PL['barrel_scale']
        meta_b = json.dumps({'kind': 'powder', 'powder_lb': 100})
        for i, b in enumerate(R['barrels']):
            cli(['op=work', 'sub=model', 'persona=gura', 'work=' + W, 'name=' + b['name'], 'source_work=' + PL['barrel_work'], 'at=' + xyz(b['at']),
                 'pivot=' + xyz(PL['barrel_pivot']), 'rotate=0,0,0', 'scale=' + xyz([s, s, s]), 'overwrite=1', 'meta=' + meta_b,
                 'note=火藥桶 第 %d 層（magazines_placement.json）' % b['tier']])
            if (i + 1) % 60 == 0:
                print('  %s 桶 %d／%d' % (key, i + 1, len(R['barrels'])), flush=True)
        lb = len(R['barrels']) * 100
        cli(['op=work', 'sub=link', 'persona=gura', 'work=' + ASM, 'name=' + R['link'], 'source_work=' + W, 'at=' + xyz(R['at']), 'overwrite=1',
             'note=%s（階段九 TASK-0562）' % R['title'], 'meta=' + json.dumps({'kind': 'magazine', 'pos': R['pos'], 'powder_lb': lb})])
        print('✓', key, W, '格', R['cells'], '桶', len(R['barrels']), '關聯', R['link'], R['at'])
elif step == 'fittings':
    V = json.load(open(os.path.join(D, 'verify_fittings.json'), encoding='utf-8'))
    for r in V['rows']:
        cli(['op=work', 'sub=model', 'persona=gura', 'work=gura-tridente-01m-deck-spar', 'name=' + r['model'], 'source_work=' + r['work'],
             'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=0,0,0', 'scale=%g' % r['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
             'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True), 'note=三叉戟號 %s（階段九 draft_fittings.py）' % r['type']])
        print('✓ 模型', r['model'], r['at'], r['mirror'])
    for rp in V['ropes']:
        cli(['op=work', 'sub=rope', 'persona=gura', 'work=' + ASM, 'name=' + rp['name'], 'from=' + rp['from'], 'to=' + rp['to'], 'color=' + rp['color'],
             'thickness=%g' % rp['thickness'], 'slack=%g' % rp['slack'], 'group=' + rp['group'], 'overwrite=1', 'note=舵索（階段九）'])
        print('✓ 繩', rp['name'])
    cli(['op=work', 'sub=meta', 'persona=gura', 'work=' + ASM, 'part=rope', 'name=wheel-rope-a', 'meta={"kind":"steering"}'])
    cli(['op=work', 'sub=meta', 'persona=gura', 'work=' + ASM, 'part=rope', 'name=wheel-rope-b', 'meta={"kind":"steering"}'])
else:
    raise SystemExit('步驟？ magazines|fittings')
print(step, 'ok', ok, 'IOException 重試', retried)
