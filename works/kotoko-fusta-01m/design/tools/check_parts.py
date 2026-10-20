# 越嶺號 結果帳（每個階段共用）：子作品匯出（export format=list links=none）vs 設計清單 —— 缺／多／色差
#   用法：python -I -X utf8 tools/check_parts.py <清單資料夾（相對 design/）> <清單名=子作品 id> …
#   例：python -I -X utf8 tools/check_parts.py masks/upper deck=kotoko-fusta-01m-deck-main apostis=kotoko-fusta-01m-apostis
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.stdout.reconfigure(encoding='utf-8')
import wio

folder = os.path.join(HERE, sys.argv[1])
bad = 0
for a in sys.argv[2:]:
    name, work = a.split('=')
    w = wio.export_list(work, None)
    d = np.loadtxt(os.path.join(folder, name + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw = dict(zip(wio.key(w).tolist(), w[:, 3].tolist()))
    cd = dict(zip(wio.key(d).tolist(), d[:, 3].tolist()))
    mi, ex = len(set(cd) - set(cw)), len(set(cw) - set(cd))
    cdiff = sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])
    bad += mi + ex + cdiff
    print('%-10s %-34s 作品 %6d ／ 設計 %6d ⇒ 缺 %d、多 %d、色差 %d' % (name, work, len(cw), len(cd), mi, ex, cdiff))
sys.exit(1 if bad else 0)
