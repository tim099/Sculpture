# 威尼斯 1666 的住宅（TASK-1291 那一張單上 Tim 加的：「威尼斯可以建造專門風格的住宅房屋(可以參考文獻資料與現存古蹟)」）—— 共用
#   借 summit-bourg-fr-01m/design 的 kit.py（Model、屋頂、圖紙、部件的擺法）；骨架照 kaguya-cpl-housing-1453（低密度三型＋中、高密度四型、配色變化、樣板街）。
#   部件是這一套自己的（vparts.py）⇒ 建成 <ROOT>-part-<id> 的子作品，房子用關聯擺。
# 座標同 kit.py：x 臨路寬（從街上看左 → 右）、y 進深（y 0 臨路）、z 往上（z 0 整平面）；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料與出處：../notes.md（house_sources 的整理）。這裡只記做法：
#   牆 ＝ 磚砌抹灰（intonaco：威尼斯紅、粉、土黃、米白）；門框、窗框、窗台、樓層的線腳、牆角、井欄 ＝ 伊斯特拉石（pietra d'Istria，白）；
#   窗 ＝ 哥德式的反曲尖拱（arco inflesso）單窗、主樓層中間的三連窗（trifora）照亮 portego；17 世紀的方窗（石框）；綠漆的木窗板（scuri）；
#   紅陶筒瓦（coppi）緩坡頂；喇叭形的煙囪（camino a campana／a imbuto，de' Barbari 1500、Carpaccio 1494 都畫了一整片）；
#   屋頂上的木平台（altana）；伸出巷子的木托架（barbacani）；院子的井欄（vera da pozzo）。
import os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
WORKS = os.path.dirname(os.path.dirname(HERE))
FR_DESIGN = os.path.join(WORKS, 'summit-bourg-fr-01m', 'design')
if FR_DESIGN not in sys.path:
    sys.path.insert(0, FR_DESIGN)

from kit import *                                     # noqa: E402,F401,F403

# ── 這一套的調色盤（RGB332 index）：會換色的角色各只用一個色 ──
ISTRIA, ISTRIA_G = 219, 182                    # 伊斯特拉石（白、偏冷）、風化的灰
ROSSO, ROSA, OCRA, CREMA = 169, 246, 213, 218  # 灰泥：威尼斯紅（cocciopesto 那種磚紅）、粉、土黃、米白（marmorino，17 世紀最普及）—— 一棟只用一色（配色變化換它）
REGAL, REGAL_L = 165, 255                      # regalzier：赤鐵礦的飽和紅灰泥＋白色畫的假磚縫（中世紀最常見的外牆，16 世紀民宅還在用）—— 不換色
MATTONE, MATTONE_D, MALTA = 168, 136, 182      # 露出來的紅磚、深磚、灰縫
SCURI = SH_GREEN                               # 木窗板（綠漆）—— kit 的 M.shutter 換它
PORTA = 100                                    # 門板（深褐的木）
LEGNO = WOOD_G                                 # 風吹雨淋的灰木：屋頂平台、托架
PAVE = 146                                     # 院子、巷口的石板（trachite 的灰）


def h(x, y, z, salt=0, tag='v'):
    return h01(tag, x, y, z, salt)


def shell(M, R, z0, z1, t, fn, layer='body'):
    """外框 R、厚 t 的四面牆，照 fn(x, y, z) 給色。"""
    X0, Y0, X1, Y1 = R
    for z in range(z0, z1):
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                if X0 + t <= x < X1 - t and Y0 + t <= y < Y1 - t:
                    continue
                M.put(layer, x, y, z, fn(x, y, z))


def brick(x, y, z, salt=0):
    """露出來的磚（一順一丁：每層 0.1 m 一皮、每 3 皮一道灰縫；磚色深淺不一）。"""
    if z % 3 == 2:
        return MALTA
    k = (x + y + (z // 3) * 3) // 3
    return MATTONE_D if h01('br', k, z // 3, salt) < 0.25 else MATTONE


def regalzier(x, y, z):
    """紅灰泥上用白線畫的假磚縫：每 3 層一道橫線、每 8 格一道豎線（上下兩皮錯開半塊）。0.1 m 的格畫不出真磚的 7 cm ⇒ 放大成一塊 0.8 × 0.3 m 的「磚」。"""
    if z % 3 == 0:
        return REGAL_L
    u = x + y + (4 if (z // 3) % 2 else 0)
    return REGAL_L if u % 8 == 0 else REGAL


def regal_wall(M, R, z0, z1, t, layer='body'):
    shell(M, R, z0, z1, t, lambda x, y, z: regalzier(x, y, z), layer)


def plastered(M, R, z0, z1, t, color, worn=0.0, salt=0, layer='body'):
    """抹灰的磚牆；worn > 0 ⇒ 灰泥剝落一小塊一小塊露出磚（威尼斯的牆都這樣）。"""
    def fn(x, y, z):
        if worn and h01('worn', (x + y) // 4, z // 3, salt) < worn:
            return brick(x, y, z, salt)
        return color
    shell(M, R, z0, z1, t, fn, layer)


def brickwall(M, R, z0, z1, t, salt=0, layer='body'):
    shell(M, R, z0, z1, t, lambda x, y, z: brick(x, y, z, salt), layer)


def stone_band(M, R, z0, z1=None, out=0, layer='body'):
    """伊斯特拉石的線腳（樓層那一道 marcapiano）：牆外表面那一圈換色；out ⇒ 另外凸出 out 格。"""
    z1 = z0 + 1 if z1 is None else z1
    X0, Y0, X1, Y1 = R
    for z in range(z0, z1):
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                if X0 < x < X1 - 1 and Y0 < y < Y1 - 1:
                    continue
                if (x, y, z) in M.cells:
                    M.cells[(x, y, z)] = (layer, ISTRIA)
        if out:
            for x in range(X0 - out, X1 + out):
                for d in range(1, out + 1):
                    M.put(layer, x, Y0 - d, z, ISTRIA)


def quoin(M, R, z0, z1, faces=('front',), w=3, layer='body'):
    """牆角的伊斯特拉石（只做臨街那兩個角）。"""
    X0, Y0, X1, Y1 = R
    for z in range(z0, z1):
        for x in list(range(X0, X0 + w)) + list(range(X1 - w, X1)):
            if (x, Y0, z) in M.cells:
                M.cells[(x, Y0, z)] = (layer, ISTRIA_G if (z // 4) % 2 else ISTRIA)


def plinth(M, R, h=3):
    X0, Y0, X1, Y1 = R
    M.box('body', X0, Y0, 0, X1, Y1, h, ISTRIA_G)


def slab(M, R, z0, z1, t=3):
    X0, Y0, X1, Y1 = R
    M.box('body', X0 + t, Y0 + t, z0, X1 - t, Y1 - t, z1, WOOD)


def steps(M, cx, y_wall, w=14, n=3):
    for k in range(n):
        M.box('body', cx - w // 2, y_wall - 1 - k, 0, cx + w - w // 2, y_wall - k, n - k, ISTRIA_G)


def dentils(M, R, z, color=MATTONE):
    """簷下一道磚的齒形線腳（dentello）：外面一層每隔一格凸出一格。"""
    X0, Y0, X1, Y1 = R
    for x in range(X0, X1):
        if x % 2 == 0:
            M.put('body', x, Y0 - 1, z, color)
            M.put('body', x, Y1, z, color)
    for y in range(Y0, Y1):
        if y % 2 == 0:
            M.put('body', X0 - 1, y, z, color)
            M.put('body', X1, y, z, color)


def barbacani(M, xs, y_wall, y_out, z_top, layer='body', w=2):
    """伸出巷子的樓板底下的木托架（barbacani）：一根一根的擱柵頭從牆裡伸出、底下一塊斜撐（實心三角）。"""
    for bx in xs:
        for y in range(y_out, y_wall):
            dz = (y - y_out) // 2 + 1
            M.box(layer, bx, y, z_top - dz, bx + w, y + 1, z_top, LEGNO)


def jetty_floor(M, x0, x1, y0, y1, z0, z1):
    for x in range(x0, x1):
        M.box('body', x, y0, z0, x + 1, y1, z1, LEGNO if x % 5 < 2 else WOOD)


def poggiolo(M, x0, x1, y_wall, depth, z, layer='gallery'):
    """主樓層窗前的石陽台（poggiolo）：伊斯特拉石的板、下面兩塊石托、欄杆是一根一根的小石柱（balaustri）、上面一道扶手。"""
    y0 = y_wall - depth
    M.box(layer, x0, y0, z - 2, x1, y_wall, z, ISTRIA)
    for bx in (x0 + 1, x1 - 3):
        for y in range(y0 + 1, y_wall):
            dz = (y - y0)
            M.box(layer, bx, y, z - 2 - dz, bx + 2, y + 1, z - 2, ISTRIA_G)
    for x in range(x0, x1):
        M.put(layer, x, y0, z + 9, ISTRIA)
        M.put(layer, x, y0, z, ISTRIA)
        if (x - x0) % 2 == 0 or x == x1 - 1:
            M.box(layer, x, y0, z + 1, x + 1, y0 + 1, z + 9, ISTRIA)
    for xs in (x0, x1 - 1):
        for y in range(y0, y_wall):
            M.put(layer, xs, y, z + 9, ISTRIA)
            M.put(layer, xs, y, z, ISTRIA)
            if (y - y0) % 2 == 0:
                M.box(layer, xs, y, z + 1, xs + 1, y + 1, z + 9, ISTRIA)


def altana(M, x0, y0, x1, y1, z_floor, piers, layer='gallery'):
    """屋頂上的木平台（altana）：磚墩（從屋面穿上來，底在 piers 給的 z）頂著木地板、四邊木欄杆；晾衣服的橫桿一根。"""
    for (px, py, pz) in piers:
        M.box(layer, px, py, pz, px + 3, py + 3, z_floor - 2, MATTONE)
    for (px, py, pz) in piers:
        M.box(layer, px, py, z_floor - 2, px + 3, py + 3, z_floor, LEGNO)
    M.box(layer, x0, y0, z_floor - 1, x1, y1, z_floor, LEGNO)
    for x in range(x0, x1, 3):
        M.box(layer, x, y0, z_floor - 2, x + 1, y1, z_floor - 1, LEGNO)        # 擱柵
    for x in range(x0, x1):
        for y in (y0, y1 - 1):
            M.put(layer, x, y, z_floor + 9, LEGNO)
            if (x - x0) % 4 == 0 or x == x1 - 1:
                M.box(layer, x, y, z_floor, x + 1, y + 1, z_floor + 9, LEGNO)
    for y in range(y0, y1):
        for x in (x0, x1 - 1):
            M.put(layer, x, y, z_floor + 9, LEGNO)
            if (y - y0) % 4 == 0 or y == y1 - 1:
                M.box(layer, x, y, z_floor, x + 1, y + 1, z_floor + 9, LEGNO)
    xm = (x0 + x1) // 2                                                           # 晾衣桿：兩根立柱、一道橫桿
    for y in (y0 + 2, y1 - 3):
        M.box(layer, xm, y, z_floor, xm + 1, y + 1, z_floor + 16, LEGNO)
    M.box(layer, xm, y0 + 2, z_floor + 16, xm + 1, y1 - 2, z_floor + 17, LEGNO)


def chimney(M, cx, cy, z0, z_top, cone=9, layer='body', color=None):
    """煙囪（fumaiolo）：1.0 m 見方的抹灰煙道從 z0 爬到 z_top − cone（每 9 層一道石帶）、頂上一個陶的倒錐帽（截頭倒圓錐，往上張開到 2.0 m 徑 ≈ 煙道的 2 倍：
    攔火星、防火 —— Carpaccio 1494、de' Barbari 1500 畫的一整片「煙囪森林」）、錐口一圈深陶的冠、中間煙口（暗處）。回傳煙口那一格（smoke 固定點）。"""
    color = color if color is not None else getattr(M, 'plaster', CREMA)
    zc = z_top - cone
    for z in range(z0, zc):
        M.box(layer, cx - 5, cy - 5, z, cx + 5, cy + 5, z + 1, color if (z - z0) % 9 else ISTRIA_G)
    for k in range(cone):
        r = 5 + 4.5 * (k + 1) / cone
        for x in range(int(cx - r - 1), int(cx + r + 1)):
            for y in range(int(cy - r - 1), int(cy + r + 1)):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= r and (d > r - 1.6 or k < 1):
                    M.put(layer, x, y, zc + k, MATTONE if k < cone - 1 else MATTONE_D)
    for x in range(cx - 5, cx + 5):
        for y in range(cy - 5, cy + 5):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= 3.2:
                M.put(layer, x, y, zc, DARK)
    return (cx, cy, zc + 1)


def vera(M, cx, cy, layer='body'):
    """院子的井欄（vera da pozzo）：伊斯特拉石的八角筒、外面一圈凸起的石台（兩級）、中間暗處、一道鍛鐵的吊桶架。"""
    for x in range(cx - 11, cx + 11):
        for y in range(cy - 11, cy + 11):
            dx, dy = abs(x + 0.5 - cx), abs(y + 0.5 - cy)
            oct_d = max(dx, dy, (dx + dy) / 1.414)
            if oct_d <= 10.5:
                M.put(layer, x, y, 0, ISTRIA_G)
            if oct_d <= 8.5:
                M.put(layer, x, y, 1, ISTRIA_G)
            if 4.0 < oct_d <= 6.5:
                M.box(layer, x, y, 2, x + 1, y + 1, 10, ISTRIA)
                if oct_d > 5.6:
                    M.put(layer, x, y, 10, ISTRIA_G)
            elif oct_d <= 4.0:
                M.put(layer, x, y, 1, DARK)
    for x in (cx - 6, cx + 5):                                                    # 鍛鐵的吊桶架：兩根立柱、一道橫桿、中間垂下的鉤
        M.box(layer, x, cy, 10, x + 1, cy + 1, 21, IRON)
    M.box(layer, cx - 6, cy, 21, cx + 6, cy + 1, 22, IRON)
    M.box(layer, cx, cy, 17, cx + 1, cy + 1, 21, IRON)


def corte_wall(M, R, h=26, t=3, salt=0, color=None, layer='body'):
    """院牆：磚、頂上一道筒瓦壓頂。"""
    X0, Y0, X1, Y1 = R
    for x in range(X0, X1):
        for y in range(Y0, Y1):
            for z in range(h):
                M.put(layer, x, y, z, brick(x, y, z, salt) if color is None else color, force=True)
            M.put(layer, x, y, h, TILE_R)


LANTERN = {'source': 'summit-rocher-01m-lantern', 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}


def model(kind, name, at):
    return dict(kind, name=name, at=list(at))
