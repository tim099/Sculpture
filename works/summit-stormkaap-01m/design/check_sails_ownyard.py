# 階段十讀數補一格：模擬後的布落在「自己那根帆桁」裡的點，離釘住的邊（上緣）多遠、在帆桁哪一側 —— 分得出「上緣往下穿過桁身」與「布在別處繞回帆桁」
# 用法：python -I -X utf8 -B check_sails_ownyard.py <design 資料夾> <匯出資料夾>
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_running
from draft_running import Run
from draft_sails import seg_dist
from check_sails import read_obj
draft_running.LINKKEY.update({'channels': 'channels_S', 'channels-鏡像': 'channels_P'})
d, ex = sys.argv[1], sys.argv[2]
VS = json.load(open(os.path.join(d, 'verify_sails.json'), encoding='utf-8'))
VY = json.load(open(os.path.join(d, 'verify_yards.json'), encoding='utf-8'))
dia = {P['member']: P['meta'].get('diameter_m') for P in VY['placements']}
r = Run(d); lab, names = r.w.lab, r.w.names
O = read_obj(os.path.join(ex, 'ship.obj'))
for sl in VS['sails']:
    nm = sl['name']; V, F = O[nm]
    W = [np.array(w) for w in sl['corners_world']]; n = len(W)
    bound = [int(b) for b in sl['bind'].split(',') if b != '']
    code = r.w.code('yard:' + nm)
    pts = np.vstack([V, V[F].mean(1)])
    ds = []
    for p in pts:
        c = tuple(int(math.floor(x)) for x in p)
        if lab[c] == code:
            e = min(seg_dist(p, W[b], W[(b + 1) % n]) for b in bound)
            if e >= 1.2: ds.append(e)
    ds = np.array(ds)
    print('%-16s 桁徑 %.1f 格  落在自己帆桁 %4d 點  離上緣 %.2f–%.2f 格（95%% %.2f）' % (nm, (dia[nm] or 0) * 10, len(ds), ds.min(), ds.max(), np.percentile(ds, 95)))
