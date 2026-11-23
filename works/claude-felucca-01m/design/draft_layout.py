# 海鷗號 新圖紙 02（TASK-0024 步驟 3）：配置 ⇒ 圖紙 sheet02_layout_v1.png、讀數 verify_layout.json
#   用法：python -I -X utf8 draft_layout.py [--probe=benches.x0=3]
#   · 只讀 plan.json 與 masks/hull/hull_01.vox.txt（線形那張清單），不碰作品、不產清單（步驟 5 以後各自的程式照這些數字落格）。
#   · 量的是「配置放得進這個船殼嗎」：艙底板、坐板、平台兩頭貼不貼得到船殼內面、跟船殼重疊幾格；槳栓腳下是不是舷頂；
#     坐板比站的那格高幾格（遊戲一步 ≤ 3）；舷牆比平台高多少；桅腳、砲位落在哪一層。
#   · --probe：反向對照用（點名的那一格加減，⛔ 不寫檔）。
#   出處：結構照 kotoko-fusta-01m/design/draft_upper.py 的「plan.layout ⇒ 讀數」做法，自己寫；圖紙字用英文＋Pillow 內建字型（逐位元組相同）。
import sys, os, json, copy
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
NX, NY, NZ = 170, 161, 50


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load_hull():
    a = np.loadtxt(os.path.join(HERE, 'masks', 'hull', 'hull_01.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    G = np.zeros((NX, NY, NZ), np.uint8)
    G[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    return G


def span(G, x, z, YC):
    """(x, z) 那一排從中線往兩舷第一個船殼格之間的空格 ⇒ (lo, hi)；中線本身是船殼 ⇒ None。"""
    if G[x, YC, z]:
        return None
    lo = YC
    while lo - 1 >= 0 and not G[x, lo - 1, z]:
        lo -= 1
    hi = YC
    while hi + 1 < NY and not G[x, hi + 1, z]:
        hi += 1
    if lo == 0 or hi == NY - 1:
        return None                                            # 沒碰到牆 ⇒ 不在船裡
    return lo, hi


def rail_top(G, x, dy, YC):
    """(x, YC+dy) 那一欄最高的船殼格的 z（沒有 ⇒ None）。"""
    zs = np.where(G[x, YC + dy, :] > 0)[0]
    return int(zs.max()) if len(zs) else None


def readings(plan, G):
    L = HL.Lines(plan)
    YC = L.YC
    lay = {k: V(v) for k, v in plan['layout'].items() if k != 'src'}
    R = {}
    # ── 艙底板 ──
    fl = lay['floor']
    bad = []
    cells = 0
    for x in range(fl['x0'], fl['x1'] + 1):
        sp = span(G, x, fl['board_z'], YC)
        if sp is None:
            bad.append(x)
            continue
        cells += sp[1] - sp[0] + 1
    R['floor'] = {'board_z': fl['board_z'], 'stand_z': fl['board_z'] + 1, 'x': [fl['x0'], fl['x1']], 'cells': cells, 'columns_not_inside': bad,
                  'width_mid_m': round((lambda s: (s[1] - s[0] + 1) * 0.1)(span(G, 84, fl['board_z'], YC)), 1)}
    # ── 坐板 ──
    b = lay['benches']
    benches = []
    for i in range(b['n']):
        x = b['x0'] + i * b['pitch']
        rows = []
        for xx in range(x, x + b['w']):
            sp = span(G, xx, b['seat_z'], YC)
            rows.append(None if sp is None else [sp[0] - YC, sp[1] - YC])
        benches.append({'x': x, 'seat_top_z': b['seat_z'] + 1, 'step_above_floor': b['seat_z'] + 1 - (fl['board_z'] + 1),
                        'dy_span': rows, 'rail_above_seat_m': round((rail_top(G, x, 15, YC) + 1 - (b['seat_z'] + 1)) * 0.1, 2) if rail_top(G, x, 15, YC) is not None else None})
    R['benches'] = benches
    # ── 槳栓（右舷；左舷鏡像）：腳下那格是不是舷頂、是不是最外一格 ──
    t = lay['tholes']
    tholes = []
    for bb in benches:
        x = bb['x'] + t['dx']
        zr = int(np.where(G[x, YC + 2:, :].any(axis=0))[0].max())          # 那一欄舷頂（最高的船殼格）
        dy = int(np.where(G[x, :, zr] > 0)[0].max() - YC)                   # 舷頂那一層最外一格：槳栓立在它上面
        under = int(G[x, YC + dy, zr])
        free = not G[x, YC + dy, zr + 1:zr + 1 + t['h']].any()
        tholes.append({'x': x, 'dy': dy, 'z': [zr + 1, zr + t['h']], 'under_is_hull': under > 0, 'cell_free': bool(free),
                       'pivot': [x + 0.5, YC + dy + 1.0, float(zr + 1)]})
    R['tholes'] = tholes
    gaps = [tholes[i + 1]['x'] - tholes[i]['x'] for i in range(len(tholes) - 1)]
    R['thole_pitch_m'] = sorted(set(round(g * 0.1, 2) for g in gaps))
    # ── 平台 ──
    for key in ('bow_platform', 'stern_platform'):
        pf = lay[key]
        bad = []
        cells = 0
        bulwark = {}
        for x in range(pf['x0'], pf['x1'] + 1):
            sp = span(G, x, pf['board_z'], YC)
            if sp is None:
                bad.append(x)
                continue
            cells += sp[1] - sp[0] + 1
            if x % 4 == 0:
                side = G[x, YC + int(L.keel_hw) + 1:, :] > 0           # 中線外（不算艏艉柱）的船殼格
                rt = int(np.where(side.any(axis=0))[0].max())
                bulwark[str(x)] = round((rt + 1 - (pf['board_z'] + 1)) * 0.1, 2)
        R[key] = {'board_z': pf['board_z'], 'stand_z': pf['board_z'] + 1, 'x': [pf['x0'], pf['x1']], 'cells': cells, 'columns_not_inside': bad,
                  'step_above_floor': pf['board_z'] - fl['board_z'], 'bulwark_above_stand_m': bulwark}
    # ── 桅 ──
    m = lay['masts']
    mm = {}
    for name, mv in m.items():
        x = mv['x']
        zs = np.where(G[x, YC, :] > 0)[0]
        inside_bottom = int(zs[zs < 10].max()) + 1 if len(zs[zs < 10]) else None
        mm[name] = {'x': x, 'heel_z': inside_bottom, 'rake_deg': mv['rake_deg'],
                    'deck_level': 'floor' if fl['x0'] <= x <= fl['x1'] and not (lay['bow_platform']['x0'] <= x <= lay['bow_platform']['x1']) else 'bow_platform'}
        if name == 'main':
            mm[name]['top_z'] = round(rail_top(G, x, 16, YC) + 1 + mv['above_rail_m'] * 10, 1)
        else:
            mm[name]['top_z'] = round(lay['bow_platform']['board_z'] + 1 + mv['above_platform_m'] * 10, 1)
    R['masts'] = mm
    R['mast_spacing_m'] = round((m['fore']['x'] - m['main']['x']) * 0.1, 2)
    # ── 砲位：腳下是什麼 ──
    gl = []
    for g in lay['guns']:
        x, dy = g['x'], g['dy']
        if g['mount'] == 'post':
            pf = lay['bow_platform']
            on = 'bow_platform' if pf['x0'] <= x <= pf['x1'] else '?'
            gl.append({'id': g['id'], 'kind': g['kind'], 'x': x, 'dy': dy, 'stands_on': on, 'post_foot_z': pf['board_z'] + 1})
        else:
            outer = int(np.where(G[x, :, :].any(axis=1))[0].max() - YC)
            d2 = min(abs(dy), outer) * (1 if dy >= 0 else -1)
            rt = rail_top(G, x, abs(d2), YC)
            gl.append({'id': g['id'], 'kind': g['kind'], 'x': x, 'dy': d2, 'stands_on': 'rail', 'rail_top_z': rt})
    R['guns'] = gl
    # ── 槳的範圍不撞平台（槳栓最前最後離平台幾格）──
    R['oar_clearance_cells'] = {'last_thole_to_bow_platform': lay['bow_platform']['x0'] - tholes[-1]['x'],
                                'first_thole_to_stern_platform': tholes[0]['x'] - lay['stern_platform']['x1']}
    return R


def palette_rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def sheet(plan, G, R, path):
    L = HL.Lines(plan)
    YC = L.YC
    lay = {k: V(v) for k, v in plan['layout'].items() if k != 'src'}
    s = 5
    X0, X1 = 0, 170
    Wd = (X1 - X0) * s + 120
    Hh = 1640
    img = Image.new('RGB', (Wd, Hh), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((40, 14), 'al-Nawras (Sale felucca, 1666) - new sheet 02: layout (floor, thwarts, tholes, platforms, masts, yards, guns)   0.1 m/cell', fill=(20, 20, 40), font=f)
    ox = 60

    def px(x):
        return ox + (x - X0) * s

    # 1. profile with rig (z up to 175)
    ZT = 175
    oy = 40 + ZT * s // 2 * 2 // 2
    oy = 40 + ZT * 4
    sz = 4

    def pz(z):
        return oy - z * sz

    d.text((40, 30), '1. profile (bow right). hull silhouette, platforms, thwarts, masts, lateen yards at 40 deg, guns (red)', fill=(20, 20, 40), font=f)
    solid = G > 0
    for x in range(NX):
        zs = np.where(solid[x].any(axis=0))[0]
        for z in zs:
            ys = np.where(solid[x, :, z])[0]
            d.rectangle([px(x), pz(z + 1) + 1, px(x) + s - 1, pz(z)], fill=palette_rgb(int(G[x, ys.max(), z])))
    wl = plan['waterline']['z']
    d.line([px(0), pz(wl + 1), px(170), pz(wl + 1)], fill=(40, 110, 200))
    fl = lay['floor']
    d.line([px(fl['x0']), pz(fl['board_z'] + 1), px(fl['x1'] + 1), pz(fl['board_z'] + 1)], fill=(120, 80, 30), width=2)
    for k in ('bow_platform', 'stern_platform'):
        pf = lay[k]
        d.line([px(pf['x0']), pz(pf['board_z'] + 1), px(pf['x1'] + 1), pz(pf['board_z'] + 1)], fill=(120, 80, 30), width=3)
    for bb in R['benches']:
        d.rectangle([px(bb['x']), pz(bb['seat_top_z']), px(bb['x'] + 2) - 1, pz(bb['seat_top_z'] - 1)], fill=(90, 60, 20))
    for th in R['tholes']:
        d.line([px(th['x']) + 2, pz(th['z'][0]), px(th['x']) + 2, pz(th['z'][1] + 1)], fill=(20, 20, 20), width=2)
    import math
    for name, mv in R['masts'].items():
        x = lay['masts'][name]['x'] + 0.5
        rk = math.radians(mv['rake_deg'])
        zt = mv['top_z']
        z0 = mv['heel_z']
        d.line([px(x), pz(z0), px(x + (zt - z0) * math.tan(rk)), pz(zt)], fill=(60, 40, 20), width=3)
        yl = (lay['yards']['main_m'] if name == 'main' else lay['yards']['fore_m']) * 10
        a = math.radians(lay['yards']['angle_deg'])
        hx, hz = x + (zt - 8 - z0) * math.tan(rk), zt - 8
        fx, fz = hx + yl * lay['yards']['pivot_frac'] * math.cos(a), hz - yl * lay['yards']['pivot_frac'] * math.sin(a)
        ax, az = hx - yl * (1 - lay['yards']['pivot_frac']) * math.cos(a), hz + yl * (1 - lay['yards']['pivot_frac']) * math.sin(a)
        d.line([px(fx), pz(fz), px(ax), pz(az)], fill=(150, 100, 40), width=2)
        d.text((px(x) + 6, pz(zt) - 4), '%s mast top z %.0f' % (name, zt), fill=(60, 40, 20), font=f)
    ts = lay['tack_spar']
    d.line([px(ts['x0']), pz(ts['z']), px(ts['x1']), pz(ts['z'])], fill=(150, 100, 40), width=2)
    for g in R['guns']:
        z = (g['post_foot_z'] + 17) if g['stands_on'] == 'bow_platform' else (g['rail_top_z'] + 3)
        d.ellipse([px(g['x']) - 4, pz(z) - 4, px(g['x']) + 4, pz(z) + 4], outline=(200, 30, 30), width=2)
    for x in range(0, 171, 10):
        d.line([px(x), oy + 4, px(x), oy + 10], fill=(80, 80, 80))
        d.text((px(x) - 8, oy + 12), str(x), fill=(80, 80, 80), font=f)
    # 2. plan view (y), oars drawn outboard on both sides, pivot to blade centre (horizontal projection at 15 deg)
    oy2 = oy + 60 + 70 * s
    d.text((40, oy + 34), '2. plan view (centreline horizontal): floor, thwarts, platforms, thole pins (dots), oars in the half-stroke pose (blue)', fill=(20, 20, 40), font=f)

    def py(y):
        return oy2 - (y - YC) * s

    for x in range(NX):
        ys = np.where(solid[x].any(axis=1))[0]
        if len(ys):
            d.line([px(x), py(ys.max() + 1), px(x) + s - 1, py(ys.max() + 1)], fill=(30, 30, 90))
            d.line([px(x), py(ys.min()), px(x) + s - 1, py(ys.min())], fill=(30, 30, 90))
    for k in ('bow_platform', 'stern_platform'):
        pf = lay[k]
        for x in range(pf['x0'], pf['x1'] + 1):
            sp = span(G, x, pf['board_z'], YC)
            if sp:
                d.rectangle([px(x), py(sp[1] + 1), px(x) + s - 1, py(sp[0])], fill=(220, 200, 160))
    for bb in R['benches']:
        for i, r in enumerate(bb['dy_span']):
            if r:
                d.rectangle([px(bb['x'] + i), py(YC + r[1] + 1), px(bb['x'] + i) + s - 1, py(YC + r[0])], fill=(90, 60, 20))
    for th in R['tholes']:
        for sg in (1, -1):
            yy = YC + sg * th['dy']
            d.ellipse([px(th['x']), py(yy + 1), px(th['x']) + s, py(yy)], fill=(20, 20, 20))
            out = 3.0 * math.cos(math.radians(15)) * 10
            d.line([px(th['pivot'][0]), py(YC + sg * (th['dy'] + 0.5)), px(th['pivot'][0]), py(YC + sg * (th['dy'] + 0.5 + out))], fill=(40, 90, 200), width=2)
            d.line([px(th['pivot'][0]), py(YC + sg * (th['dy'] + 0.5)), px(th['pivot'][0]), py(YC + sg * (th['dy'] + 0.5 - 14))], fill=(40, 90, 200), width=1)
    for g in R['guns']:
        yy = YC + g['dy']
        d.ellipse([px(g['x']) - 4, py(yy) - 4, px(g['x']) + 4, py(yy) + 4], outline=(200, 30, 30), width=2)
    for name in ('main', 'fore'):
        x = lay['masts'][name]['x']
        d.ellipse([px(x) - 4, py(YC) - 4, px(x) + 4, py(YC) + 4], fill=(60, 40, 20))
    # 3. table
    ty = oy2 + 60 * s + 20
    rows = [
        'floor boards z %d (stand z %d), x %d-%d, width at midship %.1f m' % (R['floor']['board_z'], R['floor']['stand_z'], R['floor']['x'][0], R['floor']['x'][1], R['floor']['width_mid_m']),
        '%d thwarts x %s, seat top z %d (step %d cells above floor), rail %.2f m above seat' % (len(R['benches']), ','.join(str(b['x']) for b in R['benches']), R['benches'][0]['seat_top_z'], R['benches'][0]['step_above_floor'], R['benches'][3]['rail_above_seat_m']),
        'thole pins (per side) x %s, on the outermost rail cell, pitch %s m' % (','.join(str(t['x']) for t in R['tholes']), R['thole_pitch_m']),
        'bow platform x %d-%d board z %d; stern platform x %d-%d board z %d' % (R['bow_platform']['x'][0], R['bow_platform']['x'][1], R['bow_platform']['board_z'], R['stern_platform']['x'][0], R['stern_platform']['x'][1], R['stern_platform']['board_z']),
        'main mast x %d top z %.0f; fore mast x %d rake %d deg top z %.0f; yards %.1f / %.1f m at %d deg' % (lay['masts']['main']['x'], R['masts']['main']['top_z'], lay['masts']['fore']['x'], lay['masts']['fore']['rake_deg'], R['masts']['fore']['top_z'], lay['yards']['main_m'], lay['yards']['fore_m'], lay['yards']['angle_deg']),
        'guns: 4 x pierrier (bow post x 123 on centreline as Schellinks 1664; bow quarters x 114; stern x 18)',
        'sources: plan.json layout.*.src; references/sch_readings.json',
    ]
    for i, r in enumerate(rows):
        d.text((40, ty + i * 18), r, fill=(30, 30, 30), font=f)
    img.save(path)


def main():
    plan = HL.load_plan(HERE)
    probe = [a[len('--probe='):] for a in sys.argv[1:] if a.startswith('--probe=')]
    if probe:
        plan = copy.deepcopy(plan)
        for p in probe:
            k, v = p.split('=')
            sec, key = k.split('.')
            plan['layout'][sec]['v'][key] += float(v) if '.' in v else int(v)
    G = load_hull()
    R = readings(plan, G)
    if probe:
        print(json.dumps({'probe': probe, 'R': R}, ensure_ascii=False))
        return
    with open(os.path.join(HERE, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(plan, G, R, os.path.join(HERE, 'sheet02_layout_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
