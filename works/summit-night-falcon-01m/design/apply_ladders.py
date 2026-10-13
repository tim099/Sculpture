# 階段十九：照 verify_ladders.json 下 CLI —— 梯子子作品、甲板-後 底下的關聯（meta kind=ladders）、扶手柱頂固定點、扶手繩；
#   最後 points：把 ladder_points.py（basecamp 餘燼號那支，只算不寫）算出的 foot／lo／hi／head 登記成固定點
# 用法：python -I -X utf8 -B apply_ladders.py <design 資料夾> <步驟> [ladder_points 的 verify json]
#   步驟：create（parent 船殼、0.1 m）｜voxels（只跑一次）｜link｜anchors｜ropes｜points
#   · create 已存在 ⇒ 略過；link／anchors／ropes／points 用 overwrite=1；⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_ladders.json'), encoding='utf-8'))
PRE = 'summit-night-falcon-01m'
ASM = PRE + '-assembly'
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


xyz = lambda v: ','.join('%g' % c for c in v)
if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + V['work']])
    if rc == 0:
        print('已有', V['work'])
    else:
        bad -= 1
        cli(['op=work', 'sub=create', 'persona=summit', 'id=' + V['work'], 'title=' + V['title'], 'size=384,161,320', 'parent_work=' + PRE, 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + V['work'], 'meters_per_voxel=0.1'])
elif step == 'voxels':
    for o in V['stamp_order']['ladders']:
        rc, out = cli(['op=' + o['op'], 'persona=summit', 'work=' + V['work'], 'voxels=' + os.path.join(D, o['file']).replace('\\', '/'), 'at=0,0,0',
                       'expect_pixels=%d' % o['voxels'], 'draft=0'])
        m = re.search(r'🔢 placed = (\d+)', out)
        print(o['name'], o['op'], o['voxels'], 'placed', m.group(1) if m else '?')
elif step == 'link':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + V['link_in'], 'name=' + V['link'], 'source_work=' + V['work'], 'at=0,0,0', 'overwrite=1',
         'meta=' + json.dumps({'kind': 'ladders'}), 'note=階段十九 梯子（給遊戲 kind=ladders）'])
elif step == 'anchors':
    for a in V['anchors']:
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + V['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1', 'note=' + a['note']])
elif step == 'ropes':
    for r in V['ropes']:
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=扶手繩（階段十九）'])
elif step == 'points':
    LP = json.load(open(sys.argv[3], encoding='utf-8'))
    assert LP['assembly'] == ASM, LP['assembly']
    n = 0
    for L in LP['ladders']:
        assert L['ladder_work'] == V['work'], L['ladder_work']
        for k in ('foot', 'lo', 'hi', 'head'):
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + V['work'], 'name=%s.%s' % (L['ladder'], k), 'at=' + xyz(L[k]), 'overwrite=1',
                 'note=梯子給遊戲的點（basecamp 餘燼號 ladder_points.py 算；造船規格 §9）'])
            n += 1
    print('points', n)
else:
    raise SystemExit('步驟？ create|voxels|link|anchors|ropes|points')
print(step, 'ok', ok, 'bad', bad)
