# TASK-1045：只把「新帳 − 舊帳」那一段差套到作品上 —— 作品後來在帳以外動過的格（窗玻璃拆件、玻璃後面刻穿、百合花換色）不會被帳蓋回去
#   用法：python -I -X utf8 tools/ledger_delta.py <design> <work> <舊帳> <新帳> <輸出清單>
#   · 輸出 ＝ 作品現在的格子，套上新舊帳的差（舊有新沒有 ⇒ 拿掉、新有舊沒有 ⇒ 加上、兩邊都有顏色不同 ⇒ 換色）；之後交給 tools/delta_apply.py
#   · 先對帳：差到的格子裡，作品跟舊帳不一樣的（舊帳說有、作品沒有；或顏色不同）逐格數出來 ⇒ 不是 0 就停（帳以外動過的地方剛好在這次要改的範圍裡）
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
design, work, old_p, new_p, out = sys.argv[1:6]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list


def load(p):
    d = {}
    for l in open(p, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            d[(x, y, z)] = c
    return d


old, new = load(old_p), load(new_p)
cw = {tuple(r[:3]): r[3] for r in export_list(work, None).tolist()}
gone = [k for k in old if k not in new]
added = [k for k in new if k not in old]
recol = [k for k in new if k in old and new[k] != old[k]]
bad = [k for k in gone + recol if cw.get(k) != old[k]] + [k for k in added if k in cw]
print('%s：舊帳 %d、新帳 %d ⇒ 拿掉 %d、加上 %d、換色 %d；作品 %d 格，差到的格裡跟舊帳對不上 %d' % (
    work, len(old), len(new), len(gone), len(added), len(recol), len(cw), len(bad)))
if bad:
    for k in bad[:12]:
        print('  ✗', k, '舊帳', old.get(k), '新帳', new.get(k), '作品', cw.get(k))
    sys.exit(1)
T = dict(cw)
for k in gone:
    T.pop(k)
for k in added + recol:
    T[k] = new[k]
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# %s 目標清單（tools/ledger_delta.py：作品 ＋ 新帳 − 舊帳）\n' % work)
    for k in sorted(T):
        f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], T[k]))
print('＝ %d → %s' % (len(T), out))
