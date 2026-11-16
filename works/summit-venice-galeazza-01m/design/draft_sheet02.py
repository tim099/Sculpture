"""威尼斯 galeazza（TASK-1302）圖紙 02：船殼 01＋船殼 02 的側視與俯視（正交、照 RGB332 原色），疊上設計水線、25 支槳位、三根桅、艏樓砲門角度。

只讀 plan.json、masks/hull/hull_01.vox.txt、masks/upper/upper_01.vox.txt；輸出 sheet02_layout.png。重跑逐位元組相同。
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

D = Path(__file__).resolve().parent
S = 2      # px／格


def rgb(c):
    return np.stack([(c >> 5 & 7) * 255 // 7, (c >> 2 & 7) * 255 // 7, (c & 3) * 255 // 3], -1).astype(np.uint8)


def main():
    plan = json.loads((D / 'plan.json').read_text(encoding='utf-8'))
    A = np.concatenate([np.loadtxt(D / p, delimiter=',', dtype=np.int32) for p in
                        ('masks/hull/hull_01.vox.txt', 'masks/upper/upper_01.vox.txt')])
    NX, NY, NZ = plan['space']['hull']
    YC = plan['space']['yc']
    lay = plan['layout']
    wl = plan['waterline']['z']
    W, H = NX * S + 40, 640
    img = np.full((H, W, 3), 247, np.uint8)
    # 側視（從 +y 看，近的蓋遠的）：每個 (x, z) 取 y 最大的那格
    side_top = 40
    order = np.lexsort((A[:, 1],))
    for x, y, z, c in A[order]:
        py = side_top + (NZ - 1 - z) * S
        img[py:py + S, 20 + x * S:20 + x * S + S] = rgb(np.array(c))
    # 俯視（從上看）：每個 (x, y) 取 z 最大
    plan_top = side_top + NZ * S + 20
    order = np.lexsort((A[:, 2],))
    for x, y, z, c in A[order]:
        py = plan_top + (y - (YC - 70)) * S
        if 0 <= y - (YC - 70) < 141:
            img[py:py + S, 20 + x * S:20 + x * S + S] = rgb(np.array(c))
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    dr.text((20, 8), 'Venetian galeazza / TASK-1302 / sheet 02: hull + upperworks, 0.1 m per cell, bow right '
                     '(de Zuanne 1686: 29 passi x 25 piedi x 9 piedi)', fill=(22, 46, 52))
    zy = lambda z: side_top + (NZ - 1 - z) * S + S // 2
    dr.line((20, zy(wl), W - 20, zy(wl)), fill=(88, 140, 170))
    dr.text((W - 150, zy(wl) - 14), f'design WL z {wl}', fill=(88, 140, 170))
    for i in range(plan['oars']['per_side']):
        xo = int(np.floor(lay['oar_x0']['v'] + i * lay['oar_pitch']['v']))
        px = 20 + xo * S + S // 2
        dr.line((px, plan_top + (YC + 43 + 15 - (YC - 70)) * S, px, plan_top + 140 * S), fill=(40, 90, 140))
    for name, x in lay['masts']['v'].items():
        px = 20 + x * S + S // 2
        dr.line((px, side_top, px, zy(lay['deck_top_z']['v'])), fill=(160, 60, 40))
        dr.text((px + 3, side_top + 2), name, fill=(160, 60, 40))
        dr.ellipse((px - 5, plan_top + 70 * S - 5, px + 5, plan_top + 70 * S + 5), outline=(160, 60, 40))
    bc = lay['bow_castle']['v']
    for a in (-36, -12, 12, 36):
        ca, sa = np.cos(np.radians(a)), np.sin(np.radians(a))
        x0, y0 = 20 + (bc['cx'] + 0.5) * S, plan_top + 70 * S
        dr.line((x0, y0, x0 + ca * (bc['r'] + 25) * S, y0 + sa * (bc['r'] + 25) * S), fill=(200, 120, 0))
    dr.text((20, plan_top - 14), 'plan (top view) | blue = 25 oar stations per side | orange = lower-tier bow ports (2 x 50 lb colubrina, 2 x 20 lb cannone)',
            fill=(22, 46, 52))
    im.save(D / 'sheet02_layout.png')


if __name__ == '__main__':
    main()
