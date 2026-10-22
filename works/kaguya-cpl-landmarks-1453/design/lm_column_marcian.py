# 馬爾西安紀念柱（Column of Marcian，Kıztaşı，450–452 年市政長官 Tatianus 立）1453：三級台階、白大理石基座（北面兩位勝利女神持圓盾、其他三面花環圓盾）、
#   阿提卡式柱礎、單塊灰色花崗岩柱身、科林斯柱頭、頂墩四角各一隻鷹；頂上的 Marcian 像鄂圖曼之前就沒了 ⇒ 頂墩上空著。
#   ⛔ 不做：今天的金屬箍、廣場鋪面與欄杆。
#   研究整理：scratchpad/cpl/research_batch2.md §1；位置：OSM node 3236233297（只有點）。
import math
import byz, columns
from byz import MARBLE, STONE

KEY = 'column-marcian'
TITLE = '馬爾西安紀念柱 1453（Column of Marcian，Kıztaşı；450–452，頂上的像已失）'
TITLE_SHORT = '馬爾西安紀念柱 1453'
MPV = 0.2
W, D, H = 8.0, 8.0, 18.0
META = {'kind': 'building', 'use': 'column-marcian', 'style': 'roman', 'lot': '8,8', 'base': 0, 'variant': 'a', 'lamps': 4}
PARTS = (('body', 1, '柱（台階、基座、柱礎、柱身、柱頭）'), ('top', 2, '頂墩與四角的鷹'))
PROV = {
    '基座 2.75 m、柱礎 0.51 m、柱身 8.74 m（下徑 1.13、上徑約 1.0）、柱頭 1.49 m、頂墩約 1.6 m（下緣寬 1.52）': '參考資料：OALA（Edinburgh，Schazmann 1934 實測，經 Kollwitz 1941）',
    '柱身單塊灰色花崗岩': '參考資料：OALA；Wikipedia 說紅灰色、兩段 —— 照 OALA（現場實測）',
    '頂墩四角各一隻鷹、高同飾帶': '參考資料：OALA；TBL',
    '北面兩位勝利女神持圓盾、其他三面花環圓盾': '參考資料：OALA；TBL',
    '三級台階、每級 0.3 m': '參考資料：Columbia／Livius 說三級；每級高是設計決定（今天只露出最上一級 0.33 m）',
    '頂墩上空著（像已失）': '設計決定（WP：鄂圖曼之前就沒了；失去的年代查不到）',
    '基座寬 2.8 m、柱頭寬 1.7 m': '設計決定（查無）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    cx = cy = 4.0
    C = {'steps': [[7.0, 0.3], [6.2, 0.3], [5.4, 0.3]], 'pedestal': {'w': 2.8, 'h': 2.75, 'mat': MARBLE, 'cornice': 0.18}, 'base': {'d': 1.55, 'h': 0.51},
         'shaft': {'d0': 1.13, 'd1': 1.0, 'h': 8.74, 'mat': STONE}, 'capital': {'w': 1.7, 'h': 1.49, 'mat': MARBLE}}
    ztop = columns.column(M, cx, cy, C, lay=1)
    # 基座四面的圓盾浮雕（凸 0.2 m）；北面（模型 y 0）兩位勝利女神
    zc = 0.9 + 1.45
    for (nx, ny) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        px, py = cx + nx * 1.4, cy + ny * 1.4
        if nx == 0:
            disk = ((M.X - px) ** 2 + (M.Z - zc) ** 2 < 0.5 ** 2) & (abs(M.Y - py) < 0.2)
        else:
            disk = ((M.Y - py) ** 2 + (M.Z - zc) ** 2 < 0.5 ** 2) & (abs(M.X - px) < 0.2)
        M.add(disk, MARBLE, 1)
    for sx in (-1, 1):                                           # 勝利女神：盾兩側各一個站立的人形（凸 0.2 m）
        M.add(M.box(cx + sx * 0.75 - 0.15, cx + sx * 0.75 + 0.15, cy - 1.6, cy - 1.4, 1.1, 2.9), MARBLE, 1)
        M.add(((M.X - (cx + sx * 0.75)) ** 2 + (M.Z - 3.05) ** 2 < 0.17 ** 2) & (M.Y >= cy - 1.6) & (M.Y < cy - 1.4), MARBLE, 1)
    # 頂墩（1.52 m 見方、1.6 m 高）＋ 四角的鷹（高同頂墩）
    M.add(M.box(cx - 0.76, cx + 0.76, cy - 0.76, cy + 0.76, ztop, ztop + 1.6), MARBLE, 2)
    for ex in (-1, 1):
        for ey in (-1, 1):
            ax, ay = cx + ex * 0.78, cy + ey * 0.78
            M.add(((M.X - ax) / 0.24) ** 2 + ((M.Y - ay) / 0.24) ** 2 + ((M.Z - (ztop + 0.75)) / 0.6) ** 2 <= 1, MARBLE, 2)       # 身
            M.add((M.X - (ax + ex * 0.12)) ** 2 + (M.Y - (ay + ey * 0.12)) ** 2 + (M.Z - (ztop + 1.45)) ** 2 <= 0.15 ** 2, MARBLE, 2)   # 頭
            for (wx, wy) in ((ex, 0), (0, ey)):                  # 兩翼貼著頂墩的兩面
                M.add(M.box(ax - 0.1 - 0.25 * abs(wy), ax + 0.1 + 0.25 * abs(wy), ay - 0.1 - 0.25 * abs(wx), ay + 0.1 + 0.25 * abs(wx), ztop + 0.4, ztop + 1.2)
                      & (((M.X - ax) * ex >= -0.05) | (wy != 0)) & (((M.Y - ay) * ey >= -0.05) | (wx != 0)), MARBLE, 2)
    G, L = M.finish(shell_m=0.8, seed=451)
    anchors = {'lot-0': [0, 0, 0], 'top': M.cell(cx, cy, ztop + 1.5)}
    return G, L, anchors, {'柱頭頂（m）': round(ztop, 2), '頂墩頂（m）': round(ztop + 1.6, 2)}
