# 憲法號 階段四十 艙口格柵（Tim 2026-10-13「1~3 GO」⇒ todo 170「艙口格柵（gratings；spar deck 長艙口、main／fore hatch）」）
# 出處（查資料 agent 下載、裁切圖我自己看過標字）：USS Constitution Museum 模型資源
#   - Navy plan No. 19274「Arrangement of Hatch Coamings, Hatch Bars and Solid Wood Shutters on Spar, Gun and Berth Decks (After End)」1930：
#     PLAN OF SPAR DECK MAIN HATCH —— 格柵「W. OAK / ASH 2" SPACING」；橫的 hatch bar 15"×(11")、8"×(5")，中線縱 bar 10"×(7")；格 45½"／48"／48"、中線到圍板 6'-10½"。
#     SPAR DECK MAIN HATCH 立面 —— 格柵頂比甲板高 16¾"、格柵 2" 厚；GUN DECK MAIN HATCH 立面 —— 16½"、2"。
#     gun deck main hatch 平面（agent 讀）：中間一根 8"×5" 橫 bar、兩格 47½"；縱向 8"×4"、10"×8" bar、每格 32½"。
#   - No. 24423（gun deck GA 1931）：別的 gun deck 艙口旁寫「GRATING STOWED P&S」⇒ 那些不鋪（只鋪 main hatch）。
#   - No. 24422（spar deck GA 1931）：main hatch 兩端 P／S 是「DOWN」梯口。
# 作品對照（量 deck-spar／deck-gun 子作品）：
#   spar：開口 X 440–501、y 141–179；圍板 X 438–503、y 139–181、z 105–107（頂 108）；開口船尾那一段 X 441–455 站著兩座梯子（y 148–156、164–172）
#     ⚠ 作品的開口是 1849 年 02 號圖的 Long Hatchway（比 1931 的 main hatch 短、窄、位置也不同）⇒ 只鋪作品現有的開口、不刻甲板（只加不刻）。
#   gun：main hatch 開口 X 392–419、y 141–179；圍板 X 390–421、y 139–181、z 82–84（頂 85）；開口裡沒有東西。
# 設計：每個艙口一件子作品（0.05 m／格；2" 的條 ≈ 1 格、2" 的空 ≈ 1 格），當外部模型 scale 0.5 掛在該層甲板子作品上、meta kind=grating。
#   本地座標：x ＝ (世界 X − 圍板最船尾那格)×2、y ＝ (世界 y − 139)×2、z 0 ＝ 圍板頂（世界 108／85）。
#   - 圍板頂再加一圈 cap（2 格 ＝ 0.1 m）⇒ 格柵頂 ＝ 世界 109.0／86.0（＝ 甲板上 15.7"；圖 16¾"／16½"）
#   - hatch bar：頂齊格柵頂，往下照圖的深度（11"→6 格、7"→4、5"→3、4"→2、8"→4）
#   - 格柵：頂那一層（z 1），(i 偶 或 j 偶) 是條 ⇒ 1 格條、1 格空；橫的條（沿 y）橡木 136、縱的 ash 177；cap 與 bar 照圍板色 104。
# 用法：python -I draft_gratings.py <design 資料夾>
import sys, os, json
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
OUT = os.path.join(D, 'masks', 'gratings')
os.makedirs(OUT, exist_ok=True)
OAK, ASH, BAR = 136, 177, 104
Y0 = 139          # 圍板最 −y 那格（兩個艙口一樣）
CAP = 2           # cap 高（格，0.05 m）


def build(name, coam_x, coam_y, inner_x, inner_y, top_z, bars_x, bars_y, open_x):
    """coam_*／inner_*：世界格（含）；bars_x：[(世界 X 起, 世界 X 迄, 深度格)] 橫的（沿 y）；bars_y：[(本地 y 起, 迄, 深)] 縱的；open_x：(世界 X 起, 迄) 不鋪（梯口）"""
    X0 = coam_x[0]
    lx = lambda w: (w - X0) * 2
    ly = lambda w: (w - Y0) * 2
    nx, ny = lx(coam_x[1] + 1), ly(coam_y[1] + 1)
    ix0, ix1 = lx(inner_x[0]), lx(inner_x[1] + 1)        # 開口本地範圍 [ix0, ix1)
    iy0, iy1 = ly(inner_y[0]), ly(inner_y[1] + 1)
    deep = max([d for _, _, d in bars_x] + [d for _, _, d in bars_y])
    zoff = max(0, deep - CAP)                             # 本地 z 往上平移，最深的 bar 底 ＝ 0
    vox = {}

    def put(x, y, z, c):
        vox[(x, y, z + zoff)] = c

    # cap：圍板那一圈，z 0..CAP-1
    for x in range(nx):
        for y in range(ny):
            if not (ix0 <= x < ix1 and iy0 <= y < iy1):
                for z in range(CAP):
                    put(x, y, z, BAR)
    top = CAP - 1
    # 橫的 bar（沿 y 跨開口，兩頭搭在 cap 上）
    barcells = set()
    for wx0, wx1, d in bars_x:
        for x in range(lx(wx0), lx(wx1 + 1)):
            for y in range(iy0, iy1):
                for z in range(top - d + 1, top + 1):
                    put(x, y, z, BAR)
                barcells.add((x, y))
    # 縱的 bar（沿 x；梯口那一段不放）
    ox0, ox1 = (lx(open_x[0]), lx(open_x[1] + 1)) if open_x else (0, 0)
    for y0, y1, d in bars_y:
        for x in range(ix0, ix1):
            if ox0 <= x < ox1:
                continue
            for y in range(y0, y1 + 1):
                for z in range(top - d + 1, top + 1):
                    put(x, y, z, BAR)
                barcells.add((x, y))
    # 格柵：開口裡、不是 bar、不在梯口 ⇒ z top 那一層
    grat = 0
    for x in range(ix0, ix1):
        if ox0 <= x < ox1:
            continue
        for y in range(iy0, iy1):
            if (x, y) in barcells:
                continue
            if x % 2 == 0:
                put(x, y, top, OAK); grat += 1
            elif y % 2 == 0:
                put(x, y, top, ASH); grat += 1
    size = (nx, ny, top + 1 + zoff)
    G = np.zeros(size, bool)
    for k in vox:
        G[k] = True
    _, ncomp = ndimage.label(G)
    with open(os.path.join(OUT, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 憲法號 艙口格柵 %s（0.05 m／格；draft_gratings.py）\n' % name)
        for (x, y, z), c in sorted(vox.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    at = [X0, Y0, top_z - zoff * 0.5]
    print('%s：size %s、%d 格（格柵條 %d）、元件 %d、at %s、格柵頂 世界 z %.2f' % (name, size, len(vox), grat, ncomp, at, at[2] + (top + 1 + zoff) * 0.5))
    return {'size': list(size), 'cells': len(vox), 'grating_cells': grat, 'components': int(ncomp), 'at': at, 'pivot': [0, 0, 0], 'scale': 0.5,
            'top_world_z': at[2] + (top + 1 + zoff) * 0.5}


V = {}
# spar deck：船尾那段 X 440–456 是梯口；橫 bar A 15"（X 457–460、深 11"→6）、B 8"（473–474、5"→3）、C 15"（487–490、6）；格 12／12／11 格 ＝ 47"／47"／43"
#   中線縱 bar 10"×7" ⇒ 本地 y 40–45（6 格 ＝ 11.8"，對 y 160.5 對稱）、深 4；只在梯口以外
V['spar_main'] = build('spar_main', (438, 503), (139, 181), (440, 501), (141, 179), 108,
                       [(457, 460, 6), (473, 474, 3), (487, 490, 6)], [(40, 45, 4)], (440, 456))
# gun deck main hatch：中間橫 bar 8"×5"（X 405–406、深 3）⇒ 兩格 13 格 ＝ 51"（圖 47½"）；
#   縱 bar：中線 10"×8"（本地 40–45、深 4）、兩側 8"×4"（20–23、62–65、深 2）⇒ 每格 16 格 ＝ 31.5"（圖 32½"）
V['gun_main'] = build('gun_main', (390, 421), (139, 181), (392, 419), (141, 179), 85,
                      [(405, 406, 3)], [(40, 45, 4), (20, 23, 2), (62, 65, 2)], None)
json.dump(V, open(os.path.join(D, 'verify_gratings.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
