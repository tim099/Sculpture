# 蓬特號 新圖紙 05（TASK-0754）：舷側舵槳（古埃及蓬特船，通用部件；S 舷做、P 舷 mirror=y；整船的框、0.1 m）
#   C09／W12：兩支舵槳，各綁在一根高的舵柱上、另一處綁在船殼；舵手握插在槳柄上的舵柄、轉槳柄。
#   ⇒ masks/steer/rudder.vox.txt、steer_placement.json（固定點、兩個模型的 at／mirror／meta）、verify_steer.json
#   用法：python -I -X utf8 draft_steer.py [--sink=3]   （反向對照：整支往下沉幾格 ⇒ 碰撞要報出來）
#   · 槳柄從綁點 P（舵柱頂外側）往上伸到槳柄頂 T（stock-top），往下往外往後伸進水裡；槳葉中心 B 在水線下。
#   · 遊戲：模型 kind=rudder、繞槳柄（axis ＝ P→B）轉 ±35°（spin rudder）；stock-top 旁 8 格內有舵柱 ⇒ 掛得住。
#   · 量：0°、±35° 三個角度的格心＋八角不落在船的實心；P 舷照鏡像同一份讀數。
import sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import SX, SY, V
from draft_oars import occupancy

sys.stdout.reconfigure(encoding='utf-8')


def rot_axis(v, k, ang):
    c, s = math.cos(ang), math.sin(ang)
    return v * c + np.cross(k, v) * s + np.outer(v @ k, k) * (1 - c) if v.ndim == 2 else v * c + np.cross(k, v) * s + k * (k @ v) * (1 - c)


def main():
    sink = float(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--sink=')), 0))
    plan = HL.load_plan()
    K = {k: V(v) for k, v in plan['steer'].items()}
    C = K['colors']
    YC = plan['space']['yc']
    occ = occupancy(plan)
    P = np.array(K['lash'], float) - [0, 0, sink]
    B = np.array(K['blade_center'], float) - [0, 0, sink]
    d = (B - P) / np.linalg.norm(B - P)
    T = P - d * K['loom_up']
    w = np.cross(d, [0, 1, 0])
    w /= np.linalg.norm(w)
    n = np.cross(d, w)
    cells = {}

    def disk(c, r, col, thick=None):
        for x in range(int(c[0] - r - 2), int(c[0] + r + 3)):
            for y in range(int(c[1] - r - 2), int(c[1] + r + 3)):
                for z in range(int(c[2] - r - 2), int(c[2] + r + 3)):
                    q = np.array([x + 0.5, y + 0.5, z + 0.5]) - c
                    a = q @ d
                    if abs(a) > 0.5:
                        continue
                    rr = q - a * d
                    if np.linalg.norm(rr) <= r + 1e-6:
                        cells[(x, y, z)] = col
    # 槳柄：T → 槳葉頂（半徑 loom_r，往下細一點）
    blade_half = K['blade_len'] / 2
    top_b = B - d * blade_half
    Lloom = np.linalg.norm(top_b - T)
    for s in np.arange(0, Lloom + 1e-9, 0.25):
        r = K['loom_r'][0] + (K['loom_r'][1] - K['loom_r'][0]) * s / Lloom
        disk(T + d * s, r, C['loom'])
    # 槳葉：沿 d 長 blade_len、沿 w 寬 blade_w（中間寬、兩頭收）、沿 n 厚 1
    for s in np.arange(-blade_half, blade_half + 1e-9, 0.25):
        t = (s + blade_half) / K['blade_len']
        half_w = K['blade_w'] / 2 * (0.55 + 0.45 * math.sin(math.pi * min(1, t * 1.15)))
        for u in np.arange(-half_w, half_w + 1e-9, 0.25):
            p = B + d * s + w * u
            cells[tuple(np.floor(p).astype(int))] = C['tip'] if t > 0.9 else C['blade']
    # 舵柄：從槳柄頂往船裡、往下（舵手站在艉台上握）
    E = np.array(K['tiller_end'], float) - [0, 0, sink]
    Lt = np.linalg.norm(E - T)
    for s in np.arange(0, Lt + 1e-9, 0.25):
        p = T + (E - T) * s / Lt
        cells[tuple(np.floor(p).astype(int))] = C['tiller']
    arr = np.array([[x, y, z] for (x, y, z) in cells])
    # 讀數：0°、±35° 繞槳柄（過 P、沿 d）轉之後的碰撞
    corners = np.array([[dx, dy, dz] for dx in (-.5, .5) for dy in (-.5, .5) for dz in (-.5, .5)])
    R = {'cells': len(cells), 'loom_m': round((Lloom + K['blade_len']) * 0.1, 2), 'T': T.round(2).tolist(), 'P': P.tolist(), 'B': B.tolist(), 'axis': d.round(4).tolist(), 'collide': {}}
    pts = np.concatenate([arr + 0.5] + [arr + 0.5 + c for c in corners])
    for side, sgn in (('S', 1), ('P', -1)):
        for deg in (0, 35, -35):
            q = rot_axis(pts - P, d, math.radians(deg)) + P
            if sgn < 0:
                q[:, 1] = 2 * (YC + 0.5) - q[:, 1]
            ci = np.floor(q).astype(int)
            ok = (ci[:, 2] >= 0) & (ci[:, 1] >= 0) & (ci[:, 1] < SY)
            R['collide']['%s%+d' % (side, deg)] = int(occ[ci[ok, 0], ci[ok, 1], ci[ok, 2]].sum())
            if deg == 0:
                R['min_z_' + side] = float(q[:, 2].min())
    # 掛點：stock-top 旁 8 格內有船的格
    t = np.floor(T).astype(int)
    R['stock_top_near_cells'] = int(occ[t[0] - 8:t[0] + 9, t[1] - 8:t[1] + 9, t[2] - 8:t[2] + 9].sum())
    wl = plan['waterline']['z']
    R['blade_center_below_wl_m'] = round((wl + 0.5 - B[2]) * 0.1, 2)
    if sink:
        print(json.dumps({'sink': sink, 'collide': R['collide']}, ensure_ascii=False))
        return
    anchors = {'stock-top': np.floor(T).astype(int).tolist(), 'hinge': np.floor(P).astype(int).tolist(), 'blade-tip': np.floor(B + d * blade_half).astype(int).tolist(),
               'tiller-end': np.floor(E).astype(int).tolist()}
    meta = {'kind': 'rudder', 'rudder': 'quarter', 'hinge_x': P[0], 'hinge_y': P[1], 'hinge_z': P[2], 'axis_x': round(float(d[0]), 4), 'axis_y': round(float(d[1]), 4),
            'axis_z': round(float(d[2]), 4), 'max_deg': 35, 'turn_axis': 'hinge', 'spin': 'rudder', 'spin_k': 35, 'spin_min': -35, 'spin_max': 35, 'spin_lag': 0.3}
    mP = dict(meta, hinge_y=2 * (YC + 0.5) - P[1], axis_y=-meta['axis_y'])
    out = {'anchors': anchors, 'models': [
        {'name': 'rudder-S', 'at': P.tolist(), 'pivot': P.tolist(), 'mirror': '', 'meta': meta},
        {'name': 'rudder-P', 'at': [P[0], 2 * (YC + 0.5) - P[1], P[2]], 'pivot': P.tolist(), 'mirror': 'y', 'meta': mP}]}
    os.makedirs(os.path.join(HERE, 'masks', 'steer'), exist_ok=True)
    with open(os.path.join(HERE, 'masks', 'steer', 'rudder.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蓬特號 舷側舵槳 S 舷（draft_steer.py）x,y,z,color —— at 0,0,0（整船的框）\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(cells.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1]))) + '\n')
    with open(os.path.join(HERE, 'steer_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_steer.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
