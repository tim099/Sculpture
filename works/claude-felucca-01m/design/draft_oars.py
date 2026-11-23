# 海鷗號 新圖紙 10（TASK-0024 步驟 13）：槳 —— 每舷 7 支、每支 1 人，引用杉心號的通用槳 ⇒ masks/oars/tholes.vox.txt（槳栓子作品）、oars_placement.json、verify_oars.json
#   出處：擺法照杉心號 basecamp-piragua-01m/design/draft_oars.py（Ship_Oars §9.10.1：at ＝ pivot ＝ 舷頂外緣那條稜上、槳柄底的格角離舷頂面半格；右舷原樣、
#         左舷 mirror=y；rotate 的 x 角補到槳葉中心落在水面，左舷反號）；槳栓擺在槳的船頭側 2 格（皇家號 v1 槳柄半徑 0.75 格穿過槳栓的教訓）。
#   用法：python -I -X utf8 draft_oars.py [--sink=S3] [--drop=P7]   （反向對照：那一支往下沉 3 格 ⇒ 只有它報碰撞；不擺 ⇒ 那一舷少一支）
#   · 為什麼引用杉心號的槳（3.4 m：裡 0.8、外 2.6）：它的 seat 在槳座下 0.4 m、往裡 0.65 m —— 本船舷頂比坐板面高 0.4 m、坐板一直鋪到 |dy| 13 ⇒ 槳手剛好坐在坐板上；
#     持火號、越嶺號的槳是站著划或坐在走道邊，seat 對不上。
#   · 槳的 x ＝ 坐板的 x（槳手坐在那張坐板上）；v1 的槳栓在坐板的船尾側 3 格（步驟 3 的配置）⇒ seat 落在艙底板上、不在坐板上 ⇒ 改。
import sys, os, json, math, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio

sys.stdout.reconfigure(encoding='utf-8')
YC = 80
OAR = 'basecamp-piragua-01m-oar'                    # 3×67×23、0.05 m；pivot (1,16,16)、blade (1,66,4)、seat (1,3,8)
PIV = np.array([1.5, 16.5, 16.5])
SEAT = np.array([1.5, 3.5, 8.5])
K = 0.5
LOOM_R = 0.8                                        # 杉心號 oars_build.loom_r（元件格）
THOLE_C = 141


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)) for x, y, z, c in a}


def rot_x(v, deg):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return np.stack([v[:, 0], v[:, 1] * c - v[:, 2] * s, v[:, 1] * s + v[:, 2] * c], axis=1)


def main():
    sink = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--sink=')), None)
    drop = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--drop=')), None)
    plan = HL.load_plan(HERE)
    surf = plan['waterline']['z'] + 1.0             # 水面（水線那一格的頂；吃水 0.7 m）
    lay = {k: (v['v'] if isinstance(v, dict) and 'v' in v else v) for k, v in plan['layout'].items() if k != 'src'}
    B = lay['benches']
    hull = load('masks/hull/hull_01.vox.txt')
    deck = load('masks/decks/deck_main.vox.txt') | load('masks/guns/post.vox.txt')
    ship = hull | deck | load('masks/magazine/chest.vox.txt') | load('masks/masts/main.vox.txt') | load('masks/masts/fore.vox.txt') | \
        load('masks/masts/tack_spar.vox.txt') | load('masks/deco/stem_head.vox.txt') | load('masks/helm/rudder.vox.txt') | load('masks/helm/tiller.vox.txt')
    src = wio.export_list(OAR, None)
    arr = src[:, :3].astype(float)
    # 其他模型的外框（Ship_Oars §9.10.2-5：槳不准穿過砲、座、錨、灶、桶）
    import draft_magazine as DM
    boxes = []
    for f, key in (('guns_placement.json', 'models'), ('magazine_placement.json', 'models')):
        for m in json.load(open(os.path.join(HERE, f), encoding='utf-8'))[key]:
            boxes.append((m['name'], DM.box_of(m['at'], m['pivot'], m['work'], m['scale'], m['rotate'][2])))
    hp = json.load(open(os.path.join(HERE, 'helm_placement.json'), encoding='utf-8'))['anchor']
    boxes.append((hp['name'], DM.box_of(hp['at'], hp['pivot'], hp['work'], hp['scale'], 0)))
    corners = [np.array([0.0, 0.0, 0.0])] + [np.array([dx, dy, dz]) * K for dx in (-.5, .5) for dy in (-.5, .5) for dz in (-.5, .5)]
    tholes, place, R = {}, [], {'per_side': {'P': 0, 'S': 0}, 'oars': {}}
    occ_o = {}
    for side, sg in (('S', 1), ('P', -1)):
        for i in range(B['n']):
            nm = 'oar-%s%d' % (side, i + 1)
            x = B['x0'] + i * B['pitch']                 # 槳 ＝ 坐板那一欄
            ys = [k for k in hull if k[0] == x and (k[1] - YC) * sg > 2]
            zt = max(k[2] for k in ys)
            yo = max((k[1] for k in ys if k[2] == zt), key=lambda v: (v - YC) * sg)
            # 槳栓：槳的船頭側 2 格、立在那一欄舷頂最外一格上、高 0.3 m
            xt = x + 2
            ys2 = [k for k in hull if k[0] == xt and (k[1] - YC) * sg > 2]
            zt2 = max(k[2] for k in ys2)
            yo2 = max((k[1] for k in ys2 if k[2] == zt2), key=lambda v: (v - YC) * sg)
            for z in range(zt2 + 1, zt2 + 4):
                tholes[(xt, yo2, z)] = THOLE_C
            if drop == '%s%d' % (side, i + 1):
                continue
            at = np.array([x + 0.5, yo + (1.0 if sg > 0 else 0.0), zt + 1 + (LOOM_R + 0.5) * K])
            if sink == '%s%d' % (side, i + 1):
                at[2] -= 3
            bc = np.array([1.5, 66.5 - 7, 4.5 + 1.5])     # 槳葉中心（元件格）：槳葉 14 格長、末端 blade (1,66,4) 往裡半個槳葉
            bc_rel = (bc - PIV) * K
            ang0 = math.degrees(math.atan2(-bc_rel[2], bc_rel[1]))
            want = math.degrees(math.asin(min(1.0, (at[2] - surf) / np.linalg.norm(bc_rel[1:]))))
            rx = -(want - ang0)
            q = rot_x((arr + 0.5 - PIV) * K, rx)
            if sg < 0:
                q[:, 1] = -q[:, 1]
            pts = q + at
            hits = 0
            hit_cells = set()
            for off in corners:
                k = np.floor(pts + off).astype(int)
                for kk in map(tuple, k):
                    if kk in ship or kk in tholes:
                        hit_cells.add(kk)
            hits = len(hit_cells)
            box_hits = [n for n, b in boxes if ((pts >= np.array(b[0]) - 0.0) & (pts <= np.array(b[1]))).all(axis=1).any()]
            bw = rot_x(bc_rel[None, :], rx)[0]
            if sg < 0:
                bw[1] = -bw[1]
            bw = bw + at
            sr = rot_x(((SEAT - PIV) * K)[None, :], rx)[0]
            if sg < 0:
                sr[1] = -sr[1]
            sw = tuple(int(v) for v in np.floor(sr + at))
            seat_ok = (sw not in ship) and ((sw[0], sw[1], sw[2] - 1) in deck) and not any((sw[0], sw[1], z) in ship for z in range(sw[2], sw[2] + 14))
            # 照遊戲的找法（Ship_Oars §9.10.2-2：seat 站不住 ⇒ 在 seat 旁 6 格內往下找第一個站得住的格；站 ＝ 腳下實心、頭上 14 格空）：
            #   槳往下轉了 6.5–9.3° 讓槳葉到水面 ⇒ 舷內那一頭翹起來、seat 比坐板高 1 格
            seat_game = None
            for dz in range(0, 7):
                c = (sw[0], sw[1], sw[2] - dz)
                if c not in ship and ((c[0], c[1], c[2] - 1) in ship or (c[0], c[1], c[2] - 1) in tholes) and not any((c[0], c[1], z) in ship for z in range(c[2], c[2] + 14)):
                    seat_game = list(c)
                    break
            near = sum(1 for k in hull if abs(k[0] - at[0]) <= 8 and abs(k[1] - at[1]) <= 8 and abs(k[2] - at[2]) <= 8)
            for kk in set(map(tuple, np.floor(pts).astype(int))):
                occ_o.setdefault(kk, set()).add(nm)
            R['per_side'][side] += 1
            R['oars'][nm] = {'at': [round(float(v), 3) for v in at], 'rot_x': round(rx, 3), 'hits': hits, 'model_hits': box_hits,
                             'blade_center_above_water_m': round(float(bw[2] - surf) * 0.1, 3), 'seat_world': list(sw), 'seat_ok': bool(seat_ok), 'seat_game': seat_game, 'seat_game_on_thwart': bool(seat_game and (seat_game[0], seat_game[1], seat_game[2] - 1) in deck and seat_game[2] - 1 == B['seat_z']),
                             'hull_cells_near_pivot': near, 'thole': [xt, yo2, zt2 + 1]}
            place.append({'name': nm, 'at': [round(float(v), 3) for v in at], 'pivot': PIV.tolist(), 'scale': K,
                          'rotate': [round(rx if sg > 0 else -rx, 3), 0, 0], 'mirror': 'y' if sg < 0 else '',
                          'meta': {'kind': 'oar', 'rowers': 1, 'side': side, 'stroke_deg': 30, 'dip_deg': 12, 'id': 'oar-%d' % (2 * i + (1 if side == 'S' else 2))}})
    R['oar_oar_shared_cells'] = sum(1 for v in occ_o.values() if len(v) > 1)
    R['total_hits'] = sum(o['hits'] for o in R['oars'].values())
    R['model_hits'] = sum(len(o['model_hits']) for o in R['oars'].values())
    R['seats_ok'] = sum(1 for o in R['oars'].values() if o['seat_ok'])
    R['seats_game_on_thwart'] = sum(1 for o in R['oars'].values() if o['seat_game_on_thwart'])
    R['blade_above_water_m_range'] = [min(o['blade_center_above_water_m'] for o in R['oars'].values()), max(o['blade_center_above_water_m'] for o in R['oars'].values())]
    R['tholes'] = {'cells': len(tholes), 'overlap_ship': len(set(tholes) & ship), 'mirror_diff': sum(1 for (x, y, z) in tholes if (x, 2 * YC - y, z) not in tholes)}
    if sink or drop:
        print(json.dumps({'sink': sink, 'drop': drop, 'per_side': R['per_side'], 'hits': {k: v['hits'] for k, v in R['oars'].items() if v['hits']}, 'total_hits': R['total_hits']}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'oars'), exist_ok=True)
    fn = os.path.join(HERE, 'masks', 'oars', 'tholes.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 海鷗號 槳栓（draft_oars.py；子作品、整船的框）x,y,z,color —— at 0,0,0\n')
        f.write(''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(tholes.items())))
    with open(os.path.join(HERE, 'oars_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'component': OAR, 'host': 'claude-felucca-01m-tholes', 'tholes_work': 'claude-felucca-01m-tholes', 'models': place}, f, ensure_ascii=False, indent=1)
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('masks/oars/tholes.vox.txt', 'oars_placement.json')}
    with open(os.path.join(HERE, 'verify_oars.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'oars'}, ensure_ascii=False))
    for k, v in R['oars'].items():
        if v['hits'] or v['model_hits'] or not v['seat_game_on_thwart']:
            print(k, v)


if __name__ == '__main__':
    main()
