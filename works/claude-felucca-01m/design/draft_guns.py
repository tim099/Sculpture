# 海鷗號 新圖紙 07（TASK-0024 步驟 9）：四門迴旋砲 pierrier ⇒ guns_placement.json、masks/guns/post.vox.txt（船首砲柱，落在甲板-main）、verify_guns.json、sheet07_guns_v1.png
#   出處：擺法照杉心號 basecamp-piragua-01m/design/draft_guns.py（共用件 apex-one-reale-01m-gun-pierrier＋拆好的 -mount、scale 0.5、pivot 在叉架插銷底
#         (5.5,18.5,0)、meta kind=gun gun=pierrier mount=turret arc rate、座 kind=gunmount mount_of）；碰撞量法照 Ship_Guns §4.2（格心＋八角）自己寫，
#         多量每 10° 一個角度與砲口往外 4 m 的射線。
#   用法：python -I -X utf8 draft_guns.py [--probe=bow_post_h=-4]
#   · 讀前面每一步的設計清單（船殼、甲板、桅、桿、艏柱頭）與兩根帆桁的世界格；共用砲件的格子用 CLI export 讀（唯讀、別人的作品）。
import sys, os, json, math, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio

sys.stdout.reconfigure(encoding='utf-8')
YC = 80
GUN, MOUNT = 'apex-one-reale-01m-gun-pierrier', 'apex-one-reale-01m-gun-pierrier-mount'
PIV = (5.5, 18.5, 0.0)                    # 叉架插銷底（共用件的固定點 pivot (5,18,0) 那一格的底面中心）
MUZ, BRE = (5.5, 36.5, 9.5), (5.5, 5.5, 9.5)   # muzzle（內膛那一格）、breech 的格心
SCALE = 0.5
POST_C = 132                              # 砲柱色（設計決定：Ship_Guns §4.1 的砲架色）


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)) for x, y, z, c in a}


def rail_cell(hull, x, side):
    ys = [k for k in hull if k[0] == x and (k[1] - YC) * side > 2]
    zt = max(k[2] for k in ys)
    y = max((k[1] for k in ys if k[2] == zt), key=lambda v: (v - YC) * side)
    return (x, y, zt)


def world(p, at, rot):
    """模型座標 p（0.05 m 格）⇒ 世界（0.1 m 格）：先減 pivot、縮 scale、繞 z 轉 rot、加 at。"""
    dx, dy, dz = (p[0] - PIV[0]) * SCALE, (p[1] - PIV[1]) * SCALE, (p[2] - PIV[2]) * SCALE
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return (at[0] + c * dx - s * dy, at[1] + s * dx + c * dy, at[2] + dz)


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    hull = load('masks/hull/hull_01.vox.txt')
    deck = load('masks/decks/deck_main.vox.txt')
    ship = hull | deck | load('masks/masts/main.vox.txt') | load('masks/masts/fore.vox.txt') | load('masks/masts/tack_spar.vox.txt') | load('masks/deco/stem_head.vox.txt')
    for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
        for (x, y, z) in load('masks/yards/lateen-%s.vox.txt' % p['mast']):
            ship.add((int(round(x - p['pivot'][0] + p['at'][0])), int(round(y - p['pivot'][1] + p['at'][1])), int(round(z - p['pivot'][2] + p['at'][2]))))
    G = wio.export_list(GUN, None)
    M = wio.export_list(MOUNT, None)
    src = [tuple(r[:3]) for r in G.tolist()] + [tuple(r[:3]) for r in M.tolist()]
    corners = [(a, b, c) for a in (-0.5, 0.5) for b in (-0.5, 0.5) for c in (-0.5, 0.5)] + [(0, 0, 0)]
    lay = {k: (v['v'] if isinstance(v, dict) and 'v' in v else v) for k, v in plan['layout'].items() if k != 'src'}
    bp = lay['bow_platform']
    # ── 四門的位置 ──
    post_h = 11 + int(probe.get('bow_post_h', 0))           # 船首砲柱：平台站面 z 10 起，11 格高（砲膛離站面 1.6 m、高過艏柱旁的舷頂，正前方射線不碰船；SCH 的砲架在柱子上、砲口高）。10 格時正前方 1.5 m 撞到船頭頂
    bow_y = YC + int(probe.get('bow_dy', -5))
    post = {(123, bow_y, z) for z in range(bp['board_z'] + 1, bp['board_z'] + 1 + post_h)}
    guns = []
    # 船首那門偏左舷 5 格（中線是艏柱頭與渦卷、右舷 2 格是船頭那根桿）；arc 只到正前方 +5°：往右舷前方 10–20° 會打到前桅（射線量到），那一塊給右舷船頭那門
    guns.append({'id': 'gun-1', 'name': '迴旋砲-F01', 'pos': 'bow', 'at': [123.5, bow_y + 0.5, float(bp['board_z'] + 1 + post_h)], 'rot': -90, 'arc': (-90, 5),
                 'host': 'deck', 'stand': 'post'})
    # 船尾那門 v1 在 x 20：舵柄轉 ±35° 會掃到它的座（步驟 11 量到）⇒ 往船頭挪到 x 32（舵柄只伸到 x 26）
    for i, (x, side, sd) in enumerate(((114, 1, 'S'), (114, -1, 'P'), (32, 1, 'S')), 2):
        rx, ry, rz = rail_cell(hull, x, side)
        rot = 0 if side > 0 else 180
        guns.append({'id': 'gun-%d' % i, 'name': '迴旋砲-%s%02d' % ('Q' if x > 60 else 'A', i), 'pos': 'bow' if x > 60 else 'aft', 'at': [rx + 0.5, ry + 0.5, float(rz + 1)],
                     'rot': rot, 'arc': (-90, 90), 'host': 'deck', 'stand': 'rail', 'side': sd})
    solid = ship | post
    R = {'probe': probe or None, 'guns': []}
    for g in guns:
        rows = []
        for ang in sorted(set(range(g['arc'][0], g['arc'][1] + 1, 10)) | {g['arc'][1]}):
            rot = g['rot'] + ang
            hit = 0
            for (i, j, k) in src:
                for (a, b, c) in corners:
                    w = world((i + 0.5 + a, j + 0.5 + b, k + 0.5 + c), g['at'], rot)
                    if tuple(int(math.floor(v)) for v in w) in solid:
                        hit += 1
                        break
            mz = world(MUZ, g['at'], rot)
            br = world(BRE, g['at'], rot)
            u = np.array(mz) - np.array(br)
            u = u / np.linalg.norm(u)
            ray = None
            for t in np.arange(0.5, 40.0, 0.5):
                q = np.array(mz) + t * u
                if tuple(int(math.floor(v)) for v in q) in solid:
                    ray = round(float(t), 1)
                    break
            rows.append({'deg': ang, 'cells_hit': hit, 'muzzle': [round(v, 2) for v in mz], 'ray_blocked_at_cells': ray})
        g2 = {k: v for k, v in g.items()}
        g2['angles'] = rows
        g2['bore_above_stand_m'] = round((world(MUZ, g['at'], g['rot'])[2] - (bp['board_z'] + 1 if g['pos'] == 'bow' and g['stand'] == 'post' else (lay['stern_platform']['board_z'] + 1 if g['pos'] == 'aft' else bp['board_z'] + 1))) * 0.1, 2)
        R['guns'].append(g2)
    R['total_cells_hit'] = sum(r['cells_hit'] for g in R['guns'] for r in g['angles'])
    R['rays_blocked'] = [(g['id'], r['deg'], r['ray_blocked_at_cells']) for g in R['guns'] for r in g['angles'] if r['ray_blocked_at_cells'] is not None]
    R['post'] = {'cells': len(post), 'overlap_ship': len(post & ship), 'on_platform': (123, bow_y, bp['board_z']) in deck}
    if probe:
        print(json.dumps({'probe': probe, 'total_cells_hit': R['total_cells_hit'], 'rays_blocked': R['rays_blocked'][:12], 'post': R['post']}, ensure_ascii=False))
        return
    # ── 寫檔 ──
    os.makedirs(os.path.join(HERE, 'masks', 'guns'), exist_ok=True)
    fn = os.path.join(HERE, 'masks', 'guns', 'post.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 海鷗號 船首砲柱（draft_guns.py；落在甲板-main）x,y,z,color —— at 0,0,0\n')
        f.write(''.join('%d,%d,%d,%d\n' % (x, y, z, POST_C) for (x, y, z) in sorted(post)))
    models = []
    for g in guns:
        meta = {'kind': 'gun', 'gun': 'pierrier', 'deck': 'main', 'id': g['id'], 'mount': 'turret', 'arc': '%d,%d' % g['arc'], 'rate': 45, 'port': g['pos']}
        base = {'at': g['at'], 'pivot': list(PIV), 'scale': SCALE, 'rotate': [0, 0, g['rot']], 'host': g['host']}
        models.append(dict(base, name=g['name'], work=GUN, meta=meta))
        models.append(dict(base, name=g['name'] + '座', work=MOUNT, meta={'kind': 'gunmount', 'id': 'gunmount-%s' % g['id'].split('-')[1], 'mount_of': g['id']}))
    with open(os.path.join(HERE, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'hosts': {'deck': 'claude-felucca-01m-deck-main', 'hull': 'claude-felucca-01m'}, 'models': models}, f, ensure_ascii=False, indent=1)
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('guns_placement.json', 'masks/guns/post.vox.txt')}
    with open(os.path.join(HERE, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: R[k] for k in ('total_cells_hit', 'rays_blocked', 'post')} | {'guns': [(g['id'], g['at'], g['rot'], g['bore_above_stand_m'], g['angles'][9]['muzzle']) for g in R['guns']]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
