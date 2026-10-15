# 砲塔裝甲子模組（TASK-0631）：建 -turret-armor／-turret-roof、落格子、組裝件掛關聯（kind=armor、mount ＝ 砲塔模型路徑）、
# 砲塔模型的元件 -turret 拿掉圓筒（只剩兩門砲 ⇒ 模型外框只包砲、砲班站得進砲塔）。
# 用法：python -I -X utf8 apply_armor.py <out 資料夾（gen_armor 的輸出）>
import sys, os, json, subprocess, shutil
out = sys.argv[1]
A = json.load(open(os.path.join(out, 'armor_meta.json'), encoding='utf-8'))
S = shutil.which('senate'); W = 'meadow-monitor-01m'; ASM = W + '-assembly'; PER = 'meadow'
WORKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
MOUNT = '甲板-main/砲塔'


def run(*a, ok=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok: print((p.stdout + p.stderr)[-900:]); sys.exit(1)
    return p.stdout


PARTS = [('armor', '莫尼特號 砲塔裝甲（圓筒、8 層 1 in 鐵；跟著砲轉的裝甲子模組）', {'kind': 'armor', 'mount': MOUNT, 'material': 'iron', 'render': 'smooth'}, '砲塔裝甲'),
         ('roof', '莫尼特號 砲塔頂（鐵軌格柵、艙口蓋；跟著砲轉的裝甲子模組）', {'kind': 'armor', 'mount': MOUNT, 'material': 'iron'}, '砲塔頂')]
for key, title, meta, link in PARTS:
    wid = W + '-turret-' + key; d = A[key]
    size = '%d,%d,%d' % tuple(d['size'])
    if not os.path.exists(os.path.join(WORKS, wid, 'work.json')):
        run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', wid), ('title', title), ('parent_work', W), ('size', size), ('tags', 'sub'))
        print('＋ 建立', wid)
    run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', wid), ('meters_per_voxel', '0.1'), ('size', size), ('tags', 'sub'), ('title', title))
    fn = os.path.join(out, 'turret_%s.txt' % key).replace(os.sep, '/')
    tmp = os.path.join(out, 'cur_%s.txt' % key).replace(os.sep, '/')
    run(('op', 'export'), ('format', 'list'), ('work', wid), ('out', tmp), ('links', 'none'))
    have = sum(1 for l in open(tmp, encoding='utf-8') if l.strip() and l[0] != '#') if os.path.exists(tmp) else 0
    if have == 0:
        o = run(('op', 'stampvox'), ('persona', PER), ('work', wid), ('at', '0,0,0'), ('voxels', fn), ('expect_pixels', str(d['count'])), ('share', '0'))
        print('  stampvox', d['count'], [l.strip() for l in o.splitlines() if 'placed' in l][:1])
    else:
        print('  已有 %d 格（要重做先 carve；預期 %d）' % (have, d['count']))
    run(('op', 'work'), ('sub', 'link'), ('work', ASM), ('persona', PER), ('name', link), ('source_work', wid), ('at', '%d,%d,%d' % tuple(d['at'])),
        ('meta', json.dumps(meta, ensure_ascii=False)))
    print('✓ 關聯', link, d['at'], meta)
# 砲塔模型的元件只剩兩門砲
o = run(('op', 'work'), ('sub', 'links'), ('work', W + '-turret'))
if '圓筒' in o:
    run(('op', 'work'), ('sub', 'unlink'), ('work', W + '-turret'), ('persona', PER), ('name', '圓筒'))
    print('✓ -turret 拿掉圓筒')
print('done')
