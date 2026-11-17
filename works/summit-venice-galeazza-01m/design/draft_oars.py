"""威尼斯 galeazza（TASK-1302）步驟 13：槳（Ship_Oars §9.10）—— 每舷 25 支、每支 6 人、14 m（plan oars）。

- 槳是共用元件：皇家號的 galère 槳 apex-one-reale-01m-oar（13.15 m、0.05 m、7 人；pivot (3,88,38)、blade (3,260,5)、seat (5,68,33)），
  照長度放大 scale 0.5 × 14 / 13.15（⚠ 放大後槳柄、槳葉跟著粗 6%）。元件的格清單複製在 masks/oars/ref_apex-one-reale-01m-oar.list.txt（只拿來量）。
- 本船的槳從舷牆的拱形槳門穿出（draft_upper.py：舷牆 |dy| 57–58、槳門 |x − xo| ≤ 2、z 38–42）⇒ pivot ＝ 槳門洞底往上一格（z 39）、
  舷牆厚度的正中（S 舷 y 218.0；P 舷照皇家號 y → 321 − y、mirror=y）。槳 x ＝ plan 槳位 xo（160 起每 1.25 m）的格中心。
- 每一支量：
  ① 槳的格（格心＋八角，照元件放大後的位置）落在船的實心裡幾點（船殼、上層、甲板、划凳、桅、底艙…全算；扣掉舵柄口）；
  ② 槳葉（元件最外 1.6 m）中心離水線幾格；③ 槳座旁 8 格內有船的格（遊戲的掛點）；
  ④ 槳手：seat 起沿槳柄往船裡每 0.6 m 一位、共 6 位，每一位照遊戲的找法（那一點往下 8 格內第一個腳下實心、頭上 14 格空的格）站得住。
  ⑤ 划槳掃掠：繞 pivot 直立軸每 5° 掃 ±30°、槳葉抬 0／12°，槳的格心落在船的實心幾點；每支再照 1° 找掃得開幾度 ⇒ meta stroke_deg
     （兩頭的槳柄會掃到艉樓前牆 x 150、艏樓後牆 x 468 ⇒ 那幾支 stroke 小於 30；遊戲的動畫照 meta 掃）。
  反向對照：--probe-sink=N 把第 1 支往下沉 N 格 ⇒ 只有它該報碰撞。
輸出 oar_layout.json、verify_oars.json。
"""
import json
import math
from pathlib import Path
import sys

import numpy as np

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from lines import load_plan

REF = dict(work='apex-one-reale-01m-oar', file='masks/oars/ref_apex-one-reale-01m-oar.list.txt', len_m=13.15,
           pivot=(3, 88, 38), blade=(3, 260, 5), seat=(5, 68, 33), blade_len_cells=32)


def load(occ, p, val=None):
    a = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    occ[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3] if val is None else val


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sink = int(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--probe-sink=')), '0'))
    plan = load_plan(D)
    NX, NY, _ = plan['space']['hull']
    NZ = 360
    YC = plan['space']['yc']
    lay = {k: v['v'] for k, v in plan['layout'].items()}
    WL = plan['waterline']['z']
    O = plan['oars']
    occ = np.zeros((NX, NY, NZ), np.uint8)
    load(occ, D / 'masks/hull/hull_01.vox.txt')
    load(occ, D / 'masks/upper/upper_01.vox.txt')
    for p in sorted((D / 'masks/upper').glob('hull_cut_*.vox.txt')):
        load(occ, p, 0)
    for sub in ('decks', 'deco', 'rig', 'hold', 'helm'):
        for p in sorted((D / 'masks' / sub).glob('*.vox.txt')):
            if p.name == 'hatch.vox.txt':
                continue
            load(occ, p)
    for p in ('ladder_bow', 'ladder_stern'):
        a = np.loadtxt(D / f'masks/decks/{p}.vox.txt', delimiter=',', dtype=np.int32)
        occ[a[:, 0], 2 * YC - a[:, 1], a[:, 2]] = a[:, 3]
    solid = occ > 0

    src = np.loadtxt(D / REF['file'], delimiter=',', comments='#', dtype=np.int32)[:, :3].astype(float)
    length_m = float(O['length_m'])
    s = round(0.5 * length_m / REF['len_m'], 4)
    piv = np.array(REF['pivot'], float) + 0.5
    blade_cells = src[src[:, 1] >= src[:, 1].max() - REF['blade_len_cells'] + 1]
    blade_c = blade_cells.mean(0) + 0.5
    seat_src = np.array(REF['seat'], float) + 0.5

    port = lay['oar_port']
    per = int(O['per_side'])
    rowers = int(O['rowers_per_oar'])
    xs = [int(math.floor(lay['oar_x0'] + i * lay['oar_pitch'])) for i in range(per)]
    OUT = int(plan['lines']['half_beam']['v']) + lay['postizza_out']           # 58
    y_mid = YC + OUT - 0.5 + 0.5                                               # 舷牆 |dy| 57–58 ⇒ 連續座標 217..219 的正中 218.0
    z_piv = port['z0'] + 1 + 0.5                                               # 洞底 z 38 往上一格 z 39 的格中心
    corners = np.array([[dx, dy, dz] for dx in (-.5, .5) for dy in (-.5, .5) for dz in (-.5, .5)]) * s

    def place(at, mirror):
        rel = (src + 0.5 - piv) * s
        if mirror:
            rel[:, 1] *= -1
        return at + rel

    def stand(x, y, z0):
        """遊戲的找法（簡版）：那一點往下 8 格內第一個腳下實心、頭上 14 格空的格。"""
        xi, yi = int(math.floor(x)), int(math.floor(y))
        for z in range(int(math.floor(z0)), int(math.floor(z0)) - 9, -1):
            if solid[xi, yi, z - 1] and not solid[xi, yi, z:z + 14].any():
                return z
        return None

    layout, bad = [], []
    for side, sgn in (('S', 1), ('P', -1)):
        for i, xo in enumerate(xs):
            y_at = y_mid if sgn > 0 else NY - y_mid
            at = np.array([xo + 0.5, y_at, z_piv])
            if sink and side == 'S' and i == 0:
                at[2] -= sink
            pts = place(at, sgn < 0)
            hits = 0
            for p in pts:
                for c in corners:
                    q = np.floor(p + c).astype(int)
                    if solid[q[0], q[1], q[2]]:
                        hits += 1
                        break
            # 划槳掃掠（遊戲的動畫：繞 pivot 的直立軸前後掃 ±stroke、回槳時繞沿船身的軸把槳葉抬 dip）：
            # 每 5° 一個姿勢 × 槳葉抬 0／12°，槳的格心落在船的實心幾點（只是畫面，但穿牆會被看見）
            rel = pts - at

            def hits_at(th, dip):
                ph, t = math.radians(dip), math.radians(th)
                yy = rel[:, 1] * math.cos(ph) - sgn * rel[:, 2] * math.sin(ph)
                zz = sgn * rel[:, 1] * math.sin(ph) + rel[:, 2] * math.cos(ph)
                xx = rel[:, 0] * math.cos(t) - yy * math.sin(t)
                y2 = rel[:, 0] * math.sin(t) + yy * math.cos(t)
                q = np.floor(np.stack([xx, y2, zz], 1) + at).astype(int)
                return int(solid[q[:, 0], q[:, 1], q[:, 2]].sum())

            sweep = {f'{th:+d}/{dip}': n for dip in (0, 12) for th in range(-30, 31, 5) for n in [hits_at(th, dip)] if n}
            # 這一支前後掃得開幾度（每 1°、兩個方向、槳葉抬 0／12° 都 0 點）⇒ meta stroke_deg（遊戲的動畫是對稱的）
            stroke = 30
            for th in range(1, 31):
                if any(hits_at(sg * th, dip) for sg in (1, -1) for dip in (0, 12)):
                    stroke = th - 1
                    break
            bc = at + (blade_c - piv) * s * np.array([1, sgn, 1])
            seat = at + (seat_src - piv) * s * np.array([1, sgn, 1])
            hang = int(solid[int(at[0]) - 8:int(at[0]) + 9, int(at[1]) - 8:int(at[1]) + 9, int(at[2]) - 8:int(at[2]) + 9].sum())
            # 槳柄往船裡的方向（S 舷 −y）
            stands = []
            for k in range(rowers):
                ry = seat[1] - sgn * 6 * k
                stands.append(stand(seat[0], ry, seat[2]))
            name = f'oar-{side}{i + 1:02d}'
            row = dict(name=name, side=side, at=[round(float(v), 3) for v in at], mirror='y' if sgn < 0 else '',
                       clash_cells=hits, blade_z=round(float(bc[2]), 2), blade_above_wl_m=round(float(bc[2] - WL) * 0.1, 2),
                       seat=[round(float(v), 2) for v in seat], hang_cells=hang, rowers_stand=stands, sweep_hits=sweep, stroke_deg=stroke)
            layout.append(row)
            if hits or hang == 0 or any(v is None for v in stands):
                bad.append(name)
    bz = [r['blade_above_wl_m'] for r in layout]
    stats = dict(scale=s, ref=REF['work'], per_side=per, rowers=rowers, xs=xs, pivot_y_S=y_mid, pivot_z=z_piv,
                 count=dict(S=sum(r['side'] == 'S' for r in layout), P=sum(r['side'] == 'P' for r in layout)),
                 clash_total=sum(r['clash_cells'] for r in layout), clash_oars=[r['name'] for r in layout if r['clash_cells']],
                 blade_above_wl_m=[min(bz), max(bz)], hang_min=min(r['hang_cells'] for r in layout),
                 rowers_standing=sum(sum(v is not None for v in r['rowers_stand']) for r in layout), rowers_needed=len(layout) * rowers,
                 stand_z=sorted({v for r in layout for v in r['rowers_stand'] if v is not None}), bad=bad, probe_sink=sink,
                 sweep_oars={r['name']: r['sweep_hits'] for r in layout if r['sweep_hits']},
                 stroke_limited={r['name']: r['stroke_deg'] for r in layout if r['stroke_deg'] < 30})
    if not sink:
        meta = dict(ref=REF, scale=s, oars=[dict(name=r['name'], at=r['at'], mirror=r['mirror'], side=r['side'], stroke_deg=r['stroke_deg']) for r in layout],
                    meta=dict(kind='oar', rowers=rowers, stroke_deg=30, dip_deg=12))
        (D / 'oar_layout.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        (D / 'verify_oars.json').write_text(json.dumps(dict(stats, layout=layout), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    main()
