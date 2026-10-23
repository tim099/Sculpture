# 廢墟的共用形狀（TASK-0748 第四批：大皇宮台地、馬格瑙拉、元老院、Chalke）—— 從 lm_boukoleon.py、lm_blachernae.py 那幾段斷牆、倒柱、碎石抽出來。
#   亂數一律照呼叫的人給的 random.Random（決定論：同一個種子 ⇒ 逐格相同）。
import byz
from byz import BANDED, STONE, MARBLE, BRICK


def wall(M, x0, x1, y0, y1, h, rnd, lay, mat=BANDED, bite=0.6, step=2.4):
    """斷牆：一道牆（沿長的那一軸）每 step 公尺一段，牆頂往下咬 0～bite·h（高低不齊）。"""
    M.add(M.box(x0, x1, y0, y1, 0, h), mat, lay)
    along_x = (x1 - x0) >= (y1 - y0)
    L = (x1 - x0) if along_x else (y1 - y0)
    k = 0.0
    while k < L:
        w = step * (0.5 + rnd.random() * 0.5)
        z = h - rnd.random() * bite * h
        if along_x:
            M.air(M.box(x0 + k, x0 + k + w, y0 - 1, y1 + 1, z, 999))
        else:
            M.air(M.box(x0 - 1, x1 + 1, y0 + k, y0 + k + w, z, 999))
        k += w


def shell(M, x0, x1, y0, y1, h, t, rnd, lay, mat=BANDED, bite=0.6, floor=MARBLE, step=2.4):
    """沒有屋頂的廳：四面斷牆（厚 t）＋地坪；step ＝ 斷牆一段多長（短 ⇒ 咬得整齊、像雉堞）。"""
    for a in ((x0, x1, y0, y0 + t), (x0, x1, y1 - t, y1), (x0, x0 + t, y0, y1), (x1 - t, x1, y0, y1)):
        wall(M, a[0], a[1], a[2], a[3], h, rnd, lay, mat, bite, step)
    if floor:
        M.add(M.box(x0 + t, x1 - t, y0 + t, y1 - t, 0, M.mpv), floor, lay)


def stub(M, cx, cy, r, h, lay, mat=MARBLE, base=True):
    """殘柱：柱礎（方）＋斷在 h 的柱身；h ≤ 0 ⇒ 只剩柱礎。"""
    if base:
        M.add(M.box(cx - r - 0.25, cx + r + 0.25, cy - r - 0.25, cy + r + 0.25, 0, 0.5), mat, lay)
    if h > 0.5:
        M.add(M.cyl(cx, cy, r, 0.5, h), mat, lay)


def fallen(M, cx, cy, r, L, lay, axis='x', mat=MARBLE):
    """倒在地上的柱段（沿 axis、從 (cx, cy) 起長 L）。"""
    if axis == 'x':
        M.add(((M.Y - cy) ** 2 + (M.Z - r) ** 2 < r * r) & (M.X >= cx) & (M.X < cx + L), mat, lay)
    else:
        M.add(((M.X - cx) ** 2 + (M.Z - r) ** 2 < r * r) & (M.Y >= cy) & (M.Y < cy + L), mat, lay)


def rubble(M, rnd, x0, x1, y0, y1, n, lay, rmin=0.5, rmax=1.6):
    """碎石堆 n 個（半球，石三磚一）。"""
    for k in range(n):
        cx, cy = x0 + rnd.random() * (x1 - x0), y0 + rnd.random() * (y1 - y0)
        r = rmin + rnd.random() * (rmax - rmin)
        M.add(M.dome(cx, cy, 0.0, r, r * 0.45), STONE if k % 3 else BRICK, lay)


def plots(M, rnd, x0, x1, y0, y1, lay, pw=8.0, pd=12.0, fallow=0.3, field=None):
    """菜畦（照種子：種菜的一條一條壟、休耕的整塊土）。
    field ＝ 種菜那幾塊的件號（Blocksail 匯入時照關聯的 meta kind=field 把壟拿掉、土留著，遊戲在上面種生成式的作物 —— PRODUCTION §5、§7）；沒給 ⇒ 跟 lay 同一件。"""
    nx, ny = max(1, int((x1 - x0) // pw)), max(1, int((y1 - y0) // pd))
    sx, sy = (x1 - x0) / nx, (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            a0, a1, b0, b1 = x0 + i * sx + 0.6, x0 + (i + 1) * sx - 0.6, y0 + j * sy + 0.6, y0 + (j + 1) * sy - 0.6
            grow = rnd.random() >= fallow
            fl = field if grow and field is not None else lay
            M.add(M.box(a0, a1, b0, b1, 0, 2 * M.mpv), byz.SOIL, fl)
            if grow:
                rows = ((M.Y - b0) // 1.2) % 2 == 0 if (i + j) % 2 else ((M.X - a0) // 1.2) % 2 == 0
                M.add(M.box(a0, a1, b0, b1, 2 * M.mpv, 3 * M.mpv) & rows, byz.GREEN, fl)
