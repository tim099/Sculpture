# 階段十八：照 verify_magazine.json 下 CLI —— 艙房地板的 lazarette 艙口、彈藥庫子作品＋組裝件關聯（meta kind=magazine）、固定點、火藥桶模型
# 用法：python -I -X utf8 -B apply_magazine.py <design 資料夾> <步驟>
#   步驟：create（-magazine，parent 船殼、0.1 m）｜voxels（主甲板 mark stage18 → 刻艙口；彈藥庫落格）｜anchors｜link｜kegs
#   · create 已存在 ⇒ 略過；anchors／link／kegs 用 overwrite=1；voxels 只跑一次；⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_magazine.json'), encoding='utf-8'))
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
fa = V['frame_at']
if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + V['work']])
    if rc == 0:
        print('已有', V['work'])
    else:
        bad -= 1
        cli(['op=work', 'sub=create', 'persona=summit', 'id=' + V['work'], 'title=夜隼號 彈藥庫（艙房地板底下；銅皮、松木地板）',
             'size=' + xyz(V['frame_size']), 'parent_work=' + PRE, 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + V['work'], 'meters_per_voxel=0.1'])
elif step == 'voxels':
    for key, w in (('main', PRE + '-deck-main'), ('magazine', V['work'])):
        if key == 'main':
            cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + w, 'name=stage18', 'phase=begin', 'note=階段十八：lazarette 艙口'])
        for o in V['stamp_order'][key]:
            rc, out = cli(['op=' + o['op'], 'persona=summit', 'work=' + w, 'voxels=' + os.path.join(D, o['file']).replace('\\', '/'), 'at=0,0,0',
                           'expect_pixels=%d' % o['voxels'], 'draft=0'])
            m = re.search(r'🔢 placed = (\d+)', out)
            print(key, o['name'], o['op'], o['voxels'], 'placed', m.group(1) if m else '?')
        if key == 'main':
            cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + w, 'name=stage18', 'phase=end', 'note=階段十八'])
elif step == 'anchors':
    for a in V['anchors']:
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + V['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
             'note=給遊戲（階段十八）；世界座標 %s' % xyz(a['world'])])
elif step == 'link':
    L = V['link']
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=' + L['name'], 'source_work=' + V['work'], 'at=' + xyz(L['at']), 'overwrite=1',
         'meta=' + json.dumps(L['meta'], ensure_ascii=False, sort_keys=True), 'note=階段十八 彈藥庫'])
elif step == 'kegs':
    K = V['kegs']
    for i, w in enumerate(K['at_world'], 1):
        at = [w[0] - fa[0], w[1] - fa[1], w[2] - fa[2]]
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + V['work'], 'name=桶-%02d' % i, 'source_work=' + K['source_work'], 'at=' + xyz(at),
             'pivot=' + xyz(K['pivot']), 'rotate=0,0,0', 'scale=%g' % K['scale'], 'overwrite=1', 'meta=' + json.dumps(K['meta'], ensure_ascii=False, sort_keys=True),
             'note=火藥桶（basecamp 憲法號 -powder-barrel 引用；階段十八）'])
    print('kegs', len(K['at_world']))
else:
    raise SystemExit('步驟？ create|voxels|anchors|link|kegs')
print(step, 'ok', ok, 'bad', bad)
