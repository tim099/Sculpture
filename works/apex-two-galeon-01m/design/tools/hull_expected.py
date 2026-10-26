# 直接出處：gura-pinas-01m/design/tools/hull_expected.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成康塞普西翁號（TASK-0969）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/tools/hull_expected.py（收穫號，照抄後改成康塞普西翁號 —— TASK-0969）
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
for f in sorted(os.listdir(os.path.join(design, 'masks', 'hull'))):      # 康塞普西翁號：船殼清單有三份（hull_01..03）⇒ 讀全部
    if f.startswith('hull_') and f.endswith('.vox.txt'):
        H.update(load(os.path.join(design, 'masks', 'hull', f)))
n0 = len(H)
steps = [('hull_fix', os.path.join(design, 'masks', 'hull_fix', 'carve_breaks.vox.txt'), 'carve'),
         ('砲門刻', os.path.join(ports, 'carve.vox.txt'), 'carve'),
         ('塗裝', os.path.join(ports, 'paint.vox.txt'), 'paint'),
         ('艏斜桅孔', os.path.join(design, 'masks', 'bowsprit_hole', 'carve.vox.txt'), 'carve'),
         ('側廊窗洞', os.path.join(design, 'masks', 'deco', 'gallery_carve.vox.txt'), 'carve')]   # draft_deco.py 側廊 v2（2026-10-26）：側廊窗玻璃後面刻穿船殼的牆到艙裡
print('船殼 %d' % n0)
for nm, p, kind in steps:
    if not os.path.exists(p):          # 康塞普西翁號沒有 hull_fix；艏斜桅孔在步驟 7 才有
        print('  · %s：沒有清單，跳過' % nm)
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
    f.write('# 康塞普西翁號 船殼設計帳（tools/hull_expected.py）\n')
    for k in sorted(H):
        f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], H[k]))
print('＝ %d → %s' % (len(H), out))
