# 瓦倫斯引水渠 1453｜收尾（兩頭接進山坡的實心橋台）：同斷面的牆身、不開拱、往 +x 4 m；遊戲照城牆的收尾擺（wall-a 接牆身、起點那一頭轉 180°）。
#   見 lm_aqueduct.py（斷面）。尺寸是設計決定。
import byz
import lm_aqueduct as A

KEY = 'aqueduct-valens-end'
TITLE = '瓦倫斯引水渠 1453｜收尾（兩頭的橋台）'
TITLE_SHORT = '瓦倫斯引水渠 1453｜收尾'
MPV = A.MPV
W, D, H = 4.0, A.D, A.H
META = {'kind': 'wall', 'part': 'end', 'set': 'aqueduct-valens', 'style': 'roman', 'variant': 'end', 'len': 4.0, 'deck': A.DECK}
PARTS = (('body', 1, '橋台（實心牆身、渠道）'),)
PROV = {'兩頭接進山坡的實心橋台、長 4 m': '設計決定（引水渠兩端的形式查不到；照斷面不開拱）'}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.4, 1.2)
    M.band_z0 = 16.8
    A.section(M, 0.0, W, arch=False)
    G, L = M.finish(shell_m=1.2, seed=378)
    yc = M.NY // 2
    anchors = {'wall-a': [0, yc, 0], 'deck': M.cell(W / 2, D / 2, A.DECK - 0.1)}
    return G, L, anchors, {'渠頂（m）': A.DECK}
