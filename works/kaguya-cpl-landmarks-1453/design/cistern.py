# 露天蓄水池（艾提烏斯、阿斯帕、莫齊烏斯）1453：掘進地下的長方大池，opus listatum（磚帶＋石帶）；1453 年早就沒水、池底是菜園與果園（Clavijo 1403「城中有許多圍地種穀物與果園」）。
#   z 0 ＝ 池底（菜園面）：Blocksail 的特殊建築表寫 sink（地塊整平到地面下 sink 公尺，遊戲只挖地塊裡面）⇒ 牆從池底砌到街面上 parapet 公尺。
#   參數：L、W（外框）、depth（街面到池底）、wall_t（牆厚）、parapet、band（磚帶高, 石帶高）、seed；池內：畦田、果樹、看守小屋、沿牆一條坡道。
#   果樹另外兩件（件號 TREE_LAY：果樹、橄欖）：Blocksail 匯入時照關聯的 meta kind=tree 把格子拿掉、換成遊戲自己生成的樹（BUILDING_SPEC §5.2）⇒ 這裡的方塊樹只是標位置、高度、樹冠寬。
import math, random
import numpy as np
import byz
from byz import BANDED, STONE, GREEN, SOIL, TREE, WOOD, TILE, BRICK


TREE_LAY = {'fruit': 3, 'olive': 4}


def cistern(M, P, wall=1, garden=2):
    L, Wd, dep, t, par = M.w, M.d, P['depth'], P['wall_t'], P['parapet']
    zt = dep + par
    inner = M.box(t, L - t, t, Wd - t, -1, 999)
    M.add(M.box(0, L, 0, Wd, 0, zt) & ~inner, P.get('mat', BANDED), wall)
    # 牆頂：街面那一層是步道（石），女兒牆只在內緣 0.8 m
    M.add(M.box(0, L, 0, Wd, dep - 0.4, dep) & ~inner, STONE, wall)
    M.S[M.full(M.box(0, L, 0, Wd, dep, zt) & ~inner & ~M.box(t - 0.8, L - t + 0.8, t - 0.8, Wd - t + 0.8, -1, 999))] = False
    # 內壁的扶壁壁龕（每 pitch 一道淺拱龕）
    pitch = P.get('niche', 0)
    if pitch:
        for xx in np.arange(t + pitch / 2, L - t, pitch):
            for yy in (t, Wd - t):
                M.win(M.arch_open(xx, yy, 1.0, dep * 0.7, pitch * 0.55, normal='y', depth=0.8))
        for yy in np.arange(t + pitch / 2, Wd - t, pitch):
            for xx in (t, L - t):
                M.win(M.arch_open(xx, yy, 1.0, dep * 0.7, pitch * 0.55, normal='x', depth=0.8))
    # 池底：畦田（照種子每塊 種菜／休耕）、田埂、果樹、看守小屋、坡道
    rnd = random.Random(P.get('seed', 0))
    x0, x1, y0, y1 = t + 3.0, L - t - 3.0, t + 3.0, Wd - t - 3.0
    pw, pd = P.get('plot', (12.0, 18.0))
    nx, ny = max(1, int((x1 - x0) // pw)), max(1, int((y1 - y0) // pd))
    sx, sy = (x1 - x0) / nx, (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            a0, a1, b0, b1 = x0 + i * sx + 0.6, x0 + (i + 1) * sx - 0.6, y0 + j * sy + 0.6, y0 + (j + 1) * sy - 0.6
            u = rnd.random()
            if u < 0.25:                                     # 果園：一排一排的樹（六成果樹、四成橄欖，一塊一種）
                tl = TREE_LAY['fruit'] if rnd.random() < 0.6 else TREE_LAY['olive']
                for xx in np.arange(a0 + 2.5, a1 - 1.5, 5.0):
                    for yy in np.arange(b0 + 2.5, b1 - 1.5, 5.0):
                        r = rnd.uniform(1.6, 2.3); h = rnd.uniform(3.0, 4.5)
                        M.add(M.cyl(xx, yy, 0.3, 0, h - 0.5 * r), WOOD, tl)
                        M.add(((M.X - xx) ** 2 + (M.Y - yy) ** 2) / (r * r) + ((M.Z - h) / (r * 0.85)) ** 2 <= 1, TREE, tl)
                M.add(M.box(a0, a1, b0, b1, 0, M.mpv), GREEN, garden, over=False)
            elif u < 0.85:                                   # 菜畦：一條一條的壟
                rows = (np.floor((M.Y - b0) / 1.2) % 2 == 0) if (i + j) % 2 else (np.floor((M.X - a0) / 1.2) % 2 == 0)
                M.add(M.box(a0, a1, b0, b1, 0, M.mpv), SOIL, garden)
                M.add(M.box(a0, a1, b0, b1, M.mpv, 2 * M.mpv) & rows, GREEN, garden)
            else:                                            # 休耕
                M.add(M.box(a0, a1, b0, b1, 0, M.mpv), SOIL, garden)
    # 看守小屋（池底一角）
    hx, hy = t + 1.0, t + 1.0
    M.add(M.box(hx, hx + 4.0, hy, hy + 3.0, 0, 2.6), BRICK, garden)
    M.add(M.gable(hx - 0.3, hx + 4.3, hy - 0.3, hy + 3.3, 2.6, 1.2, 'x'), TILE, garden)
    M.door(M.arch_open(hx + 2.0, hy + 3.0, 0, 1.9, 0.9, normal='y', depth=0.8))
    # 坡道：沿長邊內壁從街面斜到池底（寬 2.4 m）
    rl = dep * 4.0
    rx0 = L - t - 2.0 - rl
    zr = dep * np.clip((M.X - rx0) / rl, 0, 1)
    M.add(M.box(rx0, L - t, Wd - t - 2.4, Wd - t, 0, 999) & (M.Z < dep - zr + 0.2), STONE, wall)
    return zt
