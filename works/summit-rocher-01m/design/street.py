# 岩堡港 街景（TASK-0580 第六階段，2026-10-16）：可重複用的小件（子作品，0.05 m／格）＋擺放（外部模型，scale 0.5）。
# 用法：python -I -X utf8 -B street.py <design 資料夾>
#   Tim 2026-10-16：「街上的物件都做成可以重複使用的子物件」「燈籠可以有光源」
#   ⇒ 每一種物件一件子作品，在組裝件裡用 `work sub=model source_work=…` 擺很多次（遊戲裡網格只存一份）；
#     燈籠與燻肉架的火 meta kind=light、來源作品登記固定點 wick（火焰中心）—— 遊戲在 wick 放點光源（Sculpture_Shipbuilding.md 的 light）。
#   · 小件座標：x 寬、y 深、z 往上。模型座標是連續的：第 i 格佔 [i, i+1)（obj 頂點在格角；固定點整數 ⇒ 格心 i+0.5）。
#     pivot ＝ 底面中心（燈籠 ＝ 背板背面的掛點）。世界也一樣：地面第一層空氣 g ⇒ 地面頂 ＝ g。
#   · 擺放：placements 由本檔算（燈籠照房屋的 lantern-L／R 固定點＋那條關聯的 at／mirror；其他照下面的表），
#     驗證交給 apply_street.py verify（拿組裝件匯出的格子量：撞到幾格、底下沒撐住幾格）。
#   · 輸出：masks/street/<件>.vox.txt、street.json（小件的外框、固定點、擺放）。重跑逐位元組相同。
import sys, os, json, math
import numpy as np

D = os.path.abspath(sys.argv[1])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
PAL = plan['palette']
IRON, WOOD, WOOD_G, DARK, GLOW = PAL['void_dark'], PAL['wood'], PAL['wood_grey'], PAL['timber_dark'], PAL['lantern']


def hash2(x, y, s):
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return (h ^ (h >> 16)) / 4294967296.0


PROPS = {}


def prop(name, title, cells, pivot, anchors, meta=None):
    PROPS[name] = {'title': title, 'cells': cells, 'pivot': pivot, 'anchors': anchors, 'meta': meta or {}}


# ── 燈籠（壁掛）：背板貼柱子正面、鐵臂往 −y 伸 0.4 m、燈吊在臂端；燈身 7×7、玻璃發亮（245） ──
c = {}
for z in range(10, 21):                                                   # 背板 3 寬 × 11 高、2 厚（y 11–12）
    for x in range(3, 6):
        for y in (11, 12):
            c[(x, y, z)] = IRON
for y in range(3, 11):                                                    # 臂（z 19–20）
    for z in (19, 20):
        c[(4, y, z)] = IRON
for i in range(7):                                                        # 斜撐：背板下段到臂中段（階梯狀，每一格面對面相連）
    c[(4, 10 - i, 12 + i)] = IRON
    c[(4, 10 - i, 13 + i)] = IRON
for z in (17, 18):                                                        # 吊鍊
    c[(4, 4, z)] = IRON
for x in range(1, 8):                                                     # 燈身：x 1–7、y 1–7、z 2–13
    for y in range(1, 8):
        for z in range(2, 14):
            edge = x in (1, 7) or y in (1, 7)
            if not edge and 2 < z < 13:
                continue                                                  # 裡面空的（火焰另放）
            post = (x in (1, 7)) and (y in (1, 7))
            if z == 2 and x in (2, 6) and y in (2, 6):
                continue                                                  # 底板四個通氣孔（燈身才不是封死的空腔）
            if z in (2, 13) or post:
                c[(x, y, z)] = IRON                                       # 底、頂框、四根角柱
            else:
                c[(x, y, z)] = GLOW                                       # 四面玻璃（亮）
for x in range(2, 7):                                                     # 頂蓋（金字塔）
    for y in range(2, 7):
        c[(x, y, 14)] = IRON
for x in range(3, 6):
    for y in range(3, 6):
        c[(x, y, 15)] = IRON
c[(4, 4, 16)] = IRON
for z in range(5, 9):                                                     # 火焰（燈芯在 z 6.5）
    c[(4, 4, z)] = GLOW
c[(4, 4, 4)] = IRON                                                       # 燈座
for z in range(3, 5):
    c[(4, 4, z)] = IRON
prop('lantern', '岩堡港｜壁掛燈籠（鐵臂＋吊燈；光源 wick）', c, [4.5, 13, 15.5],
     {'wick': [4, 4, 6], 'mount': [4, 12, 15]}, {'kind': 'light'})

# ── 酒桶：直徑 12（腰）／10（兩端）、高 18；桶板兩色交錯、四道鐵箍、頂蓋 ──
c = {}
for z in range(18):
    t = (z - 8.5) / 9.0
    r = 5.0 + 1.0 * (1 - t * t)
    hoop = z in (1, 2, 5, 12, 15, 16)
    for x in range(12):
        for y in range(12):
            d = math.hypot(x - 5.5, y - 5.5)
            if d > r:
                continue
            if d > r - 1.2:
                ang = math.atan2(y - 5.5, x - 5.5)
                c[(x, y, z)] = IRON if hoop else (WOOD if int((ang + math.pi) / (2 * math.pi) * 14) % 2 else WOOD_G)
            else:
                c[(x, y, z)] = WOOD                                       # 實心（空心封死的桶是一個空腔，網格也多一層朝內的面）
prop('barrel', '岩堡港｜酒桶（0.6 m × 0.9 m）', c, [6, 6, 0], {'base': [5, 5, 0]})

# ── 貨箱：12³；六面木板（每 3 格一道暗縫）、十二條邊深色框 ──
c = {}
for x in range(12):
    for y in range(12):
        for z in range(12):
            on = [x in (0, 11), y in (0, 11), z in (0, 11)]
            if sum(on) == 0:
                c[(x, y, z)] = WOOD                                       # 實心
                continue
            if sum(on) >= 2:
                c[(x, y, z)] = DARK
            else:
                u = z if (on[0] or on[1]) else x
                c[(x, y, z)] = WOOD_G if u % 3 == 0 else WOOD
prop('crate', '岩堡港｜貨箱（0.6 m 見方）', c, [6, 6, 0], {'base': [5, 5, 0]})

# ── 燻肉架（boucan）：四根柱、離地 1 m 的青木格柵、上面一條條肉；底下石圈火坑（火是光源 wick） ──
c = {}
LX, LY, ZG = 32, 20, 20
for (px, py) in ((0, 0), (LX - 2, 0), (0, LY - 2), (LX - 2, LY - 2)):     # 柱 2×2、高 24
    for x in (px, px + 1):
        for y in (py, py + 1):
            for z in range(24):
                c[(x, y, z)] = WOOD
for x in range(LX):                                                       # 兩根長橫木
    for y in (0, 1, LY - 2, LY - 1):
        c[(x, y, ZG)] = DARK
for x in range(1, LX - 1, 3):                                             # 格柵（橫跨的細枝，每 3 格）
    for y in range(2, LY - 2):
        c[(x, y, ZG)] = DARK
for k, x0 in enumerate(range(4, LX - 3, 6)):                              # 肉條（紅，鋪在細枝上 —— x0 對準細枝，⛔ 不懸在兩根中間）
    for y in range(4, LY - 4):
        if hash2(k, y, 31) > 0.25:
            c[(x0, y, ZG + 1)] = PAL['shutter_red']
            c[(x0 + 1, y, ZG + 1)] = PAL['shutter_red']
cxf, cyf = (LX - 1) / 2, (LY - 1) / 2
prop('boucan', '岩堡港｜燻肉架 boucan（1.6 × 1.0 m；底下的火是另一件 -campfire）', c, [LX / 2, LY / 2, 0], {'base': [15, 9, 0]})

# ── 營火（火坑）：石圈、灰與炭火、兩根交叉的柴、火苗；光源 wick（燻肉架底下用，也可以單獨擺） ──
c = {}
C0 = 6
for x in range(13):
    for y in range(13):
        d = math.hypot(x - C0, y - C0)
        if 5.0 <= d < 6.5:
            c[(x, y, 0)] = PAL['stone']
            if hash2(x, y, 33) > 0.5:
                c[(x, y, 1)] = PAL['stone']
        elif d < 5.0:
            c[(x, y, 0)] = IRON if d > 3 else GLOW
for i in range(-3, 4):                                                    # 兩根柴：一根順 x（z 1）、一根順 y（z 2），在中心上下相疊
    c[(C0 + i, C0, 1)] = DARK
    c[(C0, C0 + i, 2)] = DARK
for (dx, dy, z) in ((0, 0, 3), (0, 0, 4), (1, 0, 4), (0, 0, 5), (0, 1, 5), (0, 0, 6)):   # 火苗（一串相連）
    c[(C0 + dx, C0 + dy, z)] = GLOW
c[(C0 + 1, C0, 3)] = GLOW
c[(C0, C0 + 1, 3)] = GLOW
prop('campfire', '岩堡港｜營火（火坑；光源 wick）', c, [C0 + 0.5, C0 + 0.5, 0], {'wick': [C0, C0, 4], 'base': [C0, C0, 0]}, {'kind': 'light', 'light': 'fire'})

# ── 豬：身長 18、寬 9；粉（246）、蹄與眼深色、鼻頭紅 ──
c = {}
PINK, SNOUT = PAL['plaster_salmon'], PAL['shutter_red']
for x in range(2, 16):
    for y in range(9):
        for z in range(4, 13):
            if ((x - 9) / 7.0) ** 2 + ((y - 4) / 4.5) ** 2 + ((z - 8) / 4.5) ** 2 <= 1:
                c[(x, y, z)] = PINK
for (lx, ly) in ((4, 1), (4, 6), (13, 1), (13, 6)):                       # 腳 2×2、高 5（蹄 1 格）
    for x in (lx, lx + 1):
        for y in (ly, ly + 1):
            for z in range(0, 5):
                c[(x, y, z)] = DARK if z == 0 else PINK
for x in range(15, 19):                                                   # 頭
    for y in range(1, 8):
        for z in range(6, 12):
            if ((x - 16) / 2.6) ** 2 + ((y - 4) / 3.2) ** 2 + ((z - 9) / 3.0) ** 2 <= 1:
                c[(x, y, z)] = PINK
for y in range(3, 6):                                                     # 鼻頭
    for z in (7, 8):
        c[(19, y, z)] = SNOUT
c[(17, 2, 10)] = IRON; c[(17, 6, 10)] = IRON                              # 眼（嵌在頭上）
for (y, z) in ((2, 12), (6, 12), (2, 13), (6, 13)):                       # 耳
    c[(16, y, z)] = PINK
for (x, z) in ((2, 10), (1, 10), (1, 11), (1, 12), (2, 12)):             # 尾巴（捲；一串相連、接在屁股上）
    c[(x, 4, z)] = PINK
prop('pig', '岩堡港｜豬（身長 0.9 m）', c, [10, 4.5, 0], {'base': [9, 4, 0]})

# ═════════ 擺放 ═════════
links = json.load(open(os.path.join(os.path.dirname(D), 'links.json'), encoding='utf-8'))['links']
VH = json.load(open(os.path.join(D, 'verify_houses.json'), encoding='utf-8'))
place = []
for L in links:
    w = L['work']
    if '-house-' not in w:
        continue
    var = w.rsplit('-', 1)[1].upper()
    A, W = VH[var]['anchors'], VH[var]['bbox'][0]
    for side in ('L', 'R'):
        a = A.get('lantern-' + side)
        if not a:
            continue
        ax = (W - a[0]) if 'x' in (L.get('mirror') or '') else a[0]     # 固定點是連續座標（柱子中心 x、柱前一格的格心 y）⇒ 翻面 ＝ W − x
        place.append({'name': '燈籠-%s-%s' % (L['name'].split('-')[1], side), 'prop': 'lantern',
                      'at': [L['at'][0] + ax, L['at'][1] + a[1] + 0.5, L['at'][2] + a[2] - 2], 'rot': 0})   # y +0.5 ＝ 柱子正面；低 2 格：背板頂才不會頂到屋簷
# 地面上的小件：at ＝ 底面中心（z 由 verify 讀地面高度補：這裡寫 None）；rot 度（繞 z）
GROUND = [
    # 西棧橋頭的貨堆（碼頭面）
    ('貨-西-1', 'barrel', 424, 312, 0), ('貨-西-2', 'barrel', 431, 312, 40), ('貨-西-3', 'barrel', 427.5, 318, 15),
    ('貨-西-4', 'crate', 438, 313, 0), ('貨-西-5', 'crate', 438, 320.5, 8), ('貨-西-6', 'crate', 438, 316, 3, 1),
    # 東棧橋頭
    ('貨-東-1', 'barrel', 840, 310, 0), ('貨-東-2', 'barrel', 846.5, 310, 25), ('貨-東-3', 'barrel', 854, 310, 60),
    ('貨-東-4', 'barrel', 843.5, 317.5, 10), ('貨-東-5', 'barrel', 850.5, 317.5, 70),
    # 倉庫 Q1 門前（碼頭步道）
    ('貨-倉-1', 'crate', 326, 344, 0), ('貨-倉-2', 'crate', 333.5, 344, 5), ('貨-倉-3', 'crate', 329.5, 351.5, 12),
    ('貨-倉-4', 'barrel', 340, 350, 0), ('貨-倉-5', 'crate', 330, 346, 4, 1),
    # 酒館 Q3 門前
    ('貨-酒館-1', 'barrel', 556, 350, 0), ('貨-酒館-2', 'barrel', 563, 350, 30), ('貨-酒館-3', 'barrel', 559.5, 350, 50, 1),
    # 燻肉架：鎮的兩頭空地
    ('燻肉架-西', 'boucan', 281, 410, 90), ('燻肉架-東', 'boucan', 980, 420, 90),
    ('營火-西', 'campfire', 281, 410, 0), ('營火-東', 'campfire', 980, 420, 0),
    # 豬
    ('豬-1', 'pig', 622, 418, 20), ('豬-2', 'pig', 641, 445, 200), ('豬-3', 'pig', 286, 440, 300),
    ('豬-4', 'pig', 399, 430, 95), ('豬-5', 'pig', 632, 590, 160),
]
for g in GROUND:
    nm, pr, x, y, rot = g[:5]
    place.append({'name': nm, 'prop': pr, 'at': [x, y, None], 'rot': rot, 'stack': g[5] if len(g) > 5 else 0})

out = {'scale': 0.5, 'meters_per_voxel': 0.05, 'props': {}, 'placements': place}
os.makedirs(os.path.join(D, 'masks', 'street'), exist_ok=True)
for nm, p in PROPS.items():
    cells = sorted((k[0], k[1], k[2], v) for k, v in p['cells'].items())
    a = np.array([t[:3] for t in cells])
    assert a.min() >= 0, nm
    with open(os.path.join(D, 'masks', 'street', nm + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 岩堡港 街景小件 %s（street.py 產；x,y,z,color）\n' % nm)
        f.write(''.join('%d,%d,%d,%d\n' % t for t in cells))
    out['props'][nm] = {'title': p['title'], 'voxels': len(cells), 'bbox': [int(v) for v in a.max(0) + 1], 'pivot': p['pivot'],
                        'anchors': p['anchors'], 'meta': p['meta']}
with open(os.path.join(D, 'street.json'), 'w', encoding='utf-8', newline='\n') as fo:
    json.dump(out, fo, ensure_ascii=False, indent=1, sort_keys=True); fo.write('\n')
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ('voxels', 'bbox')} for k, v in out['props'].items()}, ensure_ascii=False), len(place), 'placements')
