# 杉心號 步驟 11（TASK-1152）：右舷船尾側的舵槳（一支）＋右舷船頭外側掛一隻四爪錨 ⇒
#   masks/steer/rudder.vox.txt、helm_placement.json、verify_helm.json
#   出處：apex-one-punt-01m/design/draft_steer.py（蓬特號的舷側舵槳：繞槳柄轉、stock-top 旁 8 格內有船）—— 只做右舷一支、不鏡像；
#         錨的掛法照 kotoko-fusta-01m 的 anchor-S（四爪錨 pivot 在錨環頂、掛在船頭外側）。
#   用法：python -I -X utf8 draft_helm.py [--sink=3]   （反向對照：舵槳往下沉、錨往船殼推幾格 ⇒ 碰撞要報出來）
#   · 一手出處沒寫怎麼操舵 ⇒ 舵槳是推論（研究筆記 §4）；船尾後面只有 1.5 m、組裝件底是 z 0 ⇒ 中線搭船尾平板的舵槳槳葉會穿出框底 ⇒ 改右舷船尾側。
#   · 量：舵槳 0°、±35° 三個角度、錨，格心＋八角不落在船的實心；全部格 z ≥ 0。
import sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_guns as DG

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 140, 101, 100
ANCHOR = 'kotoko-fusta-01m-anchor-grapnel'


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def rot_axis(v, k, ang):
    c, s = math.cos(ang), math.sin(ang)
    return v * c + np.cross(k, v) * s + np.outer(v @ k, k) * (1 - c)


def solids(plan):
    G = V(plan['guns'])
    post = [(G['post']['x'], plan['space']['yc'], z) for z in range(G['post']['z0'], G['post']['z1'] + 1)]
    occ = DG.solids(plan, post)
    f = os.path.join(HERE, 'masks', 'magazine', 'board.vox.txt')     # 彈藥庫墊板（v1；步驟 14 做了船尾平台之後拿掉 ⇒ 檔案不在）
    if os.path.exists(f):
        b = np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
        occ[b[:, 0], b[:, 1], b[:, 2]] = True
    return occ


def main():
    sink = float(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--sink=')), 0))
    plan = HL.load_plan()
    K = V(plan['steer'])
    C = K['colors']
    occ = solids(plan)
    P = np.array(K['lash'], float) - [0, 0, sink]
    B = np.array(K['blade_center'], float) - [0, 0, sink]
    d = (B - P) / np.linalg.norm(B - P)
    T = P - d * K['loom_up']
    w = np.cross(d, [0, 1, 0])
    w /= np.linalg.norm(w)
    cells = {}

    def disk(c, r, col):
        for x in range(int(c[0] - r - 2), int(c[0] + r + 3)):
            for y in range(int(c[1] - r - 2), int(c[1] + r + 3)):
                for z in range(int(c[2] - r - 2), int(c[2] + r + 3)):
                    q = np.array([x + 0.5, y + 0.5, z + 0.5]) - c
                    a = q @ d
                    if abs(a) > 0.5:
                        continue
                    if np.linalg.norm(q - a * d) <= r + 1e-6:
                        cells[(x, y, z)] = col
    blade_half = K['blade_len'] / 2
    top_b = B - d * blade_half
    Lloom = np.linalg.norm(top_b - T)
    for s in np.arange(0, Lloom + 1e-9, 0.25):
        disk(T + d * s, K['loom_r'], C['loom'])
    for s in np.arange(-blade_half, blade_half + 1e-9, 0.25):
        t = (s + blade_half) / K['blade_len']
        half_w = K['blade_w'] / 2 * (0.55 + 0.45 * math.sin(math.pi * min(1, t * 1.15)))
        for u in np.arange(-half_w, half_w + 1e-9, 0.25):
            cells[tuple(np.floor(B + d * s + w * u).astype(int))] = C['tip'] if t > 0.9 else C['blade']
    E = np.array(K['tiller_end'], float) - [0, 0, sink]
    Lt = np.linalg.norm(E - T)
    for s in np.arange(0, Lt + 1e-9, 0.25):
        cells[tuple(np.floor(T + (E - T) * s / Lt).astype(int))] = C['tiller']
    arr = np.array(list(cells.keys()))
    corners = np.array([[dx, dy, dz] for dx in (-.5, .5) for dy in (-.5, .5) for dz in (-.5, .5)])
    pts = np.concatenate([arr + 0.5] + [arr + 0.5 + c for c in corners])
    R = {'cells': len(cells), 'oar_m': round((Lloom + K['blade_len']) * 0.1, 2), 'T': T.round(2).tolist(), 'P': P.tolist(), 'B': B.tolist(), 'axis': d.round(4).tolist(),
         'min_z': int(arr[:, 2].min()), 'collide': {}}
    for deg in (0, 35, -35):
        q = rot_axis(pts - P, d, math.radians(deg)) + P
        ci = np.floor(q).astype(int)
        ok = (ci[:, 2] >= 0) & (ci[:, 1] >= 0) & (ci[:, 1] < SY) & (ci[:, 0] >= 0)
        R['collide']['%+d' % deg] = int(occ[ci[ok, 0], ci[ok, 1], ci[ok, 2]].sum())
        R['min_z_%+d' % deg] = round(float(q[:, 2].min()), 2)
    t = np.floor(T).astype(int)
    p_ = np.floor(P).astype(int)
    R['stock_top_near_cells'] = int(occ[p_[0] - 8:p_[0] + 9, p_[1] - 8:p_[1] + 9, max(0, p_[2] - 8):p_[2] + 9].sum())
    wl = plan['waterline']['z']
    R['blade_center_below_wl_m'] = round((wl - B[2]) * 0.1, 2)
    # 錨：四爪錨掛在右舷船头外側，錨環頂 ＝ pivot
    A = V(plan['anchor'])
    an = DG.anchors(ANCHOR)
    apiv = [an['ring'][0] + 0.5, an['ring'][1] + 0.5, an['ring'][2] + 1.0]
    aat = [A['at'][0], A['at'][1] - sink, A['at'][2]]                  # 反向對照：錨往船殼那一側（−y）推（掛在船外，往下沉什麼都碰不到）
    acells = DG.export(ANCHOR)[:, :3].astype(float)
    ahits = 0
    for off in [(0.5, 0.5, 0.5)] + [(dx, dy, dz) for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]:
        p = DG.place(acells + np.array(off), aat, apiv, A['scale'], A['rotate_z'])
        k = np.floor(p).astype(int)
        ok = (k[:, 2] >= 0)
        ahits += int(occ[k[ok, 0], k[ok, 1], k[ok, 2]].sum())
    ap = DG.place(acells + 0.5, aat, apiv, A['scale'], A['rotate_z'])
    R['anchor'] = {'at': aat, 'hits': ahits, 'bbox': [ap.min(0).round(2).tolist(), ap.max(0).round(2).tolist()], 'height_m': round(float(ap[:, 2].max() - ap[:, 2].min()) * 0.1, 2)}
    if sink:
        print(json.dumps({'sink': sink, 'collide': R['collide'], 'anchor_hits': ahits}, ensure_ascii=False))
        return
    meta = {'kind': 'rudder', 'rudder': 'quarter', 'hinge_x': P[0], 'hinge_y': P[1], 'hinge_z': P[2], 'axis_x': round(float(d[0]), 4), 'axis_y': round(float(d[1]), 4),
            'axis_z': round(float(d[2]), 4), 'max_deg': 35, 'turn_axis': 'hinge', 'spin': 'rudder', 'spin_k': 35, 'spin_min': -35, 'spin_max': 35, 'spin_lag': 0.3, 'id': 'rudder-1'}
    out = {'steer_work': 'basecamp-piragua-01m-rudder',
           'steer_anchors': {'stock-top': p_.tolist(), 'loom-top': t.tolist(), 'blade-tip': np.floor(B + d * blade_half).astype(int).tolist(), 'tiller-end': np.floor(E).astype(int).tolist()},
           'models': [{'host': 'basecamp-piragua-01m-assembly', 'name': '舵槳', 'work': 'basecamp-piragua-01m-rudder', 'at': P.tolist(), 'pivot': P.tolist(), 'scale': 1, 'rotate': [0, 0, 0], 'meta': meta},
                      {'host': 'basecamp-piragua-01m-deck-main', 'name': 'anchor-S', 'work': ANCHOR, 'at': aat, 'pivot': apiv, 'scale': A['scale'], 'rotate': [0, 0, A['rotate_z']],
                       'meta': {'kind': 'anchor', 'anchor': 'bower', 'id': 'anchor-1'}}],
           'hull_anchors': {'hawse-S': A['hawse']}}
    os.makedirs(os.path.join(HERE, 'masks', 'steer'), exist_ok=True)
    with open(os.path.join(HERE, 'masks', 'steer', 'rudder.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 杉心號 右舷船尾側的舵槳（draft_helm.py）x,y,z,color —— at 0,0,0（整船的框）\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(cells.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1]))) + '\n')
    with open(os.path.join(HERE, 'helm_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_helm.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
