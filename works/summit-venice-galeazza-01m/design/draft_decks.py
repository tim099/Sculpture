"""威尼斯 galeazza（TASK-1302）步驟 5：甲板、corsia、划凳、梯子（Ship_Decks §9.3）。

層：main（主甲板＝划槳甲板，板 z 31、第一層空氣 z 32；含舷外槳架上的板、兩座樓底下的地板）、
    forecastle（圓形艏樓頂，板 z 51）、quarter（艉樓平台，板 z 51）。
另有：corsia（中央走道，實心 z 32–37、兩頭兩階）、划凳（每支槳一張，凳面 z 34）、
    梯子：艏樓 S 舷一座、艉樓 S 舷一座（P 舷用 mirror=y 關聯）、底艙一座（corsia 中線往下）。
輸出 masks/decks/*.vox.txt、ladders.json（foot／lo／hi／head）、deck_meta.json；只放船殼 01＋02 沒有的格。
梯子的擺法：每階升 3 格、往前 2 格（踏板＋豎板，一階一階面接著面）；梯頂最後一階正前方就是上層的板（head ＝ 板上第一層空氣），
    艙口只開在「站在那一階、頭上 1.2 m 會撞到上層樑」的那幾階上面（Ship_Decks §9.3 開梯口的做法）。
"""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy import ndimage

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from lines import Lines, load_plan

WOOD, PLANK, DARK = 141, 141, 68
STEP_RISE, STEP_RUN, HEAD = 3, 2, 12


def main():
    plan = load_plan(D)
    L = Lines(plan)
    YC = plan['space']['yc']
    NX, NY, NZ = plan['space']['hull']
    lay = {k: v['v'] for k, v in plan['layout'].items()}
    occ = np.zeros((NX, NY, NZ), np.uint8)
    for p in ('masks/hull/hull_01.vox.txt', 'masks/upper/upper_01.vox.txt'):
        a = np.loadtxt(D / p, delimiter=',', dtype=np.int32)
        occ[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]

    DZ = lay['deck_top_z']                     # 31
    B2 = int(plan['lines']['half_beam']['v'])
    OUT = B2 + lay['postizza_out']             # 58
    bc, sc = lay['bow_castle'], lay['stern_castle']
    TZ = bc['deck_z']                          # 51：兩座樓頂的板
    xa, xb = sc['x_front'], bc['x_back']       # 150、466
    oars_x = [int(math.floor(lay['oar_x0'] + i * lay['oar_pitch'])) for i in range(plan['oars']['per_side'])]
    cor = lay['corsia']
    bench = lay['bench']

    parts = {k: {} for k in ('deck_main', 'corsia', 'benches', 'deck_bow', 'deck_stern', 'ladder_bow', 'ladder_stern', 'ladder_hold')}
    taken = set()

    def put(part, x, y, z, c):
        if occ[x, y, z] or (x, y, z) in taken:
            return
        parts[part][(x, y, z)] = c
        taken.add((x, y, z))

    hb = lambda x, z: float(L.hb(x + 0.5, z + 0.5))
    shx = [float(L.sheer(x + 0.5)) for x in range(NX)]
    sx0 = int(next(x for x in range(int(L.x_sh), NX) if hb(x, L.z_side) >= 2))

    # ── 梯子（先排，甲板讓開艙口） ──
    def ladder(part, name, x_foot, y0, d, z_foot, z_head, plank_bottom):
        """x_foot：梯腳站的那一格；d ＝ ±1 往上走的方向；y0..y0+4 五格寬；回傳 (踏板格, 艙口格, 點)。"""
        n = math.ceil((z_head - z_foot - STEP_RISE) / STEP_RISE)
        cells, hatch = {}, set()
        ym = y0 + 2
        prev_top = z_foot - 1
        for k in range(1, n + 1):
            s = z_foot + STEP_RISE * k                 # 站在第 k 階的那一格
            xs = [x_foot + d * (2 * k - 1), x_foot + d * (2 * k)]
            for y in range(y0, y0 + 5):
                for x in xs:
                    cells[(x, y, s - 1)] = WOOD          # 踏板
                for z in range(max(prev_top, z_foot), s - 1):   # 豎板：從上一階的踏板那一層起（面接著面）；第一階從地板起
                    cells[(xs[0], y, z)] = WOOD
            prev_top = s - 1
            if s + HEAD > plank_bottom:
                for x in xs:
                    for y in range(y0, y0 + 5):
                        hatch.add((x, y))
        s_hi = z_foot + STEP_RISE * n
        x_hi = x_foot + d * (2 * n)
        pts = dict(foot=[x_foot, ym, z_foot], lo=[x_foot + d * 1, ym, z_foot + STEP_RISE],
                   hi=[x_hi, ym, s_hi], head=[x_hi + d * 2, ym, z_head])
        assert z_head - s_hi <= STEP_RISE, (name, z_head, s_hi)
        return cells, hatch, pts

    lad = {}
    # 艏樓：S 舷 y 172..176、梯腳 x 470 往 +x
    c_bow, h_bow, p_bow = ladder('ladder_bow', 'bow-S', 470, YC + 12, +1, DZ + 1, TZ + 1, TZ - 2)
    # 艉樓：S 舷 y 172..176、梯腳 x 148 往 −x
    c_st, h_st, p_st = ladder('ladder_stern', 'stern-S', xa - 2, YC + 12, -1, DZ + 1, TZ + 1, TZ - 2)
    # 底艙：中線 y 158..162、梯腳 x 190 往 +x，頂上是 corsia 頂（第一層空氣 top_z + 1）
    xf = 190
    zf_hold = int(max(z for z in range(NZ) if occ[xf, YC, z]) + 1)
    for x in range(xf, xf + 26):                        # 梯子一路要踩在船殼內底上方（量最高那格）
        zf_hold = max(zf_hold, int(max(z for z in range(NZ) if occ[x, YC, z] and z < 20) + 1))
    c_hold, h_hold, p_hold = ladder('ladder_hold', 'hold', xf, YC - 2, +1, zf_hold, cor['top_z'] + 1, DZ - 2)
    lad['bow-S'], lad['stern-S'], lad['hold'] = p_bow, p_st, p_hold
    for part, cells in (('ladder_bow', c_bow), ('ladder_stern', c_st), ('ladder_hold', c_hold)):
        for (x, y, z), c in cells.items():
            put(part, x, y, z, c)
    # 底艙梯在 corsia 裡要整條井：從梯頂那一端往回、站上去會撞到 corsia／甲板的那幾階上面全開
    hold_well = set(h_hold)
    hatch_top = set(h_bow) | set(h_st)
    hatch_top |= {(x, 2 * YC - y) for x, y in hatch_top}      # 板是一整件：P 舷（鏡像那座）的艙口一起開

    # ── 艏樓、艉樓頂板（z 51）＋樑（z 49–50） ──
    cx, r, th = bc['cx'], bc['r'], bc['wall']
    for x in range(xb, NX):
        for y in range(NY):
            dy = abs(y - YC)
            rr = math.hypot(x + 0.5 - (cx + 0.5), y - YC) if x >= cx else dy
            if rr > r + 0.5 - th:
                continue
            if (x, y) in hatch_top:
                continue
            put('deck_bow', x, y, TZ, PLANK)
            if (x - xb) % 12 in (5, 6) and x > xb + 2:
                for z in (TZ - 2, TZ - 1):
                    put('deck_bow', x, y, z, DARK)
    for x in range(sx0 + 2, xa + 2):
        h = hb(x, L.z_side)
        for y in range(NY):
            if abs(y - YC) > h - 2 or (x, y) in hatch_top:
                continue
            put('deck_stern', x, y, TZ, PLANK)
            if (x - sx0) % 12 in (5, 6) and x < xa:
                for z in (TZ - 2, TZ - 1):
                    put('deck_stern', x, y, z, DARK)

    # ── 主甲板板 z 31：船殼裡＋舷外槳架上（|dy| ≤ OUT − 2）＋艏樓圓盤；樑 z 29–30 只在船殼裡 ──
    beam_x = set()
    for i in range(len(oars_x) + 1):
        beam_x.add(int(round(lay['oar_x0'] + (i - 0.5) * lay['oar_pitch'])))
    beam_x |= set(range(sx0 + 8, xa, 12)) | set(range(xb + 6, int(L.x_st) - 6, 12))
    for x in range(sx0, NX):
        h_in = hb(x, DZ)
        for y in range(NY):
            dy = abs(y - YC)
            inside = dy <= h_in
            waist = xa <= x <= xb and dy <= OUT - 2
            disk = x >= xb and ((math.hypot(x + 0.5 - (cx + 0.5), y - YC) if x >= cx else dy) <= r + 0.5 - th)
            if not (inside or waist or disk):
                continue
            if (x, y) in hold_well:
                continue
            put('deck_main', x, y, DZ, PLANK)
            if x in beam_x and dy <= hb(x, DZ - 1) and (x, y) not in hold_well:
                for z in (DZ - 2, DZ - 1):
                    put('deck_main', x, y, z, DARK)

    # ── corsia：x 156..459 實心 z 32..37、兩頭各一階（z 32..34），底艙梯井穿過 ──
    c0, c1 = xa + 6, xb - 7
    for x in range(xa + 2, xb):
        for y in range(YC - cor['half_w'], YC + cor['half_w'] + 1):
            if (x, y) in hold_well:
                continue
            top = cor['top_z'] if c0 <= x <= c1 else DZ + 3
            for z in range(DZ + 1, top + 1):
                put('corsia', x, y, z, DARK if abs(y - YC) == cor['half_w'] else WOOD)

    # ── 划凳：每支槳一張（槳的船尾那一側 x−5..x−2），凳面 z 34、腳 z 32–33 在 |dy| 8、31、54 ──
    for xo in oars_x:
        for x in range(xo - 5, xo - 1):
            for side in (1, -1):
                for d in range(bench['y_in'], bench['y_out'] + 1):
                    y = YC + side * d
                    put('benches', x, y, bench['top_z'], WOOD)
                    if d in (bench['y_in'], 31, bench['y_out']):
                        for z in range(DZ + 1, bench['top_z']):
                            put('benches', x, y, z, DARK)

    # ── 驗 ──
    union = occ > 0
    for part, cells in parts.items():
        for (x, y, z) in cells:
            union[x, y, z] = True
    # P 舷梯子（mirror=y）也要算進去
    mir = {}
    for part in ('ladder_bow', 'ladder_stern'):
        for (x, y, z), c in parts[part].items():
            mir[(x, 2 * YC - y, z)] = c
    clash = [k for k in mir if union[k]]
    for k in mir:
        union[k] = True
    # 甲板板在 P 舷的艙口也要開（板是整件、兩舷一起）：檢查 P 舷梯子上面沒有板
    lab, ncomp = ndimage.label(union)
    voids = ndimage.binary_fill_holes(np.pad(union, 1))[1:-1, 1:-1, 1:-1] & ~union
    vl, nv = ndimage.label(voids)
    stats = {'parts': {k: len(v) for k, v in parts.items()}, 'mirror_ladder_cells': len(mir), 'mirror_ladder_clash': len(clash),
             'union_components': int(ncomp), 'union_enclosed_air': int(voids.sum()), 'void_regions': int(nv),
             'ladders': lad, 'zf_hold': zf_hold}
    if nv:
        stats['void_bbox'] = [[int(a) for a in np.argwhere(vl == i + 1).min(0)] + [int(a) for a in np.argwhere(vl == i + 1).max(0)] for i in range(min(nv, 6))]
    out = D / 'masks/decks'
    out.mkdir(parents=True, exist_ok=True)
    shas = {}
    for part, cells in parts.items():
        body = ''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(cells.items())).encode('ascii')
        (out / f'{part}.vox.txt').write_bytes(body)
        shas[part] = hashlib.sha256(body).hexdigest()[:16]
    stats['sha16'] = shas
    (D / 'ladders.json').write_text(json.dumps(lad, indent=1) + '\n', encoding='utf-8')
    meta = {
        'deck_main': dict(kind='deck', deck='main', level=0, name='主甲板（划槳甲板）', floor=f'{sx0}:{DZ + 1},{int(cx + r)}:{DZ + 1}', thick=3,
                          walk=f'{xa + 2}:{DZ + 4},{c0 - 1}:{DZ + 4},{c0}:{cor["top_z"] + 1},{c1}:{cor["top_z"] + 1},{c1 + 1}:{DZ + 4},{xb - 1}:{DZ + 4}',
                          walk_y=f'{YC - cor["half_w"]}:{YC + cor["half_w"]}'),
        'deck_bow': dict(kind='deck', deck='forecastle', level=1, name='艏樓（圓形砲樓頂）', floor=f'{xb}:{TZ + 1},{int(cx + r)}:{TZ + 1}', thick=3),
        'deck_stern': dict(kind='deck', deck='quarter', level=2, name='艉樓平台', floor=f'{sx0 + 2}:{TZ + 1},{xa + 1}:{TZ + 1}', thick=3),
    }
    (D / 'deck_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (D / 'verify_decks.json').write_text(json.dumps(stats, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    main()
