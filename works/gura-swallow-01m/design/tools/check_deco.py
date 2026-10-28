# 抄來的（燕子號 TASK-0968）：出處 gura-flyingfish-01m/design/tools/check_deco.py（飛魚號；作品 id、船名、單號已換）
# 燕子號 步驟 6 讀數（TASK-0968）：船殼結果帳（砲門塗裝之後 ＋ 金魚換色 − 玻璃後面刻掉 − 拆出去的玻璃）、玻璃件 ＝ 原本的窗玻璃格、
#   玻璃後面那一格在組裝件裡是空的、船首像作品 ＝ 清單；作品那一側一律從 CLI 匯出讀。
#   用法：python -I -X utf8 tools/check_deco.py <design>
import os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key

HULL = 'gura-swallow-01m'
rd = lambda p: np.loadtxt(os.path.join(design, 'masks', *p), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
d = lambda a: dict(zip(key(a).tolist(), a[:, 3].tolist()))
before = d(export_list(HULL, '裝飾:begin'))
want = dict(before)
want.update(d(rd(('deco', 'emblem_paint.vox.txt'))))
for k in d(rd(('glass', 'carve_behind.vox.txt'))):
    want.pop(k)
glass_want = {k: c for k, c in want.items() if c == 87}
for k in glass_want:
    want.pop(k)
got = d(export_list(HULL, None))
bad = 0
def ledger(name, got, want):
    global bad
    miss, extra = len(set(want) - set(got)), len(set(got) - set(want))
    cd = sum(1 for k in set(want) & set(got) if want[k] != got[k])
    bad += miss + extra + cd
    print('%-10s 作品 %d、設計 %d、缺 %d、多 %d、色差 %d' % (name, len(got), len(want), miss, extra, cd))
ledger('船殼', got, want)
ledger('窗玻璃', d(export_list(HULL + '-stern-glass', None)), glass_want)
ledger('船首像', d(export_list(HULL + '-figurehead', None)), d(rd(('deco', 'figurehead.vox.txt'))))
asm = set(key(export_list(HULL + '-assembly', None, links=None)).tolist())
behind_air = sum(1 for k in glass_want if (k + 1000000) not in asm)        # 鍵 ＝ (x·1000 ＋ y)·1000 ＋ z ⇒ x ＋ 1 ＝ ＋10⁶
print('玻璃 %d 格：組裝件裡往船頭那一格是空的 %d' % (len(glass_want), behind_air))
print('問題合計 %d' % (bad + len(glass_want) - behind_air))
