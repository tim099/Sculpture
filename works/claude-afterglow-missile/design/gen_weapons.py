"""餘暉號的兩種彈藥 —— 飛彈與動能彈的產生器（雕刻作品 claude-afterglow-missile、claude-afterglow-slug）

跟餘暉號同一套做法與調色盤：x ＝ 長度方向（尾在小的那端、彈頭朝 +x），y ＝ 寬，z ＝ 上；每格 0.1 m。
  飛彈    長 4.8 m、彈身直徑 0.7 m：尖拱形彈頭（前端是深色的尋標器罩）、彈身兩道面板環與紅橘識別帶、
          彈身中段四片短翼（×字）、彈尾四片後掠尾翼（＋字）、鐘形噴嘴，噴嘴裡一片發光的引擎盤（黑洞模擬的工具靠它找引擎）、
          彈身上下各一顆紅色的信標燈。
  動能彈  長 2.0 m、直徑 0.5 m 的實心穿甲彈：深色的尖錐彈頭、錐底一圈燒紅的環、兩道橘色的導帶、
          四片小尾翼、彈底一片發光的曳光盤。
原創設計，不照抄任何現有的彈種。

用法：python -I gen_weapons.py <輸出資料夾>
輸出：missile.txt、slug.txt（stampvox 清單 x,y,z,color；at=0,0,0），summary.json（格數、顏色分布、外框）。
"""
import json
import os
import sys

import numpy as np

# 顏色（RGB332 調色盤 index）—— 跟 claude-afterglow/design/gen_ship.py 同一張表
HULL_B = 146     # 冷灰面板
HULL_C = 218     # 淺色面板
MID = 109        # 中灰：面板縫、環
DARK = 73        # 深灰
VDARK = 37       # 更深
RED = 164        # 紅色識別帶
ORANGE = 240     # 橘色識別帶
GLASS = 41       # 尋標器罩
GLOW_CORE = 191  # 引擎核心（發光）
GLOW = 83        # 引擎外圈（發光）
NAV_RED = 224    # 信標燈（發光，會閃）
WINDOW = 248     # 曳光（發光）
HOT = 236        # 燒紅（黑洞模擬裡登記成會發光；雕刻的預覽裡只是橘紅色）


def grid(nx, ny, nz):
    col = np.zeros((nx, ny, nz), np.uint8)
    X, Y, Z = np.meshgrid(np.arange(nx), np.arange(ny), np.arange(nz), indexing="ij")
    return col, X, Y, Z


def put(col, mask, color, overwrite=False):
    m = mask if overwrite else (mask & (col == 0))
    col[m] = color


def missile():
    nx, ny, nz = 48, 21, 21
    col, X, Y, Z = grid(nx, ny, nz)
    c = 10                                   # 軸心在第 10 格的格心（y ↔ 20 − y、z ↔ 20 − z 對稱）
    dy, dz = Y - c, Z - c
    R2 = dy * dy + dz * dz
    R = np.sqrt(R2)
    rb = 3.4                                 # 彈身半徑 ⇒ 直徑 7 格

    # 噴嘴（x 0..5）：鐘形，往後張開；裡面是空的，x = 4 那一片是發光的引擎盤
    r_out = np.where(X <= 5, 3.0 - 0.12 * X, 0.0)
    nozzle = (X <= 5) & (R <= r_out)
    hollow = (X <= 3) & (R <= r_out - 1.05)
    put(col, nozzle & ~hollow & (X != 4), DARK)
    put(col, (X == 4) & (R <= 1.2), GLOW_CORE)
    put(col, (X == 4) & (R > 1.2) & (R <= r_out - 1.05 + 0.6), GLOW)
    put(col, (X == 4) & (R <= r_out), DARK)                       # 引擎盤外面那一圈噴嘴壁
    put(col, (X <= 1) & nozzle & ~hollow, VDARK, overwrite=True)  # 噴嘴口燒黑

    # 彈身（x 6..36）
    body = (X >= 6) & (X <= 36) & (R <= rb)
    put(col, body & ((X == 13) | (X == 26)), MID)                 # 兩道面板環
    put(col, body & (X >= 29) & (X <= 30), RED)                   # 紅色識別帶
    put(col, body & (X == 32), ORANGE)                            # 橘色識別帶
    put(col, body & (X >= 6) & (X <= 7), DARK)                    # 接噴嘴的那一段
    put(col, body & (X >= 14) & (X <= 25) & (dz <= -3), HULL_B)   # 腹部的冷灰面板
    put(col, body, HULL_C)

    # 彈頭（x 37..47）：尖拱形；最前面是深色的尋標器罩
    t = np.clip((X - 36) / 11.5, 0, 1)
    r_nose = rb * (1 - t ** 1.7)
    nose = (X >= 37) & (R <= r_nose)
    put(col, nose & (X >= 44), GLASS)
    put(col, nose & (X == 43), VDARK)
    put(col, nose & (X == 37), MID)
    put(col, nose, HULL_B)

    # 尾翼（＋字，x 1..11）：前緣後掠，翼尖紅色
    span = 3.4 + np.clip(11 - X, 0, 7) * 0.72                      # 越靠尾越長，最長到離軸 8.4
    for a, b in ((dy, dz), (dz, dy)):
        fin = (X >= 1) & (X <= 11) & (a == 0) & (np.abs(b) > 2.5) & (np.abs(b) <= span)
        put(col, fin & (np.abs(b) >= span - 1.0) & (X <= 8), RED)
        put(col, fin, HULL_B)

    # 短翼（×字，x 17..24）：彈身中段，一格厚
    strake = (X >= 17) & (X <= 24) & (np.abs(dy) == np.abs(dz)) & (np.abs(dy) >= 2) & (np.abs(dy) <= 4 - (X >= 23))
    put(col, strake, DARK)

    # 信標燈：彈身上下各一顆
    put(col, (X == 20) & (dy == 0) & (np.abs(dz) == 4), NAV_RED, overwrite=True)
    put(col, (X >= 19) & (X <= 21) & (dy == 0) & (np.abs(dz) == 3), VDARK, overwrite=True)
    return col


def slug():
    nx, ny, nz = 20, 11, 11
    col, X, Y, Z = grid(nx, ny, nz)
    c = 5
    dy, dz = Y - c, Z - c
    R = np.sqrt(dy * dy + dz * dz)
    rb = 2.3                                 # 直徑 5 格

    # 彈底：一片發光的曳光盤，外面一圈深色
    put(col, (X == 0) & (R <= 1.5), WINDOW)
    put(col, (X <= 1) & (R <= rb), DARK)
    # 彈身（x 2..12）：中灰，兩道橘色導帶
    body = (X >= 2) & (X <= 12) & (R <= rb)
    put(col, body & ((X == 4) | (X == 10)), ORANGE)
    put(col, body & (X == 7), DARK)
    put(col, body, MID)
    # 彈頭（x 13..19）：深色的尖錐，錐底一圈燒紅
    r_tip = rb * (1 - np.clip((X - 12) / 7.6, 0, 1))
    tip = (X >= 13) & (R <= r_tip)
    put(col, tip & (X == 13), HOT)
    put(col, tip, VDARK)
    # 小尾翼（＋字，x 0..3）
    for a, b in ((dy, dz), (dz, dy)):
        put(col, (X <= 3) & (a == 0) & (np.abs(b) > 2) & (np.abs(b) <= 4 - (X >= 3)), DARK)
    return col


def dump(col, path):
    idx = np.argwhere(col > 0)
    with open(path, "w", encoding="utf-8", newline="\n") as fo:
        for x, y, z in idx:
            fo.write("%d,%d,%d,%d\n" % (x, y, z, col[x, y, z]))
    vals, cnt = np.unique(col[col > 0], return_counts=True)
    mn, mx = idx.min(0), idx.max(0)
    mirror_y = int((col != col[:, ::-1, :]).sum())
    mirror_z = int((col != col[:, :, ::-1]).sum())
    return {"cells": int(len(idx)), "colors": {int(v): int(n) for v, n in zip(vals, cnt)},
            "box": [int(mn[0]), int(mx[0]), int(mn[1]), int(mx[1]), int(mn[2]), int(mx[2])],
            "size": list(col.shape), "mirror_diff_y": mirror_y, "mirror_diff_z": mirror_z}


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    summary = {"missile": dump(missile(), os.path.join(out, "missile.txt")),
               "slug": dump(slug(), os.path.join(out, "slug.txt"))}
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as fo:
        json.dump(summary, fo, ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
