# 義大利 1666 的通用城市住宅（gura-italy-housing-1666；TASK-1291，Tim 2026-11-15「參考菜單概念（可以混合多地區菜單） 讓住宅也可以混合多風格
#   例如 威尼斯可以混義大利風格住宅？（或其他通用風格）」⇒ 選 A：新雕一套通用義大利住宅）—— 共用
#   借 summit-bourg-fr-01m/design 的 kit.py（Model、屋頂、圖紙、部件的擺法）；骨架照 gura-venice-housing-1666（低三型＋淺版小版、中高四型、超高五種、配色變化、樣板街）。
#   兩種地方做法混在同一套（Blocksail 的風格 italy）：
#     托斯卡納（佛羅倫斯、里窩那）：抹灰（黃赭、紅赭、石灰白）、pietra serena（灰藍）的門窗框與樓層線、筒瓦＋平瓦、很深的木屋簷（gronda，看得到木椽與木板底）、
#       頂樓的開敞涼廊（altana／loggia）、宅邸一樓的跪窗（finestra inginocchiata）加鐵柵與 pietra forte 的粗面石（bugnato）。
#     利古里亞（熱那亞）：窄而高、抹灰（粉、淡綠、黃赭）上畫白色的窗框與樓層線（facciata dipinta，16 世紀中～17 世紀全盛）、深色基座帶、
#       黑色 ardesia（石板）的門框、ardesia 石板屋頂（淺灰）、一樓連成一排的拱頂店鋪（volta）。
#   ⛔ 1666 年沒有的：百葉（persiane，18 世紀末起）⇒ 實心木窗板（scuri）；機製瓦（1841）⇒ 筒瓦。史料與出處：../notes.md。
# 座標同 kit.py：x 臨路寬（從街上看左 → 右）、y 進深（y 0 臨路）、z 往上（z 0 整平面）；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
import os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
WORKS = os.path.dirname(os.path.dirname(HERE))
FR_DESIGN = os.path.join(WORKS, 'summit-bourg-fr-01m', 'design')
if FR_DESIGN not in sys.path:
    sys.path.insert(0, FR_DESIGN)

from kit import *                                     # noqa: E402,F401,F403

# ── 調色盤（RGB332 index）：會換色的角色各只用一個色 ──
GIALLO, ROSSO_O, CALCE, ROSA, VERDINO, ARANCIO = 213, 205, 218, 246, 186, 209   # 灰泥：黃赭、紅赭、石灰白、粉、淡綠（利古里亞）、橙赭 —— 一棟一色（配色變化換它）
BIANCO = 255                                          # 利古里亞畫上去的白框、白線
ZOCCOLO = 173                                         # 利古里亞的深色基座帶（雙色立面的下段）
SERENA, SERENA_D = 146, 110                           # pietra serena（灰藍）、陰影那一面
FORTE, FORTE_D = 177, 141                             # pietra forte（黃褐）、粗面石的縫
ARDESIA = 73                                          # 黑色石板（門框、窗台、屋脊）
ARD_A, ARD_B = 110, 146                               # 石板屋頂（風化成淺灰的 abbadini）
SCURO = SH_GREEN                                      # 實心木窗板（kit 的 49：M.shutter 換它）
PORTA = 100                                           # 門板（深褐）
TRAVE = 68                                            # 屋簷的木椽（深木）
TAVOLA = 104                                          # 屋簷底的木板
PAVE = 146                                            # 院子的石板


def h(x, y, z, salt=0, tag='i'):
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


def wall(M, R, z0, z1, t, color, layer='body'):
    shell(M, R, z0, z1, t, lambda x, y, z: color, layer)


def bugnato(M, R, z0, z1, t):
    """pietra forte 的粗面石（一樓）：每塊 1.2 × 0.6 m、上下兩皮錯開半塊、縫深一色。"""
    def fn(x, y, z):
        if (z - z0) % 6 == 5:
            return FORTE_D
        u = x + y + (6 if ((z - z0) // 6) % 2 else 0)
        return FORTE_D if u % 12 == 0 else FORTE
    shell(M, R, z0, z1, t, fn)


def surface(M, R, z0, z1, color, only, faces=('front', 'back')):
    """牆外表面那一層換色（畫上去的：白線、白框、深色基座帶）—— 只換 only 裡的色（門窗挖掉的洞、部件不碰）。"""
    X0, Y0, X1, Y1 = R
    for z in range(z0, z1):
        for x in range(X0, X1):
            for y in ([Y0] if 'front' in faces else []) + ([Y1 - 1] if 'back' in faces else []):
                c = M.cells.get((x, y, z))
                if c and c[1] in only:
                    M.cells[(x, y, z)] = (c[0], color)


def band(M, R, z0, z1, color, out=1, faces=('front', 'back')):
    """石的樓層線（marcapiano）：牆外表面換色＋往外凸 out 格（只做臨街、背面）。"""
    X0, Y0, X1, Y1 = R
    for z in range(z0, z1):
        for x in range(X0, X1):
            if 'front' in faces:
                for d in range(0, out + 1):
                    M.put('body', x, Y0 - d, z, color, force=d == 0)
            if 'back' in faces:
                for d in range(0, out + 1):
                    M.put('body', x, Y1 - 1 + d, z, color, force=d == 0)


def plinth(M, R, h=3, color=SERENA):
    X0, Y0, X1, Y1 = R
    M.box('body', X0, Y0, 0, X1, Y1, h, color)


def slab(M, R, z0, z1, t=3):
    X0, Y0, X1, Y1 = R
    M.box('body', X0 + t, Y0 + t, z0, X1 - t, Y1 - t, z1, WOOD)


def steps(M, cx, y_wall, w=16, n=2, color=SERENA):
    for k in range(n):
        M.box('body', cx - w // 2, y_wall - 1 - k, 0, cx + w - w // 2, y_wall - k, n - k + 1, color)


def slate_color(x, y, facet, ridge, edge):
    """石板屋頂：風化的淺灰兩色一排一排、屋脊與簷口一圈黑石板。"""
    if ridge or edge:
        return ARDESIA
    a = x if facet in ('front', 'back') else y
    b = y if facet in ('front', 'back') else x
    return ARD_A if ((b // 2) + (a // 4) * 0) % 2 == 0 and h01('sl', a // 3, b // 2) < 0.8 else ARD_B


def gronda(M, top, X0, X1, y_wall, y_out, step=4, side='front'):
    """托斯卡納的深木屋簷（gronda）：屋面底下一層木板（tavolato）＋每 step 格一根伸出牆的木椽（correnti，簡單、不雕形）。"""
    ys = range(y_out, y_wall) if side == 'front' else range(y_wall, y_out)
    for x in range(X0, X1):
        for y in ys:
            zt = top.get((x, y))
            if zt is None:
                continue
            M.put('body', x, y, zt - 2, TAVOLA)
            if (x - X0) % step == 1:
                M.put('body', x, y, zt - 3, TRAVE)
                M.put('body', x, y, zt - 4, TRAVE)


def chimney(M, top, cx, cy, h=24, color=None, cap='coppi'):
    """煙囪：0.8 m 見方的抹灰煙道從屋面冒出、頂上四根小墩撐一頂小雙坡帽（托斯卡納：筒瓦；利古里亞：石板），帽下四面煙口（暗處）。回傳煙口那一格。"""
    color = color if color is not None else getattr(M, 'plaster', CALCE)
    z0 = top[(cx, cy)] - 2
    zt = z0 + h
    M.box('body', cx - 4, cy - 4, z0, cx + 4, cy + 4, zt, color)
    M.box('body', cx - 3, cy - 3, zt - 1, cx + 3, cy + 3, zt, DARK)
    for (px, py) in ((cx - 4, cy - 4), (cx + 2, cy - 4), (cx - 4, cy + 2), (cx + 2, cy + 2)):
        M.box('body', px, py, zt, px + 2, py + 2, zt + 4, color)
    cc = TILE_R if cap == 'coppi' else ARDESIA
    for k in range(3):
        M.box('body', cx - 5 + k, cy - 5, zt + 4 + k, cx + 5 - k, cy + 5, zt + 5 + k, cc)
    if 'smoke' not in M.anchors:
        M.anchor('smoke', cx, cy, zt + 1)
    return (cx, cy, zt + 1)


def loggia(M, x0, x1, y0, y1, z0, z1, col=SERENA, posts=None, rail=WOOD_D):
    """頂樓的開敞涼廊（altana／loggia）：四角＋每隔一段一根石柱（或木柱）、上面一道過梁、木欄杆半人高；裡面是暗的（看進去是屋裡）。"""
    posts = posts or list(range(x0, x1 - 1, 20)) + [x1 - 3]
    for px in posts:
        for py in (y0, y1 - 3):
            M.box('body', px, py, z0, px + 3, py + 3, z1, col)
    M.box('body', x0, y0, z1 - 2, x1, y1, z1, col)
    for x in range(x0, x1):
        for y in (y0, y1 - 1):
            M.put('body', x, y, z0 + 9, rail)
            if (x - x0) % 3 == 0:
                M.box('body', x, y, z0, x + 1, y + 1, z0 + 9, rail)
    M.box('body', x0 + 3, y0 + 6, z0, x1 - 3, y1 - 3, z0 + 1, WOOD)


def pozzo(M, cx, cy, layer='body'):
    """院子的井：圓的石井欄（serena）、兩根鐵柱一道橫桿吊桶。"""
    for x in range(cx - 7, cx + 7):
        for y in range(cy - 7, cy + 7):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 6.5:
                M.put(layer, x, y, 0, SERENA_D)
            if 3.6 < d <= 5.5:
                M.box(layer, x, y, 1, x + 1, y + 1, 9, SERENA)
            elif d <= 3.6:
                M.put(layer, x, y, 1, DARK)
    for x in (cx - 5, cx + 4):
        M.box(layer, x, cy, 9, x + 1, cy + 1, 20, IRON)
    M.box(layer, cx - 5, cy, 20, cx + 5, cy + 1, 21, IRON)


def corte_wall(M, R, h=26, color=CALCE, layer='body'):
    """院牆：抹灰、頂上一道筒瓦壓頂。"""
    X0, Y0, X1, Y1 = R
    for x in range(X0, X1):
        for y in range(Y0, Y1):
            for z in range(h):
                M.put(layer, x, y, z, color, force=True)
            M.put(layer, x, y, h, TILE_R)


def back_corte(M, X0, X1, y0, y1, gate=None, color=CALCE, t=3):
    corte_wall(M, (X0, y0, X0 + t, y1), color=color)
    corte_wall(M, (X1 - t, y0, X1, y1), color=color)
    corte_wall(M, (X0, y1 - t, X1, y1), color=color)
    if gate:
        cx, w = gate
        M.clear(cx - w // 2, y1 - t, 0, cx + w - w // 2, y1, 27)
        M.box('body', cx - w // 2, y1 - 2, 0, cx + w - w // 2, y1 - 1, 21, PORTA)


def laundry(M, x0, x1, y, h=26):
    for x in (x0, x1 - 1):
        M.box('body', x, y, 0, x + 1, y + 1, h, WOOD_G)
    for x in range(x0, x1):
        M.put('body', x, y, h - 1, WOOD_D)
    for (a, b, c) in ((x0 + 3, x0 + 9, 255), (x0 + 12, x0 + 17, 42), (x0 + 20, x0 + 27, 218)):
        if b < x1 - 1:
            M.box('body', a, y, h - 9, b, y + 1, h - 1, c)


LANTERN = {'source': 'summit-rocher-01m-lantern', 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}


def model(kind, name, at):
    return dict(kind, name=name, at=list(at))
