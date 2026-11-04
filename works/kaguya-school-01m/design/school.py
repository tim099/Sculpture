# 歐式學校（kaguya 2026-11-04，TASK-1186；Tim「/scp-task 1186 GO」）：君士坦丁堡、加拉塔、里斯本蓋的學校不再是空地、也不再借西班牙殖民地那一款。
#   挑模型的退路（Blocksail TOWN_BUILD §2.1，量過 world/townplans 的 styles）：君士坦丁堡 roman ⇒ common ⇒ fr、加拉塔 genoa ⇒ common ⇒ fr、
#   阿姆斯特丹 nl ⇒ common ⇒ fr（三套都沒有學校）；里斯本、豐沙爾、安格拉 pt ⇒ es ⇒ common ⇒ fr（借 es-school）。
#   ⇒ 兩款：common-school（共用那一套：上面三座都走到；carib、en、es 的城退路先碰到自己那一款，不受影響）、pt-school（葡萄牙那一套）。
# 平面、教室裡面、工作點全借 calli-civic-01m 的 gaps.py（carib／en／es 三款學校同一個平面：school_room、school_work）⇒ 五款學校在遊戲裡同一套站位。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊 12 × 10 m、⛔ 什麼都不伸出框。
# 史料與設計的分界：
#   〔摘：通說〕拜占庭的孩子跟街坊的蒙學老師（grammatistes）學讀寫，教室多半是老師自己的屋子或教堂旁的一間；17 世紀荷蘭的學校也多在老師家裡、一間屋子坐滿長凳；
#      葡萄牙 1660 年代教「讀、寫、算」的老師（mestres de ler, escrever e contar）領市政或王室的執照、教室是租來的一間；
#      17 世紀葡萄牙的牆裙常貼一圈藍、黃兩色的花磚（azulejos de padrão）；里斯本的房子刷石灰白、門窗框與牆角用米白的 lioz 石灰石。
#   〔沒查到〕三地 15～17 世紀學校房子的樣子 ⇒ 平面、尺寸、壁爐、字母板、門上的花磚聖像、窗台全部〔設計〕；還沒有黑板 ⇒ 不放（同 calli 的三款）。
#   common 照共用那一套的語彙（BUILDING_SPEC §6.14：毛石、木板、木瓦）⇒ 擺在君士坦丁堡、加拉塔、阿姆斯特丹都不突兀；共用的那一款不掛宗教的東西（三座城三種教會）。
import math
from gaps import *                                                     # noqa: F401,F403  es 的全部（tile_floor、cobbles…）＋ english、townpub、carib／kit 的全部
from gaps import school_room, school_work, desk, book_row, bell_at, tablet, BOOKS   # noqa: E402,F401
from houses import PARTS                                               # noqa: E402

LIOZ, LIOZ_D, LIOZ_J = 250, 246, 218   # lioz 石灰石（米白）、帶粉的紋、灰縫 —— 牆角柱（cunhais）、門窗框（cantaria）、簷線（cimalha）
BARRA = 213                            # 牆腳一道黃赭（barra）
AZ_W, AZ_B, AZ_Y = 219, 42, 212        # 花磚：釉白（帶一點藍）、鈷藍、黃 —— RGB332：219 ＝ (218,218,255)、42 ＝ (36,72,170)、212 ＝ (218,182,0)
SOOT = DARK                            # 壁爐裡燻黑的牆


def opening(pid, face, rect, center, z):
    """put_part 那一個部件在牆上的開口（socket）⇒ (沿牆起, 沿牆止, z 起, z 止)：front／back 量 x、left／right 量 y（開口左右對稱 ⇒ 四面同一個公式）。"""
    P = PARTS[pid]
    W = P['dims'][0]
    s0, s1, z0, z1 = P['socket']
    assert s0 + s1 == W, (pid, P['socket'], W)                         # 對稱 ⇒ 轉 180° 開口不動
    a = center - W // 2
    return a + s0, a + s1, z + z0, z + z1


def face_cells(rect, face, t, outer=True):
    """牆的那一面（外面或裡面）那一層：回傳 (固定的那一軸是 x 還是 y, 那一軸的值)。"""
    X0, Y0, X1, Y1 = rect
    if face == 'front':
        return 'y', (Y0 if outer else Y0 + t - 1)
    if face == 'back':
        return 'y', (Y1 - 1 if outer else Y1 - t)
    if face == 'left':
        return 'x', (X0 if outer else X0 + t - 1)
    return 'x', (X1 - 1 if outer else X1 - t)


def recolor_face(M, rect, face, t, a0, a1, z0, z1, color_fn, outer=True):
    """那一面（外／裡那一層）沿牆 [a0, a1) × [z0, z1) 已經有的格換色：color_fn(沿牆, z) ⇒ 色（None ＝ 不動）。"""
    ax, v = face_cells(rect, face, t, outer)
    for a in range(a0, a1):
        for z in range(z0, z1):
            k = (v, a, z) if ax == 'x' else (a, v, z)
            if k in M.cells:
                c = color_fn(a, z)
                if c is not None:
                    M.cells[k] = (M.cells[k][0], c)


def rubble_gable(M, x0, x1, y0, y1, ze, p, z0, salt=0):
    """毛石的山牆（屋脊沿 x、這一端的三角在 y–z 平面；同 townpub.end_gable 的形狀，照 carib.rubble_walls 的砌法上色）。
    屋面蓋過山牆（鄉間毛石屋的出簷）⇒ 已經是屋頂的格不動（要先鋪屋頂再砌山牆）；en、es 那兩款是山牆高出屋面，這一款不是。"""
    for y in range(y0, y1):
        d = min(y + 0.5 - y0, y1 - y - 0.5)
        zt = int(math.floor(ze + p * d))
        for z in range(z0, zt + 1):
            rowi = (z - z0) // 5
            u = y + (3 if rowi % 2 else 0)
            for x in range(x0, x1):
                old = M.cells.get((x, y, z))
                if old and old[0] == 'roof':
                    continue
                if (z - z0) % 5 == 4 or u % 7 == 0:
                    c = MORTAR
                else:
                    c = RUBBLE_D if h01('rg', u // 7, rowi, salt) < 0.15 else RUBBLE
                M.put('body', x, y, z, c, force=True)


def hourglass(M, x, y, z):
    """桌上的沙漏（2 × 2 × 5）：木的上下座、中間兩格沙。"""
    M.box('body', x, y, z, x + 2, y + 2, z + 1, FRAME)
    M.box('body', x, y, z + 1, x + 2, y + 2, z + 2, EARTH_W)
    M.box('body', x, y, z + 2, x + 2, y + 2, z + 4, LIME)
    M.box('body', x, y, z + 4, x + 2, y + 2, z + 5, FRAME)


def log_pile(M, x0, x1, y0, y1, h, salt=0):
    """柴堆：橫放的圓木（斷面朝外，一根 3 格見方、亮的年輪芯、深的樹皮）。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(0, h):
                u, v = (x - x0) % 3, z % 3
                c = BOARD if (u == 1 and v == 1) else (BOARD_D if h01('lg', (x - x0) // 3, z // 3, salt) < 0.4 else FRAME)
                M.put('body', x, y, z, c)


# ─────────────────────────────── 共用那一套的學校（common）12 × 10 m ───────────────────────────────
def common_school():
    """共用的學校：毛石牆一間教室（10 × 5.2 m、牆高 3.2 m）、木瓦兩坡頂、兩端毛石山牆、右端山牆上一根毛石煙囪；
    正面雙扇木板門、窗是開著的木板百葉（前 2、後 2；右牆是壁爐；沒上漆）、門窗上面壓一道木楣；門前石板小路；
    裡面木地板、左端講台（老師的桌椅、桌上一只沙漏）、講台後面的後牆上一塊字母板、前牆左角書架、四排長桌長凳面向講台、右牆一座壁爐（石的爐床、木的爐楣、抹灰的煙罩）；
    後院矮毛石牆、吊鐘的木架、柴堆、長凳、水桶。
    - 照什麼：牆、屋頂、門窗照共用那一套（BUILDING_SPEC §6.14 的鐵匠鋪：毛石三面牆、毛石山牆、木瓦兩坡頂）；教室裡面照 calli 的 school_room（同一套站位）。
    - 設計：壁爐（冬天上課要燒火：君士坦丁堡、阿姆斯特丹都冷）、字母板、沙漏、吊鐘全部是設計；不掛十字架、聖像（共用：東正教、天主教、改革宗三座城都會用到）。"""
    X, Y, Z = 120, 100, 80
    M = Model((X, Y, Z))
    R = (10, 20, 110, 72)
    t, H = 4, 32
    for x in range(50, 70):                                             # 門前石板小路
        for y in range(0, R[1]):
            M.put('body', x, y, 0, RUBBLE_D if h01('fp', x // 4, y // 5, 4101) < 0.35 else RUBBLE)
    rubble_walls(M, R, 0, H, t, salt=4102)
    M.box('body', R[0] + t, R[1] + t, 0, R[2] - t, R[3] - t, 1, FLOOR)  # 木地板
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.7, 'over': (3, 3, 4, 4), 'gable': 'x'}], salt=4103)
    for x0, x1 in ((R[0], R[0] + t), (R[2] - t, R[2])):
        rubble_gable(M, x0, x1, R[1], R[3], H, 0.7, H, salt=4104 + x0)
    # 門窗（借來的部件 put_part 本來就換成沒上漆的木色 SHUT）＋上面的木楣：楣 ＝ 開口上面 2 格、左右各多 2 格，穿過整個牆厚
    put_part(M, 'door-double', '前-門', 'front', R, 60, 0, t)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 60, 0, t)
    wins = [('前-窗1', 'front', 34), ('前-窗2', 'front', 86), ('後-窗1', 'back', 28), ('後-窗2', 'back', 90)]   # 右牆是壁爐 ⇒ 不開窗
    for nm, f, c in wins:
        put_part(M, 'window-board', nm, f, R, c, 10, t)
    for pid, f, c, z in [('door-double', 'front', 60, 0), ('door-plank', 'back', 60, 0)] + [('window-board', f, c, 10) for _, f, c in wins]:
        a0, a1, z0, z1 = opening(pid, f, R, c, z)
        ax, v0 = face_cells(R, f, t)
        for ly in range(t):
            v = v0 + ly if f in ('front', 'left') else v0 - ly
            for a in range(a0 - 2, a1 + 2):
                for zz in range(z1, z1 + 2):
                    k = (v, a, zz) if ax == 'x' else (a, v, zz)
                    if k in M.cells:
                        M.cells[k] = (M.cells[k][0], FRAME)
    # 教室（calli 的 school_room）＋沙漏、字母板
    zp = school_room(M, *R, t, 1)
    hourglass(M, 26, 50, zp + 8)
    tablet(M, 16, 30, R[3] - t - 1, 14, 28)                             # 字母板（講台後面的後牆；ABC 一行一行，形制是設計）
    # 壁爐：右牆中間（右牆裡面 x 106）—— 石的爐床、燻黑的爐膛、木的爐楣、抹灰的煙罩往上收進牆、毛石煙囪穿出右端山牆
    xi = R[2] - t                                                       # 右牆裡面那一層的 x
    M.box('body', xi - 5, 40, 1, xi, 52, 2, RUBBLE_D)                   # 爐床（高出地板一格）
    for y in (40, 50):
        M.box('body', xi - 4, y, 2, xi, y + 2, 14, RUBBLE)              # 爐膛兩側的石墩
    M.recolor(xi, 42, 1, xi + 1, 50, 16, SOOT)                          # 爐膛的後牆燻黑
    M.box('body', xi - 5, 39, 14, xi, 53, 16, FRAME)                    # 爐楣
    for z in range(16, H):                                              # 煙罩：從 4 格深往上收到貼牆
        d = max(1, 4 - (z - 16) // 4)
        M.box('body', xi - d, 41, z, xi, 51, z + 1, MORTAR)
    M.box('body', xi - 2, 44, 2, xi - 1, 48, 3, FRAME)                  # 柴架上兩根柴
    M.box('body', xi - 4, 44, 2, xi - 3, 48, 3, FRAME)
    zc = 60                                                             # 煙囪頂（屋脊 ≈ 32 ＋ 0.7 × 26 ≈ 50）
    for x in range(R[2] - t, R[2]):
        for y in range(42, 50):
            for z in range(H, zc):
                c = MORTAR if (z == zc - 1 or (z - H) % 5 == 4) else (RUBBLE_D if h01('ch', y // 3, z // 5, 4105) < 0.2 else RUBBLE)
                M.put('body', x, y, z, c, force=True)
    M.clear(R[2] - t + 1, 44, zc - 1, R[2] - 1, 48, zc, 'body')         # 煙囪口
    # 後院：矮毛石牆（後牆中間開口）、吊鐘的木架、柴堆、長凳、水桶
    for (x0, y0, x1, y1) in ((10, R[3], 14, 98), (106, R[3], 110, 98)):
        rubble_walls(M, (x0, y0, x1, y1), 0, 14, 4, salt=4110 + x0)
    for (x0, x1) in ((10, 54), (66, 110)):
        rubble_walls(M, (x0, 94, x1, 98), 0, 14, 4, salt=4120 + x0)
    for x in (88, 100):
        M.box('body', x, 84, 0, x + 2, 86, 30, FRAME)
    M.box('body', 86, 84, 30, 104, 86, 32, FRAME)
    bc = bell_at(M, 95, 85, 30)
    log_pile(M, 15, 42, 88, 93, 9, salt=4130)
    bench(M, 18, 44, 80, 83)
    M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [46.5, R[1], 22.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '水桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [72, 82, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    yield_to_parts(M)
    M.anchor('door', 60, R[1] - 1, 1)                                     # 門前石板路上一格
    M.anchor('bell', *bc)
    M.anchor('smoke', R[2] - t + 2, 46, zc)                               # 煙囪口（遊戲從這裡冒煙）
    M.anchor('lot-0', 0, 0, 0)
    school_work(M, R[1], R[3], t, 1, zp)
    return {'key': 'common-school', 'style': 'common',
            'title': '共用的學校（毛石一間教室、木瓦兩坡頂、毛石山牆與煙囪、雙扇木板門與木板百葉窗、木楣；講台、老師的桌椅與沙漏、字母板、書架、四排長桌長凳、壁爐；後院矮毛石牆、吊鐘木架、柴堆）',
            'use': 'school', 'lot': (12, 10), 'M': M, 'layers': {'body': '教室與後院', 'roof': '屋頂'}}


# ─────────────────────────────── 葡萄牙那一套的學校（pt）12 × 10 m ───────────────────────────────
def pt_walls(M, rect, z0, z1, t, plinth=6, cornice=0, corners=True, salt=0):
    """刷白的牆（caiado）＋牆腳一道黃赭（barra）＋四角 4 格寬的 lioz 牆角柱（cunhais）；cornice ＞ 0 ⇒ 頂上那幾層換成往外凸 1 格的 lioz 簷線（cimalha）；
    corners ＝ False（院子的矮牆）⇒ 不做牆角柱、頂上壓一層 lioz。"""
    X0, Y0, X1, Y1 = rect
    stucco_walls(M, rect, z0, z1, t, CAL)
    if not corners:
        M.recolor(X0, Y0, z1 - 1, X1, Y1, z1, LIOZ)
    for f in ('front', 'back', 'left', 'right'):
        n = (X1 - X0) if f in ('front', 'back') else (Y1 - Y0)
        a_lo = X0 if f in ('front', 'back') else Y0

        def col(a, z, a_lo=a_lo, n=n):
            i = a - a_lo
            if corners and (i < 4 or i >= n - 4):                       # 牆角柱：切石，每 6 層一道灰縫、偶爾一塊帶粉的紋
                if (z - z0) % 6 == 5:
                    return LIOZ_J
                return LIOZ_D if h01('lz', a // 4, (z - z0) // 6, salt) < 0.06 else LIOZ
            return BARRA if z < z0 + plinth else None
        recolor_face(M, rect, f, t, a_lo, a_lo + n, z0, z1 - (0 if corners else 1), col)
    if cornice:
        band(M, rect, z1 - cornice, z1, LIOZ, out=1)
        band(M, rect, z1 - cornice, z1 - cornice + 1, LIOZ_J, out=1)    # 簷線底下一道灰縫的影


def pt_portal(M, rect, cx, w=20, h=27):
    """門的 lioz 石框（同 es.portal 的形：兩側壁柱凸出牆外 1 格、上面一道楣、再一層簷線）—— 只做正面。"""
    X0, Y0, X1, Y1 = rect
    y = Y0 - 1
    a, b = cx - w // 2, cx + w // 2
    for x in list(range(a - 3, a)) + list(range(b, b + 3)):
        for z in range(0, h + 1):
            M.put('body', x, y, z, LIOZ_J if z % 6 == 5 else LIOZ, force=True)
    for x in range(a - 4, b + 4):
        for z in range(h + 1, h + 4):
            M.put('body', x, y, z, LIOZ_J if z == h + 3 else LIOZ, force=True)
        if a - 2 <= x < b + 2:
            for z in range(h + 4, h + 6):
                M.put('body', x, y, z, LIOZ, force=True)


def registo(M, rect, cx, z0, w=10, h=9):
    """門上的花磚聖像（registo de azulejos）：藍框白底、中間一個藍十字（形制是設計）—— 貼在正面牆的外面那一層。"""
    a0, a1 = cx - w // 2, cx + w // 2

    def col(a, z):
        if a in (a0, a1 - 1) or z in (z0, z0 + h - 1):
            return AZ_B
        if a in (cx - 1, cx) and z0 + 1 < z < z0 + h - 1:
            return AZ_B
        if z == z0 + h - 4 and cx - 3 <= a < cx + 3:
            return AZ_B
        return AZ_W
    recolor_face(M, rect, 'front', 4, a0, a1, z0, z0 + h, col)


def silhar(M, rect, t, z0=1, z1=14):
    """教室牆裙的花磚（azulejos de padrão，17 世紀那一種藍、黃兩色）：裡面那一層 [z0, z1)：每 6 格一個單元（中心黃、外一圈藍的菱形、四角藍點），
    頂上兩層是收邊（cercadura：一道黃、一道藍）。門窗的開口已經挖掉 ⇒ 只換還在的格。"""
    def col(a, z):
        if z == z1 - 1:
            return AZ_B
        if z == z1 - 2:
            return AZ_Y
        u, v = a % 6, (z - z0) % 6
        d = abs(u - 3) + abs(v - 3)
        if d <= 1:
            return AZ_Y
        if d == 2 or (u == 0 and v == 0):
            return AZ_B
        return AZ_W
    X0, Y0, X1, Y1 = rect
    for f in ('front', 'back', 'left', 'right'):
        a0, a1 = ((X0 + t, X1 - t) if f in ('front', 'back') else (Y0 + t, Y1 - t))
        recolor_face(M, rect, f, t, a0, a1, z0, z1, col, outer=False)


def pt_school():
    """葡萄牙的學校（escola de ler, escrever e contar）：刷白的一間教室（10 × 5.2 m、牆高 4.6 m）、黃赭牆腳、lioz 牆角柱與簷線、紅陶瓦四坡頂；
    lioz 石框的雙扇門、門上一小塊花磚聖像、窗是開著的木板百葉（前 2、後 2、右 1；沒上漆 —— 綠漆的百葉像是更晚的事，沒查到就不上）、lioz 窗框與凸出的窗台；門前石鋪的一小片；
    裡面陶磚地、一圈藍黃花磚的牆裙、左端講台（老師的桌椅）、左牆上木十字、前牆左角書架、四排長桌長凳面向講台；後院刷白矮牆、石井欄與轆轤、長凳、水桶。
    - 照什麼：刷白、lioz 石框、牆裙花磚〔摘：通說〕；屋頂、陶磚地、門框的形照 es.py（同一個半島、同一套陶瓦；es-school 的鐘牆不做 ⇒ 兩款分得出來）。
    - 設計：里斯本 1666 年學校房子的樣子〔沒查到〕⇒ 平面、牆高、門上的花磚聖像（registo 多半是 18 世紀的事 ⇒ 標設計）、窗台、井全部是設計。"""
    X, Y, Z = 120, 100, 100
    M = Model((X, Y, Z))
    R = (10, 20, 110, 72)
    t, H = 4, 46
    for x in range(0, X):                                               # 門前石鋪（lioz 與灰石兩色）
        for y in range(0, R[1]):
            M.put('body', x, y, 0, LIOZ_J if h01('pv', x // 4, y // 4, 4201) < 0.4 else LIOZ)
    pt_walls(M, R, 0, H, t, plinth=6, cornice=3, salt=4202)
    tile_floor(M, R[0] + t, R[1] + t, R[2] - t, R[3] - t)
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.55, 'over': (4, 4, 4, 4)}], salt=4203)
    put_part(M, 'door-double', '前-門', 'front', R, 60, 0, t)
    pt_portal(M, R, 60, 20, 27)
    registo(M, R, 60, 34)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 60, 0, t)
    wins = [('前-窗1', 'front', 34), ('前-窗2', 'front', 86), ('後-窗1', 'back', 28), ('後-窗2', 'back', 90), ('右-窗', 'right', 46)]
    for nm, f, c in wins:
        put_part(M, 'window-board', nm, f, R, c, 14, t)
        a0, a1, z0, z1 = opening('window-board', f, R, c, 14)
        recolor_face(M, R, f, t, a0 - 2, a1 + 2, z0 - 2, z1 + 2, lambda a, z: LIOZ)   # 窗框：開口外一圈 2 格（開口已挖掉 ⇒ 只換牆）
        ax, v = face_cells(R, f, t)
        vo = v - 1 if f in ('front', 'left') else v + 1                 # 窗台：開口底下凸出牆外 1 格
        for a in range(a0 - 2, a1 + 2):
            M.put('body', *(((vo, a, z0 - 1) if ax == 'x' else (a, vo, z0 - 1))), LIOZ)
    zp = school_room(M, *R, t, 1)
    silhar(M, R, t)
    M.box('body', R[0] + t, 45, 18, R[0] + t + 1, 47, 32, FRAME)        # 左牆上的木十字（牆裙上面）
    M.box('body', R[0] + t, 42, 26, R[0] + t + 1, 50, 28, FRAME)
    # 後院：刷白矮牆（後牆中間開口）、石井欄與轆轤、長凳、水桶
    for (x0, y0, x1, y1) in ((10, R[3], 14, 98), (106, R[3], 110, 98)):
        pt_walls(M, (x0, y0, x1, y1), 0, 18, 4, plinth=4, corners=False, salt=4210 + x0)
    for (x0, x1) in ((10, 54), (66, 110)):
        pt_walls(M, (x0, 94, x1, 98), 0, 18, 4, plinth=4, corners=False, salt=4220 + x0)
    cx, cy, r = 92, 84, 6                                               # 井：圓的 lioz 井欄、暗的井口、兩根柱一道橫木吊轆轤
    for x in range(cx - r, cx + r):
        for y in range(cy - r, cy + r):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d < r:
                M.box('body', x, y, 0, x + 1, y + 1, 8, LIOZ if d >= r - 2 else DARK)
    for x in (cx - r, cx + r - 2):
        M.box('body', x, cy - 1, 8, x + 2, cy + 1, 22, FRAME)
    M.box('body', cx - r, cy - 1, 22, cx + r, cy + 1, 24, FRAME)
    M.box('body', cx - 2, cy - 1, 18, cx + 2, cy + 1, 22, FRAME)        # 轆轤
    bench(M, 18, 44, 84, 87)
    M.models += [{'name': '水桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [72, 82, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-門', (46.5, R[1], 26))
    yield_to_parts(M)
    M.anchor('door', 60, R[1] - 1, 1)                                     # 門前石鋪上一格
    M.anchor('lot-0', 0, 0, 0)
    school_work(M, R[1], R[3], t, 1, zp)
    return {'key': 'pt-school', 'style': 'pt',
            'title': '葡萄牙的學校（escola de ler, escrever e contar：刷白一間教室、黃赭牆腳、lioz 牆角柱與簷線、紅陶瓦四坡頂、lioz 石框的雙扇門、門上的花磚聖像、木板百葉與石窗框；藍黃花磚牆裙、講台、老師的桌椅、木十字、書架、四排長桌長凳；後院刷白矮牆、石井欄）',
            'use': 'school', 'lot': (12, 10), 'M': M, 'layers': {'body': '教室與後院', 'roof': '屋頂'}}


ALL = [common_school, pt_school]
