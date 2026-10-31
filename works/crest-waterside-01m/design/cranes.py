# 起重機的繩換成真的繩（Blocksail TASK-0899；Tim 2026-10-31「建築的繩索GO 同時可以修改起重機 用繩索替換掉格子」）。
# 起重架（sheers）是 trailhead 的作品 trailhead-harbour-01m-sheers（design/quay.py sheers，TASK-0843）—— 別人的作品只有作者能雕 ⇒ 照它的產生程式另做一件，
#   只把繩（前後穩索、吊滑車索、兩道吊索、貨網的四條吊索、拉索）從格子換成 rope（berth.py；遊戲照 Blockside 63_towns.js townRopes 畫），其他一格不改；
#   城鎮模型 common-sheers 改指這一件（Blocksail tools/townmodels.py MODELS）。史料、尺寸、擺法照原作（作品 references/README.md）。
from berth import *                                                    # noqa: F401,F403  quay（spar、tackle_block、bollard）、harbour（capstan、rope_coil）、civic／kit ＋ rope


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
    rope(M, '前穩索', (hx + 0.5, hy - 2.5, hz + 3.5), (50.5, 4.5, 9.5), thick=0.7)   # 繩：真的繩（rope；2026-10-31 crest-001 換掉格子，TASK-0899）
    M.box('body', 48, 94, 0, 52, 98, 16, FRAME)
    rope(M, '後穩索', (hx + 0.5, hy + 3.5, hz + 3.5), (50.5, 95.5, 15.5), thick=0.7)
    # 吊具：叉口下掛滑車 ⇒ 吊索往下到吊鉤；拉的那一頭往後經導向滑車到絞盤
    rope(M, '吊滑車索', (hx + 0.5, hy + 0.5, hz - 2), (hx + 0.5, hy + 0.5, hz - 8), thick=0.7)
    tackle_block(M, hx, hy, hz - 14, 6)
    rope(M, '吊索-1', (hx - 0.5, hy + 0.5, hz - 14), (hx - 0.5, hy + 0.5, 34), thick=0.6)
    rope(M, '吊索-2', (hx + 1.5, hy + 0.5, hz - 14), (hx + 1.5, hy + 0.5, 34), thick=0.6)
    tackle_block(M, hx, hy, 28, 6)                                     # 下滑車＋鉤
    M.box('body', hx, hy, 24, hx + 1, hy + 1, 28, IRON, force=True)
    for k, (dx, dy) in enumerate(((-5, -4), (5, -4), (-5, 5), (5, 5))):   # 貨網的四條吊索（繩）⇒ 底下一張網兜著兩個酒桶（網是繩色的格）
        rope(M, '貨網吊索-%d' % (k + 1), (hx + 0.5, hy + 0.5, 24), (hx + 0.5 + dx, hy + 0.5 + dy, 14), thick=0.4)
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
    rope(M, '拉索', (hx + 2.5, hy + 0.5, hz - 9), (51.5, 62.5, 3.5), thick=0.6)   # 拉的那一頭 ⇒ 地上的導向滑車
    M.box('body', 49, 60, 0, 54, 66, 3, FRAME)                         # 導向滑車的底座（短方木）
    tackle_block(M, 50, 62, 3, 4)
    capstan(M, 50, 82)
    rope(M, '拉索-絞盤', (51.5, 64.5, 5.5), (51.5, 78.5, 5.5), thick=0.6)
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
    for nm, at, to in (('a1', (52, 28, 0), (50, 20, 9)), ('b1', (38, 20, 0), (46, 16, 9)), ('c1', (62, 14, 0), (54, 16, 9)), ('b2', (41, 5, 0), (48, 8, 9))):   # 工作點：照原作登記的（trailhead-harbour-01m-sheers 的 work-*）
        M.anchor('work-' + nm, *at)
        M.anchor('work-' + nm + '-to', *to)
    return {'key': 'sheers', 'title': '起重架（共用：照 trailhead-harbour-01m-sheers，穩索、吊索、拉索換成真的繩；兩根圓材叉成 A 字、滑車與吊鉤、導向滑車接絞盤；碼頭邊卸貨）',
            'use': 'sheers', 'lot': (10, 10), 'M': M, 'style': 'common', 'layers': {'body': '起重架與絞盤'}}


ALL = [sheers]
