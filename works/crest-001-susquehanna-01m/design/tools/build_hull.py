# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/build_hull.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 船殼＋鐵甲帶落格（kaguya 自己寫的；拿破崙號是先貼船殼、再刻砲門、再換色三步 —— 本船從零開始，直接貼最終狀態）
#   蘇士奎哈納號改：木殼、沒有鐵甲帶 ⇒ 最終 ＝ mio.hull_now（船殼清單 − 砲門刻 ＋ 換色）整份落在船殼作品。
#   ⇒ masks/build/hull_NN.vox.txt，照順序 stampvox、每刀讀回 placed。
#   用法：python -I -X utf8 tools/build_hull.py <design> [--lists-only]
import os, sys, re, json, hashlib, subprocess
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
sys.path.insert(0, design)
import mio

HULL = 'crest-001-susquehanna-01m'
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
bk = set()   # 蘇士奎哈納號改：木殼、沒有鐵甲帶 ⇒ 船殼 ＝ hull_now 全部
is_armor = np.zeros(len(H), bool)
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
    n, h = write(p, hull[k:k + CH].tolist(), '# 蘇士奎哈納號 船殼（tools/build_hull.py：hull_now）x,y,z,color；at 0,0,0\n')
    files.append((p, n, h))
R['lists'] = [[os.path.basename(p), n, h] for p, n, h in files]
print(json.dumps(R, ensure_ascii=False))
json.dump(R, open(os.path.join(od, 'build_hull.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
if ONLY:
    sys.exit(0)


def stamp(work, path, n):
    out = cli('op=stampvox', 'persona=crest-001', 'work=' + work, 'voxels=' + path.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  stampvox %s → %s：%d ✓' % (os.path.basename(path), work, n), flush=True)


works = os.path.dirname(os.path.dirname(design))
cli('op=work', 'sub=mark', 'persona=crest-001', 'work=' + HULL, 'name=船殼', 'phase=begin', 'upto=start', ok=(0, 2))
for p, n, h in files:
    stamp(HULL, p, n)
cli('op=work', 'sub=mark', 'persona=crest-001', 'work=' + HULL, 'name=船殼', 'phase=end')
WL = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['waterline']['z']
cli('op=work', 'sub=link', 'persona=crest-001', 'work=' + ASM, 'name=船殼', 'source_work=' + HULL, 'at=0,0,0', 'note=階段一',
    'meta=' + json.dumps({'kind': 'ship', 'waterline_z': WL}), ok=(0, 2))
for nm, want in (('船殼', {'kind': 'ship', 'waterline_z': WL}),):   # 讀回：關聯 meta 真的寫進去了
    cli('op=work', 'sub=meta', 'persona=crest-001', 'work=' + ASM, 'part=link', 'name=' + nm, 'meta=' + json.dumps(want))
print('✓ 關聯 船殼（kind=ship）')
