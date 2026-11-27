# 蠍子號 新圖紙 08（TASK-0023 步驟 10）：艙底的藥艙（彈藥庫）＋火藥桶、艉燈 ⇒ masks/magazine/room.vox.txt、magazine_placement.json、verify_magazine.json、sheet08_magazine_v1.png
#   出處：海鷗號 claude-felucca-01m/design/draft_magazine.py（彈藥庫子作品＋火藥桶模型、關聯 meta kind=magazine pos、固定點 blast／door；模型外框照來源作品實際有格的範圍）；
#         藥艙的牆、地板、門洞照 Ship_Magazine §8（銅皮 168、松木地板 177、橡木壓條 136、門洞 5 格寬），越嶺號 kotoko-fusta-01m 的彈藥庫也在艙底。
#   改的地方：這艘甲板上排滿划手座，放不下藥箱 ⇒ 照 Ship_Magazine「甲板沒有地方放的找船底的藏藥艙」做在船首那段艙底（plan.json magazine 的 src）；
#            多一把「遊戲會把取用點擺在哪」的尺：照 Blockside 23_powder.js makeStations／findSpot 與 10_ship.js gunDecksMeta 的 zr 重寫（只量，不 import 遊戲）。
#   用法：python -I -X utf8 draft_magazine.py [--probe=room_x=-40] [--probe=door=0]
#   · 讀前面每一步的設計清單與共用件（CLI export，唯讀）；不讀自己的作品 ⇒ 落格之後重跑一樣。
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio
import draft_guns as DG

sys.stdout.reconfigure(encoding='utf-8')


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    MG = V(plan['magazine'])
    hull = load('masks/hull/hull_01.vox.txt')
    hole = load('masks/masts/deck_hole.vox.txt')
    deck = {k for k in load('masks/decks/deck_main.vox.txt') if k not in hole}
    ship = set(hull) | deck | set(load('masks/decks/bow.vox.txt')) | set(load('masks/deco/spur.vox.txt')) | set(load('masks/deco/poop.vox.txt')) \
        | set(load('masks/masts/main.vox.txt')) | set(load('masks/guns/posts.vox.txt'))
    awning = set(load('masks/deco/awning.vox.txt'))
    HX, HY, HZ = [int(v) for v in plan['space']['hull']]

    # ── 艙底的空氣（船殼裡面、甲板底下）：從框外灌水灌不到、又在甲板以下的空格 ──
    G = np.zeros((HX, HY, HZ), bool)
    for k in ship:
        if k[2] < HZ:
            G[k] = True
    lab, n = ndimage.label(~G)
    outside = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, -1].ravel()])))
    # 艙底跟外面是靠艙口格柵的孔接著的（步驟 5）⇒ 用「頭上有甲板／船殼」判斷是不是艙裡：每一柱往上找得到實心 ⇒ 在艙裡
    roof = np.flip(np.maximum.accumulate(np.flip(G, axis=2), axis=2), axis=2)     # roof[x,y,z]：z 以上（含）有實心
    hold = (~G) & np.roll(roof, -1, axis=2)
    hold[:, :, -1] = False

    # ── 藥艙：船首那段艙底一個盒子（x0..x1、y 中線 ±half），盒子跟艙底空氣的交集；牆 1 格（銅皮）、地板 ＝ 每一柱最低的那一格（松木）、牆頂一格橡木壓條；
    #    後牆中線開門洞（5 格寬、door_h 高）；兩側離船殼留空，前後的艙底照樣接得通（不封出空腔）──
    x0 = MG['x'][0] + int(probe.get('room_x', 0))
    x1 = MG['x'][1] + int(probe.get('room_x', 0))
    hw = MG['half']
    # 地板高度照每一個 x 切片定：那一片中線 ±half 整排都是艙底空氣的最低一格（船底往船頭收高 ⇒ 地板一階一階往前抬）
    FZ = {}
    for x in range(x0, x1 + 1):
        FZ[x] = next(z for z in range(1, HZ) if all(hold[x, y, z] for y in range(YC - hw, YC + hw + 1)))
    room, inner = {}, set()
    for x in range(x0, x1 + 1):
        fz = FZ[x]
        for y in range(YC - hw, YC + hw + 1):
            top = fz
            while top + 1 < HZ and hold[x, y, top + 1]:
                top += 1
            for z in range(fz, top + 1):
                wall = x in (x0, x1) or y in (YC - hw, YC + hw)
                if z == fz:
                    room[(x, y, z)] = MG['colors']['floor']
                elif wall:
                    room[(x, y, z)] = MG['colors']['rim'] if z == top else MG['colors']['wall']
                else:
                    inner.add((x, y, z))
        # 地板往前抬一格的地方：前一片地板比這一片低 ⇒ 這一片地板底下那一格露空，補一片立板（跟地板同色）把台階封起來
        if x > x0 and FZ[x - 1] < fz:
            for y in range(YC - hw, YC + hw + 1):
                for z in range(FZ[x - 1] + 1, fz):
                    if hold[x, y, z]:
                        room[(x, y, z)] = MG['colors']['floor']
    door = set()
    if probe.get('door', '1') != '0':
        for y in range(YC - 2, YC + 3):
            for z in range(FZ[x0] + 1, FZ[x0] + 1 + MG['door_h']):
                if (x0, y, z) in room:
                    door.add((x0, y, z))
    for k in door:
        room.pop(k)
    R = {'probe': probe or None, 'room': {'cells': len(room), 'x': [x0, x1], 'y': [YC - hw, YC + hw], 'floor_z': [min(FZ.values()), max(FZ.values())],
                                          'inner_air': len(inner), 'door_cells': len(door), 'overlap_ship': len(set(room) & ship),
                                          'interior_height_m': None}}
    tops = {}
    for (x, y, z) in inner:
        tops[(x, y)] = max(tops.get((x, y), 0), z - FZ[x])
    R['room']['interior_height_m'] = [round(min(tops.values()) * 0.1, 1), round(max(tops.values()) * 0.1, 1)]

    # ── 火藥桶：藥艙地板上，沿中線排（Ship_Magazine §8：一定要放；kind=powder）──
    BAR = MG['barrel']
    src_b = [tuple(r[:3]) for r in wio.export_list(BAR['work'], None).tolist()]
    models = []
    for i, bx in enumerate(MG['barrels_x'], 1):
        at = [bx + 0.5, YC + 0.5, float(FZ[bx] + 1)]
        models.append({'host': 'magazine', 'name': '桶-%03d' % i, 'work': BAR['work'], 'at': at, 'pivot': BAR['pivot'], 'scale': BAR['scale'], 'rotate': [0, 0, 0],
                       'meta': {'kind': 'powder', 'powder_lb': BAR['powder_lb'], 'id': 'powder-%d' % i}})
    occ = ship | set(room)
    R['barrels'] = []
    for m in models:
        b = DG.model_box(src_b, m['pivot'], m['scale'], m['at'], 0)
        hit = DG.cells_hit(src_b, m['pivot'], m['scale'], m['at'], 0, occ)
        inside = x0 < b[0] and b[3] < x1 + 1 and YC - hw < b[1] and b[4] < YC + hw + 1 and all((int(math.floor(v[0])), int(math.floor(v[1])), int(m['at'][2])) in inner for v in [(b[0], b[1]), (b[3] - 0.01, b[4] - 0.01)])
        inside = inside and all(FZ[x] == FZ[int(m['at'][0])] for x in range(int(math.floor(b[0])), int(math.ceil(b[3]))))   # 桶整個站在同一階地板上
        R['barrels'].append({'name': m['name'], 'bbox': [round(v, 2) for v in b], 'cells_hit': hit, 'inside_room': bool(inside)})

    # ── 艉燈：艉燈桿頂（步驟 6 留的位置 (24,120,62)）；共用件 gura-tridente-01m-lantern，照皇家號的擺法（scale 0.5、pivot 8.5,8.5,0、meta kind=light）──
    LA = MG['lantern']
    src_l = [tuple(r[:3]) for r in wio.export_list(LA['work'], None).tolist()]
    lat = [float(v) for v in LA['at']]
    models.append({'host': 'poop', 'name': '艉燈', 'work': LA['work'], 'at': lat, 'pivot': LA['pivot'], 'scale': LA['scale'], 'rotate': [0, 0, 0],
                   'meta': {'kind': 'light', 'id': 'light-1'}})
    lb = DG.model_box(src_l, LA['pivot'], LA['scale'], lat, 0)
    R['lantern'] = {'bbox': [round(v, 2) for v in lb], 'cells_hit': DG.cells_hit(src_l, LA['pivot'], LA['scale'], lat, 0, occ | awning),
                    'on_pole_top': (int(lat[0]), int(lat[1]), int(lat[2]) - 1) in ship}

    # ── 艙蓋（Ship_Fittings §9.7：低乾舷的船露天的出入口都該有門 ⇒ 沒有門的開口遊戲不當進水口）：步驟 5 的艙口格柵上面蓋一片艙蓋，
    #    共用件 meadow-monitor-01m-hatch（0.1 m、17×13×4、hinge-a (0,0,0) → hinge-b (16,0,0) ⇒ 往上掀），照開口縮放、平貼在格柵頂上一格；
    #    艙口前後被艉台（x 56）與中央走道的台階（x 62）夾住 ⇒ 沿 x 只能跟開口一樣長（§9.7 寫每邊大一格），沿 y 每邊大一格 ──
    HT = MG['hatch']
    hx0, hx1, hhalf = HT['x'][0], HT['x'][1], HT['half']
    hcells = [k for k in deck if hx0 <= k[0] <= hx1 and abs(k[1] - YC) <= hhalf + 1 and k[2] < 30]
    hzb = max(k[2] for k in hcells) + 1                              # 坐在艙口緣圍（y ±4 那兩條，比格柵高一格）頂上
    src_h = [tuple(r[:3]) for r in wio.export_list(HT['work'], None).tolist()]
    sz = [max(k[i] for k in src_h) + 1 for i in range(3)]
    hy0, hy1 = YC - hhalf - 1, YC + hhalf + 1
    hsc = [round((hx1 - hx0 + 1 - 0.04) / sz[0], 4), round((hy1 - hy0 + 1) / sz[1], 4), HT['scale_z']]   # x 兩頭各讓 0.02 格：外框剛好貼著艉台（x 56）與台階（x 62）那一面，不壓進去
    hat = [hx0 + 0.02, float(hy0), float(hzb)]
    hpts = [(hat[0] + (i + 0.5 + a) * hsc[0], hat[1] + (j + 0.5 + b) * hsc[1], hat[2] + (k + 0.5 + c) * hsc[2]) for (i, j, k) in src_h for (a, b, c) in DG.CORNERS]
    hhit = sum(1 for q in hpts if (int(math.floor(q[0])), int(math.floor(q[1])), int(math.floor(q[2]))) in occ)
    hbox = [hat[0], hat[1], hat[2], hat[0] + sz[0] * hsc[0], hat[1] + sz[1] * hsc[1], hat[2] + sz[2] * hsc[2]]
    opening = [(x, y, hzb - 1) for x in range(hx0, hx1 + 1) for y in range(hy0, hy1 + 1) if (x, y, hzb - 1) not in ship]
    models.append({'host': 'deck', 'name': '艙蓋-艙口', 'work': HT['work'], 'at': hat, 'pivot': [0, 0, 0], 'scale': hsc, 'rotate': [0, 0, 0],
                   'meta': {'kind': 'door', 'open': 'up', 'id': 'door-1'}})
    R['hatch'] = {'coaming_top_z': hzb - 1, 'at': hat, 'scale': hsc, 'bbox': [round(v, 2) for v in hbox], 'corner_hits': hhit, 'opening_cells_under_lid': len(opening),
                  'hinge_world': [[hat[0], hat[1], hat[2]], [round(hat[0] + 16 * hsc[0], 3), hat[1], hat[2]]], 'neighbours_x': [(hx0 - 1, YC, max(z for (x, y, z) in ship if x == hx0 - 1 and y == YC and z < 40)), (hx1 + 1, YC, max(z for (x, y, z) in ship if x == hx1 + 1 and y == YC and z < 40))]}

    # ── 結構：船＋藥艙 1 元件、封閉空腔 0（艙底照樣從艙口格柵接到外面）；藥艙裡面接得到門洞外 ──
    G2 = G.copy()
    for k in room:
        G2[k] = True
    labs, nc = ndimage.label(G2, structure=ndimage.generate_binary_structure(3, 1))
    la, na = ndimage.label(~G2, structure=ndimage.generate_binary_structure(3, 1))
    border = set(np.unique(np.concatenate([la[0].ravel(), la[-1].ravel(), la[:, 0].ravel(), la[:, -1].ravel(), la[:, :, -1].ravel(), la[:, :, 0].ravel()])))
    cav = [int((la == i).sum()) for i in range(1, na + 1) if i not in border]
    R['structure'] = {'components': int(nc), 'cavities': len(cav), 'cavity_cells': sum(cav)}
    some_inner = sorted(inner)[len(inner) // 2]
    R['room']['inner_reaches_outside'] = bool(la[some_inner] in border)
    mir = sum(1 for (x, y, z), c in room.items() if room.get((x, 2 * YC - y, z)) != c)
    R['room']['mirror_diff'] = mir

    # ── 遊戲會把取用點擺在哪（Blockside 23_powder.js makeStations：只有一間彈藥庫 ⇒ anchors 前後各一個：
    #    從彈藥庫外框前端 +16 往船頭（dir 1）、後端 −16 往船尾（dir −1）找 10×10、頭上 8 格空、離砲的外框 2 格以外的平地；
    #    站人的高度 zr 照 10_ship.js gunDecksMeta：第一門砲架底 z、比地板高 8 以上就照它正下方的地板 ⇒ [a−8, a+5]）──
    GP = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))['models']
    T = {}
    gb = []
    for g in GP:
        if g['work'] not in T:
            T[g['work']] = [tuple(r[:3]) for r in wio.export_list(g['work'], None).tolist()]
        b = DG.model_box(T[g['work']], g['pivot'], g['scale'], g['at'], g['rotate'][2])
        if g['meta']['kind'] == 'gun':
            gb.append(b)
    AZ = int(plan['space']['assembly'][2])
    B = np.zeros((HX, HY, AZ), bool)
    for k in occ:
        if k[2] < AZ:
            B[k] = True

    def standZ(x, y, z0, z1, head=8):
        for z in range(z1, z0 - 1, -1):
            if z < 1 or z + head >= AZ or not (0 <= x < HX and 0 <= y < HY):
                continue
            if B[x, y, z - 1] and not B[x, y, z:z + head].any():
                return z
        return -1
    a = int(math.floor(min(b[2] for b in gb)))                     # 8l 架底 z 26（平台站面）
    zr = [a - 8, a + 5]

    def clear(x, y, z):
        for dy in range(0, 10, 3):
            for dx in range(0, 10, 3):
                if standZ(x + dx, int(math.floor(y + dy)), z - 1, z + 1) < 0:
                    return False
        return not any(x + 11 > b[0] and x - 2 < b[3] and y + 11 > b[1] and y - 2 < b[4] and z + 8 > b[2] and z - 3 < b[5] for b in gb)

    CYf = YC + 0.5                                                 # 遊戲的中線 T.cy ＝ 框寬 241 ÷ 2 ＝ 120.5（05_hull.js；verifier10 抓到 v1 用 120）

    def find_spot(x0_, d):
        for ex in range(0, 401, 2):
            for oy in (CYf + 6, CYf - 15, CYf + 16, CYf - 25):
                x2 = x0_ + d * ex
                z2 = standZ(x2 + 4, int(math.floor(oy + 4)), zr[0], zr[1])
                if z2 >= 0 and clear(x2, oy, z2):
                    return [x2, oy, z2]
        return None
    # 只有一間彈藥庫 ⇒ anchors 前後各一：彈藥庫外框照 23_powder.js makeMags —— 關聯外框（0..420）比船殼外框大 ⇒ 改用裡面火藥桶的外框（verifier10 抓到 v1 用藥艙的 x）
    kx0 = min(b['bbox'][0] for b in R['barrels'])
    kx1 = max(b['bbox'][3] for b in R['barrels'])
    jr = lambda v: int(math.floor(v + 0.5))                         # JS Math.round
    st = {'fore': find_spot(jr(kx1) + 16, 1), 'aft': find_spot(jr(kx0) - 16, -1)}
    R['game_pickup'] = {'zr': zr, 'mag_box_x_from_barrels': [kx0, kx1], 'search_from_x': {'fore': jr(kx1) + 16, 'aft': jr(kx0) - 16}, 'stations': st}
    if st['fore']:
        R['game_pickup']['fore_margin_to_8l_box_y_cells'] = round(min(abs((st['fore'][1] - 2) - gb[0][4]), abs((st['fore'][1] + 11) - gb[0][1])), 2)
    for k, s in st.items():
        if s:
            R['game_pickup'][k + '_to_8l_m'] = round(math.dist((s[0] + 4.5, s[1] + 4.5), ((gb[0][0] + gb[0][3]) / 2, (gb[0][1] + gb[0][4]) / 2)) * 0.1, 1)
    anchors = {}
    cx = sum(k[0] for k in inner) / len(inner)
    cy = sum(k[1] for k in inner) / len(inner)
    cz = sum(k[2] for k in inner) / len(inner)
    anchors['blast'] = list(min(inner, key=lambda k: (k[0] - cx) ** 2 + (k[1] - cy) ** 2 + (k[2] - cz) ** 2))
    anchors['door'] = [x0, YC, FZ[x0] + 1]
    R['anchors'] = anchors
    R['anchor_blast_is_air'] = tuple(anchors['blast']) in inner
    R['problems'] = (R['room']['overlap_ship'] + sum(b['cells_hit'] for b in R['barrels']) + sum(1 for b in R['barrels'] if not b['inside_room'])
                     + R['lantern']['cells_hit'] + (not R['lantern']['on_pole_top']) + (R['structure']['components'] != 1) + R['structure']['cavities']
                     + (not R['room']['inner_reaches_outside']) + R['room']['mirror_diff'] + (not R['anchor_blast_is_air'])
                     + (0 if any(st.values()) else 1) + R['hatch']['corner_hits'] + (R['hatch']['opening_cells_under_lid'] == 0))
    if probe:
        print(json.dumps({k: R[k] for k in ('probe', 'problems', 'room', 'structure', 'barrels', 'game_pickup')}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'magazine'), exist_ok=True)
    with open(os.path.join(HERE, 'masks', 'magazine', 'room.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蠍子號 船首那段艙底的藥艙（draft_magazine.py；彈藥庫子作品、船殼的框）x,y,z,color —— at 0,0,0\n')
        f.write(''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(room.items())))
    out = {'hosts': {'magazine': 'claude-galiot-01m-magazine', 'poop': 'claude-galiot-01m-poop', 'deck': 'claude-galiot-01m-deck-main'},
           'link': {'name': '彈藥庫', 'parent': '', 'meta': {'kind': 'magazine', 'pos': MG['pos'], 'powder_lb': BAR['powder_lb'] * len(MG['barrels_x']), 'id': 'magazine-1'}},
           'anchors': anchors, 'models': models}
    with open(os.path.join(HERE, 'magazine_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('masks/magazine/room.vox.txt', 'magazine_placement.json')}   # 圖紙與本檔的 sha 在 notes（自己不能寫進自己）
    with open(os.path.join(HERE, 'verify_magazine.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    # 圖紙 08：藥艙的平面（上看，z ＝ 地板上一格）與 x 剖面（後牆、門洞）、遊戲的取用點
    s_ = 8
    W0, W1, Y0, Y1 = x0 - 30, 372, YC - 30, YC + 30
    img = Image.new('RGB', ((W1 - W0) * s_ // 2 + 80, (Y1 - Y0) * s_ + 260), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((20, 8), '%s - new sheet 08: powder room in the hold (fwd), barrels, game pickup station (23_powder.js findSpot)' % plan['title_en'], fill=(20, 20, 40), font=f)
    hs = s_ // 2
    for x in range(W0, W1):
        for y in range(Y0, Y1):
            fz = FZ.get(x, 10)
            z = fz + 1
            c = None
            if (x, y, z) in room or (x, y, fz) in room and (x, y, z) not in inner:
                c = (150, 90, 40) if room.get((x, y, z), room.get((x, y, fz))) == MG['colors']['wall'] else (190, 150, 90)
            elif (x, y, z) in inner:
                c = (240, 228, 200)
            elif x0 <= x <= x1 and any((x, y, zz) in ship for zz in range(fz, fz + 3)):
                c = (120, 120, 120)
            if c:
                d.rectangle([40 + (x - W0) * hs, 40 + (Y1 - 1 - y) * s_, 40 + (x - W0) * hs + hs - 1, 40 + (Y1 - 1 - y) * s_ + s_ - 1], fill=c)
    for b in R['barrels']:
        bb = b['bbox']
        d.ellipse([40 + (bb[0] - W0) * hs, 40 + (Y1 - bb[4]) * s_, 40 + (bb[3] - W0) * hs, 40 + (Y1 - bb[1]) * s_], outline=(20, 20, 20), width=2)
    for k, s in st.items():
        if s and W0 <= s[0] < W1:
            d.rectangle([40 + (s[0] - W0) * hs, 40 + (Y1 - 10 - s[1]) * s_, 40 + (s[0] + 10 - W0) * hs, 40 + (Y1 - s[1]) * s_], outline=(200, 30, 30), width=2)
            d.text((44 + (s[0] - W0) * hs, 44 + (Y1 - s[1]) * s_), 'pickup (%s) z %d' % (k, s[2]), fill=(200, 30, 30), font=f)
    for b in gb:
        d.rectangle([40 + (b[0] - W0) * hs, 40 + (Y1 - b[4]) * s_, 40 + (b[3] - W0) * hs, 40 + (Y1 - b[1]) * s_], outline=(30, 30, 160), width=1)
    yb = 40 + (Y1 - Y0) * s_ + 20
    for y in range(Y0, Y1):
        for z in range(0, 22):
            x = x0
            c = (190, 150, 90) if (x, y, z) in room else (240, 228, 200) if (x + 1, y, z) in inner else (120, 120, 120) if (x, y, z) in ship else None
            if c:
                d.rectangle([40 + (y - Y0) * 3, yb + (22 - z) * 3, 40 + (y - Y0) * 3 + 2, yb + (22 - z) * 3 + 2], fill=c)
    d.text((240, yb + 10), 'section at the aft wall x %d (door %d cells wide, %d high); room interior %s m high; pickup %s' % (x0, 5, MG['door_h'], R['room']['interior_height_m'], st), fill=(30, 30, 30), font=f)
    img.save(os.path.join(HERE, 'sheet08_magazine_v1.png'))
    print(json.dumps({k: v for k, v in R.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
