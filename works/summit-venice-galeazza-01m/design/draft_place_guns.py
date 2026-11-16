"""威尼斯 galeazza（TASK-1302）步驟 9：32 門砲的擺法（Ship_Guns §4.2：每門從砲門外往裡退到零碰撞——模型每一格的格心＋八角不在實心裡，再要求砲口在船殼外）。

de Zuanne 1686 的 32 門（plan.json guns.src）；每一門的位置是設計：
  艏樓下層（主甲板 z 32）：2 × ven50（meadow 的 corsiero，平行朝前、離中線 ±13 格）、2 × ven20（±36°）、4 × ven30c（兩舷側砲門 x 486／504）
  艏樓頂（z 52）：2 × ven14（±18°）、2 × ven6（meadow 的 falcone，±45°）、4 × ven14p（±72°、兩舷 x 510）
  艉樓下艙（主甲板 z 32）：2 × ven30（艉封板窗、朝後）、2 × ven30c（側砲門 x 128）
  艉樓平台（z 52）：2 × ven14（x 128 欄杆砲眼）、2 × ven3（x 147 欄杆砲眼）
  兩舷舷牆頂（z 49）：8 × ven14p（槳與槳之間的叉架，Furttenbach 1629）
世界座標：x 船長、y 寬（中線 160，S 舷 y > 160）、z 高；角度 a：0 ＝ 船頭 +x、+90 ＝ S 舷；模型 rotate z ＝ a − 90（meadow corsiero 的 −90 ＝ 朝前）。
讀：組裝件的匯出清單（argv[1]）＋各砲件的格子清單；寫 gun_layout.json（每門的 host、at、pivot、rotate、scale、meta、讀數）。
"""
import json
import math
from pathlib import Path
import sys

import numpy as np

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from lines import Lines, load_plan

YC = 160
SCR = Path(sys.argv[2]) if len(sys.argv) > 2 else None


def load_cells(p):
    a = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int64, ndmin=2)
    return a[:, :3]


def main():
    plan = load_plan(D)
    L = Lines(plan)
    solid = set(map(tuple, load_cells(sys.argv[1]).tolist()))
    vg = json.loads((D / 'verify_guns_venice.json').read_text(encoding='utf-8'))
    W = D.parent.parent
    MEADOW = {'ven50': ('meadow-venice-galea-01m-corsiero', 1.0, {'muzzle': [6, 34, 9], 'breech': [6, 7, 9]}, 6.5),
              'ven6': ('meadow-venice-galea-01m-falcone-6-veneto', 0.5, {'muzzle': [6, 44, 14], 'breech': [6, 5, 14]}, 6.5)}
    parts = {}
    for code, r in vg.items():
        parts[code] = dict(work=f'{D.parent.name}-gun-{code}', scale=0.5, cells=load_cells(D / f'masks/guns/gun-{code}.vox.txt'),
                           anchors=r['anchors'], ax=(r['size'][0] - 1) / 2 + 0.5)
    for code, (w, s, anc, ax) in MEADOW.items():
        parts[code] = dict(work=w, scale=s, cells=load_cells(SCR / f'{w}.txt'), anchors=anc, ax=ax)
    corners = np.array([[dx, dy, dz] for dx in (0.02, 0.98) for dy in (0.02, 0.98) for dz in (0.02, 0.98)] + [[0.5, 0.5, 0.5]])

    def world_pts(code, at, a):
        p = parts[code]
        th = math.radians(a - 90)
        R = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
        piv = np.array([p['ax'], 0.0, 0.0]) if code != 'ven14p' else np.array(vg['ven14p']['pivot'], float)
        loc = (p['cells'][:, None, :] + corners[None, :, :]).reshape(-1, 3) - piv
        return at + (loc * p['scale']) @ R.T, R, piv

    def anchor_world(code, at, name, a):
        p = parts[code]
        _, R, piv = world_pts(code, at, a)
        return at + ((np.array(p['anchors'][name], float) + 0.5 - piv) * p['scale']) @ R.T

    def hits(pts):
        c = np.floor(pts).astype(np.int64)
        return sum(1 for t in map(tuple, c.tolist()) if t in solid)

    bc = plan['layout']['bow_castle']['v']
    cx, cy, rr = bc['cx'] + 0.5, YC + 0.5, bc['r'] + 0.5
    hbf = lambda x: int(math.floor(float(L.hb(x + 0.5, L.z_side + 0.5))))
    sx0 = int(next(x for x in range(int(L.x_sh), 660) if float(L.hb(x + 0.5, L.z_side + 0.5)) >= 2))
    OUT = plan['lines']['half_beam']['v'] + plan['layout']['postizza_out']['v']
    oars_x = [int(math.floor(plan['layout']['oar_x0']['v'] + i * plan['layout']['oar_pitch']['v'])) for i in range(25)]
    G = []   # (name, code, host, z0, a, B 或 None, fixed_at 或 None)
    for sgn, sd in ((1, 'S'), (-1, 'P')):
        G.append((f'b50-{sd}', 'ven50', 'deck', 32, 0, (cx + math.sqrt(rr * rr - 13 * 13), cy + sgn * 13), None))   # 平行朝前、離中線 ±13
        a = sgn * 36
        G.append((f'b20-{sd}', 'ven20', 'deck', 32, a, (cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))), None))
        for i, xs in enumerate((486, 504), 1):
            G.append((f'b30c-{sd}{i}', 'ven30c', 'deck', 32, sgn * 90, (xs + 0.5, YC + 0.5 + sgn * (OUT + 0.5)), None))
        for code, a0, tag in (('ven14', 18, 'f14'), ('ven6', 45, 'f6'), ('ven14p', 72, 'fp')):
            a = sgn * a0
            G.append((f'{tag}-{sd}', code, 'deck-bow', 52, a, (cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))), None))
        G.append((f'fp-{sd}2', 'ven14p', 'deck-bow', 52, sgn * 90, (cx - 10, YC + 0.5 + sgn * (OUT + 0.5)), None))
        G.append((f's30-{sd}', 'ven30', 'deck', 32, 180, (sx0 + 0.0, YC + 0.5 + sgn * 10), None))
        G.append((f's30c-{sd}', 'ven30c', 'deck', 32, sgn * 90, (128.5, YC + 0.5 + sgn * (hbf(128) + 1)), None))
        G.append((f'q14-{sd}', 'ven14', 'deck-stern', 52, sgn * 90, (128.5, YC + 0.5 + sgn * (hbf(128) + 1)), None))
        G.append((f'q3-{sd}', 'ven3', 'deck-stern', 52, sgn * 90, (147.5, YC + 0.5 + sgn * (hbf(147) + 1)), None))
        for i, (o0, o1) in enumerate(((2, 3), (8, 9), (14, 15), (20, 21)), 1):
            xm = (oars_x[o0] + oars_x[o1]) // 2
            G.append((f'wp-{sd}{i}', 'ven14p', 'deck', 49, sgn * 90, None, (xm + 0.5, YC + 0.5 + sgn * (OUT - 1), 49.0)))

    placed, out = [], []
    for name, code, host, z0, a, B, fixed in G:
        d = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0])
        if fixed is not None:
            at = np.array(fixed)
            pts, _, _ = world_pts(code, at, a)
            h = hits(pts)
            back = 0.0
        else:
            # 砲口放在牆外 2 格，再沿 −d 每 0.5 格退；第一次零碰撞就停
            mz = anchor_world(code, np.zeros(3), 'muzzle', a)
            at = np.array([B[0], B[1], z0]) + d * 2.0 - np.array([mz[0], mz[1], 0.0])
            back, h = 0.0, None
            for k in range(0, 160):
                t = at - d * 0.5 * k
                pts, _, _ = world_pts(code, t, a)
                h = hits(pts)
                if h == 0:
                    at, back = t, 0.5 * k
                    break
            else:
                at = at - d * 0.5 * 159
        mz = anchor_world(code, at, 'muzzle', a)
        out_of_hull = None if B is None else float(np.dot(mz[:2] - np.array(B), d[:2]))
        ray = sum(1 for k in range(1, 40) if tuple(np.floor(mz + d * k).astype(int).tolist()) in solid)
        pts, _, piv = world_pts(code, at, a)
        arc = None
        if code == 'ven14p':                                    # 叉架迴旋砲（mount=turret）：每 5° 量零碰撞，取兩邊對稱、最大到 ±70° 的轉角
            arc = 0
            for k in range(5, 75, 5):
                if hits(world_pts(code, at, a + k)[0]) or hits(world_pts(code, at, a - k)[0]):
                    break
                arc = k
            for k in range(-arc, arc + 1, 5):
                for t in map(tuple, np.floor(world_pts(code, at, a + k)[0]).astype(np.int64).tolist()):
                    solid.add(t)                                # 轉得到的範圍都佔著
        for t in map(tuple, np.floor(pts).astype(np.int64).tolist()):
            solid.add(t)                                        # 後面的砲要讓開前面的
        out.append(dict(name=name, gun=code, host=host, work=parts[code]['work'], at=[round(v, 3) for v in at.tolist()],
                        pivot=[round(v, 3) for v in piv.tolist()], rotate=[0, 0, a - 90], scale=parts[code]['scale'],
                        hits=h, back=back, arc=arc, muzzle=[round(v, 2) for v in mz.tolist()], muzzle_out=out_of_hull, ray_hits=ray))
    bad = [o['name'] for o in out if o['hits'] or (o['muzzle_out'] is not None and o['muzzle_out'] < 0) or o['ray_hits']]
    res = dict(guns=len(out), bad=bad, by_gun={c: sum(1 for o in out if o['gun'] == c) for c in sorted({o['gun'] for o in out})}, layout=out)
    (D / 'gun_layout.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for o in out:
        print(f"{o['name']:9s} {o['gun']:6s} hits={o['hits']} back={o['back']:5.1f} out={o['muzzle_out']} ray={o['ray_hits']} arc={o['arc']}")
    print('bad', bad, res['by_gun'])


if __name__ == '__main__':
    main()
