# 建子作品（沒有才建）＋把格子同步成產生程式的清單（刻掉多的與換色的、補上缺的；重跑只動差的那幾格）。
# 用法：python -I -X utf8 apply_build.py <out 資料夾（gen_monitor／gen_turret 的輸出）> [部件…]
import sys, os, json, subprocess, shutil, tempfile
out = sys.argv[1]; ONLY = set(sys.argv[2:])
S = shutil.which('senate'); W = 'meadow-monitor-01m'; PER = 'meadow'
WORKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')


def run(*a, ok_codes=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok_codes: print((p.stdout + p.stderr)[-900:]); sys.exit(1)
    return p.stdout


def fwd(p): return p.replace(os.sep, '/')


# 部件 → (作品 ID, 名稱, 清單檔, 尺寸, 一格幾公尺)
HULL = '544,131,80'; TUR = '133,133,60'
PARTS = [
    ('hull', W, '莫尼特號 船殼', 'part_hull.txt', HULL, 0.1),
    ('raft-iron', W + '-raft-iron', '莫尼特號 浮筏鐵甲（5×1 in）', 'part_raft-iron.txt', HULL, 0.1),
    ('raft-wood', W + '-raft-wood', '莫尼特號 浮筏橡木背襯與底板', 'part_raft-wood.txt', HULL, 0.1),
    ('deck-main', W + '-deck-main', '莫尼特號 主甲板（鐵板＋木、樑）', 'part_deck-main.txt', HULL, 0.1),
    ('deck-berth', W + '-deck-berth', '莫尼特號 住艙甲板', 'part_deck-berth.txt', HULL, 0.1),
    ('pilothouse', W + '-pilothouse', '莫尼特號 駕駛塔', 'part_pilothouse.txt', HULL, 0.1),
    ('funnel', W + '-funnel', '莫尼特號 煙囪（右舷；左舷鏡像）', 'part_funnel.txt', HULL, 0.1),
    ('boilers', W + '-boilers', '莫尼特號 鍋爐（右舷一座＋煙道；左舷鏡像）', 'part_boilers.txt', HULL, 0.1),
    ('engine', W + '-engine', '莫尼特號 振動槓桿式主機', 'part_engine.txt', HULL, 0.1),
    ('shaft', W + '-shaft', '莫尼特號 螺旋槳軸', 'part_shaft.txt', HULL, 0.1),
    ('screw', W + '-screw', '莫尼特號 螺旋槳（四葉 9 ft）', 'part_screw.txt', HULL, 0.1),
    ('deck-fittings', W + '-deck-fittings', '莫尼特號 鼓風機進氣管', 'part_deck-fittings.txt', HULL, 0.1),
    ('magazine', W + '-magazine', '莫尼特號 彈藥庫（右舷、鐵牆襯鉛）', 'part_magazine.txt', HULL, 0.1),
    ('cabins', W + '-cabins', '莫尼特號 艙房（軍官艙、砲彈艙、廚房爐）', 'part_cabins.txt', HULL, 0.1),
    ('ladders', W + '-ladders', '莫尼特號 梯子', 'part_ladders.txt', HULL, 0.1),
    ('turret-gun', W + '-turret-gun', '莫尼特號 XI 吋 Dahlgren＋Ericsson 滑架（砲塔的框，0.05 m）', 'turret_gun.txt', TUR, 0.05),
    ('turret-shell', W + '-turret-shell', '莫尼特號 砲塔圓筒與頂（0.05 m）', 'turret_shell.txt', TUR, 0.05),
    ('turret', W + '-turret', '莫尼特號 砲塔（整座：圓筒＋兩門砲，0.05 m）', None, TUR, 0.05),
]
ASM = (W + '-assembly', '莫尼特號')


def exists(wid): return os.path.exists(os.path.join(WORKS, wid, 'work.json'))


def ensure(wid, title, size, mpv, tags):
    if not exists(wid):
        run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', wid), ('title', title), ('parent_work', W), ('size', size), ('tags', tags))
        print('＋ 建立', wid)
    run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', wid), ('meters_per_voxel', str(mpv)), ('size', size), ('tags', tags), ('title', title))


def load(f):
    d = {}
    for l in open(f, encoding='utf-8'):
        l = l.strip()
        if not l or l[0] == '#': continue
        a = l.split(','); d[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return d


def sync(wid, listfile):
    tmp = tempfile.mkdtemp(prefix='msync_'); cur = fwd(os.path.join(tmp, 'cur.txt'))
    run(('op', 'export'), ('format', 'list'), ('work', wid), ('out', cur), ('links', 'none'))
    old = load(cur) if os.path.exists(cur) else {}
    new = load(listfile)
    rm = [k for k, c in old.items() if new.get(k) != c]
    add = [k for k, c in new.items() if old.get(k) != c]
    print('%s：現在 %d、新的 %d ⇒ 刻 %d、補 %d' % (wid, len(old), len(new), len(rm), len(add)))
    for name, lst, op in (('rm', rm, 'carvevox'), ('add', add, 'stampvox')):
        for i in range(0, len(lst), 900000):
            part = lst[i:i + 900000]; fn = fwd(os.path.join(tmp, '%s%d.txt' % (name, i)))
            with open(fn, 'w') as f:
                f.write('\n'.join('%d,%d,%d,%d' % (k[0], k[1], k[2], old[k] if op == 'carvevox' else new[k]) for k in part) + '\n')
            o = run(('op', op), ('persona', PER), ('work', wid), ('at', '0,0,0'), ('voxels', fn), ('expect_pixels', str(len(part))), ('share', '0'))
            got = [l for l in o.splitlines() if 'placed' in l or 'carved' in l][:1]
            print('  %s %d ✓ %s' % (op, len(part), got[0].strip() if got else ''))


# 船殼（任務作品）先記比例與尺寸
run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', W), ('meters_per_voxel', '0.1'), ('size', HULL), ('tags', 'sub'))
if not exists(ASM[0]):
    run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', ASM[0]), ('title', ASM[1]), ('parent_work', W), ('size', HULL))
    print('＋ 建立', ASM[0])
run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', ASM[0]), ('meters_per_voxel', '0.1'), ('size', HULL), ('tags', ''))
for key, wid, title, lf, size, mpv in PARTS:
    if ONLY and key not in ONLY: continue
    if wid != W: ensure(wid, title, size, mpv, 'sub')
    if lf: sync(wid, os.path.join(out, lf))
print('done')
