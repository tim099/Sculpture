# 抄來的（飛魚號 TASK-0971）：出處 ame-labelle-01m/design/layout.py（拉貝爾號；作品 id、persona、船名、作品尺寸已換）
# 飛魚號 配置（TASK-0971）：甲板高度與範圍、砲門位置、桅與帆桁 —— 只吃 plan.json 與 lines，給圖紙與之後的階段共用
#   出處：calli-cosecha-01m/design/layout.py（收穫號）；舷弧的兩端改讀 plan.decks.sheer 的 x_aft／x_fwd。
#   甲板高度 ＝ 甲板面（甲板板最上面那一格）；站人從 +1 起。
import math
import numpy as np

CELL = 0.1


def deck_row(plan, key):
    return next(r for r in plan['decks']['rows'] if r['key'] == key)


def deck_z(plan, key, x):
    """那一層甲板在 x 的甲板面高度。主甲板有舷弧（拋物線往兩頭抬）；船尾小艙、後甲板、船首樓、貨艙地板平的。"""
    row = deck_row(plan, key)
    x = np.asarray(x, float)
    if key != 'main':
        return np.full(x.shape, float(row['z']))
    s = plan['decks']['sheer']
    xm = s['x_mid']
    t_aft = np.clip((xm - x) / (xm - s['x_aft']), 0, 1)       # 舷弧量到 x_aft／x_fwd 為止，再過去不外推（收穫號 v1 外推 ⇒ 最船尾 wale 抬進船樓菱格）
    t_fwd = np.clip((x - xm) / (s['x_fwd'] - xm), 0, 1)
    return row['z'] + np.round(s['aft'] * t_aft ** 2 + s['fwd'] * t_fwd ** 2)


def deck_span(plan, L, key):
    """那一層甲板在 x 上的範圍（含端點）：船殼在那個高度的前後 ∩ row 的 x_from／x_to。"""
    row = deck_row(plan, key)
    z = float(row['z'])
    xa = int(math.ceil(float(L.x_aft(z + 0.5))))
    xs = int(math.floor(float(L.x_stem(z + 0.5))))
    return max(xa, row.get('x_from', xa)), min(xs, row.get('x_to', xs))


def ports(plan):
    """每一層每一舷的砲門：[{deck, i, x0, x1, z0, z1, gun}]（含端點；兩舷同一組 x）。"""
    out = []
    for t in plan['ports']['tiers']:
        n, w, h = t['per_side'], t['w'], t['h']
        cs = t['xc'] if 'xc' in t else np.linspace(t['x_from'] + w / 2.0, t['x_to'] - w / 2.0, n)   # 本船：逐門指定中心（等距會落在主桅旁）
        for i, c in enumerate(cs):
            x0 = int(round(c - w / 2.0))
            x1 = x0 + w - 1
            pad = t.get('ref_pad')
            if pad:       # 量砲門左右各多 pad 格那一段甲板的最高處（砲架比砲門寬、舷弧是一格一格的台階 ⇒ 砲站在高的那一階；階段八主甲板第 7 門）
                zc = float(max(int(deck_z(plan, t['deck'], x + 0.5)) for x in range(x0 - pad, x1 + pad + 1)))
            else:
                zc = float(deck_z(plan, t['deck'], (x0 + x1) / 2.0))
            z0 = int(zc) + t['sill']
            out.append({'deck': t['deck'], 'i': i + 1, 'x0': x0, 'x1': x1, 'z0': z0, 'z1': z0 + h - 1, 'gun': t['gun']})
    return out


def masts(plan, L):
    """每根桅：步（x、z）、下桅頂、平台、上桅頂、帆桁的高度與長度（格）。
    設計（plan.masts.rows 的長度照 Cano／Palacio）：masthead ＝ 下桅的 8%、平台在 masthead 下緣；上桅腳在平台、頂 ＝ 平台 ＋ 上桅長；
    course 帆桁掛在平台下 12 格；topsail 帆桁在上桅頂往下 18%；lateen 帆桁掛在桅的 85% 高、前低後高 35°（設計決定）。"""
    out = []
    for m in plan['masts']['rows']:
        k = m['key']
        if k == 'bowsprit':
            continue
        x = m['x_step']
        lower = m['lower_m'] / CELL
        z_heel = heel_z(plan, L, k, x)
        head = 0.08 * lower
        z_top_lower = z_heel + lower
        z_plat = z_top_lower - head
        r = {'key': k, 'x': x, 'rake': m['rake_deg'], 'heel': z_heel, 'lower_top': z_top_lower, 'platform': z_plat, 'yards': {}}
        if 'top_m' in m:
            r['truck'] = z_plat + m['top_m'] / CELL
        else:
            r['truck'] = z_top_lower
        for yk, ylen in m['yards'].items():
            if isinstance(ylen, dict):      # 本船：帆桁直接寫長度與 jaws／中心的世界 z（gaff、boom 再帶仰角：正 ＝ 往船尾往上）
                r['yards'][yk] = {'z': float(ylen['z']), 'len': ylen['len_m'] / CELL, 'angle': float(ylen.get('angle_deg', 0))}
                continue
            yl = ylen / CELL
            if yk == 'course':
                z = z_plat - 12
            elif yk == 'topsail':
                z = r['truck'] - 0.18 * m['top_m'] / CELL
            else:      # lateen：掛點在桅的 85% 高
                z = z_heel + 0.85 * lower
            r['yards'][yk] = {'z': float(z), 'len': yl}
        out.append(r)
    return out


def heel_z(plan, L, key, x):
    """桅腳：前桅、主桅立在 keelson（龍骨頂＋4）—— 前桅那一站 deadwood 抬高，取那一站船底內面；後桅、bonaventure 立在主甲板（設計決定）。"""
    if key in ('mizzen', 'bonaventure'):
        return float(deck_z(plan, 'main', x))
    zs = np.arange(0, 120) + 0.5
    hb = L.hb(np.full(zs.shape, x + 0.5), zs)
    zr = zs[np.argmax(hb > L.keel_hw + 0.5)] if np.any(hb > L.keel_hw + 0.5) else 5
    return float(max(L.z_keel_top + 4, zr))


def mast_axis_x(plan, key, z, L):
    """桅軸在高度 z 的 x（x_step 是桅腳那一格；往上照 rake 倒：正 ＝ 往船尾）。"""
    m = next(r for r in plan['masts']['rows'] if r['key'] == key)
    z_heel = heel_z(plan, L, key, m['x_step'])
    return m['x_step'] - (np.asarray(z, float) - z_heel) * math.tan(math.radians(m['rake_deg']))


def bowsprit(plan):
    m = next(r for r in plan['masts']['rows'] if r['key'] == 'bowsprit')
    z0 = float(deck_z(plan, m.get('deck', 'main'), m['x_step'])) + m.get('heel_dz', 1)      # 飛魚號：腳架在甲板上的 bitts（heel_dz）
    a = math.radians(m['angle_deg'])
    ln = m['len_m'] / CELL
    return {'x0': m['x_step'], 'z0': z0, 'x1': m['x_step'] + ln * math.cos(a), 'z1': z0 + ln * math.sin(a), 'angle': m['angle_deg'],
            'len': ln, 'spritsail_len': m['yards'].get('spritsail', 0) / CELL}
