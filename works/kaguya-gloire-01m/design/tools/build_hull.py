# 光榮號 船殼＋鐵甲帶落格（kaguya 自己寫的；拿破崙號是先貼船殼、再刻砲門、再換色三步 —— 本船從零開始，直接貼最終狀態）
#   最終 ＝ mio.hull_now（船殼清單 − 砲門刻 ＋ 換色）；其中鐵甲帶（masks/armor/belt_all.vox.txt 裡、沒被刻掉的格）另一件子作品。
#   ⇒ masks/build/hull_NN.vox.txt（船殼作品）、masks/build/armor.vox.txt（鐵甲帶子作品），再照順序 stampvox、每刀讀回 placed。
#   用法：python -I -X utf8 tools/build_hull.py <design> [--lists-only]
import os, sys, re, json, hashlib, subprocess
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
sys.path.insert(0, design)
import mio

HULL = 'kaguya-gloire-01m'
ARMOR = HULL + '-armor'
ASM = HULL + '-assembly'
ONLY = '--lists-only' in sys.argv


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def write(path, rows, head):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(head)
        for x, y, z, c in rows:
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    return len(rows), hashlib.sha256(open(path, 'rb').read()).hexdigest()


H = mio.hull_now(design)
belt = np.loadtxt(os.path.join(design, 'masks', 'armor', 'belt_all.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
bk = set(map(tuple, belt[:, :3].tolist()))
is_armor = np.array([(x, y, z) in bk for x, y, z in H[:, :3].tolist()])
hull, armor = H[~is_armor], H[is_armor]
od = os.path.join(design, 'masks', 'build')
os.makedirs(od, exist_ok=True)
for f in os.listdir(od):
    if f.endswith('.vox.txt'):
        os.remove(os.path.join(od, f))
files, R = [], {'hull_now': int(len(H)), 'hull': int(len(hull)), 'armor': int(len(armor)), 'belt_carved_by_ports': int(len(bk) - len(armor))}
CH = 300000
for k in range(0, len(hull), CH):
    p = os.path.join(od, 'hull_%02d.vox.txt' % (k // CH + 1))
    n, h = write(p, hull[k:k + CH].tolist(), '# 光榮號 船殼（tools/build_hull.py：hull_now − 鐵甲帶）x,y,z,color；at 0,0,0\n')
    files.append((p, n, h))
pa = os.path.join(od, 'armor.vox.txt')
na, ha = write(pa, armor.tolist(), '# 光榮號 鐵甲帶（tools/build_hull.py）x,y,z,color；at 0,0,0\n')
R['lists'] = [[os.path.basename(p), n, h] for p, n, h in files] + [['armor.vox.txt', na, ha]]
R['armor_colors'] = {int(c): int(n) for c, n in zip(*np.unique(armor[:, 3], return_counts=True))}
print(json.dumps(R, ensure_ascii=False))
json.dump(R, open(os.path.join(od, 'build_hull.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
if ONLY:
    sys.exit(0)


def stamp(work, path, n):
    out = cli('op=stampvox', 'persona=kaguya', 'work=' + work, 'voxels=' + path.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  stampvox %s → %s：%d ✓' % (os.path.basename(path), work, n), flush=True)


works = os.path.dirname(os.path.dirname(design))
if not os.path.exists(os.path.join(works, ARMOR, 'work.json')):
    cli('op=work', 'sub=create', 'persona=kaguya', 'id=' + ARMOR, 'title=光榮號 鐵甲帶（鍛鐵，舷側整條）', 'parent_work=' + HULL, 'size=1200,400,800', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=kaguya', 'work=' + ARMOR, 'meters_per_voxel=0.1')
    print('✓ 建立', ARMOR)
cli('op=work', 'sub=mark', 'persona=kaguya', 'work=' + HULL, 'name=船殼', 'phase=begin', 'upto=start', ok=(0, 2))
for p, n, h in files:
    stamp(HULL, p, n)
cli('op=work', 'sub=mark', 'persona=kaguya', 'work=' + HULL, 'name=船殼', 'phase=end')
stamp(ARMOR, pa, na)
WL = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['waterline']['z']
cli('op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=船殼', 'source_work=' + HULL, 'at=0,0,0', 'note=階段一',
    'meta=' + json.dumps({'kind': 'ship', 'waterline_z': WL}), ok=(0, 2))
# Tim 2026-10-15：「鐵甲部分記得用子模組標記材質（遊戲中才會有鋼鐵的防禦力）」⇒ 鐵甲帶是獨立一件子作品、關聯 meta material=iron（造船規格 §9.5）
cli('op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=鐵甲帶', 'source_work=' + ARMOR, 'at=0,0,0', 'note=階段一：鍛鐵甲帶 120 mm',
    'meta=' + json.dumps({'material': 'iron', 'render': 'smooth'}), ok=(0, 2))
for nm, want in (('船殼', {'kind': 'ship', 'waterline_z': WL}), ('鐵甲帶', {'material': 'iron', 'render': 'smooth'})):   # 讀回：關聯 meta 真的寫進去了
    cli('op=work', 'sub=meta', 'persona=kaguya', 'work=' + ASM, 'part=link', 'name=' + nm, 'meta=' + json.dumps(want))
print('✓ 關聯 船殼（kind=ship）、鐵甲帶（material=iron、render=smooth）')
