# 加勒比海的公共建築（TASK-0772）—— 共用工具照 summit-carib-01m 的產生程式（同一套調色盤、牆、屋頂、部件；import 它的 design/，不另抄一份）。
# 座標同 kit.py：x 臨路寬（從路上看左 → 右）、y 進深（y 0 臨路）、z 往上（z 0 整平面）；0.1 m／格；作品框 ＝ 地塊。
# 史料：作品 references/research_civic.md（這一套查的）＋ summit-carib-01m/references/research_1640-1700.md（代號 DT1、LB2…）。
import os, sys, math
import numpy as np
from scipy import ndimage

WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUMMIT = os.path.join(WORKS, 'summit-carib-01m', 'design')
if SUMMIT not in sys.path:
    sys.path.insert(0, SUMMIT)
from carib import *                                                    # noqa: E402,F401  調色盤、Model、牆、屋頂
from houses import put_part, free_part, lean_roof_posts, hearth       # noqa: E402,F401
from public import flagpole, flag_sail, GUN, GUN_PIVOT                # noqa: E402,F401
import parts as PT                                                     # noqa: E402
import houses as _H                                                    # noqa: E402


def _borrow_fr(*names):
    """再借法式套件的幾件部件（同 summit 的 parts.borrowed：同一件作品 ⇒ 遊戲只存一次）：玻璃窗（只有總督家有玻璃，DT2 p.452）、煙囪（只有總督家有，DT2 p.451）。
    百葉色 49 由 put_part 換成這一套的 SHUT（沒上漆的木作）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location('fr_parts2', os.path.join(PT.FR_DESIGN, 'parts.py'))
    sys.path.insert(0, PT.FR_DESIGN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sys.path.pop(0)
    for nm in names:
        q = getattr(m, nm)()
        _H.PARTS.setdefault(q['id'], dict(q, src=PT.FR_ROOT + '-part-' + q['id']))


_borrow_fr('window', 'chimney')

ROCK, ROCK_D, ROCK_W = 182, 146, 177       # 石灰岩：淺灰米、深一點的裂縫、偏暖的風化面（同毛石那幾色 ⇒ 岩與砌石看起來是同一種石頭）
WATER = 46                                 # 泉水的水面（只用在這裡）


def crag_solid(cx, cy, rx0, ry0, rx1, ry1, h, X, Y, salt=0):
    """一塊陡岩（實心）：底 (rx0, ry0)、頂 (rx1, ry1) 的超橢圓，往上線性收；每一層邊緣照雜湊凹凸（± 6 格）。回傳 bool 陣列 [X, Y, h]。"""
    S = np.zeros((X, Y, h), bool)
    xs = np.arange(X)[:, None] + 0.5
    ys = np.arange(Y)[None, :] + 0.5
    ang = np.arctan2(ys - cy, xs - cx)
    for z in range(h):
        u = z / max(1, h - 1)
        rx = rx0 + (rx1 - rx0) * u
        ry = ry0 + (ry1 - ry0) * u
        k = (z // 6)
        wob = np.zeros_like(ang)
        for i, f in enumerate((3, 5, 7, 11)):                          # 幾道不同頻率的凹凸：每 6 層換一組相位 ⇒ 岩面一層一層錯開，像風化的層理
            ph = h01('crag', salt, i, k) * 2 * math.pi
            wob = wob + (6.0 / (i + 1)) * np.sin(f * ang + ph)
        d = (np.abs(xs - cx) / rx) ** 3 + (np.abs(ys - cy) / ry) ** 3
        r = 1.0 + wob / max(rx, ry)
        S[:, :, z] = d <= r ** 3
    return S


def hollow(S, keep=6):
    """只留離外面的空氣 keep 格內的殼（同聖索菲亞的做法；地面以下當實心 ⇒ 底下不開口）。"""
    pad = np.concatenate([np.ones(S.shape[:2] + (keep + 1,), bool), S], axis=2)
    inner = ndimage.binary_erosion(pad, iterations=keep, border_value=0)[:, :, keep + 1:]
    return S & ~inner


def put_mask(M, S, color_fn, layer='body', z0=0):
    xs, ys, zs = np.nonzero(S)
    for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
        M.put(layer, x, y, z + z0, color_fn(x, y, z + z0))


def rock_color(x, y, z):
    """天然岩面：大片的風化色塊（1.4 m × 1 m）＋細碎的暗點＋斷續的層理；⛔ 不要小方塊（第一版 0.5 m 的塊看起來像砌磚）。"""
    if z % 9 == 8 and h01('ly', x // 20, y // 20, z // 9) < 0.35:      # 斷續的層理
        return ROCK_D
    if h01('sp', x // 3, y // 3, z // 3) < 0.06:
        return ROCK_D
    return ROCK_W if h01('rk', (x + z // 3) // 14, (y + z // 5) // 14, z // 10) < 0.25 else ROCK


def drystone(M, x0, y0, x1, y1, h, salt=0, layer='body'):
    """乾砌石（沒有灰漿：石縫暗、石塊大小不一）的實心一段。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(h):
                row = z // 4
                u = x + y + (5 if row % 2 else 0)
                if (z % 4 == 3 and z != h - 1) or (u % 9 == 0 and z != h - 1):   # 頂上那一皮是壓頂的石板，不留縫
                    c = ROCK_D
                else:
                    c = ROCK_W if h01('ds', u // 9, row, salt) < 0.25 else ROCK
                M.put(layer, x, y, z, c)


def gun(M, name, x, y, z, face):
    """風暴角號 6 磅砲（外部模型，0.05 m）：face ＝ 砲口朝哪一面（front −y、back +y、left −x、right +x）。"""
    rz = {'front': 180, 'back': 0, 'left': 90, 'right': 270}[face]
    M.models.append({'name': name, 'source': GUN, 'at': [x, y, z], 'pivot': GUN_PIVOT, 'rotate': [0, 0, rz], 'meta': {'kind': 'deco'}})


# ─────────────────────────────── 碉堡：Fort de la Roche（托爾圖加）30 × 30 m ───────────────────────────────
def fort_roche():
    """Fort de la Roche（Levasseur 1640 後建；references/research_civic.md §3）—— 骨架照 Moreau 1797 量遺跡（MSM1 pp.732–733）：
    不規則五邊形的乾砌石圍牆；中央一塊岩高 20–25 法尺（取 7 m）；岩到牆約 35 法尺（地塊塞不下，縮到 9–11 m）；門寬 6 法尺、朝東南；
    泉包在堡裡、順一條溝流出去；總督住岩頂、彈藥也放岩頂；守軍住岩腳靠岩搭的披屋；上岩只靠一具活動鐵梯（Oexmelin：先鑿 10–12 級台階）。
    岩頂：Levasseur 的住屋（木構釘板＋essente，大小是推測）、小火藥庫、四門砲（Oexmelin：2 銅 2 鐵；1665 年移交筆錄全島只有這 4 門上架）、
    像煙囪的通風井（DT1）。正面（y 0）＝ 門那一面（城鎮那一筆的 rot 照史料朝東南）：門旁那一段牆是守港口的砲台（Charlevoix：一座在岩上、一座在台地上）。
    ⛔ 不放「la Tour」：那是 1667 年在另一處較低位置起建的圓塔（另一棟建築，MSM1）。砲台的砲眼、牆高、岩頂屋的大小是設計。"""
    X, Y, Z = 300, 300, 140
    M = Model((X, Y, Z))
    WH, WT = 24, 16                                                     # 圍牆 2.4 m 高、1.6 m 厚（乾砌石）
    PENT = [(14, 4), (286, 12), (296, 176), (176, 296), (4, 206)]      # 不規則五邊形（照遺跡「不規則」；頂點是設計）
    from PIL import Image, ImageDraw
    im = Image.new('1', (X, Y), 0)
    ImageDraw.Draw(im).polygon(PENT, fill=1)
    inside = np.array(im, bool).T                                       # [x, y]
    dist = ndimage.distance_transform_edt(inside)
    wall = inside & (dist <= WT)
    GX0, GX1 = 30, 50                                                   # 門：1.95 m（6 法尺）
    for x, y in zip(*np.nonzero(wall)):
        if GX0 <= x < GX1 and y < 40:
            continue
        for z in range(WH):
            row = z // 4
            u = int(x) + int(y) + (5 if row % 2 else 0)
            c = ROCK_D if (z % 4 == 3 and z != WH - 1) or (u % 9 == 0 and z != WH - 1) else (ROCK_W if h01('ds', u // 9, row) < 0.25 else ROCK)
            M.put('body', int(x), int(y), z, c)
    for gx in (GX0 - 3, GX1):                                           # 門柱＋橫楣、兩扇開著的木門（往裡開）
        M.box('body', gx, 4, 0, gx + 3, 22, 30, FRAME, force=True)
    M.box('body', GX0 - 3, 10, 28, GX1 + 3, 14, 31, FRAME, force=True)
    for (x0, x1) in ((GX0, GX0 + 2), (GX1 - 2, GX1)):
        M.box('body', x0, 22, 0, x1, 36, 24, SHUT)
    M.anchor('door', (GX0 + GX1) // 2, 2, 0)
    # 正面那一段牆的砲台：三個砲眼（兩角淺色石）、木砲床、三門 6 磅砲（朝外 ＝ −y）
    guns = (110, 170, 230)
    for cx in guns:
        yt = int(np.nonzero(wall[cx])[0].min())                          # 這一欄牆的外緣
        for y in range(yt, yt + WT + 1):
            half = 5 + (yt + WT - y) * 5 // WT
            for x in range(cx - half, cx + half):
                for z in range(10, WH + 2):
                    M.cells.pop((x, y, z), None)
            for x in (cx - half - 1, cx + half):
                for z in range(10, WH):
                    if (x, y, z) in M.cells:
                        M.cells[(x, y, z)] = ('body', MORTAR)
        for y in range(yt + WT + 1, yt + WT + 37):
            for x in range(cx - 13, cx + 13):
                for z in range(0, 4):
                    M.put('body', x, y, z, FLOOR if z == 3 and (x - cx) % 6 else FRAME)
        gun(M, '砲台-砲%d' % (guns.index(cx) + 1), cx, yt + WT + 16, 4, 'front')
    # 中央的岩（底 11 × 10 m、頂 9 × 8 m、高 7 m；頂很平 —— Oexmelin）
    RH = 70
    cx, cy = 150, 168
    S = crag_solid(cx, cy, 55, 50, 45, 40, RH, X, Y, salt=7)
    # 鑿出來的台階：正面、從左往右爬 11 級（每級高 0.3 m、深 0.3 m）到 3.3 m（約半高）
    sx0, sy0, SW = 104, 112, 12
    for k in range(11):
        zk = (k + 1) * 3
        for x in range(sx0 + 3 * k, sx0 + 3 * k + 3):
            S[x, sy0:sy0 + SW, :zk] = True
            S[x, sy0:sy0 + SW, zk:] = False
    top_x = sx0 + 33                                                    # 台階頂的平台（x 137..149、z 33）
    S[top_x:top_x + 12, sy0:sy0 + SW, :33] = True
    S[top_x:top_x + 12, sy0:sy0 + SW, 33:] = False
    S[176:184, 140:148, 20:] = False                                    # 通風井（像煙囪：岩頂一個 0.8 m 方口往下，挖穿到殼裡）
    put_mask(M, hollow(S, 6), rock_color)
    for x in range(174, 186):                                          # 井口的木框
        for y in range(138, 150):
            if not (176 <= x < 184 and 140 <= y < 148):
                M.put('body', x, y, RH, FRAME)
    # 活動鐵梯：從台階頂的平台斜靠到岩頂（兩根直桿、每 3 格一道踏棍；上端多伸 0.4 m）
    lx, ya = top_x + 3, sy0 + SW - 2
    hit = np.nonzero(S[lx:lx + 7, :, RH - 1].any(axis=0))[0]
    yb = int(hit.min()) - 1 if len(hit) else ya
    py = ya
    for z in range(33, RH + 4):
        u = min(1.0, (z - 33) / (RH - 1 - 33))
        yy = int(round(ya + (yb - ya) * u))
        for x in (lx, lx + 6):
            for y in range(min(py, yy), max(py, yy) + 1):              # 往裡挪的那一層連上一層的位置也補 ⇒ 面相連（不然算成浮空）
                M.put('body', x, y, z, IRON)
        if z % 3 == 0 and z < RH:
            for x in range(lx + 1, lx + 6):
                M.put('body', x, yy, z, IRON)
        py = yy
    # 岩頂：總督的住屋（木構釘板、essente 四坡頂；5.2 × 3.8 m）、小火藥庫（毛石）、四門砲（木砲床）
    HR = (124, 162, 176, 200)
    M.box('body', HR[0], HR[1], RH - 3, HR[2], HR[3], RH + 1, ROCK)   # 墊平（岩頂不平）
    board_walls(M, HR, RH + 1, RH + 28, 2)
    put_part(M, 'door-plank', '住屋-門', 'front', HR, 150, RH + 1, 2)
    put_part(M, 'window-board', '住屋-窗1', 'front', HR, 134, RH + 9, 2)
    put_part(M, 'window-board', '住屋-窗2', 'front', HR, 166, RH + 9, 2)
    shingle_roof(M, [{'x0': HR[0], 'y0': HR[1], 'x1': HR[2], 'y1': HR[3], 'ze': RH + 28, 'p': 0.9, 'over': (3, 3, 3, 3)}], salt=63)
    mr = (180, 178, 198, 196)
    M.box('body', mr[0], mr[1], RH - 3, mr[2], mr[3], RH, ROCK)
    rubble_walls(M, mr, RH, RH + 27, 3, salt=61)
    put_part(M, 'door-plank', '火藥庫-門', 'left', mr, (mr[1] + mr[3]) // 2, RH, 3)
    clear_under_link(M)
    shingle_roof(M, [{'x0': mr[0], 'y0': mr[1], 'x1': mr[2], 'y1': mr[3], 'ze': RH + 27, 'p': 0.8, 'over': (2, 2, 2, 2)}], salt=62)
    for (gx, gy, face) in ((140, 138, 'front'), (160, 138, 'front'), (113, 176, 'left'), (186, 162, 'right')):
        for x in range(gx - 7, gx + 7):
            for y in range(gy - 7, gy + 7):
                M.put('body', x, y, RH, FLOOR if (x + y) % 5 else FRAME, force=True)
        gun(M, '岩頂-砲-%s%d' % ({'front': '前', 'left': '左', 'right': '右'}[face], gx), gx, gy, RH + 1, face)
    # 旗杆＋白旗：住屋後面
    ft, fb = flagpole_on(M, 150, 202, RH, RH + 56)
    M.anchor('flag', 150, 202, RH + 57)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 30, toward=1)]
    # 岩腳：守軍住的披屋兩間（靠岩、棕櫚葉單坡頂，外側兩根柱；MSM1）
    lean_roof_posts(M, 44, 140, 98, 196, 30, 0.25, 'left', thatch_color, [(46, 142), (46, 192)], salt=64)
    lean_roof_posts(M, 120, 222, 180, 262, 30, 0.25, 'back', thatch_color, [(122, 258), (176, 258)], salt=65)
    # 泉：堡裡、岩的右後方；石砌池＋順一條溝流到後牆、穿牆出去（MSM1：溝被一面牆與一個鋸齒凸角縱射 —— 凸角沒做）
    M.box('body', 212, 196, 0, 232, 214, 5, RUBBLE)
    M.box('body', 214, 198, 3, 230, 212, 5, WATER, force=True)
    for k in range(0, 80):                                             # 溝：往右後方（+x +y）斜走到牆、穿過去
        x, y = 222 + k, 214 + k
        if not (0 <= x < X - 1 and 0 <= y < Y - 1):
            break
        for (dx, dy) in ((0, 0), (1, 0), (0, 1)):
            for z in range(0, WH):
                M.cells.pop((x + dx, y + dy, z), None)
            M.put('body', x + dx, y + dy, 0, WATER)
        for (dx, dy) in ((-1, 1), (2, -1), (1, 2), (-1, 2), (2, 0)):
            if (x + dx, y + dy, 0) not in M.cells:
                M.put('body', x + dx, y + dy, 0, RUBBLE)
        if not inside[min(x, X - 1), min(y, Y - 1)]:
            break
    M.models += [{'name': '火藥桶-岩頂', 'source': 'summit-rocher-01m-barrel', 'at': [186, 200, RH], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-披屋', 'source': 'summit-rocher-01m-barrel', 'at': [60, 180, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [GX1 + 1.5, 3, 22.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'fort-roche', 'title': 'Fort de la Roche（托爾圖加的岩堡：不規則五邊形的乾砌石圍牆、門朝東南、門旁的砲台三門砲；中央 7 m 的岩、鑿出的台階接活動鐵梯；岩頂總督的住屋、火藥庫、四門砲、通風井、白旗；岩腳守軍的披屋；堡裡的泉與排水溝）',
            'use': 'fort-de-la-roche', 'lot': (30, 30), 'M': M, 'style': 'carib',
            'layers': {'body': '圍牆、岩與岩頂', 'roof': '屋頂'}, 'flags': flags}


def clear_under_link(M, layers=('body', 'gallery')):
    """最後擺的那個部件壓到的牆格 ⇒ 拿掉（弧牆、厚牆的轉角：部件框比挖的開口大）。"""
    for k in M.links[-1]['cells']:
        if k in M.cells and M.cells[k][0] in layers:
            del M.cells[k]


def rubble_walls_cell(M, x, y, z, vx, vy, z0):
    """圓塔的毛石：一皮 5 格、沿圓周每 8 格一道灰縫、上下皮錯縫（vx, vy ＝ 離塔心）。"""
    row = (z - z0) // 5
    a = int(((math.atan2(vy, vx) + math.pi) * 36) + (4 if row % 2 else 0))
    if (z - z0) % 5 == 4 or a % 8 == 0:
        c = MORTAR
    else:
        c = RUBBLE_D if h01('tw', a // 8, row) < 0.15 else RUBBLE
    M.put('body', x, y, z, c)


def flagpole_on(M, x, y, z0, z_top, layer='body'):
    """站在 z0 的旗杆（2 × 2、頂上一顆圓頭）。回傳布旗的綁邊（旗杆 +x 那一格的空氣，上、下）。"""
    M.box(layer, x, y, z0, x + 2, y + 2, z_top, FRAME)
    M.box(layer, x, y, z_top, x + 2, y + 2, z_top + 2, GOLD)
    return (x + 2, y, z_top - 2), (x + 2, y, z_top - 20)


ALL = [fort_roche]
