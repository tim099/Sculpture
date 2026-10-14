# 三叉戟號 配置（TASK-0554）：甲板舷弧、砲門位置、桅與帆桁的高度 —— 只吃 plan.json，給圖紙與之後的階段共用
import math
import numpy as np


def deck_z(plan, key, x):
    """那一層甲板在 x 的甲板面高度（甲板板最上面那一格；站人從 +1 起）：船中 z ＋ 舷弧（拋物線，往兩頭抬）。"""
    D = plan['decks']
    row = next(r for r in D['rows'] if r['key'] == key)
    s = D['sheer']
    x = np.asarray(x, float)
    xm = s['x_mid']
    t_aft = np.clip((xm - x) / (xm - 100.0), 0, None)
    t_fwd = np.clip((x - xm) / (720.0 - xm), 0, None)
    return row['z'] + np.round(s['aft'] * t_aft ** 2 + s['fwd'] * t_fwd ** 2)


def ports(plan):
    """每一層每一舷的砲門：[{deck, i, x0, x1, z0, z1}]（x0..x1、z0..z1 含端點；兩舷同一組 x）。"""
    out = []
    for t in plan['ports']['tiers']:
        n, w, h = t['per_side'], t['w'], t['h']
        cs = np.linspace(t['x_from'] + w / 2.0, t['x_to'] - w / 2.0, n)
        for i, c in enumerate(cs):
            x0 = int(round(c - w / 2.0))
            x1 = x0 + w - 1
            zc = float(deck_z(plan, t['deck'], (x0 + x1) / 2.0))
            z0 = int(zc) + t['sill']
            out.append({'deck': t['deck'], 'i': i + 1, 'x0': x0, 'x1': x1, 'z0': z0, 'z1': z0 + h - 1})
    return out


def mast_spars(plan):
    """每根桅：下桅、上桅、頂桅的 (z 底, z 頂) 與平台高度、帆桁高度（設計：帆桁在桅頭／平台下方）。"""
    out = []
    for m in plan['masts']['rows']:
        lo, tp, tg = m['lower'], m['top'], m['tg']
        z_heel = m['heel_z']
        z_lo_top = z_heel + lo['len']
        z_platform = z_lo_top - lo['head']
        z_tp_top = z_platform + tp['len']
        z_xtree = z_tp_top - tp['head']
        z_tg_top = z_xtree + tg['len']
        yz = {}
        Y = m['yards']
        if 'course' in Y:
            yz['course'] = z_platform - 12
        if 'crossjack' in Y:
            yz['crossjack'] = z_platform - 12
        yz['topsail'] = z_xtree - 18
        yz['topgallant'] = z_xtree + int(tg['len'] * 0.45)
        if 'royal' in Y:
            yz['royal'] = z_xtree + int(tg['len'] * 0.8)
        if 'gaff' in Y:
            yz['gaff'] = z_platform - 30
            yz['boom'] = 180 + 14
        out.append({'key': m['key'], 'x': m['x'], 'rake': m['rake_deg'], 'heel': z_heel, 'lower_top': z_lo_top, 'platform': z_platform,
                    'top_top': z_tp_top, 'crosstrees': z_xtree, 'truck': z_tg_top, 'yard_z': yz,
                    'yard_len': {k: v[0] for k, v in Y.items()}})
    return out
