# 皇家號 新圖紙 05（TASK-0704）：舵（含舵柄）、艙底地板＋壓艙、彈藥庫與火藥桶、艙口梯、錨 ⇒ 清單、擺法、固定點、讀數 verify_hold.json、圖紙 sheet05
#   用法：python -I -X utf8 draft_hold.py [--probe=floor=+3]
#   · 只讀 plan.json、前四階段的清單（＝ 作品）與元件（CLI 匯出），不碰作品。整船的框、at 0,0,0、兩舷照 |dy| 產（舵在中線）。
#   · 模型（火藥桶、錨）照 draft_guns 的取樣：格心＋八角不落在實心格。
#   · --probe：反向對照（只印讀數）。floor=+3 ⇒ 艙底地板抬 3 格（頭頂淨空要報不夠、梯子點要報站不住）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio
import draft_guns as DG

sys.stdout.reconfigure(encoding='utf-8')
YC = 160
SX, SY, SZ = 720, 321, 140


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def ld(p):
    return np.loadtxt(os.path.join(HERE, p), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def put(cells, x, dy, z, c):
    cells[(x, YC + dy, z)] = c
    cells[(x, YC - dy, z)] = c


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan(HERE)
    H = V(plan['hold'])
    L = HL.Lines(plan)
    D = {k: V(v) for k, v in plan['layout'].items()}
    C = {k: V(v) for k, v in plan['layout']['colors'].items()}
    occ_l = [wio.load_lists(os.path.join(HERE, 'masks', 'hull'))]
    for nm in ('deck', 'apostis', 'rambade', 'eperon', 'stern', 'ladders'):
        occ_l.append(ld('masks/upper/%s.vox.txt' % nm))
    for nm in ('main', 'fore'):
        occ_l.append(ld('masks/masts/%s.vox.txt' % nm))
    allc = np.concatenate(occ_l)
    hull = ld('masks/hull/hull_01.vox.txt')
    occ = set(map(tuple, allc[:, :3].tolist()))
    hullset = set(map(tuple, hull[:, :3].tolist()))
    deck = ld('masks/upper/deck.vox.txt')
    deckset = set(map(tuple, deck[:, :3].tolist()))
    R = {}
    out = {}

    # ───── 舵（舵葉＋舵頭＋舵柄）─────
    rd = H['rudder']
    t = lambda z: np.clip(z / L.z_sh, 0, 1)
    xa = lambda z: float(L.x_aft(z))
    zt0 = rd['tangent_z']
    slope = float((L.x_aft(zt0 + 0.5) - L.x_aft(zt0 - 0.5)))          # dx/dz 在切點
    hinge = lambda z: xa(zt0) + slope * (z - zt0) - rd['gap']        # 鉸鏈線（舵的前緣）：艉柱在 z0 的切線、往後 gap 格
    rud = {}
    z_top_blade, z_head = rd['blade_top_z'], rd['head_z']
    wl = plan['waterline']['z']
    for z in range(0, z_head + 1):
        xh = hinge(z + 0.5)
        if z <= z_top_blade:
            w = rd['w_heel'] + (rd['w_head'] - rd['w_heel']) * z / z_top_blade
        else:
            w = 2.0                                                  # 舵頭（stock）
        for x in range(int(math.floor(xh - w)), int(math.floor(xh)) + 1):
            if x + 0.5 > xh or x + 0.5 < xh - w:
                continue
            for dy in range(rd['half_thick'] + 1):
                c = C['gold'] if z == z_head else (218 if z <= wl else C['navy'])
                put(rud, x, dy, z, c)
    xs_top = int(math.floor(hinge(z_head + 0.5) - 1))
    for x in range(xs_top, rd['tiller_x1'] + 1):                       # 舵柄：從舵頭往前、水平
        for z in (z_head, z_head + 1):
            put(rud, x, 0, z, C['dark'] if x < rd['tiller_x1'] else C['gold'])
    hit = sorted(p for p in rud if p in occ)
    R['rudder'] = {'cells': len(rud), 'hits_ship': len(hit), 'hinge_bottom': [round(hinge(0), 2), YC + 0.5, 0.0], 'hinge_top': [round(hinge(z_head + 1), 2), YC + 0.5, z_head + 1]}
    # 舵頭離船尾最近的船殼格（遊戲在 stock-top 旁 8 格內找掛點）
    st = (int(math.floor(hinge(z_head - 1.5) - 1)), YC, z_head - 2)
    near = min((math.dist(st, p) for p in hullset if abs(p[0] - st[0]) <= 10 and abs(p[2] - st[2]) <= 10 and abs(p[1] - YC) <= 3), default=99)
    R['rudder']['stock_top'] = list(st)
    R['rudder']['stock_top_to_hull'] = round(near, 2)
    ax_ = np.array([slope, 0.0, 1.0])
    ax_ = ax_ / np.linalg.norm(ax_)
    hb = [round(hinge(0), 3), YC + 0.5, 0.0]
    out['rudder'] = {'cells': rud, 'stock_top': list(st),
                     'meta': {'kind': 'rudder', 'hinge_x': hb[0], 'hinge_y': hb[1], 'hinge_z': 0.0, 'axis_x': round(float(ax_[0]), 4), 'axis_y': 0.0,
                              'axis_z': round(float(ax_[2]), 4), 'max_deg': rd['max_deg'], 'turn_axis': 'hinge', 'spin': 'rudder', 'spin_k': rd['max_deg'],
                              'spin_min': -rd['max_deg'], 'spin_max': rd['max_deg'], 'spin_lag': 0.3}, 'at': hb, 'pivot': hb}
    occ |= set(rud)

    # ───── 艙底地板＋壓艙（x0..x1、艙裡）─────
    hx0, hx1 = H['floor_x']
    fz = int(H['floor_top_z'] + probe.get('floor', 0))
    holdc = {}
    for x in range(hx0, hx1 + 1):
        ys = [y for y in range(SY) if (x, y, fz) not in hullset]
        # 那一層艙裡（兩舷船殼之間）
        inside = [y for y in range(YC, SY) if (x, y, fz) not in hullset]
        yo = YC
        while (x, yo + 1, fz) not in hullset and yo + 1 < SY:
            yo += 1
        hw = yo - YC
        if hw < 3:
            continue
        for dy in range(hw + 1):
            for z in (fz - 1, fz):
                if (x, YC + dy, z) not in hullset:
                    put(holdc, x, dy, z, C['deck'])
            z = fz - 2
            while z >= 0 and (x, YC + dy, z) not in hullset:            # 地板下面一路填到船底：壓艙（碎石）⇒ 不留封閉空腔
                put(holdc, x, dy, z, H['ballast_color'])
                z -= 1
    for p in list(holdc):
        if p in occ:
            del holdc[p]
    occ |= set(holdc)
    out['hold'] = holdc
    # 頭頂淨空：地板上第一格空氣往上到甲板（含橫樑）最低那一格
    clear = []
    for x in range(hx0 + 2, hx1 - 1, 4):
        if (x, YC + 6, fz) not in holdc:                               # 只量有地板的那幾欄（兩頭船底往上收的地方沒地板）
            continue
        z = fz + 1
        while (x, YC + 6, z) not in occ and z < 60:
            z += 1
        clear.append(z - fz - 1)
    R['hold'] = {'floor_top_z': fz, 'cells': len(holdc), 'headroom_min': min(clear), 'headroom_max': max(clear)}

    # ───── 彈藥庫（銅皮牆、門洞朝船尾那側的艙口）─────
    M = H['magazine']
    mx0, mx1 = M['x']
    mh = M['half']
    mag = {}
    zc = {}
    for x in range(mx0, mx1 + 1):
        for dy in range(mh + 1):
            z = fz + 1
            while (x, YC + dy, z) not in occ and z < 60:
                z += 1
            zc[(x, dy)] = z
    for x in range(mx0, mx1 + 1):
        for dy in range(mh + 1):
            wall = x in (mx0, mx1) or dy == mh
            door = x == mx0 and dy <= M['door_half']
            if wall and not door:
                for z in range(fz + 1, zc[(x, dy)]):
                    put(mag, x, dy, z, M['copper'])
    for p in list(mag):
        if p in occ:
            del mag[p]
    occ |= set(mag)
    out['magazine'] = mag
    # 火藥桶（模型）：房裡排成格子
    PB = H['barrels']
    bsrc = wio.export_list(PB['source'], None)
    bpiv = [11.0, 11.0, 0.0]
    occ_k = np.array(sorted((x * 1000 + y) * 1000 + z for (x, y, z) in occ), dtype=np.int64)
    barrels = []
    for i, bx in enumerate(range(mx0 + 4, mx1 - 2, PB['pitch'])):
        for j, dy in enumerate(PB['dy']):                                  # 兩舷對稱：格心 160.5 ± dy
            at = [bx + 0.5, YC + dy + 0.5, fz + 1]
            n = DG.collide(occ_k, bsrc, PB['scale'], bpiv, at, 0)
            barrels.append({'name': 'keg-%02d-%02d' % (i, j), 'at': at, 'collide': n})
    out['barrels'] = [b for b in barrels if b['collide'] == 0]
    R['magazine'] = {'cells': len(mag), 'room_x': [mx0, mx1], 'half': mh, 'barrels': len(out['barrels']), 'barrels_skipped_collide': len(barrels) - len(out['barrels']),
                     'powder_lb': 100 * len(out['barrels'])}

    # ───── 艙口梯（艙底地板 → 甲板）─────
    LD = H['ladder']
    lad = {}
    deck_top_at = lambda x, dy: max(z for z in range(0, 60) if (x, YC + dy, z) in deckset) if any((x, YC + dy, z) in deckset for z in range(0, 60)) else None
    ztop = deck_top_at(LD['head_x'] + 1, LD['dm'])                 # 艙口船尾那一邊（圍欄底下）的甲板面
    zhead = max(z for z in range(0, 45) if (LD['head_x'], YC + LD['dm'], z) in occ)   # 梯頭那一柱最高的實心（甲板，或躺在甲板上的 joug）
    zfoot = fz
    zs = [zfoot + 3 * k for k in range(1, 40) if zfoot + 3 * k < ztop - 1]   # 每 3 格一階；最上一階在艙口船尾那一邊（x_top），往下每階往船頭 1 格
    rungs = [(LD['x_top'] + (len(zs) - 1 - i), z) for i, z in enumerate(zs)]
    for (x, z) in rungs:
        for dy in range(LD['half'] + 1):
            put(lad, x, dy, z, C['dark'])
    for side in (LD['half'] + 1,):
        for k_, (x, z) in enumerate(rungs):
            z_from = fz + 1 if k_ == 0 else rungs[k_ - 1][1]
            for zz in range(z_from, z + 3):
                if (x, YC + side, zz) not in occ:
                    put(lad, x, side, zz, C['dark'])
    for p in list(lad):
        if p in occ:
            del lad[p]
    occ |= set(lad)
    out['ladder'] = lad
    xlo, xhi = rungs[0][0], rungs[-1][0]
    pts = {'hold': {'foot': [xlo + 2, YC, fz + 1], 'lo': [rungs[0][0], YC, rungs[0][1] + 1], 'hi': [rungs[-1][0], YC, rungs[-1][1] + 1],
                    'head': [LD['head_x'], YC + LD['dm'], zhead + 1]}}
    chk = {}
    for k_, (x, y, z) in pts['hold'].items():
        need = 7
        chk[k_] = {'at': [x, y, z], 'empty': (x, y, z) not in occ, 'solid_below': (x, y, z - 1) in occ,
                   'blocked_above_within': next((h for h in range(1, need + 1) if (x, y, z + h) in occ), 0)}
    R['ladder'] = {'cells': len(lad), 'rungs': len(rungs), 'points': chk}
    out['ladder_points'] = pts

    # ───── 錨（模型，掛在砲台前緣外側兩角）─────
    AN = H['anchors']
    asrc = wio.export_list(AN['source'], None)
    apiv = [23.5, 16.5, 56.5]
    occ_k = np.array(sorted((x * 1000 + y) * 1000 + z for (x, y, z) in occ), dtype=np.int64)
    anchors = []
    for side, sg in (('S', 1), ('P', -1)):
        at = [AN['x'] + 0.5, YC + sg * AN['dy'] + 0.5, AN['ring_z']]
        deg = sg * AN['rotate']
        n = DG.collide(occ_k, asrc, AN['scale'], apiv, at, deg)
        crown = DG.anchor_world([23, 16, 2], AN['scale'], apiv, at, deg)
        sup = min((math.dist((at[0], at[1], at[2]), (p[0] + 0.5, p[1] + 0.5, p[2] + 0.5)) for p in occ if abs(p[0] - at[0]) < 6 and abs(p[1] - at[1]) < 6 and abs(p[2] - at[2]) < 6), default=99)
        hz = AN['hawse']                                                 # 錨鏈孔：船殼在那個 x、z 的外緣（meta hawse，誰都能標）
        hy = max(y for y in range(YC, SY) if (hz[0], y, hz[1]) in hullset) if sg > 0 else min(y for y in range(0, YC + 1) if (hz[0], y, hz[1]) in hullset)
        hawse = '%g,%g,%g' % (hz[0] + 0.5, hy + 0.5, hz[1] + 0.5)
        anchors.append({'name': '錨-' + side, 'at': at, 'pivot': apiv, 'scale': AN['scale'], 'rotate': deg, 'collide': n, 'crown_z': round(crown[2], 1),
                        'ring_to_solid': round(sup, 2), 'meta': {'kind': 'anchor', 'anchor': 'bower', 'hawse': hawse}})
    out['anchors'] = anchors
    R['anchors'] = [{k: v for k, v in a.items() if k != 'meta'} for a in anchors]

    if probe:
        print(json.dumps({'probe': probe, 'hold': R['hold'], 'ladder_points': R['ladder']['points']}, ensure_ascii=False))
        return
    mk = os.path.join(HERE, 'masks', 'hold')
    os.makedirs(mk, exist_ok=True)
    lists = []
    for nm in ('rudder', 'hold', 'magazine', 'ladder'):
        cells = out[nm]['cells'] if nm == 'rudder' else out[nm]
        fn = os.path.join(mk, nm + '.vox.txt')
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 皇家號 %s（draft_hold.py）x,y,z,color —— at 0,0,0、整船的框\n' % nm)
            f.write('\n'.join('%d,%d,%d,%d' % (p[0], p[1], p[2], c) for p, c in sorted(cells.items())) + '\n')
        lists.append({'file': os.path.relpath(fn, HERE).replace('\\', '/'), 'cells': len(cells), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()})
    R['lists'] = lists
    place = {'rudder': {k: v for k, v in out['rudder'].items() if k != 'cells'}, 'barrels': out['barrels'], 'barrel_source': PB['source'], 'barrel_scale': PB['scale'],
             'barrel_pivot': bpiv, 'ladder_points': out['ladder_points'], 'anchors': out['anchors'], 'anchor_source': AN['source'],
             'magazine_meta': {'kind': 'magazine', 'pos': 'aft', 'powder_lb': R['magazine']['powder_lb'], 'hoist': '甲板-main/梯子/hold'}}
    with open(os.path.join(HERE, 'hold_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_hold.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'lists'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
