# 松島號的舵輪座（鑄鐵）—— 共用雙舵輪 basecamp-frigate-constitution-01m-wheel 的座拆出去之後（TASK-0640），松島號只掛了輪 ⇒ 輪浮在艦橋上。
#   Tim 2026-10-23：「另外松島號的舵輪會浮空」「因為是共用模型」「其他船的舵輪支架跟松島號不同」
#   ⇒ 不照抄帆船那件木頭雙柱座（-wheel-stand，色 136／104），做一件鋼鐵艦的：
#     · 底板：沿軸躺在鼓輪底下（x 14–85），厚 3 格（6 cm），四角倒角；
#     · 兩根鑄鐵立柱：撐在兩段露出來的軸（x 13–25、74–85，r ≤ 2.5）底下，下寬上窄、腳往兩側張開；
#     · 柱頂的軸承座：包住軸的環（r 3–5.5，不碰軸的格），上半黃銅蓋。
#   座標跟共用舵輪同一套（0.02 m／格、size 104、軸 y 52 z 55.5）⇒ 擺法照抄舵輪那一條（at、pivot、scale）。
#   色：鑄鐵黑 36（37 小件會畫成藏青 —— 見 notes 裝飾那一段）、黃銅 180（plan 的 brass）。
#   用法：python -I -X utf8 draft_wheel_stand.py <輸出.txt>   ⇒ x,y,z,color（子作品座標），stampvox at 0,0,0。重跑逐位元組相同。
import math, sys

AX_Y, AX_Z = 52.0, 55.5            # 輪軸（共用舵輪 hub-aft／hub-fore 的 y、z ＋ 0.5 格心）
IRON, BRASS = 36, 180
POSTS = ((16, 23), (76, 83))       # 立柱的 x（含端點）：在兩段露出來的軸底下，避開輪（x 8–11、88–91）與鼓輪（x 26–73）
cells = {}


def put(x, y, z, c):
    cells[(x, y, z)] = c


# 底板
for x in range(14, 86):
    for y in range(43, 61):
        cx = min(x - 14, 85 - x)
        cy = min(y - 43, 60 - y)
        if cx + cy < 2:            # 四角倒角
            continue
        for z in range(0, 3):
            put(x, y, z, IRON)

# 立柱：z 3 起，腳往 y 兩側張開（z 3–8），往上收到軸承座底下（z 49）
for x0, x1 in POSTS:
    for z in range(3, 50):
        hw = 7.5 if z <= 8 else 7.5 - (z - 8) * (3.5 / 41.0)   # 半寬：腳 7.5 ⇒ 頂 4
        for x in range(x0, x1 + 1):
            for y in range(int(math.floor(AX_Y - hw)), int(math.ceil(AX_Y + hw))):
                if abs(y + 0.5 - AX_Y) <= hw:
                    put(x, y, z, IRON)

# 軸承座：包住軸的環（格心離軸 3–5.5 格），柱頂接上；z ≥ 57 那一半黃銅
for x0, x1 in POSTS:
    for x in range(x0, x1 + 1):
        for y in range(44, 60):
            for z in range(48, 63):
                r = math.hypot(y + 0.5 - AX_Y, z + 0.5 - AX_Z)
                if 3.0 < r <= 5.5:
                    put(x, y, z, BRASS if z >= 57 else IRON)

out = sys.argv[1]
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 松島號 舵輪座（鑄鐵，draft_wheel_stand.py）x,y,z,color —— 子作品座標（0.02 m／格，同共用舵輪），stampvox at 0,0,0\n')
    for (x, y, z) in sorted(cells):
        f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
print(len(cells), 'cells')
