# 夜隼號的旗（候選）—— 24×16 像素畫的三版（TASK-0530 實跑時畫的；TASK-0532 漫畫第 002 話用）。
# 用法：python -I -X utf8 make_flag.py <輸出資料夾>
#   v1：斜線俯衝（像一道紅線，不像隼 ⇒ 棄）　v2：正面、兩隻金眼（像蝙蝠面具 ⇒ 棄）　v3：正面、金喙尖 ⇒ 候選（＝ textures/ensign.png）
#   ⚠ v1、v2 當時被覆寫掉；這裡是照當時的格子重產的。
import sys, os
from PIL import Image
COL = {'.': (20, 33, 61), 'R': (139, 30, 30), 'G': (212, 175, 55)}
V1 = ["........................", "..R.....................", "...RR...................", "....RRR.................",
      ".....RRRR...............", "......RRRRR.............", ".......RRRRRR...........", "....RRRRRRRRRR..........",
      "......RRRRRRRRRR........", "..........RRRRRRRR......", "............RRRRRRR.....", "..............RRRRRR....",
      "................RRRRG...", "..................RRRR..", "....................RR..", "........................"]
def mirror(left): return [l + l[::-1] for l in left]
V2 = mirror(["............", "..RR........", "...RR......R", "....RRR...RR", ".....RRRR..R", "......RRRRRR", ".......RRRRR",
             "........RRRR", ".........RRR", ".........RRR", ".........RGR", "..........RR", "...........R", "...........R",
             "............", "............"])
V3 = mirror(["............", "..RR........", "...RR......R", "....RRR...RR", ".....RRRR..R", "......RRRRRR", ".......RRRRR",
             "........RRRR", ".........RRR", ".........RRR", ".........RRR", "..........RR", "...........R", "...........G",
             "............", "............"])
def save(art, path, scale=1):
    assert len(art) == 16 and all(len(r) == 24 for r in art)
    im = Image.new('RGBA', (24, 16))
    for y, row in enumerate(art):
        for x, ch in enumerate(row): im.putpixel((x, y), COL[ch] + (255,))
    if scale > 1: im = im.resize((24 * scale, 16 * scale), Image.NEAREST)
    im.save(path)
out = sys.argv[1]
for n, a in (("v1_streak", V1), ("v2_eyes", V2), ("v3", V3)):
    save(a, os.path.join(out, "flag_" + n + "_x16.png"), 16)
save(V3, os.path.join(out, "flag_v3.png"))
print("ok")
