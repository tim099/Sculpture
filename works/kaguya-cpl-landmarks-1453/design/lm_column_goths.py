# 哥德柱（Column of the Goths，Gotlar Sütunu，3～4 世紀）1453：三級台階、高基座（東面拉丁銘文 FORTUNAE REDUCI OB DEVICTOS GOTHOS）、
#   整座 Proconnesian 白大理石（帶灰紋）、科林斯柱頭、柱頂板上一隻鷹；頂上的 Tyche／Byzas 像 14 世紀已經不在 ⇒ 只有柱頭和鷹。
#   1453 年這一帶是衛城與 Mangana 之間稀疏的修道院、果園（Topkapı 是之後才圍進來的）。
#   ⛔ 不做：Gülhane 公園的步道、長椅、鋪面。
#   研究整理：scratchpad/cpl/research_batch2.md §2；位置：OSM node 4695996389（只有點）。
import byz, columns
from byz import MARBLE

KEY = 'column-goths'
TITLE = '哥德柱 1453（Column of the Goths，Gotlar Sütunu；柱頂板上一隻鷹）'
TITLE_SHORT = '哥德柱 1453'
MPV = 0.2
W, D, H = 7.0, 7.0, 20.0
META = {'kind': 'building', 'use': 'column-goths', 'style': 'roman', 'lot': '7,7', 'base': 0, 'variant': 'a', 'lamps': 4}
PARTS = (('body', 1, '柱（台階、基座、柱礎、柱身、柱頭）'), ('top', 2, '柱頂板上的鷹'))
PROV = {
    '整體 18.5 m、柱身 15 m': '參考資料：Wikipedia 引 Mango 2000 p.177；TBL',
    '整座 Proconnesian 大理石': '參考資料：Wikipedia；TBL',
    '三級台階、高基座、東面銘文、柱頂板上一隻鷹': '參考資料：TBL',
    '頂上沒有雕像': '設計決定（Nikephoros Gregoras 14 世紀說「曾經」立著 Byzas 像 ⇒ 推估 1453 年已經不在）',
    '柱身下徑 1.4、上徑 1.25 m；基座 2.6 m 見方、1.3 m 高；台階每級 0.25 m': '設計決定（查不到；照高徑比約 11:1 推）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    cx = cy = 3.5
    C = {'steps': [[6.4, 0.25], [5.6, 0.25], [4.8, 0.25]], 'pedestal': {'w': 2.6, 'h': 1.3, 'mat': MARBLE, 'cornice': 0.15}, 'base': {'d': 1.8, 'h': 0.4},
         'shaft': {'d0': 1.4, 'd1': 1.25, 'h': 15.0, 'mat': MARBLE}, 'capital': {'w': 1.9, 'h': 1.05, 'mat': MARBLE}}
    ztop = columns.column(M, cx, cy, C, lay=1)
    # 東面（模型 +x）的銘文板：淺浮一格
    M.add(M.box(cx + 1.3, cx + 1.5, cy - 0.9, cy + 0.9, 0.75 + 0.35, 0.75 + 1.0), MARBLE, 1)
    # 柱頂板上的鷹（翅膀半開、朝東）
    M.add(M.box(cx - 0.3, cx + 0.3, cy - 0.3, cy + 0.3, ztop, ztop + 0.2), MARBLE, 2)                                       # 腳下的座
    M.add(((M.X - cx) / 0.36) ** 2 + ((M.Y - cy) / 0.3) ** 2 + ((M.Z - (ztop + 0.6)) / 0.5) ** 2 <= 1, MARBLE, 2)          # 身
    M.add((M.X - (cx + 0.22)) ** 2 + (M.Y - cy) ** 2 + (M.Z - (ztop + 1.12)) ** 2 <= 0.2 ** 2, MARBLE, 2)                  # 頭
    M.add(M.box(cx - 0.2, cx + 0.2, cy - 0.85, cy + 0.85, ztop + 0.45, ztop + 1.0) & (abs(M.Y - cy) * 0.35 + ztop + 0.45 <= M.Z), MARBLE, 2)   # 半開的兩翼
    G, L = M.finish(shell_m=0.8, seed=269)
    anchors = {'lot-0': [0, 0, 0], 'top': M.cell(cx, cy, ztop + 1.0)}
    return G, L, anchors, {'柱頭頂（m）': round(ztop, 2)}
