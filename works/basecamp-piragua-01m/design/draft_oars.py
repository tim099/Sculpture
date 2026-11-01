# 杉心號 步驟 13（TASK-1152）：槳 —— 一件通用槳元件（0.05 m）＋每舷 7 支 ⇒
#   masks/oar/oar.vox.txt、oars_placement.json、verify_oars.json
#   出處：erina-dromon-01m／apex-one-reale-01m 的 draft_oars.py 做法（Ship_Oars §9.10.1）—— 元件沿 +y（y 0 ＝ 槳柄端）、畫在「掃到一半」的姿勢；
#         每支 at ＝ pivot ＝ 舷頂上一點、右舷 rotate、左舷 mirror=y；rotate 的 x 角照舷弧補（槳葉中心落在水面，Ship_Oars §9.10.2-3）。
#   用法：python -I -X utf8 draft_oars.py [--sink=S3] [--drop=P7]   （反向對照：那一支往下沉 3 格／不擺 ⇒ 只有它報碰撞／那一舷少一支）
#   · 為什麼不引用持火號的下層槳：它的 seat 在槳座下 1.05 m（槳手站在艙底），擺到這艘的舷頂上換算出來落在船殼外（z −2）。
#   · Dampier 第 1 章 14 支槳；第 5 章槳用繩環（straps）掛 ⇒ 槳柄直接靠在舷頂上（沒有槳栓）。
#   · 同一塊坐板兩人各划一舷 ⇒ 兩支槳的槳柄都伸過中線 ⇒ 前後錯開（右舷 x＋1、左舷 x−1），seat 都落在那塊坐板上。
import sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_helm as DH
import draft_guns as DG
import draft_rig as DR

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 140, 101, 100


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def component(O):
    """槳元件（0.05 m 格）：沿 +y、pivot 在 (1, inb, pz)、往外往下 angle；槳柄半徑 loom_r、槳葉沿槳柄 blade_len、往上下 blade_w、厚 1。"""
    a = math.radians(O['angle_deg'])
    inb, outb = O['inboard'], O['outboard']
    pz = O['pivot_z']
    u = np.array([0.0, math.cos(a), -math.sin(a)])              # 往外（+y）往下
    P = np.array([1.5, inb + 0.5, pz + 0.5])
    H = P - u * inb                                             # 槳柄端
    E = P + u * outb                                            # 槳葉末端
    n = np.array([0.0, math.sin(a), math.cos(a)])               # 垂直槳柄、在 yz 平面裡往上
    cells = {}
    L = inb + outb
    for x in range(0, 3):
        for y in range(0, int(math.ceil(L + 2))):
            for z in range(0, O['frame_z']):
                q = np.array([x + 0.5, y + 0.5, z + 0.5])
                s = float((q - H) @ u)
                if not (0 <= s <= L):
                    continue
                r = q - H - u * s
                if s >= L - O['blade_len']:
                    t = (s - (L - O['blade_len'])) / O['blade_len']
                    hw = O['blade_w'] / 2 * (0.6 + 0.4 * math.sin(math.pi * min(1.0, t * 1.3)))
                    if abs(r[0]) <= 0.5 and abs(r @ n) <= hw:
                        cells[(x, y, z)] = O['color']
                elif math.hypot(r[0], r @ n) <= O['loom_r']:
                    cells[(x, y, z)] = O['color']
    zs = [k[2] for k in cells]
    assert min(zs) >= 0 and max(zs) < O['frame_z'], ('槳元件出框', min(zs), max(zs))
    seat = [1, inb - O['seat_in'], pz - O['seat_down']]
    bc = P + u * (outb - O['blade_len'] / 2)
    anchors = {'pivot': [1, inb, pz], 'blade': [int(v) for v in np.floor(E - u * 0.5)], 'seat': seat}
    for nm in ('pivot', 'blade'):
        assert tuple(anchors[nm]) in cells, ('槳的固定點不在格上', nm, anchors[nm])
    return cells, anchors, P, bc


def solids(plan):
    occ = DH.solids(plan)
    a = np.loadtxt(os.path.join(HERE, 'masks', 'steer', 'rudder.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    occ[a[:, 0], a[:, 1], a[:, 2]] = True                       # 舵槳在 0° 的格（它的模型就擺在原位）
    return occ


def model_boxes(plan):
    """其他模型的外框（迴旋砲、座、錨、火藥桶）⇒ 槳也不准穿（Ship_Oars §9.10.2-5）。"""
    out = []
    for f, key in (('guns_placement.json', 'models'), ('magazine_placement.json', 'models'), ('helm_placement.json', 'models')):
        for m in json.load(open(os.path.join(HERE, f), encoding='utf-8'))[key]:
            if m['name'] == '舵槳':
                continue
            c = DG.export(m['work'])[:, :3].astype(float) + 0.5
            p = DG.place(c, m['at'], m['pivot'], m['scale'], m['rotate'][2])
            out.append((m['name'], p.min(0), p.max(0)))
    return out


def rot_x(v, deg):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return np.stack([v[:, 0], v[:, 1] * c - v[:, 2] * s, v[:, 1] * s + v[:, 2] * c], axis=1)


def main():
    sink = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--sink=')), None)
    drop = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--drop=')), None)
    plan = HL.load_plan()
    O = V(plan['oars_build'])
    YC = plan['space']['yc']
    wl = plan['waterline']['z']
    cells, anc, Pc, bc = component(O)
    arr = np.array(list(cells.keys()), float)
    occ = solids(plan)
    boxes = model_boxes(plan)
    T = V(plan['layout']['thwarts'])
    seat_top = T['top_z']
    K = O['scale']
    piv = np.array([anc['pivot'][0] + 0.5, anc['pivot'][1] + 0.5, anc['pivot'][2] + 0.5])
    placements, R = [], {'component_cells': len(cells), 'oar_m': round((O['inboard'] + O['outboard']) * 0.05, 2), 'per_side': {'P': 0, 'S': 0}, 'oars': {}}
    occ_r = DR.world()
    host_pts = {}
    for side, sg in (('S', 1), ('P', -1)):
        for i, xt in enumerate(T['x'], 1):
            nm = 'oar-%s%d' % (side, i)
            if drop == '%s%d' % (side, i):
                continue
            x = xt + sg * O['stagger']
            rim = DR.rim(occ_r, x, sg, YC)
            # pivot 在舷頂外緣那條稜上（右舷 y＋1、左舷 y＋0）、槳柄底的格角離舷頂面半格（元件格）：往外往下那一段已經在船外、往裡那一段往上翹
            #   ⇒ 只靠著、不咬進去（v1 放在舷頂那一格的正上方 ⇒ 跨出槳座半格就擦到舷頂外緣，每支 2 格）
            at = np.array([x + 0.5, rim[1] + (1.0 if sg > 0 else 0.0), rim[2] + 1 + (O['loom_r'] + 0.5) * K])
            if sink == '%s%d' % (side, i):
                at[2] -= 3
            # 槳葉中心落在水面：補 rotate x
            bc_rel = (bc - piv) * K                                 # 元件裡 pivot → 槳葉中心（船的格）
            ang0 = math.degrees(math.atan2(-bc_rel[2], bc_rel[1]))
            want = math.degrees(math.asin(min(1.0, (at[2] - wl) / np.linalg.norm(bc_rel[1:]))))
            dlt = want - ang0                                       # 要再往下轉幾度
            rx = -dlt                                               # 右舷：繞 +x 轉負 ＝ 槳葉往下
            q = rot_x((arr + 0.5 - piv) * K, rx)
            if sg < 0:
                q[:, 1] = -q[:, 1]
            pts = q + at
            hits = 0
            for off in [(0, 0, 0)] + [(dx, dy, dz) for dx in (-.5 * K, .5 * K) for dy in (-.5 * K, .5 * K) for dz in (-.5 * K, .5 * K)]:
                k = np.floor(pts + np.array(off)).astype(int)
                ok = (k[:, 2] >= 0) & (k[:, 0] >= 0) & (k[:, 1] >= 0) & (k[:, 1] < SY)
                hits += int(occ[k[ok, 0], k[ok, 1], k[ok, 2]].sum())
            box_hits = [b[0] for b in boxes if ((pts >= b[1]) & (pts <= b[2])).all(axis=1).any()]
            bcw = rot_x(bc_rel[None, :], rx)[0]
            if sg < 0:
                bcw[1] = -bcw[1]
            bcw = bcw + at
            sr = rot_x(((np.array(anc['seat'], float) + 0.5 - piv) * K)[None, :], rx)[0]
            if sg < 0:
                sr[1] = -sr[1]
            sw = np.floor(sr + at).astype(int)
            seat_ok = bool(not occ[tuple(sw)] and occ[sw[0], sw[1], sw[2] - 1] and not occ[sw[0], sw[1], sw[2]:sw[2] + 14].any())
            near = int(occ_r[int(at[0]) - 8:int(at[0]) + 9, int(at[1]) - 8:int(at[1]) + 9, max(0, int(at[2]) - 8):int(at[2]) + 9].sum())
            host_pts[nm] = pts
            R['per_side'][side] += 1
            R['oars'][nm] = {'at': [round(float(v), 3) for v in at], 'rot_x': round(rx, 2), 'hits': hits, 'model_hits': box_hits,
                             'blade_center_above_wl_m': round(float(bcw[2] - wl) * 0.1, 3), 'seat_world': sw.tolist(), 'seat_ok': seat_ok, 'hull_near_pivot': near}
            # 引擎是先照 y 翻、再轉 ⇒ 左舷的 x 角要反號（Ship_Oars §9.10.2-3：右舷 −δ、左舷 mirror=y 時 ＋δ）；上面的模擬是先轉再翻，同一個幾何
            placements.append({'name': nm, 'at': [round(float(v), 3) for v in at], 'pivot': piv.tolist(), 'scale': K, 'rotate': [round(rx if sg > 0 else -rx, 3), 0, 0],
                               'mirror': 'y' if sg < 0 else '', 'meta': {'kind': 'oar', 'rowers': 1, 'side': side, 'stroke_deg': 30, 'dip_deg': 12, 'id': 'oar-%d' % (2 * i - (1 if side == 'S' else 0))}})
    # 槳跟槳之間（同一塊坐板兩支的槳柄過中線）
    pair = 0
    names = list(host_pts)
    occ_o = {}
    for nm in names:
        for k in set(map(tuple, np.floor(host_pts[nm]).astype(int))):
            occ_o.setdefault(k, set()).add(nm)
    pair = sum(1 for v in occ_o.values() if len(v) > 1)
    R['oar_oar_shared_cells'] = pair
    R['total_hits'] = sum(o['hits'] for o in R['oars'].values())
    R['model_hits'] = sum(len(o['model_hits']) for o in R['oars'].values())
    R['seats_ok'] = sum(1 for o in R['oars'].values() if o['seat_ok'])
    R['blade_wl_range_m'] = [min(o['blade_center_above_wl_m'] for o in R['oars'].values()), max(o['blade_center_above_wl_m'] for o in R['oars'].values())]
    if sink or drop:
        print(json.dumps({'sink': sink, 'drop': drop, 'per_side': R['per_side'], 'hits': {k: v['hits'] for k, v in R['oars'].items() if v['hits']}}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'oar'), exist_ok=True)
    with open(os.path.join(HERE, 'masks', 'oar', 'oar.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 杉心號 槳元件（draft_oars.py）x,y,z,color —— 0.05 m、沿 +y、子作品自己的座標\n')
        f.write(''.join('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c) for k, c in sorted(cells.items())))
    size = [3, int(np.array(list(cells.keys()))[:, 1].max()) + 1, O['frame_z']]
    with open(os.path.join(HERE, 'oars_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'component': 'basecamp-piragua-01m-oar', 'size': size, 'anchors': anc, 'host': 'basecamp-piragua-01m', 'models': placements}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_oars.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'oars'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
