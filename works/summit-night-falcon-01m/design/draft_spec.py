# 新圖紙 00 規格（TASK-0529 第零階段的拍板畫成一張圖；TASK-0532 漫畫第 001 話用）。
# 用法：python -I -X utf8 draft_spec.py <design 資料夾>
#   數字全部照 notes.md「第零階段」與 plan.json；吃水的兩個剖面是**示意**（同一個比例尺，形狀不是線形）。
import sys, os
from PIL import Image, ImageDraw, ImageFont

FONT = r"C:\Windows\Fonts\msjh.ttc"
INK, GREY, BLUE, RED, PAPER = (30, 30, 30), (150, 150, 150), (30, 90, 200), (190, 40, 40), (250, 248, 242)


def f(sz): return ImageFont.truetype(FONT, sz)


def box(g, xy, title, lines, col=INK):
    g.rectangle(xy, outline=col, width=3)
    x, y = xy[0] + 16, xy[1] + 12
    g.text((x, y), title, fill=col, font=f(24))
    for i, s in enumerate(lines): g.text((x, y + 40 + i * 30), s, fill=INK, font=f(19))


def main():
    d = sys.argv[1]
    im = Image.new('RGB', (1600, 900), PAPER)
    g = ImageDraw.Draw(im)
    g.text((24, 14), "夜隼號 Night Falcon　新圖紙 00　規格（第零階段的拍板）　summit 2026-10-13", fill=INK, font=f(28))

    # ① 規格的本尊：先後順序
    g.text((40, 70), "① 規格的本尊（依序）", fill=INK, font=f(24))
    box(g, (40, 110, 520, 290), "1　漫畫船設 night-falcon.md", ["雙桅快船（三桅進不了退潮礁區）", "極淺吃水：比鴴號只深半尺", "舵輪中央：隼徽記被剝後的疤", "船身不寫船名"])
    box(g, (40, 330, 520, 470), "2　定稿圖 night_falcon_v1.png", ["brigantine：前桅橫帆、主桅縱帆", "隼形船首像、船尾窗廊、每舷約 6 砲", "注意：看的，不是量的"], GREY)
    box(g, (40, 510, 520, 690), "3　小說正文", ["001:11「雙桅快船」", "000:21、004:51、005:9 寫成「三根」", "→ 錯在正文，照船設造雙桅", "（今天三處都改成兩根）"], RED)
    for y0, y1 in ((290, 330), (470, 510)):
        g.line([(280, y0 + 4), (280, y1 - 4)], fill=INK, width=3)
        g.polygon([(270, y1 - 16), (290, y1 - 16), (280, y1 - 2)], fill=INK)

    # ② 尺寸參照
    g.text((580, 70), "② 尺寸（參考資料：Oswego 雙桅橫帆船，1756，殘片推定）", fill=INK, font=f(24))
    rows = [("", "原值", "公尺", "格（0.1 m）", "出處"),
            ("龍骨長", "60 ft", "18.3", "183", "參考資料"),
            ("型寬", "21 ft", "6.4", "64", "參考資料"),
            ("艙深", "7 ft", "2.13", "21", "參考資料"),
            ("甲板長", "—", "約 21", "約 210", "設計決定（×1.15，估的）"),
            ("人數", "31 人", "", "", "續篇 000:23")]
    cx = [580, 700, 810, 910, 1050]
    for i, r in enumerate(rows):
        y = 116 + i * 40
        for c, s in zip(cx, r): g.text((c, y), s, fill=INK if i else GREY, font=f(20))
        if i == 0: g.line([(580, y + 32), (1560, y + 32)], fill=GREY, width=1)
    g.text((580, 362), "注意：160 噸是載重噸位（burthen），不是排水量。", fill=GREY, font=f(18))

    # ③ 吃水：字面 vs 設計（同一個比例尺的示意剖面）
    g.text((580, 420), "③ 吃水：字面讀法 vs 設計決定（同一比例尺；剖面是示意）", fill=INK, font=f(24))
    S = 60                                   # 1 m ＝ 60 px
    wl = 560
    g.line([(580, wl), (1560, wl)], fill=BLUE, width=2)
    g.text((1500, wl - 28), "水面", fill=BLUE, font=f(18))

    def section(cx0, half_m, draft_m, free_m, label, col):
        hw, dr, fb = half_m * S, draft_m * S, free_m * S
        pts = [(cx0 - hw, wl - fb), (cx0 - hw, wl + dr * 0.55), (cx0 - hw * 0.55, wl + dr), (cx0 + hw * 0.55, wl + dr), (cx0 + hw, wl + dr * 0.55), (cx0 + hw, wl - fb)]
        g.line(pts, fill=col, width=4)
        tb = g.textbbox((cx0 - hw, wl + dr + 14), label, font=f(19))
        g.rectangle((tb[0] - 4, tb[1] - 2, tb[2] + 4, tb[3] + 2), fill=PAPER)
        g.text((cx0 - hw, wl + dr + 14), label, fill=col, font=f(19))
        return wl + dr

    g.line([(1300, wl + 1.5 * S), (1300, wl + 3.0 * S)], fill=INK, width=6)
    b1 = section(780, 3.2, 0.5, 1.5, "字面：吃水約 0.5 m —— 撐不住 31 人、12 門砲", RED)
    b2 = section(1300, 3.2, 1.5, 1.5, "設計：船殼吃水 1.5 m（插板收起）", INK)
    g.text((1312, wl + 3.0 * S - 26), "中插板放下 3.0 m（可收放）", fill=INK, font=f(18))
    for x, dm in ((700, 0.5), (1220, 1.5)):
        g.line([(x, wl), (x, wl + dm * S)], fill=GREY, width=2)
        g.text((x + 8, wl + 4), f"{dm} m", fill=GREY, font=f(18))
    g.text((580, 830), "鴴號跟著讀成「比夜隼號淺半尺」的測量艇（約 1.35 m），不是吃水幾公分的小划子。", fill=GREY, font=f(18))
    g.text((580, 860), "旁證：SV Black Jack（87 ft、最大吃水 6 ft）這麼淺的雙桅船真的存在 —— 現代鋼殼、有引擎，不是史料。", fill=GREY, font=f(18))
    im.save(os.path.join(d, 'sheet00_spec_v1.png'), optimize=False)
    print('ok')


if __name__ == '__main__':
    main()
