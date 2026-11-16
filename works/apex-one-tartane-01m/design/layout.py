# 塔爾塔納 配置（TASK-1299）：甲板高度與範圍、無艦砲、雙拉丁桅與短斜桅 —— 只吃 plan.json 與 lines
import math
import numpy as np

CELL = 0.1


def deck_row(plan, key):
    return next(r for r in plan['decks']['rows'] if r['key'] == key)


def deck_z(plan, key, x):
    """主甲板帶舷弧（向艏／艉抬升）；貨艙地板、尾艙地板、艉樓後甲板平的。"""
    row = deck_row(plan, key)
    x = np.asarray(x, float)
    if key != 'main':
        return np.full(x.shape, float(row['z']))
    s = plan['decks']['sheer']
    xm = s['x_mid']
    t_aft = np.clip((xm - x) / (xm - s['x_aft']), 0, 1)
    t_fwd = np.clip((x - xm) / (s['x_fwd'] - xm), 0, 1)
    return row['z'] + np.round(s['aft'] * t_aft ** 2 + s['fwd'] * t_fwd ** 2)


def deck_span(plan, L, key):
    row = deck_row(plan, key)
    z = float(row['z'])
    xa = int(math.ceil(float(L.x_aft(z + 0.5))))
    xs = int(math.floor(float(L.x_stem(z + 0.5))))
    return max(xa, row.get('x_from', xa)), min(xs, row.get('x_to', xs))


def ports(plan):
    return []


def heel_z(plan, L, key, x):
    """兩根拉丁立桅皆立於內龍骨 keelson／deadwood 內面。"""
    if key in ('mizzen', 'bonaventure'):
        return float(deck_z(plan, 'main', x))
    zs = np.arange(0, 120) + 0.5
    hb = L.hb(np.full(zs.shape, x + 0.5), zs)
    zr = zs[np.argmax(hb > L.keel_hw + 0.5)] if np.any(hb > L.keel_hw + 0.5) else 5
    return float(max(L.z_keel_top + 4, zr))


def mast_axis_x(plan, key, z, L):
    """桅軸在高度 z 的 x；rake_deg 正 ＝ 向船尾傾、負 ＝ 向船頭傾（前桅 trinquet 約 -23°）。"""
    m = next(r for r in plan['masts']['rows'] if r['key'] == key)
    z_heel = heel_z(plan, L, key, m['x_step'])
    return m['x_step'] - (np.asarray(z, float) - z_heel) * math.tan(math.radians(m['rake_deg']))


def masts(plan, L):
    """每根拉丁單桅（à pible）：腳、calcet 桅頂滑車組（頂 6%）、高點，以及掛於 ~82% 高度之拉丁斜桁。"""
    out = []
    for m in plan['masts']['rows']:
        k = m['key']
        if k == 'bowsprit':
            continue
        x = m['x_step']
        lower = m['lower_m'] / CELL
        z_heel = heel_z(plan, L, k, x)
        head = 0.06 * lower
        z_top_lower = z_heel + lower
        z_calcet = z_top_lower - head
        r = {'key': k, 'label': m.get('label', k), 'x': x, 'rake': m['rake_deg'],
             'heel': z_heel, 'lower_top': z_top_lower, 'calcet': z_calcet, 'truck': z_top_lower, 'yards': {}}
        frac = float(m.get('yard_frac', 0.82))
        for yk, ylen in m['yards'].items():
            yl = ylen / CELL
            z = z_heel + frac * lower
            r['yards'][yk] = {'z': float(z), 'len': yl}
        out.append(r)
    return out


def bowsprit(plan, L):
    m = next(r for r in plan['masts']['rows'] if r['key'] == 'bowsprit')
    z0 = float(m['z0']) if 'z0' in m else (float(deck_z(plan, m.get('deck', 'main'), m['x_step'])) + 2)
    a = math.radians(m['angle_deg'])
    ln = m['len_m'] / CELL
    return {'x0': m['x_step'], 'z0': z0, 'x1': m['x_step'] + ln * math.cos(a), 'z1': z0 + ln * math.sin(a),
            'angle': m['angle_deg'], 'len': ln, 'extra_sail': m.get('extra_sail', '')}
