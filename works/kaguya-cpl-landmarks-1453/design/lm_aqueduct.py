# 瓦倫斯引水渠（Valens Aqueduct，Bozdoğan Kemeri，373–378）1453：跨第三、第四丘之間山谷的雙層拱橋，渠頂海拔約 61–63 m、谷底今日地面約 38.5 m。
#   一種「特殊城牆」（Tim 2026-10-23「引水渠 可以用類似城牆方式去處理嗎(讓引擎支援)」「或直接作為一種特殊城牆」）：
#   這一件 ＝ 斷面（一跨 8.4 m：兩頭各半個墩、中間一個拱、上下兩層）；遊戲照城牆那一套沿路線一節一節接、轉角斜接、
#   高度照渠頂的絕對海拔（規劃的 level）− deck（不跟地面走）、牆基那一層往下延到腳下最低的地面（只有墩是實心的 ⇒ 延下去的是墩、拱底照樣是開的）；比地面低的那一截埋進地裡。
#   1453 年：整條都立著、全是半圓拱（1509 年地震才震垮 Şehzade 附近的上層）；通水斷斷續續（Clavijo 1403 年譯文有爭議）⇒ 渠道空著。
#   ⛔ 不做：Süleyman 重建的尖拱（47–51 或 52–56 號）、Mustafa II 1696/97 的碑文、鄂圖曼的配水設施、1912 年的配水站、今天穿過拱下的 Atatürk Bulvarı。
#   研究整理：scratchpad/cpl/research_batch2.md §9（＋ research_palaces_cisterns.md §7）。
#   座標（模型）：x ＝ 沿牆、y ＝ 橫向（中線 y ＝ D/2）、z 往上；接口 wall-a（x 0）、wall-b（x 末格）在中線、最底那一層（同 kaguya-roman-1453 的城牆模組）。
import byz
from byz import STONE, BANDED

KEY = 'aqueduct-valens'
TITLE = '瓦倫斯引水渠 1453｜斷面（Valens Aqueduct；一跨 8.4 m、上下兩層拱）'
TITLE_SHORT = '瓦倫斯引水渠 1453｜斷面'
MPV = 0.2
W, D, H = 8.4, 6.4, 29.2
DECK = 29.2                                                      # 渠頂（渠道兩側矮牆頂）在模型裡的高（m）：遊戲 y ＝ level − deck
META = {'kind': 'wall', 'part': 'section', 'set': 'aqueduct-valens', 'style': 'roman', 'variant': 'section', 'len': 8.4, 'deck': DECK}
PARTS = (('body', 1, '斷面（下層拱、上層拱、渠道）'),)
PROV = {
    '雙層拱、渠頂海拔 61–63 m、最高約 29 m、坡度 1:1000': '參考資料：Wikipedia；TDV（Eyice）；TBL',
    '下層拱跨約 4 m、墩厚 3.70 m': '參考資料：Wikipedia',
    '寬 5.65 m（雙層段）': '參考資料：TDV（Eyice）；TBL —— Wikipedia 的 7.75–8.24 m 不用',
    '下層方整石灰岩琢石；上層石與小料層交替、後期拜占庭修補的磚拱': '參考資料：Wikipedia；TBL；TDV',
    '1453 年整條立著、全是半圓拱': '推估（1509 年地震才震垮上層一段，TBL；TDV）',
    '一跨 8.4 m（墩 4.4、拱 4.0）、上層拱同軸、上下層高度分配、上層退縮 0.25 m、渠道寬 1.2 m': '設計決定（查不到）',
}


def section(M, x0, x1, arch=True):
    """沿 x 從 x0 到 x1 的一段牆身；arch ⇒ 中間開上下兩層拱（墩在兩頭）。"""
    y0, y1 = 0.38, 6.02                                          # 下層寬 5.65 m（中線 3.2）
    u0, u1 = 0.63, 5.77                                          # 上層退縮
    zl, zc, zu = 16.4, 17.0, 27.6                                # 下層頂、腰線頂、上層頂（渠道底）
    M.add(M.box(x0, x1, y0, y1, 0, zl), STONE, 1)
    M.add(M.box(x0, x1, y0 - 0.2, y1 + 0.2, zl, zc), STONE, 1)                     # 腰線（挑出）
    M.add(M.box(x0, x1, u0, u1, zc, zu), BANDED, 1)
    M.add(M.box(x0, x1, u0 - 0.15, u1 + 0.15, zu - 0.4, zu), STONE, 1)             # 渠道底板的簷
    M.add(M.box(x0, x1, u0, u0 + 0.8, zu, DECK), STONE, 1)                         # 渠道兩側矮牆（渠道寬 u1 − u0 − 1.6 ≈ 3.5 m 的槽裡）
    M.add(M.box(x0, x1, u1 - 0.8, u1, zu, DECK), STONE, 1)
    if arch:
        xc = (x0 + x1) / 2
        M.air(M.arch_open(xc, 3.2, 0.0, 14.6, 4.0, normal='y', depth=8.0))    # 下層拱（從最底那一層就開：牆基往下延的只有墩）
        M.air(M.arch_open(xc, 3.2, zc + 0.2, 25.6, 3.7, normal='y', depth=8.0))   # 上層拱


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.4, 1.2)
    M.band_z0 = 16.8
    section(M, 0.0, W, arch=True)
    G, L = M.finish(shell_m=1.2, seed=373)
    yc = M.NY // 2
    anchors = {'wall-a': [0, yc, 0], 'wall-b': [M.NX - 1, yc, 0], 'deck': M.cell(W / 2, D / 2, DECK - 0.1)}
    return G, L, anchors, {'渠頂（m）': DECK, '下層拱頂（m）': 14.6, '上層拱頂（m）': 25.6}
