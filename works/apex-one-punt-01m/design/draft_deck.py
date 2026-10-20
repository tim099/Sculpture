# 蓬特號 新圖紙 02（TASK-0754）：甲板（橫樑穿出船殼）、貨艙地板、艙口、艏艉平台、舵柱、梯子、truss 叉柱
#   ⇒ masks/deck/<件>.vox.txt、deck_placement.json（梯子固定點、甲板 meta）、verify_deck.json、sheet02_deck_v1.png
#   用法：python -I -X utf8 draft_deck.py [--probe=deck_z=+1]
#   · 佔用照船殼清單（masks/hull/hull.vox.txt ＝ 作品，階段一 delta_apply 讀回差 0）。只讀，不碰作品。
#   · 每件都用整船的框（280×201×140、at 0,0,0）；後面的件扣掉前面已經有的格：船殼 ＞ 甲板 ＞ 貨艙 ＞ 平台 ＞ 叉柱 ＞ 梯子。
import sys, os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import rgb, font, SX, SY, SZ, V

sys.stdout.reconfigure(encoding='utf-8')


def load_list(path):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros((SX, SY, SZ), np.uint8)
    G[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    return G


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan()
    L = HL.Lines(plan)
    K = {k: V(v) for k, v in plan['deck'].items()}
    for k, d in probe.items():
        K[k] = K[k] + d
    C = {k: V(v) for k, v in plan['deck']['colors']['v'].items()} if isinstance(plan['deck']['colors'], dict) and 'v' in plan['deck']['colors'] else {k: V(v) for k, v in plan['deck']['colors'].items()}
    YC = L.YC
    hull = load_list(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'))
    occ = hull > 0
    S = np.zeros((SX, SY, SZ), bool)
    S[:, :, :91] = L.solid(0, SX - 1, 90, 0)            # 線形圍出來的（含殼）
    inside = S & ~occ                                   # 船裡的空氣
    parts = {}
    out = {'ladders': {}, 'decks': {}, 'posts': {}}
    R = {}

    def put(D, x, y, z, c):
        if 0 <= x < SX and 0 <= y < SY and 0 <= z < SZ and not occ[x, y, z]:
            D[(x, y, z)] = c

    def commit(name, D):
        parts[name] = D
        for (x, y, z) in D:
            occ[x, y, z] = True

    dz = int(K['deck_z'])                               # 甲板板那一層（站的地方 ＝ dz＋1）
    mx, my, mr = K['mast_x'] + 0.5, YC + 0.5, K['mast_r']
    in_mast = lambda x, y: (x + 0.5 - mx) ** 2 + (y + 0.5 - my) ** 2 <= mr * mr
    # ───── 甲板-main：橫樑（穿出船殼 beam_out 格）＋甲板板（艙口、桅孔留空）─────
    D = {}
    hx0, hx1, hh = K['hatch_x'][0], K['hatch_x'][1], K['hatch_half']
    beams = list(range(K['beam_first'], K['beam_last'] + 1, K['beam_pitch']))
    for bx in beams:
        for x in (bx, bx + 1):
            for z in (dz - 2, dz - 1):
                ys = np.where(S[x, :, z])[0]
                if len(ys) < 5:
                    continue
                y0, y1 = ys.min() - K['beam_out'], ys.max() + K['beam_out']
                for y in range(y0, y1 + 1):
                    if not in_mast(x, y):
                        put(D, x, y, z, C['beam'])
    for x in range(SX):
        for y in range(SY):
            if inside[x, y, dz] and not (hx0 <= x <= hx1 and abs(y - YC) <= hh) and not in_mast(x, y):
                put(D, x, y, dz, C['deck'])
    # 甲板範圍：每一站有板的 x
    dxs = sorted({x for (x, y, z) in D if z == dz})
    commit('deck_main', D)
    R['deck_main'] = {'cells': len(D), 'x': [dxs[0], dxs[-1]], 'beams': beams}
    # ───── 甲板-hold：貨艙地板（hold_x 範圍、z ≤ hold_z 的船裡全部填實 ＝ 壓艙＋地板）＋桅座 ─────
    D = {}
    hz = int(K['hold_z'])
    for x in range(K['hold_x'][0], K['hold_x'][1] + 1):
        for y in range(SY):
            for z in range(0, hz + 1):
                if inside[x, y, z]:
                    put(D, x, y, z, C['deck'] if z == hz else C['ballast'])
    commit('deck_hold', D)
    R['deck_hold'] = {'cells': len(D)}
    # ───── 平台（艏艉）：地板 pz、四周欄杆（船殼頂低於欄杆頂的地方才加）、前緣中間留梯口 ─────
    pz = int(K['plat_z'])
    for side, (px0, px1), edge in (('aft', K['plat_aft_x'], 'x1'), ('fwd', K['plat_fwd_x'], 'x0')):
        D = {}
        foot = {}
        for x in range(px0, px1 + 1):
            hbw = float(L.Bs(x + 0.5))
            for y in range(SY):
                if abs(y - YC) <= hbw - 0.5 and not occ[x, y, pz]:
                    # 這一柱的船殼頂
                    put(D, x, y, pz, C['deck'])
                    foot[(x, y)] = True
        # 欄杆：地板外圈那一格往上 rail_h 格（那一格已經是船殼 ⇒ 跳過）
        rail = {}
        for (x, y) in foot:
            nb = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            edge_cell = any(q not in foot and not occ[q[0], q[1], pz] for q in nb)
            if not edge_cell:
                continue
            front = (edge == 'x1' and x == px1) or (edge == 'x0' and x == px0)
            if front and abs(y - YC) <= K['plat_gap']:
                continue
            for z in range(pz + 1, pz + 1 + K['rail_h']):
                put(rail, x, y, z, C['rail'])
        D.update(rail)
        # 前緣底下兩根支柱（甲板 → 地板）
        fx = px1 if edge == 'x1' else px0
        for sy in (-1, 1):
            yy = YC + sy * K['plat_post_dy']
            for z in range(dz + 1, pz):
                for ddx in (0, 1 if edge == 'x0' else -1):
                    put(D, fx + ddx, yy, z, C['post'])
        # 舵柱（只有艉台）：地板往上 post_h，船殼內面往裡一格
        if side == 'aft':
            for sy in (-1, 1):
                x = K['rudder_post_x']
                ys = [y for y in range(SY) if (x, y) in foot]
                yy = (min(ys) + 1) if sy < 0 else (max(ys) - 1)
                pts = []
                for z in range(pz + 1, pz + 1 + K['rudder_post_h']):
                    for ddx in (0, 1):
                        for ddy in (0, -sy):
                            put(D, x + ddx, yy + ddy, z, C['post'])
                out['posts']['rudder-%s' % ('P' if sy < 0 else 'S')] = {'x': x, 'y': yy, 'top_z': pz + K['rudder_post_h']}
        commit('platform_' + side, D)
        R['platform_' + side] = {'cells': len(D), 'x': [px0, px1], 'rail_cells': len(rail)}
    # ───── truss 叉柱：甲板往上到 crutch_z，頂上兩根叉（沿 x 分開，繩從中間過）─────
    D = {}
    cy = YC + K['truss_dy']
    for cx in K['crutch_x']:
        for z in range(dz + 1, K['crutch_z'] + 1):
            put(D, cx, cy, z, C['post'])
        put(D, cx - 1, cy, K['crutch_z'], C['post'])              # 叉底橫木（叉只靠斜角相接會 6 連通斷開）
        put(D, cx + 1, cy, K['crutch_z'], C['post'])
        for z in range(K['crutch_z'] + 1, K['crutch_z'] + 4):
            put(D, cx - 1, cy, z, C['post'])
            put(D, cx + 1, cy, z, C['post'])
    commit('crutches', D)
    R['crutches'] = {'cells': len(D), 'x': K['crutch_x'], 'y': cy, 'top_z': K['crutch_z'] + 3}
    # ───── 梯子：hold（貨艙 → 甲板，艙口裡）、aft（甲板 → 艉台）、fwd（甲板 → 艏台）；兩邊扶手 ─────
    D = {}

    def ladder(nm, rungs, half, foot, head):
        for (x, z) in rungs:
            for y in range(YC - half, YC + half + 1):
                put(D, x, y, z, C['ladder'])
        for side in (-half - 1, half + 1):
            for k_, (x, z) in enumerate(rungs):
                z_from = foot[2] if k_ == 0 else rungs[k_ - 1][1]
                for zz in range(z_from, z + 3):
                    put(D, x, YC + side, zz, C['ladder'])
        out['ladders'][nm] = {'foot': foot, 'lo': [rungs[0][0], YC, rungs[0][1] + 1], 'hi': [rungs[-1][0], YC, rungs[-1][1] + 1], 'head': head}

    h0 = hz + 1
    rz = [h0 - 1 + 3 * k for k in range(1, 40) if h0 - 1 + 3 * k <= dz - 2]
    ladder('hold', [(hx0 + k, z) for k, z in enumerate(rz)], K['ladder_half'], [hx0 - 2, YC, h0], [hx1 + 3, YC, dz + 1])
    rz = [dz + 3 * k for k in range(1, 40) if dz + 3 * k <= pz]
    n = len(rz)
    ax1 = K['plat_aft_x'][1]
    ladder('aft', [(ax1 + n - k, z) for k, z in enumerate(rz)], K['ladder_half'], [ax1 + n + 2, YC, dz + 1], [ax1 - 2, YC, pz + 1])
    fx0 = K['plat_fwd_x'][0]
    ladder('fwd', [(fx0 - n + k, z) for k, z in enumerate(rz)], K['ladder_half'], [fx0 - n - 2, YC, dz + 1], [fx0 + 2, YC, pz + 1])
    commit('ladders', D)
    R['ladders'] = {'cells': len(D)}
    # ───── 讀數 ─────
    for nm, p4 in out['ladders'].items():
        R['ladders'][nm] = {k: {'at': v, 'empty': not occ[tuple(v)], 'solid_below': bool(occ[v[0], v[1], v[2] - 1]),
                                'clear_up': next((h for h in range(1, 15) if occ[v[0], v[1], v[2] + h]), 14)} for k, v in p4.items()}
    lab, ncomp = ndimage.label(occ)
    R['components'] = int(ncomp)
    la, na = ndimage.label(~occ)
    border = set(np.unique(np.r_[la[0].ravel(), la[-1].ravel(), la[:, 0].ravel(), la[:, -1].ravel(), la[:, :, 0].ravel(), la[:, :, -1].ravel()]))
    cav = [i for i in range(1, na + 1) if i not in border]
    R['cavities'] = len(cav)
    R['cavity_cells'] = int(sum((la == i).sum() for i in cav)) if cav else 0
    if cav:
        R['cavity_at'] = [np.argwhere(la == i)[0].tolist() for i in cav[:5]]
    R['mirror_diff_by_part'] = {}
    for nm, D in parts.items():
        A = np.zeros((SX, SY, SZ), bool)
        for p in D:
            A[p] = True
        R['mirror_diff_by_part'][nm] = int((A != A[:, ::-1, :]).sum())
    # 甲板 meta（floor：站的那一格；x 範圍照有板的那幾站）
    out['decks'] = {
        '甲板-main': {'kind': 'deck', 'deck': 'main', 'level': 1, 'name': '甲板', 'floor': '%d:%d,%d:%d' % (dxs[0], dz + 1, dxs[-1], dz + 1), 'thick': 3},
        '甲板-hold': {'kind': 'deck', 'deck': 'hold', 'level': 0, 'name': '貨艙', 'floor': '%d:%d,%d:%d' % (K['hold_x'][0], hz + 1, K['hold_x'][1], hz + 1), 'thick': 3},
        '平台-aft': {'kind': 'deck', 'deck': 'poop', 'level': 2, 'name': '艉台', 'floor': '%d:%d,%d:%d' % (K['plat_aft_x'][0], pz + 1, K['plat_aft_x'][1], pz + 1), 'thick': 1},
        '平台-fwd': {'kind': 'deck', 'deck': 'forecastle', 'level': 3, 'name': '艏台', 'floor': '%d:%d,%d:%d' % (K['plat_fwd_x'][0], pz + 1, K['plat_fwd_x'][1], pz + 1), 'thick': 1},
    }
    if probe:
        print(json.dumps({'probe': probe, **{k: R[k] for k in ('components', 'cavities', 'ladders')}}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'deck'), exist_ok=True)
    for nm, D in parts.items():
        with open(os.path.join(HERE, 'masks', 'deck', nm + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 蓬特號 %s（draft_deck.py）x,y,z,color —— at 0,0,0\n' % nm)
            f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(D.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1]))) + '\n')
    with open(os.path.join(HERE, 'deck_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_deck.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    # 圖紙：側面（中線往左舷一半剖開，看得到裡面）＋平面（甲板高度以上俯視）
    G = hull.copy()
    for D in parts.values():
        for p, c in D.items():
            G[p] = c
    sc = 4
    zt = 80
    W, H = SX * sc + 40, zt * sc + SY * sc + 120
    im = Image.new('RGB', (W, H), (246, 240, 226))
    d = ImageDraw.Draw(im)
    f, fs = font(22), font(15)
    d.text((20, 10), '蓬特號 新圖紙 02：甲板、貨艙、艏艉平台、舵柱、梯子、truss 叉柱（側面剖在中線；平面俯視）', fill=(40, 30, 20), font=f)
    oy = 44
    for x in range(SX):
        for z in range(zt):
            col = G[x, YC:, z]
            nz = np.nonzero(col)[0]
            if len(nz):
                d.rectangle([20 + x * sc, oy + (zt - 1 - z) * sc, 20 + x * sc + sc - 1, oy + (zt - z) * sc - 1], fill=rgb(int(col[nz[0]])))
    wl = plan['waterline']['z']
    d.line([20, oy + (zt - wl) * sc, 20 + SX * sc, oy + (zt - wl) * sc], fill=(30, 90, 200), width=2)
    for nm, p4 in out['ladders'].items():
        for k, v in p4.items():
            x, y, z = v
            d.ellipse([20 + x * sc - 3, oy + (zt - 1 - z) * sc - 3 + 2, 20 + x * sc + 3, oy + (zt - 1 - z) * sc + 3 + 2], outline=(200, 0, 0), width=2)
    oy2 = oy + zt * sc + 20
    for x in range(SX):
        for y in range(SY):
            col = G[x, y, :60]
            nz = np.nonzero(col)[0]
            if len(nz):
                d.rectangle([20 + x * sc, oy2 + y * sc, 20 + x * sc + sc - 1, oy2 + y * sc + sc - 1], fill=rgb(int(col[nz[-1]])))
    d.text((20, H - 30), '元件 %d｜空腔 %d｜甲板 %d 格（x %d–%d）、貨艙 %d、艉台 %d、艏台 %d、叉柱 %d、梯子 %d' % (
        R['components'], R['cavities'], R['deck_main']['cells'], dxs[0], dxs[-1], R['deck_hold']['cells'], R['platform_aft']['cells'], R['platform_fwd']['cells'],
        R['crutches']['cells'], R['ladders']['cells']), fill=(40, 30, 20), font=fs)
    im.save(os.path.join(HERE, 'sheet02_deck_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
