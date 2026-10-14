# 階段十三：照 verify_magazine.json、verify_ladders.json 下 CLI —— 彈藥庫（子作品、格、固定點、關聯、火藥桶）＋梯子（子作品、格、船殼缺口、關聯、扶手柱頂、扶手繩）
# 用法：python -I -X utf8 -B apply_stage13.py <design 資料夾> <步驟>
#   步驟：mag_create｜mag_stamp｜mag_anchors｜mag_link｜mag_kegs｜lad_create｜lad_stamp｜lad_carve｜lad_link｜lad_anchors｜lad_ropes
#   · 格的那幾步只跑一次（每刀讀回 placed）；其餘 overwrite=1。梯子給遊戲的 foot／lo／hi／head 用 basecamp 餘燼號 design/tools/ladder_points.py 另外算、登記。
#   · ⛔ 失敗那一行整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
VM = json.load(open(os.path.join(D, 'verify_magazine.json'), encoding='utf-8'))
VL = json.load(open(os.path.join(D, 'verify_ladders.json'), encoding='utf-8'))
PRE = 'summit-stormkaap-01m'; ASM = PRE + '-assembly'
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


def create(work, title, size):
    rc, _ = cli(['op=work', 'sub=show', 'work=' + work], quiet_fail=True)
    if rc == 0: print('已有', work)
    else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + work, 'title=' + title, 'size=' + xyz(size), 'parent_work=' + PRE, 'tags=sub']); print('建立', work)
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + work, 'meters_per_voxel=0.1'])


def stamp(work, o):
    rc, out = cli(['op=' + o['op'], 'persona=summit', 'work=' + work, 'voxels=' + fwd(o['file']), 'at=0,0,0', 'expect_pixels=%d' % o['voxels'], 'draft=0'])
    m = re.search(r'🔢 placed = (\d+)', out)
    print(o['name'], o['op'], work, 'voxels', o['voxels'], 'placed', m.group(1) if m else '?')


fa = VM['frame_at']
if step == 'mag_create':
    create(VM['work'], VM['title'], VM['frame_size'])
elif step == 'mag_stamp':
    for o in VM['stamp_order']['magazine']: stamp(VM['work'], o)
elif step == 'mag_anchors':
    for a in VM['anchors']:
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + VM['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
             'note=給遊戲（階段十三）；世界座標 %s' % xyz(a['world'])])
elif step == 'mag_link':
    L = VM['link']
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=' + L['name'], 'source_work=' + VM['work'], 'at=' + xyz(L['at']), 'overwrite=1',
         'meta=' + json.dumps(L['meta'], ensure_ascii=False, sort_keys=True), 'note=階段十三 彈藥庫'])
elif step == 'mag_kegs':
    K = VM['kegs']
    for i, w in enumerate(K['at_world'], 1):
        at = [w[0] - fa[0], w[1] - fa[1], w[2] - fa[2]]
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + VM['work'], 'name=桶-%02d' % i, 'source_work=' + K['source_work'], 'at=' + xyz(at),
             'pivot=' + xyz(K['pivot']), 'rotate=0,0,0', 'scale=%g' % K['scale'], 'overwrite=1', 'meta=' + json.dumps(K['meta'], ensure_ascii=False, sort_keys=True),
             'note=火藥桶（basecamp 憲法號 -powder-barrel 引用；階段十三）'])
    print('kegs', len(K['at_world']))
elif step == 'lad_create':
    create(VL['work'], VL['title'], [736, 261, 576])
elif step == 'lad_stamp':
    for o in VL['stamp_order']['ladders']: stamp(VL['work'], o)
elif step == 'lad_carve':
    for o in VL['stamp_order']['hull']: stamp(o['work'], o)
elif step == 'lad_link':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + VL['link_in'], 'name=' + VL['link'], 'source_work=' + VL['work'], 'at=0,0,0', 'overwrite=1',
         'meta=' + json.dumps({'kind': 'ladders'}), 'note=階段十三 梯子（給遊戲 kind=ladders）'])
elif step == 'lad_anchors':
    for a in VL['anchors']:
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + VL['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1', 'note=' + a['note']])
    print('anchors', len(VL['anchors']))
elif step == 'lad_ropes':
    for r in VL['ropes']:
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=扶手繩（階段十三）'])
    print('ropes', len(VL['ropes']))
elif step == 'lad_points':
    n = 0
    for lid, P_ in sorted(VL['points'].items()):
        for k in ('foot', 'lo', 'hi', 'head'):
            assert P_[k] is not None, (lid, k)
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + VL['work'], 'name=%s.%s' % (lid, k), 'at=' + xyz(P_[k]), 'overwrite=1',
                 'note=梯子給遊戲的點（draft_ladders.py 照 basecamp 餘燼號 ladder_points.py 的規則算；造船規格 §9）'])
            n += 1
    print('points', n)
else:
    raise SystemExit('步驟？')
print(step, 'ok', ok, 'bad', bad)
