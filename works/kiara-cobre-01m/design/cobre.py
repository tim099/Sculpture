# 埃爾科夫雷的聖母聖所（Santuario de la Virgen de la Caridad del Cobre，1660 年代；TASK-0989）—— Blocksail 的特殊建築（地標）。
#   Tim 2026-10-26：「聖所（Caridad del Cobre）開一張 asset 單做成地標。」「交給你雕刻了 GO」
# 工具全部借 basecamp-es-01m（es.py、es2.py ⇐ trailhead／apex-one／meadow／ame／summit 那一串）：牆、瓦、鐘牆、門框、部件、燈籠都是同一套 ⇒ 跟聖地牙哥的 es 建築站在一起不突兀。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料與設計的分界（查到的〔摘〕、沒查到的〔設計〕）：
#   〔摘〕聖像十七世紀上半先在礦上一座簡陋的祭壇（altar humilde），後來移進村裡、放在礦工（被奴役的礦工）醫院的小堂；
#        礦山上的舊聖所是首任神父 Onofre de Fonseca 蓋的，一直立到 1906 年塌了；十七世紀中，這尊聖像已經是那一帶最受敬拜的；
#        十七世紀末聖地牙哥的主教座堂才承認這座聖所。現在的大教堂 1927 年在 Cerro de Maboa 頂上 ⇒ ⛔ 不照它做。
#        （EcuRed〈El Cobre〉〈Basílica y Santuario del Cobre〉、cubadecentel〈The Historical Course of the Sanctuary in El Cobre〉、UCSC El Cobre map 9（1780：聖所在礦旁））
#   〔設計〕形制、尺寸全部：照同時期西屬鄉間小堂（ermita）的通法放大一號 ——
#        砌石刷白的一間長堂、正面雙拱鐘牆（兩口鐘）、門前一道木柱撐的瓦頂前廊（朝聖的人在廊下等、避雨；古巴鄉間小堂常見的 portal，年代沒查證）、
#        祭壇屏中間一個龕放聖像（金色的披風、冠；腳下一條小木船 ＝ 傳說裡三個在尼佩灣撿到聖像的人）、兩側牆上掛銅片的還願物（礦工獻銅：設計）、
#        右後一間聖器室、前面石牆圍的前庭（atrio）與石十字。
import math
from es2 import *                                                      # noqa: F401,F403  es 的全部（masonry、portal、espadana、tile_roof、gable_end、put_part、cobbles…）

COPPER = 173                     # 銅（還願的銅片、龕的邊）—— RGB332 ≈ (182, 109, 85)
SKIN = 246                       # 聖像的臉與手
MANTLE = PLAQUE_G                # 金色的披風（248）
ROBE = 42                        # 披風底下的藍袍
WAX, FLAME = 255, 252            # 蠟燭、火


def candle(M, x, y, z, h=4):
    M.box('body', x, y, z, x + 1, y + 1, z + h, WAX)
    M.put('body', x, y, z + h, FLAME)


def virgin(M, xc, y, z0):
    """聖像（設計：照現在的 Caridad 像的輪廓 —— 金披風成三角、冠、抱著聖嬰；腳下一條小船）。xc 中線、y 那一排（龕的後壁前一格）、z0 腳底。"""
    # 小船（三個 Juan 的獨木舟）：底座
    M.box('body', xc - 5, y - 2, z0, xc + 5, y + 1, z0 + 1, FRAME)
    M.box('body', xc - 6, y - 2, z0 + 1, xc + 6, y + 1, z0 + 2, FRAME)
    M.put('body', xc - 6, y - 1, z0 + 2, FRAME); M.put('body', xc + 5, y - 1, z0 + 2, FRAME)
    zb = z0 + 2
    for dz in range(0, 14):                                             # 披風：下寬上窄的三角
        r = max(1, 4 - dz // 4)
        for x in range(xc - r, xc + r):
            M.put('body', x, y, zb + dz, MANTLE if abs(x + 0.5 - xc) > 1.2 or dz < 2 else ROBE)
    M.box('body', xc - 1, y, zb + 14, xc + 1, y + 1, zb + 16, SKIN)    # 臉
    M.box('body', xc - 2, y, zb + 16, xc + 2, y + 1, zb + 17, MANTLE)   # 冠
    M.put('body', xc - 2, y, zb + 17, MANTLE); M.put('body', xc + 1, y, zb + 17, MANTLE); M.put('body', xc, y, zb + 17, MANTLE); M.put('body', xc, y, zb + 18, MANTLE)   # 冠的三個尖（中間那一支要有底）
    M.put('body', xc + 1, y - 1, zb + 9, SKIN)                          # 聖嬰（抱在左臂）
    M.put('body', xc + 1, y - 1, zb + 8, MANTLE)


def sanctuary():
    """聖所（santuario）16 × 24 m：
    前庭（atrio）：石鋪、四周一道 1 m 的砌石矮牆（正中一個 3 m 的口）、左前一支石十字；
    前廊（portal）：木柱撐的單坡瓦頂、8 m 寬、伸出 1.8 m；
    長堂：8 × 13.8 m、牆厚 0.7 m、牆高 5.6 m、兩側各兩道切石扶壁、紅陶瓦兩坡頂；正面山牆高出屋面、雙拱鐘牆兩口鐘；切石門框的雙扇木門、兩側木欄杆窗；
    裡面：陶磚地、高一階的聖壇、描金的祭壇屏中間一個龕（聖像）、蠟燭、兩側牆上的銅還願物、四排長凳；
    聖器室：右後 2.6 × 4 m、單坡瓦頂。"""
    X, Y, Z = 160, 240, 150
    M = Model((X, Y, Z))
    # ── 前庭 ──
    cobbles(M, 6, 6, 154, 64, salt=9891)
    for (x0, y0, x1, y1) in ((4, 2, 66, 6), (94, 2, 156, 6), (4, 2, 8, 64), (152, 2, 156, 64)):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(0, 10):
                    M.put('body', x, y, z, CORAL if z >= 8 else (coral_color(x, y, z, 0, 9892) if z < 3 else CAL))
    M.box('body', 63, 1, 0, 66, 7, 14, CORAL)                           # 口的兩根石墩
    M.box('body', 94, 1, 0, 97, 7, 14, CORAL)
    M.box('body', 18, 18, 1, 30, 30, 3, CORAL)                          # 石十字（座三級）
    M.box('body', 21, 21, 3, 27, 27, 5, CORAL)
    M.box('body', 23, 23, 5, 25, 25, 34, CORAL)
    M.box('body', 19, 23, 25, 29, 25, 27, CORAL)
    # ── 長堂 ──
    R = (40, 64, 120, 202)
    t, H = 7, 56
    masonry(M, R, 0, H, t, salt=9893)
    tile_floor(M, R[0] + t, R[1] + t, R[2] - t, R[3] - t)
    M.box('body', R[0] + t, 168, 1, R[2] - t, R[3] - t, 3, CORAL)       # 聖壇高一階
    for y in (104, 148):                                                # 扶壁
        for (x0, x1) in ((R[0] - 5, R[0]), (R[2], R[2] + 5)):
            for z in range(0, H - 10):
                for x in range(x0, x1):
                    for yy in range(y, y + 7):
                        M.put('body', x, yy, z, coral_color(x, yy, z, 0, 9894))
            M.box('body', x0, y, H - 10, x1, y + 7, H - 8, CORAL_J)
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.55, 'over': (4, 4, 0, 4), 'gable': 'y'}], salt=9895)
    gable_end(M, R[0], R[2], R[1], R[1] + t, H, 0.55, over=3)
    zg = int(math.floor(H + 0.55 * 40)) + 3
    bc, zt = espadana(M, 80, R[1], R[1] + t, zg - 1, w=40, steps=((0, 40), (22, 22), (30, 8)),
                      arches=[(-9, 10, 4, 9), (9, 10, 4, 9)])
    put_part(M, 'door-double', '前-正門', 'front', R, 80, 0, t)
    portal(M, R, 80, 20, 27, salt=9896)
    for cy in (90, 132):
        put_part(M, 'window-baluster', '左-窗%d' % cy, 'left', R, cy, 22, t)
        put_part(M, 'window-baluster', '右-窗%d' % cy, 'right', R, cy, 22, t)
    # ── 前廊：木柱（horcones）撐的單坡瓦頂，靠在正面牆上 ──
    for x in (42, 60, 98, 116):
        M.box('body', x, 46, 0, x + 3, 49, 34, FRAME)
        M.box('body', x - 1, 45, 0, x + 4, 50, 2, CORAL)                 # 柱礎
    M.box('body', 42, 46, 34, 119, 49, 36, FRAME)                      # 簷梁
    shed_roof(M, 40, 44, 120, R[1], 46, 0.55, low='front')
    # ── 聖壇：祭壇、祭壇屏、龕、聖像、蠟燭 ──
    yb = R[3] - t - 1                                                   # 祭壇屏那一排（貼後牆）
    M.box('body', 56, yb - 8, 3, 104, yb - 2, 12, CAL)                 # 祭壇
    M.box('body', 55, yb - 9, 12, 105, yb - 1, 13, CORAL)
    for x in range(48, 112):                                            # 祭壇屏
        for z in range(13, 52):
            M.put('body', x, yb, z, PLAQUE_G if (x - 48) % 8 == 0 or z in (13, 31, 51) else FRAME)
    M.clear(72, yb, 18, 88, yb + 1, 42)                                 # 龕：屏上開一個洞，後牆挖進去 3 格
    M.clear(72, yb + 1, 18, 88, yb + 4, 42)
    for x in range(71, 89):                                             # 龕的銅邊、上緣圓拱（拱外補回屏）
        for z in range(17, 46):
            inside = 72 <= x < 88 and 18 <= z < 42
            arch = z >= 38 and (x + 0.5 - 80) ** 2 + (z + 0.5 - 38) ** 2 > 64
            if inside and arch:
                M.put('body', x, yb, z, FRAME); continue
            if not inside and z < 44:
                M.put('body', x, yb, z, COPPER)
    M.box('body', 72, yb + 3, 18, 88, yb + 4, 38, ROBE)                  # 龕的後壁（藍）
    virgin(M, 80, yb + 2, 19)
    for x in (60, 66, 94, 100):
        candle(M, x, yb - 6, 13, 4 if x in (66, 94) else 3)
    for y in range(76, 160, 14):                                        # 長凳
        for (a, b) in ((50, 74), (86, 110)):
            bench(M, a, b, y, y + 3)
    for (x, ys) in ((R[0] + t, range(150, 164, 4)), (R[2] - t - 1, range(150, 164, 4))):   # 銅還願物：聖壇兩側牆上一排小銅片（設計）
        for y in ys:
            for z in (26, 31):
                M.box('body', x, y, z, x + 1, y + 2, z + 3, COPPER, force=True)
    # ── 聖器室 ──
    S = (124, 150, 150, 196)
    masonry(M, S, 0, 36, 4, plinth=4, salt=9897)
    tile_floor(M, S[0] + 4, S[1] + 4, S[2] - 4, S[3] - 4)
    shed_roof(M, S[0], S[1], S[2], S[3], 46, 0.5, low='right')
    put_part(M, 'door-plank', '聖器室-門', 'front', S, 137, 0, 4)
    M.box('body', S[0] + 6, S[3] - 10, 1, S[2] - 6, S[3] - 5, 10, FRAME)   # 法衣櫃
    lantern(M, '燈籠-前廊左', (61.5, 46, 26))
    lantern(M, '燈籠-前廊右', (99.5, 46, 26))
    yield_to_parts(M)
    M.anchor('door', 80, R[1] - 2, 1)
    M.anchor('bell', *bc)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'sanctuary', 'style': 'es',
            'title': '慈悲聖母聖所（Santuario de la Caridad del Cobre，1660 年代：砌石刷白的長堂、雙拱鐘牆、木柱前廊、龕裡的聖像與小船；銅的還願物、聖器室；石牆圍的前庭與石十字）',
            'use': 'caridad-cobre', 'lot': (16, 24), 'M': M, 'layers': {'body': '牆、前廊與擺設', 'roof': '屋頂'}}


ALL = [sanctuary]
