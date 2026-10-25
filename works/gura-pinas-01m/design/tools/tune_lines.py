# 藍鯊號：掃線形參數，對 Witsen 的兩個讀數 —— 吃水 10 呎的水下體積（596.2 m³）、hals 的 kimmen 寬（27 呎 在 4'5" 高）
#   用法：python -I -X utf8 tools/tune_lines.py <design> key=v1,v2,… [key=…]   （每一組參數印一行；只讀 plan.json、不寫檔）
#   體積跟 draft_lines 的 witsen_check 同一套格子（Lines.solid），只是不算牆、不畫圖
import itertools, json, math, os, sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, design)
import lines as HL

grid = [(a.split('=')[0], [float(v) for v in a.split('=')[1].split(',')]) for a in sys.argv[2:]]
base = HL.load_plan(design)
Wt = base['witsen']
ft = Wt['ft_cells']
zd = Wt['draught_ft'] * ft
for combo in itertools.product(*[v for _, v in grid]):
    plan = json.loads(json.dumps(base))
    for (k, _), v in zip(grid, combo):
        plan['lines'][k]['v'] = v
    L = HL.Lines(plan)
    S = L.solid(140, 560, int(zd) + 12)
    per = S.sum(axis=(0, 1)).astype(float)            # 每一層幾格
    cum = np.cumsum(per)
    k = int(np.searchsorted(cum, Wt['volume_m3'] * 1000))
    z596 = k + (Wt['volume_m3'] * 1000 - (cum[k - 1] if k else 0)) / per[k] if k < len(per) else float('nan')
    vol = S[:, :, :int(zd)].sum() + (zd % 1) * S[:, :, int(zd)].sum()
    xh = Wt['hals_x'] - 140
    kz = int(L.z_keel_top + Wt['kimmen_h_ft'] * ft)
    kim = int(S[xh, :, kz].sum())
    wlb = int(S[:, :, int(zd)].any(axis=0).sum())
    print(' '.join('%s=%g' % (k, v) for (k, _), v in zip(grid, combo)), '| vol %.1f m³ (要 %.1f)  到 596 m³ 的吃水 z %.1f（龍骨頂起 %.1f 呎）  kimmen %d (要 %.1f)  水線寬 %d' % (vol * 0.001, Wt['volume_m3'], z596, (z596 - L.z_keel_top) / ft, kim, Wt['kimmen_ft'] * ft, wlb))
