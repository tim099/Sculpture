# 砲塔實驗號（TASK-0659 第一期的測試船，只在 worktree 匯入、不進版控）：
#   莫尼特號（改裝船：原船拿掉「砲塔」）＋實驗砲塔（kind=turret）：圓筒、頂、吊籃地板（會轉的甲板，中間留半徑 8 的洞給艙口梯）、
#   彈藥箱（kind=magazine，借哨兵號的備便彈藥櫃）、兩門 XI 吋（固定在砲塔上）、頂上偏後 10 格疊一座小砲塔（kind=turret：底盤＋前面一塊砲盾，
#   上面一門三叉戟砲自己會轉 mount=turret arc ±60）。
# 用法：python -I -X utf8 apply_lab.py
import sys, os, json, subprocess, shutil, tempfile, math
S = shutil.which('senate'); PER = 'meadow'
WORKS = 'D:/Unity/Valhalla/Sculpture/works'
SHIP = 'meadow-turretlab-01m'; TUR = 'meadow-turretlab-turret'; FLOOR = 'meadow-turretlab-floor'; TOP = 'meadow-turretlab-top'
COL = 36


def run(*a, ok_codes=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok_codes: print((p.stdout + p.stderr)[-1500:]); sys.exit(1)
    return p.stdout


def names(wid, fn, key):
    f = os.path.join(WORKS, wid, fn)
    return [x['name'] for x in json.load(open(f, encoding='utf-8'))[key]] if os.path.exists(f) else []


def work(wid, title, size, parent):
    if not os.path.exists(os.path.join(WORKS, wid, 'work.json')):
        a = [('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', wid), ('title', title), ('size', size), ('tags', 'sub,lab' if parent else 'lab')]
        if parent: a.append(('parent_work', parent))
        run(*a)
    run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', wid), ('meters_per_voxel', '0.1'), ('size', size))


def stamp(wid, cells):
    tmp = tempfile.mkdtemp(prefix='lab_'); fn = os.path.join(tmp, 'v.txt').replace(os.sep, '/')
    cur = os.path.join(tmp, 'cur.txt').replace(os.sep, '/')
    run(('op', 'export'), ('format', 'list'), ('work', wid), ('out', cur), ('links', 'none'))
    have = sum(1 for l in open(cur, encoding='utf-8') if l.strip() and l[0] != '#') if os.path.exists(cur) else 0
    if have: print('  %s 已經有 %d 格 ⇒ 不再貼' % (wid, have)); return
    open(fn, 'w').write('\n'.join('%d,%d,%d,%d' % c for c in cells) + '\n')
    run(('op', 'stampvox'), ('persona', PER), ('work', wid), ('at', '0,0,0'), ('voxels', fn), ('expect_pixels', str(len(cells))), ('share', '0'))
    print('  %s 貼 %d 格' % (wid, len(cells)))


def link(wid, nm, src, at, meta, extra=()):
    a = [('op', 'work'), ('sub', 'link'), ('persona', PER), ('work', wid), ('name', nm), ('source_work', src), ('at', at), ('meta', json.dumps(meta, ensure_ascii=False))] + list(extra)
    if nm in names(wid, 'links.json', 'links'): a.append(('overwrite', '1'))
    run(*a); print('  關聯 %s/%s' % (wid, nm))


def model(wid, nm, src, at, pivot, rotate, scale, meta, mirror=''):
    a = [('op', 'work'), ('sub', 'model'), ('persona', PER), ('work', wid), ('name', nm), ('source_work', src), ('at', at), ('pivot', pivot), ('rotate', rotate), ('scale', scale), ('meta', json.dumps(meta, ensure_ascii=False))]
    if mirror: a.append(('mirror', mirror))
    if nm in names(wid, 'models.json', 'models'): a.append(('overwrite', '1'))
    run(*a); print('  模型 %s/%s' % (wid, nm))


def anchor(wid, nm, at):
    run(('op', 'work'), ('sub', 'anchor'), ('persona', PER), ('work', wid), ('name', nm), ('at', at), ok_codes=(0, 1))


# 組裝件（改裝船：原船拿掉砲塔）
work(SHIP, '砲塔實驗號（TASK-0659 測試船：吊籃、彈藥箱、疊層砲塔）', '544,131,80', None)
work(TUR, '砲塔實驗號 實驗砲塔', '65,65,40', 'meadow-monitor-01m-assembly')
work(FLOOR, '砲塔實驗號 吊籃地板（半徑 28、中間留 8）', '65,65,1', 'meadow-monitor-01m-assembly')
work(TOP, '砲塔實驗號 頂上的小砲塔（底盤＋砲盾）', '21,21,10', 'meadow-monitor-01m-assembly')
stamp(FLOOR, [(x, y, 0, COL) for x in range(65) for y in range(65) if 8 <= math.hypot(x + 0.5 - 32.5, y + 0.5 - 32.5) <= 28])
top = [(x, y, 0, COL) for x in range(21) for y in range(21) if math.hypot(x + 0.5 - 10.5, y + 0.5 - 10.5) <= 7]
top += [(x, y, z, COL) for x in (2, 3) for y in range(5, 16) for z in range(1, 7)]   # 前面（−x）一塊砲盾
stamp(TOP, top)
anchor(TUR, 'pivot', '32,32,0'); anchor(TUR, 'front', '0,32,0')
anchor(TOP, 'pivot', '10,10,0'); anchor(TOP, 'front', '0,10,0')
link(TUR, '裝甲', 'meadow-monitor-01m-turret-armor', '0,0,0', {'material': 'iron', 'render': 'smooth'})
link(TUR, '頂', 'meadow-monitor-01m-turret-roof', '0,0,28', {'material': 'iron'})
link(TUR, '吊籃', FLOOR, '0,0,0', {'material': 'iron'})
link(TUR, '彈藥箱', 'meadow-sentinel-01m-locker', '46,26,1', {'kind': 'magazine', 'material': 'iron', 'pos': 'mid'})
link(TUR, '頂砲塔', TOP, '12,22,30', {'kind': 'turret', 'arc': '-180,180', 'rate': 30, 'material': 'iron'})
for nm, mir in (('砲-a', ''), ('砲-b', 'x')):
    model(TUR, nm, 'meadow-monitor-01m-turret-gun', '32.5,32.5,0', '66.5,66.5,0', '0,0,90', '0.5,0.5,0.5', {'kind': 'gun', 'gun': '11d'}, mir)
model(TOP, '速射砲', 'gura-tridente-01m-gun-trident', '10.5,10.5,1', '16.5,34,0', '0,0,90', '0.5,0.5,0.5',
      {'kind': 'gun', 'gun': 'trident', 'barrels': 3, 'deck': 'main', 'mount': 'turret', 'arc': '-60,60', 'rate': 40, 'pivot': 11})
link(SHIP, '原船', 'meadow-monitor-01m-assembly', '0,0,0', {}, (('link_hide', '砲塔'),))
link(SHIP, '砲塔', TUR, '269,33,35', {'kind': 'turret', 'arc': '-180,180', 'fire': '-174,174', 'rate': 16})
print('done')
