# 出處：gura-pinas-01m/design/tools/hull_expected.py（藍鯊號 TASK-0967；2026-11-18 pinnacle 抄給金冠號 TASK-1317，作品 id／persona／船名／作品框已換）
# 出處：calli-cosecha-01m/design/tools/hull_expected.py（收穫號，照抄後改成金冠號 —— TASK-1317）
# 船殼設計帳：照清單組出船殼該有的樣子 ＝ hull_01＋hull_02（draft_lines）− hull_fix（船樓橫桿）− 砲門刻 ＋ 塗裝換色 − 艏斜桅孔 − 側廊窗洞
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
hull_dir = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--hull=')), os.path.join(design, 'masks', 'hull'))
for f in sorted(fn for fn in os.listdir(hull_dir) if fn.startswith('hull_') and fn.endswith('.vox.txt')):   # 金冠號：船殼清單 3 份（藍鯊號寫死 01、02）；--hull= 拿舊清單組控制組
    H.update(load(os.path.join(hull_dir, f)))
n0 = len(H)
steps = [('hull_fix', os.path.join(design, 'masks', 'hull_fix', 'carve_breaks.vox.txt'), 'carve'),
         ('砲門刻', os.path.join(ports, 'carve.vox.txt'), 'carve'),
         ('塗裝', os.path.join(ports, 'paint.vox.txt'), 'paint'),
         ('艏斜桅孔', os.path.join(design, 'masks', 'bowsprit_hole', 'carve.vox.txt'), 'carve'),
         ('側廊窗洞', os.path.join(design, 'masks', 'deco', 'gallery_carve.vox.txt'), 'carve'),
         ('船頭補實', os.path.join(ports, 'bow_fill.vox.txt'), 'add')]          # TASK-1317 船頭 v2：draft_ports.py 的 ports.bow_gangway（艏柱裡面除了走道填實）   # draft_deco.py 側廊 v2（2026-10-26）：側廊窗玻璃後面刻穿船殼的牆到艙裡
print('船殼 %d' % n0)
for nm, p, kind in steps:
    if not os.path.exists(p):          # 金冠號沒有 hull_fix；艏斜桅孔在步驟 7 才有
        print('  · %s：沒有清單，跳過' % nm)
        continue
    L = load(p)
    miss = [k for k in L if k not in H]
    if kind == 'carve':
        guard = sum(1 for k in L if k in H and H[k] != L[k])
        for k in L:
            H.pop(k, None)
        print('  − %s %d（不在船殼裡 %d、守門色不同 %d）' % (nm, len(L), len(miss), guard))
    elif kind == 'add':
        clash = sum(1 for k in L if k in H)
        H.update(L)
        print('  ＋ %s %d（本來就在船殼裡 %d）' % (nm, len(L), clash))
    else:
        for k, c in L.items():
            if k in H:
                H[k] = c
        print('  ＊ %s %d（不在船殼裡 %d）' % (nm, len(L), len(miss)))
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 金冠號 船殼設計帳（tools/hull_expected.py）\n')
    for k in sorted(H):
        f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], H[k]))
print('＝ %d → %s' % (len(H), out))
