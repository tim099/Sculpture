# 出處：apex-two-galeon-01m/design/layout.py（康塞普西翁號，TASK-0969）的 deck_z／ports 寫法 —— 改成星辰號（TASK-0019）
# 星辰號（al-Najm）布局：plan.json 的 decks／ports／stern ⇒ 甲板面高度、砲門、排水孔、船尾窗的格子範圍
#   跟康塞普西翁號不同：主甲板的舷弧只有船頭那段直線抬 rise（x_flat_to → rise_to_x）；船頭水槽 fore_well 往下凹 drop（smoothstep）；
#   船樓（quarter、poop）與底艙平台都是平的。
#   被 draft_ports.py 與之後的階段 import；只讀 plan.json、不碰作品。
import math
import numpy as np

from lines import smoothstep


def deck_row(plan, key):
    return next(r for r in plan['decks']['rows'] if r['key'] == key)


def sheer_rise(plan, x):
    """主甲板的舷弧（格，取整）：x_flat_to 以前 0、到 rise_to_x 直線抬到 rise。"""
    s = plan['decks']['sheer']
    x = np.asarray(x, float)
    t = np.clip((x - s['x_flat_to']) / float(s['rise_to_x'] - s['x_flat_to']), 0, 1)
    return np.floor(s['rise'] * t + 0.5)


def well_drop(plan, x):
    """船頭水槽往下凹幾格（取整）：x_from → x_full smoothstep 到 drop，再往前維持。"""
    w = plan['decks']['fore_well']
    x = np.asarray(x, float)
    return np.floor(w['drop'] * smoothstep((x - w['x_from']) / float(w['x_full'] - w['x_from'])) + 0.5)


def deck_z(plan, key, x, well=True):
    """那一層甲板在 x 的甲板面高度（站人的那一格；甲板板在它下面一格）。well=False ⇒ 主甲板不扣水槽（外面的 wale 照舷弧走）。"""
    row = deck_row(plan, key)
    x = np.asarray(x, float)
    if key != 'main':
        return np.full(x.shape, float(row['z']))
    z = row['z'] + sheer_rise(plan, x)
    if well:
        z = z - well_drop(plan, x)
    return z


def ports(plan):
    """每一層每一舷的砲門：[{deck, i, x0, x1, z0, z1, gun}]（含端點；兩舷同一組 x）。x_from／x_to 是砲門外緣。"""
    out = []
    for t in plan['ports']['tiers']:
        n, w, h = t['per_side'], t['w'], t['h']
        cs = np.linspace(t['x_from'] + w / 2.0, t['x_to'] - w / 2.0, n)
        for i, c in enumerate(cs):
            x0 = int(round(c - w / 2.0))
            x1 = x0 + w - 1
            z0 = int(deck_z(plan, t['deck'], (x0 + x1 + 1) / 2.0)) + t['sill']
            out.append({'deck': t['deck'], 'i': i + 1, 'x0': x0, 'x1': x1, 'z0': z0, 'z1': z0 + h - 1, 'gun': t['gun']})
    return out


def scuppers(plan):
    """水槽兩舷的排水孔：[{i, x0, x1, z0, z1}]（貼著水槽甲板面）。"""
    s = plan['ports'].get('scuppers')
    if not s:
        return []
    out = []
    for i, xc in enumerate(s['x']):
        x0 = int(xc - s['w'] // 2)
        z0 = int(deck_z(plan, 'main', xc + 0.5))
        out.append({'i': i + 1, 'x0': x0, 'x1': x0 + s['w'] - 1, 'z0': z0, 'z1': z0 + s['h'] - 1})
    return out


def stern_windows(plan, YC):
    """船尾窗：[{j, y0, y1, z0, z1}]；中心照 pitch 對中線排（寬要奇數 ⇒ 兩舷逐格對稱）。"""
    out = []
    for row in plan['stern']['rows']:
        n, w, h, pitch = row['n'], row['w'], row['h'], row['pitch']
        assert w % 2 == 1, '船尾窗寬要奇數（才能對中線對稱）'
        z0 = int(deck_row(plan, row['deck'])['z']) + row['sill']
        for j in range(n):
            k = int((j - (n - 1) / 2.0) * pitch)
            y0 = YC + k - (w - 1) // 2
            out.append({'j': j + 1, 'y0': y0, 'y1': y0 + w - 1, 'z0': z0, 'z1': z0 + h - 1})
    return out
