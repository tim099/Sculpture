# 船殼設計帳：照清單組出船殼該有的樣子 ＝ hull_01＋hull_02（draft_lines）− hull_fix（船樓橫桿）− 砲門刻 ＋ 塗裝換色 − 艏斜桅孔
#   用法：python -I -X utf8 tools/hull_expected.py <design> <輸出清單> [--ports=<放 carve／paint 清單的資料夾>]（不給 ⇒ masks/ports）
#   · 階段八加高主甲板砲門時寫的：先拿舊的砲門清單組 ⇒ 要跟作品逐格相同（證明帳組得對），再拿新的組 ⇒ delta_apply 套到作品
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
design, out = sys.argv[1], sys.argv[2]
ports = next((a.split('=', 1)[1] for a in sys.argv[3:] if a.startswith('--ports=')), os.path.join(design, 'masks', 'ports'))
# --skip=hull_fix（TASK-1027）：船殼重產之後不刻 hull_fix —— 那份是階段二 EXTRA 12 時代的橫桿，現在的 draft_lines（EXTRA 60）本來就沒有（舊清單裡 0 格）；
#   新的舷頂 S 形讓其中 10 格（x 195／196、dy ±44、z 129–133）變成真的舷牆，照刻會在 toldilla 前緣開洞
skip = set(next((a.split('=', 1)[1] for a in sys.argv[3:] if a.startswith('--skip=')), '').split(',')) - {''}


def load(p):
    d = {}
    for l in open(p, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            d[(x, y, z)] = c
    return d


H = {}
for f in sorted(os.listdir(os.path.join(design, 'masks', 'hull'))):      # TASK-1027：船頭船尾重畫之後船殼可能變三份清單 ⇒ 讀全部 hull_*（照康塞普西翁號）
    if f.startswith('hull_') and f.endswith('.vox.txt'):
        H.update(load(os.path.join(design, 'masks', 'hull', f)))
n0 = len(H)
steps = [('hull_fix', os.path.join(design, 'masks', 'hull_fix', 'carve_breaks.vox.txt'), 'carve'),
         ('砲門刻', os.path.join(ports, 'carve.vox.txt'), 'carve'),
         ('塗裝', os.path.join(ports, 'paint.vox.txt'), 'paint'),
         ('艏斜桅孔', os.path.join(design, 'masks', 'bowsprit_hole', 'carve.vox.txt'), 'carve')]
print('船殼 %d' % n0)
for nm, p, kind in steps:
    if nm in skip:
        print('  · %s：--skip，不套' % nm)
        continue
    if not os.path.exists(p):
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
    f.write('# 收穫號 船殼設計帳（tools/hull_expected.py）\n')
    for k in sorted(H):
        f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], H[k]))
print('＝ %d → %s' % (len(H), out))
