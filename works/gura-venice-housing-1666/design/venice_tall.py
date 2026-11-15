# 威尼斯 1666 的超高密度住宅（第 4 級；TASK-1291，Tim 2026-11-15「可以加更高容量的住宅」「人口可以先只套用威尼斯看看（目前其實太空曠）」）
#   樣子照 Ghetto 那種一再加層的出租公寓（史料見 ../notes.md「第 4 級」那一段）：
#     5～7 層、層高低（一樓 3.1 m、樓上每層 2.5 m：Ghetto 為了加層把天花板壓低）、外牆薄、抹灰、石材極少；
#     臨街一樓是 regalzier（紅灰泥畫白磚縫）的店面與好幾道門（每一道門一座樓梯）；
#     樓上一排排小方窗（0.7 × 1.3 m、間距 1.9 m），各層窗位不完全對齊（不同年代加的、分割過）；
#     最上面兩層（加蓋的）換一種灰泥色；屋頂緩坡筒瓦、幾根喇叭煙囪（很多戶沒有壁爐 ⇒ 比一般住宅少）、木平台（altana）。
#   佔地：Blocksail ZONE.fp[4] 的五種（欄 × 排，一格 4 m）—— 5 × 4、4 × 4、3 × 3、2 × 3、2 × 2；每格住 4 人（ZONE.k[4]）。
from common import *
from venice_dense import put, roof, roof_chimney, roof_altana, back_corte, PL, T, ROOF_P

G0 = (PL, 34)                     # 一樓 [地板頂, 天花)；樓板 34～36（門的半圓通氣窗頂到 3.2 m）
STORY = 25                        # 樓上每層 2.5 m（含 0.2 m 樓板）


def floors(n):
    """n 層 ⇒ [(地板頂, 天花)…]（第 0 層是一樓）；屋簷 ze ＝ 最上面那一層的樓板頂。"""
    out = [G0]
    for i in range(1, n):
        z0 = 36 + STORY * (i - 1)
        out.append((z0, z0 + STORY - 2))
    return out, 36 + STORY * (n - 1)


def row(x0, x1, w, gap):
    """沿牆 [x0, x1) 平均排 w 寬的開口、中心距約 w + gap ⇒ 中心清單。"""
    n = max(1, (x1 - x0 + gap) // (w + gap))
    span = n * w + (n - 1) * gap
    s = x0 + (x1 - x0 - span) // 2
    return [s + i * (w + gap) + w // 2 for i in range(n)]


GROUND = {80: (('door', 18), ('shop', 54)),
          120: (('shop', 22), ('door', 60), ('shop', 98)),
          160: (('shop', 22), ('door', 56), ('shop', 92), ('door', 130)),
          200: (('shop', 22), ('door', 56), ('shop', 92), ('door', 128), ('shop', 166))}


def tall(key, lot, n, plaster, top, salt, chims, alt, live, title):
    W, D = lot[0] * 10, lot[1] * 10
    F, ze = floors(n)
    M = Model((W, D, ze + 62))
    M.plaster = plaster
    X0, X1, Y0 = 2, W - 2, 12
    Y1 = 74 if D <= 80 else D - 24
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    regal_wall(M, R, PL, 36, T)
    stone_band(M, R, 34, 36)
    k_top = n - 2 if n >= 6 else n - 1                                    # 加蓋的那幾層（換色）從第幾層起
    plastered(M, R, 36, F[k_top][0] - 2, T, plaster, salt=salt)
    plastered(M, R, F[k_top][0] - 2, ze, T, top, salt=salt + 1)
    for (z0, z1) in F[1:]:
        slab(M, R, z0 - 2, z0)
    dentils(M, R, ze - 1)
    first = None
    for i, (pid, cx) in enumerate(GROUND[W]):
        put(M, pid, '前-%s%d' % ('門' if pid == 'door' else '店面', i + 1), 'front', R, cx, PL)
        if pid == 'door':
            steps(M, cx, Y0)
            first = first or cx
    M.anchor('door', first, Y0 - 1, PL)
    xs = row(X0 + 6, X1 - 6, 15, 4)
    for f in range(1, n):
        z0 = F[f][0]
        for i, cx in enumerate(xs):
            if len(xs) > 2 and h(cx, f, 0, salt, 'skip') < 0.07:            # 偶爾少一扇（分割過的那一戶封掉了）
                continue
            j = int(round((h(cx, f, 1, salt, 'jit') - 0.5) * 2.4))       # 各層窗位不完全對齊（±1 格）
            put(M, 'windowp', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx + j, z0 + 5)
    put(M, 'door', '後-門', 'back', R, (X0 + X1) // 2, PL)
    xb = row(X0 + 10, X1 - 10, 15, 12)
    for f in range(1, n):
        for i, cx in enumerate(xb):
            put(M, 'windowp', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, F[f][0] + 5)
    tp = roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ze, 'p': ROOF_P, 'over': (2, 2, 4, 4)}], salt=salt)
    for (cx, cy) in chims:
        roof_chimney(M, tp, cx, cy)
    if alt:
        roof_altana(M, tp, *alt)
    if D >= 120:
        back_corte(M, X0, X1, Y1, D, gate=(X1 - 24, 12), salt=salt + 2)
    M.models += [model(LANTERN, '燈籠-門', (first - 11.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': key, 'variant': key.split('-', 1)[1], 'level': 4, 'live': live, 'title': title,
            'use': 'house', 'lot': lot, 'M': M, 'layers': {'body': '牆身', 'gallery': '屋頂平台', 'roof': '屋頂'}}


def house_t_a():
    return tall('house-t-a', (20, 16), 7, ROSSO, CREMA, 101, ((24, 40), (100, 120), (176, 60)), (120, 50, 160, 90), 80,
                '超高密度住宅 T-A（20 × 16：七層的出租公寓 —— 一樓紅灰泥畫白磚縫、三間店面夾兩道門（兩座樓梯），樓上一排排小方窗、各層窗位不完全對齊，'
                '最上面兩層是加蓋的米白灰泥；三根喇叭煙囪、屋頂木平台；後面小院；威尼斯紅灰泥、綠窗板）')


def house_t_b():
    return tall('house-t-b', (16, 16), 7, OCRA, ROSA, 111, ((22, 44), (138, 110)), (60, 60, 100, 100), 64,
                '超高密度住宅 T-B（16 × 16：七層的出租公寓 —— 一樓兩間店面兩道門、樓上小方窗、最上面兩層加蓋的粉灰泥；兩根喇叭煙囪、屋頂木平台；後面小院；土黃灰泥、綠窗板）')


def house_t_c():
    return tall('house-t-c', (12, 12), 6, CREMA, OCRA, 121, ((20, 40), (100, 70)), (44, 40, 76, 72), 36,
                '超高密度住宅 T-C（12 × 12：六層 —— 一樓兩間店面夾門、樓上小方窗、最上面兩層加蓋的土黃灰泥；兩根喇叭煙囪、屋頂木平台；後面小院；米白灰泥、綠窗板）')


def house_t_d():
    return tall('house-t-d', (8, 12), 6, ROSA, CREMA, 131, ((60, 44),), None, 24,
                '超高密度住宅 T-D（8 × 12：六層的窄樓 —— 一樓門＋店面、樓上三列小方窗、最上面兩層加蓋的米白灰泥；一根喇叭煙囪；後面小院；粉灰泥、綠窗板）')


def house_t_e():
    return tall('house-t-e', (8, 8), 5, ROSSO, OCRA, 141, ((60, 40),), None, 16,
                '超高密度住宅 T-E（8 × 8：五層的窄樓 —— 一樓門＋店面、樓上三列小方窗、最上面一層加蓋的土黃灰泥；一根喇叭煙囪；沒有院子；威尼斯紅灰泥、綠窗板）')


ALL = [house_t_a, house_t_b, house_t_c, house_t_d, house_t_e]
# 配色變化（設計決定）：兩種灰泥一起換（加蓋那幾層跟原本的仍然不同色）、窗板換深褐或灰藍
VARIANTS = [('house-t-a2', 'house-t-a', {ROSSO: OCRA, CREMA: ROSA, SCURI: PORTA}, '超高密度住宅 T-A2（T-A 的配色變化：土黃灰泥、加蓋那兩層粉、深褐窗板；替換色，不另存格子）'),
            ('house-t-b2', 'house-t-b', {OCRA: CREMA, ROSA: OCRA, SCURI: SH_GREY}, '超高密度住宅 T-B2（T-B 的配色變化：米白灰泥、加蓋那兩層土黃、灰藍窗板；替換色，不另存格子）'),
            ('house-t-c2', 'house-t-c', {CREMA: ROSSO, OCRA: CREMA, SCURI: PORTA}, '超高密度住宅 T-C2（T-C 的配色變化：威尼斯紅灰泥、加蓋那兩層米白、深褐窗板；替換色，不另存格子）'),
            ('house-t-d2', 'house-t-d', {ROSA: OCRA, CREMA: ROSSO, SCURI: SH_GREY}, '超高密度住宅 T-D2（T-D 的配色變化：土黃灰泥、加蓋那兩層威尼斯紅、灰藍窗板；替換色，不另存格子）'),
            ('house-t-e2', 'house-t-e', {ROSSO: CREMA, OCRA: ROSA, SCURI: PORTA}, '超高密度住宅 T-E2（T-E 的配色變化：米白灰泥、加蓋那一層粉、深褐窗板；替換色，不另存格子）')]
