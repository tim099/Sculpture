# 共用的港口配套第二批（風格 common；TASK-0843，TOWN_BUILD §1.1.7）—— 起重架（sheers）、船棚（boat-shed）。
# 工具照 ame-carib-civic-01m/design（harbour.py 的絞盤、繩盤、原木堆；它再 import summit-carib-01m 的調色盤、Model、屋頂）⇒ 不另抄一份。
# 座標同 kit.py：x 臨路寬（從路上看左 → 右）、y 進深（y 0 臨路）、z 往上（z 0 整平面）；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 生成器把這兩種擺在碼頭臨陸那一側（world/town.js ⑦b）：正面（y 0）朝碼頭面、再過去就是水 ⇒ 吊臂、船的出入口都朝 −y。
# 史料（作品 references/README.md）：Aubin 1702《Dictionnaire de marine》BIGUES；Wikipedia Shear legs、Masting sheer；
#   17 世紀加勒比海的碼頭吊具、船棚都沒查到 ⇒ 尺寸、擺設是設計。
import os, sys, math

WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AME = os.path.join(WORKS, 'ame-carib-civic-01m', 'design')
if AME not in sys.path:
    sys.path.insert(0, AME)
from harbour import *                                                  # noqa: E402,F401  絞盤、繩盤、原木堆、工具棚＋ civic 的全部（調色盤、Model、屋頂、部件）

BLOCK = DARK                     # 滑車的木殼（深）


def rope_line(M, a, b, color=ROPE, layer='body', r=0):
    """兩點之間一條繩（或一根細木）：沿線每 0.25 格取一點；換格時一次只動一軸 ⇒ 六連通（⛔ 斜線只有角碰角 ⇒ 算成一塊一塊浮空，BUILDING_SPEC §6.7 踩過）。
    r ＞ 0 ⇒ 那一點周圍半徑 r 的方塊都填（粗木）。force：繩穿過自己的木件時蓋過去。"""
    n = int(max(abs(b[i] - a[i]) for i in range(3)) * 4) + 1
    prev = None
    for k in range(n + 1):
        t = k / n
        p = [int(math.floor(a[i] + (b[i] - a[i]) * t)) for i in range(3)]
        if prev is not None:
            q = list(prev)
            for i in range(3):                                         # 一軸一軸走過去
                while q[i] != p[i]:
                    q[i] += 1 if p[i] > q[i] else -1
                    M.box(layer, q[0] - r, q[1] - r, q[2] - r, q[0] + r + 1, q[1] + r + 1, q[2] + r + 1, color, force=True)
        else:
            M.box(layer, p[0] - r, p[1] - r, p[2] - r, p[0] + r + 1, p[1] + r + 1, p[2] + r + 1, color, force=True)
        prev = p


def spar(M, a, b, rad=2.2, color=LOG, end=LOG_TIP, layer='body'):
    """一根圓材：a → b、半徑 rad 格（截面是圓）；兩端那一層換淺色的截面（同原木堆的端面）。"""
    L = math.dist(a, b)
    n = int(L * 3) + 1
    R = int(math.ceil(rad))
    for k in range(n + 1):
        t = k / n
        c = [a[i] + (b[i] - a[i]) * t for i in range(3)]
        col = end if k in (0, n) else color
        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                if dx * dx + dy * dy <= rad * rad:
                    M.put(layer, int(math.floor(c[0])) + dx, int(math.floor(c[1])) + dy, int(math.floor(c[2])), col, force=True)


def tackle_block(M, cx, cy, z0, h=6):
    """滑車：深色木殼 4 × 3 × h、兩頭鐵箍。"""
    M.box('body', cx - 2, cy - 1, z0, cx + 2, cy + 2, z0 + h, BLOCK, force=True)
    for z in (z0, z0 + h - 1):
        M.box('body', cx - 2, cy - 1, z, cx + 2, cy + 2, z + 1, IRON, force=True)


def bollard(M, cx, cy, h=10):
    """繫纜木樁：方木 4 × 4、頂上一圈帽。"""
    M.box('body', cx - 2, cy - 2, 0, cx + 2, cy + 2, h, FRAME)
    M.box('body', cx - 3, cy - 3, h - 2, cx + 3, cy + 3, h - 1, FRAME)


# ─────────────────────────────── 起重架 10 × 10 m ───────────────────────────────
def sheers():
    """起重架（sheers；法文 bigues）：兩根粗圓材叉成 A 字、頭（crutch）綁在一起、腳張開，叉口掛滑車；靠前後兩條穩索撐住，吊索經地上的導向滑車繞到絞盤。
    - 照什麼：Wikipedia Shear legs（「two upright spars lashed together at their heads and their feet splayed apart」；穩索 foreguy／aftguy、叉口 crutch 掛 block and tackle、腳用 heel tackle 固定）〔開〕；
      Aubin 1702 BIGUES：撐起「機器」（machine à mâter）的那幾根桅木〔開，OCR〕；TOWN_BUILD §1.1.7 Tim 2026-10-20「起重機照史料」⇒ 加勒比海、地中海用起重架＋絞盤。
      同一套做法已經用在大船廠（ame-carib-civic-01m-shipyard-large 的起桅架）。
    - 設計：碼頭上卸貨用的小一號 —— 圓材長約 12.5 m、腳距 5 m、頭往前（朝碼頭、朝水）傾，叉口離地 11.8 m、在地塊前緣後 1.6 m（⛔ 不伸出框）；
      兩腳踩在毛石墩上；前穩索拉到前緣的繫纜樁、後穩索拉到地塊後面埋地的木樁；吊索經導向滑車到後面的絞盤；吊鉤上掛一張貨網（兩個酒桶）。
      吊多重、腳距多寬都是設計（17 世紀加勒比海的碼頭吊具沒查到）。"""
    X, Y, Z = 100, 100, 130
    M = Model((X, Y, Z))
    hx, hy, hz = 50, 16, 118                                           # 叉口（頭）
    feet = [(25, 70), (75, 70)]
    for (fx, fy) in feet:                                              # 腳下的毛石墩（1.2 × 1.2 m、高 0.4 m）＋淺淺一個卡腳的槽（木）
        rubble_walls(M, (fx - 6, fy - 6, fx + 6, fy + 6), 0, 4, 6, salt=fx)
        M.box('body', fx - 6, fy - 6, 4, fx + 6, fy + 6, 5, FRAME)
    for (fx, fy) in feet:
        spar(M, (fx + 0.5, fy + 0.5, 5), (hx + 0.5 + (fx - hx) * 0.06, hy + 0.5, hz + 6), 2.2)
    for z in range(hz - 2, hz + 7):                                    # 頭上綁的繩（一圈一圈纏，6 格高）
        for x in range(hx - 5, hx + 6):
            for y in range(hy - 3, hy + 4):
                if abs(x + 0.5 - hx - 0.5) >= 3 or abs(y - hy) >= 3:
                    if math.hypot(x + 0.5 - hx - 0.5, (y - hy) * 1.5) <= 5.5:
                        M.put('body', x, y, z, ROPE, force=True)
    # 穩索：前 ⇒ 前緣的繫纜樁；後 ⇒ 後面埋地的木樁
    bollard(M, 50, 4, 10)
    rope_line(M, (hx + 0.5, hy - 2.5, hz + 3.5), (50.5, 4.5, 9.5))
    M.box('body', 48, 94, 0, 52, 98, 16, FRAME)
    rope_line(M, (hx + 0.5, hy + 3.5, hz + 3.5), (50.5, 95.5, 15.5))
    # 吊具：叉口下掛滑車 ⇒ 吊索往下到吊鉤；拉的那一頭往後經導向滑車到絞盤
    rope_line(M, (hx + 0.5, hy + 0.5, hz - 2), (hx + 0.5, hy + 0.5, hz - 8))
    tackle_block(M, hx, hy, hz - 14, 6)
    rope_line(M, (hx - 0.5, hy + 0.5, hz - 14), (hx - 0.5, hy + 0.5, 34))
    rope_line(M, (hx + 1.5, hy + 0.5, hz - 14), (hx + 1.5, hy + 0.5, 34))
    tackle_block(M, hx, hy, 28, 6)                                     # 下滑車＋鉤
    M.box('body', hx, hy, 24, hx + 1, hy + 1, 28, IRON, force=True)
    for (dx, dy) in ((-5, -4), (5, -4), (-5, 5), (5, 5)):             # 貨網的四條吊索 ⇒ 底下一張網兜著兩個酒桶（網是繩色的格）
        rope_line(M, (hx + 0.5, hy + 0.5, 24), (hx + 0.5 + dx, hy + 0.5 + dy, 14))
    for x in range(hx - 6, hx + 7):
        for y in range(hy - 5, hy + 7):
            M.put('body', x, y, 6, ROPE, force=True)                   # 網底
            if x in (hx - 6, hx + 6) or y in (hy - 5, hy + 6):        # 網邊（往上兜到吊索）
                M.box('body', x, y, 6, x + 1, y + 1, 15, ROPE, force=True)
    for bx in (hx - 3, hx + 4):                                        # 網裡的兩個桶（橫放的圓）
        for y in range(hy - 3, hy + 5):
            for x in range(bx - 3, bx + 3):
                for z in range(7, 14):
                    if math.hypot(x + 0.5 - bx, z + 0.5 - 10.5) <= 3.2:
                        M.put('body', x, y, z, IRON if y in (hy - 3, hy + 4) else FRAME if (y - hy) % 3 == 0 else FLOOR)
    rope_line(M, (hx + 2.5, hy + 0.5, hz - 9), (51.5, 62.5, 3.5))      # 拉的那一頭 ⇒ 地上的導向滑車
    M.box('body', 49, 60, 0, 54, 66, 3, FRAME)                         # 導向滑車的底座（短方木）
    tackle_block(M, 50, 62, 3, 4)
    capstan(M, 50, 82)
    rope_line(M, (51.5, 64.5, 5.5), (51.5, 78.5, 5.5))
    rope_coil(M, 82, 86)
    # 碼頭邊的貨：箱子、酒桶（外部模型）
    M.models += [{'name': '貨箱-1', 'source': 'summit-rocher-01m-crate', 'at': [16, 22, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-2', 'source': 'summit-rocher-01m-crate', 'at': [16, 36, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [84, 22, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-2', 'source': 'summit-rocher-01m-barrel', 'at': [84, 36, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 # 夜裡的燈：掛在後穩索樁的正面（作品有燈籠 ⇒ townmodels 不再自動補門口燈；沒牆的起重架補了會懸在半空）
                 {'name': '燈籠-穩索樁', 'source': 'summit-rocher-01m-lantern', 'at': [50.5, 94, 13], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('door', 30, 0, 0)
    M.anchor('lot-0', 0, 0, 0)
    M.anchor('hoist', hx, hy + 1, hz - 15)                             # 上滑車底下那一格（之後掛滑車、吊東西用；BUILDING_SPEC §5 hoist）
    return {'key': 'sheers', 'title': '起重架（共用：兩根圓材叉成 A 字、頭綁在一起、前後穩索、滑車與吊鉤、導向滑車接絞盤；碼頭邊卸貨）',
            'use': 'sheers', 'lot': (10, 10), 'M': M, 'style': 'common', 'layers': {'body': '起重架與絞盤'}}


# ─────────────────────────────── 船棚 8 × 14 m ───────────────────────────────
def boat_shed():
    """船棚（boat-shed）：停小艇、不下水時遮日遮雨的開敞木棚。
    - 照什麼：English Harbour 的 Boat House（1790 年代、石柱上兩層、船從底下的水道進出）〔摘〕是本島後來的做法、年代對不上 ⇒ 不照它；
      17 世紀加勒比海的船棚沒查到 ⇒ 照這一套的工具棚（ame harbour.py tool_shed：木柱、木瓦）做成**兩坡木瓦頂、兩側與正面開敞、背面一道木板牆**的長棚。
    - 設計：正面（y 0，朝碼頭與水）是船的出入口；棚下兩條圓木滑道從前緣一路鋪到底；一艘 9 m 的小艇（餘燼號 cutter，外部模型）擱在滑道的墊木上；
      背面一座絞盤拉船上岸；側邊一排槳架、一盤繩、幾根備用的圓材。大小、柱距是設計。"""
    X, Y, Z = 80, 140, 70
    M = Model((X, Y, Z))
    R = (4, 6, 76, 136)                                                # 柱子圍的範圍（屋頂再往外挑 4 格）
    board_walls(M, (R[0], R[3] - 2, R[2], R[3]), 0, 36, 2, posts=False)   # 背面一道木板牆
    posts = [(x, y) for y in range(R[1], R[3] - 2, 26) for x in (R[0], R[2] - 2)] + [(R[0], R[3] - 2), (R[2] - 2, R[3] - 2)]
    for (px, py) in posts:
        M.box('body', px, py, 0, px + 2, py + 2, 36, FRAME)
    for y0 in sorted({py for _, py in posts}):                         # 柱頭的橫梁（每一對柱一根，沿 x）
        M.box('body', R[0], y0, 36, R[2], y0 + 2, 38, FRAME)
    for x0 in (R[0], R[2] - 2):                                        # 兩側的縱梁（沿 y）
        M.box('body', x0, R[1], 36, x0 + 2, R[3], 38, FRAME)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 38, 'p': 0.62, 'over': (4, 4, 6, 4), 'gable': 'y'}], salt=843)
    gable_wall(M, R[0], R[2], R[3] - 2, R[3], 38, 0.62)                # 背面的山牆（木板，沿 x 收成三角）
    # 滑道：兩條圓木（截面 4 × 3）從前緣鋪到背牆前；每 2 m 一根橫墊木
    for x0 in (28, 48):
        M.box('body', x0, 0, 0, x0 + 4, R[3] - 4, 3, LOG)
    for y in range(4, R[3] - 6, 20):
        M.box('body', 24, y, 0, 56, y + 3, 2, FRAME)
    for y in (30, 60, 90):                                             # 小艇的墊木：橫架在兩條滑道上（龍骨坐在中間）
        M.box('body', 28, y, 3, 52, y + 3, 6, FRAME)
    M.models += [{'name': '小艇', 'source': 'basecamp-ember-01m-boat', 'at': [40, 62, 6], 'pivot': [90, 26, 0], 'rotate': [0, 0, 90], 'meta': {}},   # 9 m 長 ⇒ y 17..107，碰不到後面絞盤的推桿（y 111 起）
                 {'name': '酒桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [12, 118, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    capstan(M, 40, 124)                                                # 拉船上岸的絞盤
    # 槳架（右邊）：兩根立柱＋三道橫木，靠著幾支槳（細木，斜靠）
    for py in (40, 90):
        M.box('body', 66, py, 0, 68, py + 2, 26, FRAME)
    for z in (8, 16, 24):
        M.box('body', 66, 40, z, 68, 92, z + 1, FRAME)
    for k, py in enumerate(range(44, 90, 6)):
        rope_line(M, (63.5, py + 0.5, 0.5), (66.5, py + 0.5, 25.5), FLOOR)
    rope_coil(M, 14, 30)
    log_pile(M, 8, 22, 60, 2, 3)
    M.anchor('door', 40, 0, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'boat-shed', 'title': '船棚（共用：兩坡木瓦頂的開敞長棚、背面木板牆、兩條圓木滑道、一艘 9 m 小艇、拉船的絞盤、槳架）',
            'use': 'boat-shed', 'lot': (8, 14), 'M': M, 'style': 'common', 'layers': {'body': '棚架、滑道與擺設', 'roof': '屋頂'}}


ALL = [sheers, boat_shed]
