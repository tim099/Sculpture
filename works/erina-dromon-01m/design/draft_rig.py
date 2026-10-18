# 新圖紙 03：桅與三角帆桁（lateen）。
#   桅：每根一件子作品（整船的框、關聯 at 0,0,0）—— 圓桅從艙底的桅座穿過甲板、往前傾 rake；桅頂一個滑車箱（halyard 穿過的地方）。
#   帆桁：每根一件子作品（自己的框；沒轉時沿 x 水平擺，前端 tack、後端 peak）⇒ 當外部模型掛在桅子作品裡，
#         pivot ＝ 吊點（sling，在帆桁上）、at ＝ 桅頂前面的吊點位置、rotate ＝ (0, 上翹, 0)。
#   遊戲：帆桁 meta yard=gaff（縱帆，往下風擺 —— 30_rig_physics.js braceYards）、rig=lateen（說明）。
# 用法：python -I -X utf8 -B draft_rig.py ⇒ lists/mast_<名>.txt、lists/yard_<名>.txt、verify_rig.json
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import dro

D = dro.D
P = dro.PLAN
C = dro.C
R = P['rig']
V = json.load(open(os.path.join(D, 'verify_hull.json'), encoding='utf-8'))
ZAIR = V['zair']
OUT = {'masts': {}, 'yards': {}}


def mast(name, m):
    cells = {}
    x0, zstep, ztop, rake = m['x_step'], m['z_step'], m['z_top'], m['rake_deg']
    r0, r1 = m['r_deck'], m['r_top']
    tr = math.tan(math.radians(rake))
    zd = ZAIR[int(x0)]
    for z in range(zstep, ztop + 1):
        cx = x0 + 0.5 + (z - zd) * tr                 # 往前傾（+x）
        t = max(0.0, (z - zd) / (ztop - zd))
        r = r0 + (r1 - r0) * t if z >= zd else r0 + 0.3
        for x in range(int(cx - r - 2), int(cx + r + 3)):
            for y in range(dro.YC - 4, dro.YC + 5):
                if math.hypot(x + 0.5 - cx, y + 0.5 - dro.YM) <= r:
                    cells[(x, y, z)] = C['mast']
    # 桅座（艙底，鐵箍）：桅腳四周一圈
    for x in range(int(x0) - 3, int(x0) + 4):
        for y in range(dro.YC - 3, dro.YC + 4):
            if (x, y, zstep) not in cells:
                cells[(x, y, zstep)] = C['beam']
    # 桅頂滑車箱：桅頂往下 hb 格，前後各凸 2 格
    cxh = x0 + 0.5 + (ztop - zd) * tr
    for z in range(ztop - m['head_h'], ztop + 1):
        cx = x0 + 0.5 + (z - zd) * tr
        for x in range(int(cx - r1 - 2), int(cx + r1 + 2)):
            for y in range(dro.YC - 2, dro.YC + 3):
                cells[(x, y, z)] = C['beam']
    # 桅頂上的小十字（拜占庭船常見的桅頂裝飾：設計）
    zt = ztop + 1
    cx = int(math.floor(x0 + 0.5 + (zt - zd) * tr))
    for dz in range(0, 7):
        cells[(cx, dro.YC, zt + dz)] = C['gold']
    for dy in (-2, -1, 1, 2):
        cells[(cx, dro.YC + dy, zt + 4)] = C['gold']
    ztop_all = zt + 6
    # 固定點（組裝件座標 ＝ 子作品座標）
    zs = ztop - m['head_h'] // 2
    head = (int(math.floor(x0 + 0.5 + (zs - zd) * tr)), dro.YC, zs)
    an = {'head': head, 'step': (int(x0), dro.YC, zstep + 1), 'partners': (int(x0), dro.YC, zd),
          'sheave-fwd': (int(math.floor(x0 + 0.5 + (zs - zd) * tr + r1 + 1.5)), dro.YC, zs),
          'sheave-aft': (int(math.floor(x0 + 0.5 + (zs - zd) * tr - r1 - 1.5)), dro.YC, zs)}
    for k in ('sheave-fwd', 'sheave-aft'):
        assert an[k] in cells, (name, k)
    return cells, an, ztop_all


def yard(name, y):
    # 沒轉時：沿 x 水平，x 小 ＝ 後端（peak）、x 大 ＝ 前端（tack）⇒ 模型 rotate y ＝ +tilt 讓前端往下（繞 y 正轉：+x → (cos, 0, −sin)）；吊點離前端 sling_frac·L；兩根木料在中段搭接（lateen 帆桁常是兩截綁成一根：史料圖常見；設計）
    L, r0, r1 = y['length'], y['r_mid'], y['r_end']
    sl = L - y['sling_frac'] * L                       # 從後端量
    pad = 3
    sx, sy, sz = int(L) + 2 * pad, 2 * pad + 5, 2 * pad + 5
    cyy, czz = sy / 2, sz / 2
    cells = {}
    for x in range(sx):
        u = x + 0.5 - pad
        if u < 0 or u > L:
            continue
        t = abs(u - sl) / (sl if u < sl else L - sl)
        r = r0 + (r1 - r0) * t ** 1.5
        for yy in range(sy):
            for zz in range(sz):
                if math.hypot(yy + 0.5 - cyy, zz + 0.5 - czz) <= r:
                    cells[(x, yy, zz)] = C['mast']
    # 搭接處的綁繩（三圈）
    for du in (-6, 0, 6):
        x = int(pad + sl + du)
        for yy in range(sy):
            for zz in range(sz):
                d = math.hypot(yy + 0.5 - cyy, zz + 0.5 - czz)
                if r0 - 0.2 < d <= r0 + 0.9:
                    cells[(x, yy, zz)] = C['rope']
    ym, zm = int(cyy), int(czz)
    an = {'peak': (pad, ym, zm), 'tack': (pad + int(L) - 1, ym, zm), 'pivot': (pad + int(sl), ym, zm), 'sling': (pad + int(sl), ym, zm + int(r0) + 1)}
    # 帆的上緣（luff）沿帆桁下面一格：每 8 格一個 robands 點
    for k in range(0, int(L) + 1, 8):
        an['roband-%02d' % (k // 8)] = (pad + min(k, int(L) - 1), ym, zm)
    
    for k, v in an.items():
        assert 0 <= v[0] < sx and 0 <= v[1] < sy and 0 <= v[2] < sz, (name, k, v)
    return cells, an, (sx, sy, sz)


for name, m in R['masts'].items():
    cells, an, ztop = mast(name, m)
    n = dro.write_list(os.path.join(D, 'lists', 'mast_%s.txt' % name), cells, '持火號 %s 桅（draft_rig.py）' % name)
    OUT['masts'][name] = {'file': 'lists/mast_%s.txt' % name, 'cells': n, 'anchors': an, 'z_top': ztop}
for name, y in R['yards'].items():
    cells, an, size = yard(name, y)
    n = dro.write_list(os.path.join(D, 'lists', 'yard_%s.txt' % name), cells, '持火號 %s 三角帆桁（沒轉、沿 x；draft_rig.py）' % name)
    m = R['masts'][y['mast']]
    head = OUT['masts'][y['mast']]['anchors']['head']
    # 模型擺法：吊點掛在桅頂前面（sheave-fwd 那一格再往前 1 格、往下 2 格）
    sf = OUT['masts'][y['mast']]['anchors']['sheave-fwd']
    at = (sf[0] + 1.5, dro.YM, sf[2] - 1.5)
    piv = (an['pivot'][0] + 0.5, an['pivot'][1] + 0.5, an['pivot'][2] + 0.5)
    OUT['yards'][name] = {'file': 'lists/yard_%s.txt' % name, 'cells': n, 'anchors': an, 'size': size, 'mast': y['mast'],
                          'model': {'at': at, 'pivot': piv, 'rotate': [0, y['tilt_deg'], y.get('rz_deg', 0)]}}

json.dump(OUT, open(os.path.join(D, 'verify_rig.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print(json.dumps({k: {n: v['cells'] for n, v in OUT[k].items()} for k in OUT}, ensure_ascii=False))
