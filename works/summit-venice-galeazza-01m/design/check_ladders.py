"""威尼斯 galeazza（TASK-1302）梯子點的本地量測（遊戲樓梯自檢 ②④⑦ 的簡版；正式的 admin.py ladcheck 在步驟 14 匯入後跑）。

讀作品實際匯出（組裝件 export format=list，含鏡像關聯）＋ladders.json：
  ② foot／head 腳下實心、頭上 12 格空、離那一層 floor ≤ 3；
  ④ hi → head 沿走向逐柱：梯子寬度（hi 中線 ±1）裡、腳下那一層上下 3 格內站得住的柱，連續空幾柱；
  ⑦ hi 正前方第 1 柱站得住，或第 1 柱頭上空＋第 2 柱站得住。
  反向對照：--probe-shift=N 把 head 往上抬 N 格（懸空 ⇒ ② 該報）。
用法：python -I -X utf8 check_ladders.py <組裝件匯出清單> [--probe-shift=N]
"""
import json
import sys
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parent
YC = 160


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    shift = int(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--probe-shift=')), '0'))
    a = np.loadtxt(args[0], delimiter=',', comments='#', dtype=np.int64, ndmin=2)
    solid = set(map(tuple, a[:, :3].tolist()))
    lad = json.loads((D / 'ladders.json').read_text(encoding='utf-8'))
    meta = json.loads((D / 'deck_meta.json').read_text(encoding='utf-8'))

    def stand(x, y, z, head=12):
        return (x, y, z - 1) in solid and all((x, y, z + k) not in solid for k in range(head))

    rows = []
    for name, p in lad.items():
        variants = [(name, p)]
        if not name.startswith('hold'):
            variants.append((name + '(鏡像)', {k: [v[0], 2 * YC - v[1], v[2]] for k, v in p.items()}))
        for nm, q in variants:
            hi, head, foot = q['hi'], list(q['head']), q['foot']
            head[2] += shift
            d = 1 if head[0] > hi[0] else -1
            two = dict(foot=stand(*foot), head=stand(*head))
            col = []
            for x in range(hi[0] + d, head[0] + d, d):
                ok = any(stand(x, hi[1] + dy, head[2] + dz) for dy in (-1, 0, 1) for dz in range(-3, 4))
                col.append(ok)
            gap, run = 0, 0
            for ok in col:
                run = 0 if ok else run + 1
                gap = max(gap, run)
            off = abs(head[1] - hi[1])
            f1 = any(stand(hi[0] + d, hi[1] + dy, hi[2] + dz) for dy in (-1, 0, 1) for dz in range(-1, 4))
            f2 = any(stand(hi[0] + 2 * d, hi[1] + dy, hi[2] + dz) for dy in (-1, 0, 1) for dz in range(-1, 4))
            seven = 'n/a' if off < 2 else ('ok' if f1 or f2 else '✗')
            rows.append(dict(ladder=nm, **two, gap_cols=gap, head_offset=off, rule7=seven))
    bad = [r for r in rows if not (r['foot'] and r['head'] and r['gap_cols'] < 4 and r['rule7'] != '✗')]
    res = dict(probe_shift=shift, ladders=rows, bad=len(bad))
    if not shift:
        (D / 'verify_ladders.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main()
