# 澤漢號：出處 ame-labelle-01m/design/tools/hull_expected.py（拉貝爾號；它出自收穫號）；本船多三步：裝飾換色、窗玻璃拆走（色 glass 的格整個搬到 -stern-glass）、玻璃後面刻穿。
# 船殼設計帳：照清單組出船殼該有的樣子 ＝ hull_01＋hull_02（draft_lines）− hull_fix（船樓橫桿）− 砲門刻 ＋ 塗裝換色 − 艏斜桅孔
#   用法：python -I -X utf8 tools/hull_expected.py <design> <輸出清單> [--ports=<放 carve／paint 清單的資料夾>]（不給 ⇒ masks/ports）
#   · 階段八加高主甲板砲門時寫的：先拿舊的砲門清單組 ⇒ 要跟作品逐格相同（證明帳組得對），再拿新的組 ⇒ delta_apply 套到作品
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
design, out = sys.argv[1], sys.argv[2]
ports = next((a.split('=', 1)[1] for a in sys.argv[3:] if a.startswith('--ports=')), os.path.join(design, 'masks', 'ports'))


def load(p):
    d = {}
    for l in open(p, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            d[(x, y, z)] = c
    return d


H = {}
for f in ('hull_01.vox.txt', 'hull_02.vox.txt'):
    if os.path.exists(os.path.join(design, 'masks', 'hull', f)):
        H.update(load(os.path.join(design, 'masks', 'hull', f)))
n0 = len(H)
steps = [('hull_fix', os.path.join(design, 'masks', 'hull_fix', 'carve_breaks.vox.txt'), 'carve'),
         ('砲門刻', os.path.join(ports, 'carve.vox.txt'), 'carve'),
         ('塗裝', os.path.join(ports, 'paint.vox.txt'), 'paint'),
         ('艏斜桅孔', os.path.join(design, 'masks', 'bowsprit_hole', 'carve.vox.txt'), 'carve'),
         ('裝飾換色', os.path.join(design, 'masks', 'deco', 'paint.vox.txt'), 'paint'),
         ('窗玻璃拆走', None, 'split'),
         ('玻璃後面', os.path.join(design, 'masks', 'glass', 'carve_behind.vox.txt'), 'carve')]
GLASS = __import__('json').load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['paint']['glass']
print('船殼 %d' % n0)
for nm, p, kind in steps:
    if kind == 'split':
        ks = [k for k, c in H.items() if c == GLASS]
        for k in ks:
            del H[k]
        print('  − %s %d（色 %d）' % (nm, len(ks), GLASS))
        continue
    if not os.path.exists(p):
        print('  （%s 沒有清單，跳過）' % nm)
        continue
    L = load(p)
    miss = [k for k in L if k not in H]
    if kind == 'carve':
        guard = sum(1 for k in L if k in H and H[k] != L[k])
        for k in L:
            H.pop(k, None)
        print('  − %s %d（不在船殼裡 %d、守門色不同 %d）' % (nm, len(L), len(miss), guard))
    else:
        for k, c in L.items():
            if k in H:
                H[k] = c
        print('  ＊ %s %d（不在船殼裡 %d）' % (nm, len(L), len(miss)))
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 澤漢號 船殼設計帳（tools/hull_expected.py）\n')
    for k in sorted(H):
        f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], H[k]))
print('＝ %d → %s' % (len(H), out))
