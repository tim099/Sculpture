# 海鷗號 新圖紙 08（TASK-0024 步驟 10）：艉部藥箱（彈藥庫）＋火藥桶、甲板上的沙箱灶 ⇒ masks/magazine/chest.vox.txt、magazine_placement.json、verify_magazine.json
#   出處：做法照杉心號 basecamp-piragua-01m/design/draft_magazine.py（露天小船：彈藥庫子作品＋一個火藥桶模型、關聯 meta kind=magazine pos=aft、固定點 blast／door；
#         取用點要一塊 9×9、頭上 8 格空的平地 —— 杉心號步驟 14 撞到的），自己寫；灶引用星辰號的 claude-baghlah-01m-hearth（本小姐自己的元件，kind=galley、固定點 smoke）。
#   用法：python -I -X utf8 draft_magazine.py [--probe=chest_dz=1]
#   · 讀前面每一步的設計清單（船殼、甲板＋砲柱、桅、桿、艏柱頭）與砲的模型外框；不讀作品 ⇒ 落格之後重跑一樣。
import sys, os, json, math, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import draft_decks as DD

sys.stdout.reconfigure(encoding='utf-8')
YC = 80
BARREL = 'basecamp-frigate-constitution-01m-powder-barrel'     # 22×22×27、0.02 m ⇒ scale 0.2 ＝ 0.44×0.44×0.54 m
HEARTH = 'claude-baghlah-01m-hearth'                           # 24×20×16、0.05 m ⇒ scale 0.5 ＝ 1.2×1.0×0.8 m
C_WALL, C_RIM = 177, 136                                       # 箱板松木 177、上緣橡木壓條 136（Ship_Magazine §8 的色）


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)) for x, y, z, c in a}


_EXT = {}


def extent(work):
    """來源作品實際有格的範圍（模型座標，[min, max+1)）—— 引擎印的模型外框照這個，不是照作品的框（v1 用框 ⇒ 船首砲的外框從 z 21 起、蓋住平台的頭頂）。"""
    if work not in _EXT:
        import wio
        a = wio.export_list(work, None)
        _EXT[work] = (a[:, :3].min(axis=0).tolist(), (a[:, :3].max(axis=0) + 1).tolist())
    return _EXT[work]


def box_of(at, pivot, work, scale, rot=0):
    """模型外框（世界）：來源的格子範圍減 pivot、縮 scale、繞 z 轉 rot（0／90／180／270）、加 at。"""
    lo, hi = extent(work)
    c, s = round(math.cos(math.radians(rot))), round(math.sin(math.radians(rot)))
    pts = []
    for x in (lo[0], hi[0]):
        for y in (lo[1], hi[1]):
            dx, dy = (x - pivot[0]) * scale, (y - pivot[1]) * scale
            pts.append((at[0] + c * dx - s * dy, at[1] + s * dx + c * dy))
    return [[min(p[0] for p in pts), min(p[1] for p in pts), at[2] + (lo[2] - pivot[2]) * scale],
            [max(p[0] for p in pts), max(p[1] for p in pts), at[2] + (hi[2] - pivot[2]) * scale]]


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    hull = load('masks/hull/hull_01.vox.txt')
    deck = load('masks/decks/deck_main.vox.txt') | load('masks/guns/post.vox.txt')
    ship = hull | deck | load('masks/masts/main.vox.txt') | load('masks/masts/fore.vox.txt') | load('masks/masts/tack_spar.vox.txt') | load('masks/deco/stem_head.vox.txt')
    lay = {k: (v['v'] if isinstance(v, dict) and 'v' in v else v) for k, v in plan['layout'].items() if k != 'src'}
    sp = lay['stern_platform']
    stand = sp['board_z'] + 1
    dz = int(probe.get('chest_dz', 0))
    # ── 藥箱：船尾平台左舷、7×7 外框、牆 1 格、高 6、開口朝上；箱底就是平台的板。
    #    v1 想放最後面的角落（x 20–26），可是平台在 x 18–20 只有 5–7 格寬 ⇒ 箱子只能放中線、後面還圍出一塊 0.33 m² 走不到的角 ⇒ 往前挪到 x 28–34、貼左舷 ──
    #    步驟 14 匯入檢查 ✗「找不到取用點」：船窄 ⇒ 遊戲走窄船退路（23_powder.js findLine：三個桶沿中線排 15×5 格、y ＝ 中線 −2～+2）⇒ 箱子 v2（x 28–34、y 72–78）
    #    的牆壓在 y 78 ⇒ 船尾平台排不下；船頭平台被灶（kind=galley 也算擋路）與前桅擋住 ⇒ v3 箱子挪到 x 30–36、y 71–77，讓出中線那 5 格
    x0, x1 = 30, 36
    y0, y1 = 71, 77
    chest = {}
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(stand + dz, stand + 6 + dz):
                if x in (x0, x1) or y in (y0, y1):
                    chest[(x, y, z)] = C_RIM if z == stand + 5 + dz else C_WALL
    # ── 火藥桶：箱子正中、站在板上 ──
    bat = [(x0 + x1) / 2 + 0.5, (y0 + y1) / 2 + 0.5, float(stand)]
    barrel = {'name': '桶-001', 'host': 'magazine', 'work': BARREL, 'at': bat, 'pivot': [11, 11, 0], 'scale': 0.2, 'rotate': [0, 0, 0],
              'meta': {'kind': 'powder', 'powder_lb': 50, 'id': 'powder-1'}}
    bbox = box_of(bat, (11, 11, 0), BARREL, 0.2)
    # ── 沙箱灶：船頭平台右舷 ──
    bp = lay['bow_platform']
    hat = [114.0, 85.0, float(bp['board_z'] + 1)]           # v1 (116,88)：外框碰到右舷船殼內面與右舷船頭迴旋砲的座（26 格）⇒ 往船裡挪
    hearth = {'name': '爐灶', 'host': 'deck', 'work': HEARTH, 'at': hat, 'pivot': [12, 10, 0], 'scale': 0.5, 'rotate': [0, 0, 0], 'meta': {'kind': 'galley'}}
    hbox = box_of(hat, (12, 10, 0), HEARTH, 0.5)
    # ── 讀數 ──
    occ = ship | set(chest)
    R = {'probe': probe or None, 'chest': {'cells': len(chest), 'x': [x0, x1], 'y': [y0, y1], 'z': [stand + dz, stand + 5 + dz],
                                           'overlap_ship': len(set(chest) & ship),
                                           'stands_on_board': all((x, y, sp['board_z']) in deck for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)) and dz == 0}}

    def box_hits(b, cells):
        n = 0
        for x in range(int(math.floor(b[0][0])), int(math.ceil(b[1][0]))):
            for y in range(int(math.floor(b[0][1])), int(math.ceil(b[1][1]))):
                for z in range(int(math.floor(b[0][2])), int(math.ceil(b[1][2]))):
                    if (x, y, z) in cells:
                        n += 1
        return n
    R['barrel'] = {'bbox': bbox, 'cells_in_bbox': box_hits(bbox, occ), 'inside_chest': x0 < bbox[0][0] and bbox[1][0] < x1 + 1 and y0 < bbox[0][1] and bbox[1][1] < y1 + 1}
    R['hearth'] = {'bbox': hbox, 'cells_in_bbox': box_hits(hbox, occ), 'on_board': all((x, y, bp['board_z']) in deck for x in range(int(hbox[0][0]), int(math.ceil(hbox[1][0])))
                                                                                         for y in range(int(hbox[0][1]), int(math.ceil(hbox[1][1]))))}
    # 模型外框（砲、座、灶、桶）＝ 走路格的障礙（遊戲：站位與走路格避開每個模型的外框）
    guns = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))['models']
    gb = [box_of(g['at'], g['pivot'], g['work'], g['scale'], g['rotate'][2]) for g in guns]
    boxes = gb + [hbox, bbox]

    def standing(x, y, z):
        if (x, y, z - 1) not in occ:
            return False
        for zz in range(z, z + 12):
            if (x, y, zz) in occ:
                return False
        for b in boxes:
            if b[0][0] < x + 1 and x < b[1][0] and b[0][1] < y + 1 and y < b[1][1] and b[0][2] < z + 12 and z < b[1][2]:
                return False
        return True
    # 取用點：船尾平台上一塊 9×9、頭上 8 格空的平地（杉心號步驟 14 的條件）
    spots = []
    for xa in range(sp['x0'], sp['x1'] - 7):
        for ya in range(60, 101):
            ok = True
            for x in range(xa, xa + 9):
                for y in range(ya, ya + 9):
                    if (x, y, stand - 1) not in occ or any((x, y, z) in occ for z in range(stand, stand + 8)) or \
                            any(b[0][0] < x + 1 and x < b[1][0] and b[0][1] < y + 1 and y < b[1][1] and b[0][2] < stand + 8 and stand < b[1][2] for b in boxes):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                spots.append([xa, ya])
    R['access_9x9_on_stern_platform'] = {'count': len(spots), 'x_range': [min(s[0] for s in spots), max(s[0] for s in spots) + 8] if spots else None,
                                         'y_range': [min(s[1] for s in spots), max(s[1] for s in spots) + 8] if spots else None}
    # 灶的四個面（外框外 2 格的中點，0.6 m 內有沒有走路格）
    cx, cy = (hbox[0][0] + hbox[1][0]) / 2, (hbox[0][1] + hbox[1][1]) / 2
    faces = {'-x': (hbox[0][0] - 2, cy), '+x': (hbox[1][0] + 2, cy), '-y': (cx, hbox[0][1] - 2), '+y': (cx, hbox[1][1] + 2)}
    fz = bp['board_z'] + 1
    fr = {}
    for nm, (px, py) in faces.items():
        near = [(x, y) for x in range(int(px) - 6, int(px) + 7) for y in range(int(py) - 6, int(py) + 7)
                if (x + 0.5 - px) ** 2 + (y + 0.5 - py) ** 2 <= 36 and standing(x, y, fz)]
        fr[nm] = len(near)
    R['hearth_faces_standing_cells_within_0.6m'] = fr
    # 走路格（甲板一層，模型外框當障礙）
    prof = DD.floor_profile(lay)
    ylo, yhi = {}, {}
    for (x, y, z) in hull:
        ylo[x] = min(ylo.get(x, 999), y)
        yhi[x] = max(yhi.get(x, -1), y)
    pts = {}
    for x, f in prof.items():
        for z in range(max(1, f - 2), f + 4):
            for y in range(ylo[x] + 1, yhi[x]):                # 只收船殼裡面（同一欄兩邊都有船殼；同 draft_decks.walk）
                if standing(x, y, z):
                    pts.setdefault((x, y), []).append(z)
    idx = {}
    for (x, y), zs in pts.items():
        for z in zs:
            idx[(x, y, z)] = len(idx)
    par = list(range(len(idx)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for (x, y, z), i in idx.items():
        for dx, dy in ((1, 0), (0, 1)):
            for z2 in pts.get((x + dx, y + dy), []):
                if abs(z2 - z) <= 3:
                    a, c = find(i), find(idx[(x + dx, y + dy, z2)])
                    if a != c:
                        par[a] = c
    groups = {}
    for k, i in idx.items():
        groups.setdefault(find(i), 0)
        groups[find(i)] += 1
    sizes = sorted(groups.values(), reverse=True)
    R['walk_with_model_boxes'] = {'groups': len(sizes), 'area_m2': [round(s * 0.01, 2) for s in sizes[:4]]}
    if probe:
        print(json.dumps(R, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'magazine'), exist_ok=True)
    fn = os.path.join(HERE, 'masks', 'magazine', 'chest.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 海鷗號 艉部藥箱（draft_magazine.py；彈藥庫子作品、整船的框）x,y,z,color —— at 0,0,0\n')
        f.write(''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(chest.items())))
    anchors = {'blast': [int(bat[0]), int(bat[1]), stand + 2], 'door': [int(bat[0]), y1 + 1, stand]}   # door：箱子右舷那一面外（送藥手站的地方，中線那一排）
    out = {'hosts': {'magazine': 'claude-felucca-01m-magazine', 'deck': 'claude-felucca-01m-deck-main'},
           'link': {'name': '彈藥庫', 'meta': {'kind': 'magazine', 'pos': 'aft', 'powder_lb': 50, 'id': 'magazine-1'}},
           'anchors': anchors, 'models': [barrel, hearth]}
    with open(os.path.join(HERE, 'magazine_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    R['anchors'] = anchors
    R['anchor_blast_is_air'] = tuple(anchors['blast']) not in occ
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('masks/magazine/chest.vox.txt', 'magazine_placement.json')}
    with open(os.path.join(HERE, 'verify_magazine.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
