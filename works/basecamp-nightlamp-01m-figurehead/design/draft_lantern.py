# 提燈（TASK-0538 船首像左手握的那盞）：營地的大提燈 ⇒ 子作品 basecamp-nightlamp-01m-lantern 的格子清單＋固定點
# 用法：python -I draft_lantern.py <design 資料夾>
#   · 0.01 m／格；尺寸照 plan.json lantern（以身高 H 為 1）× placement.H_m。
#   · 底板、四根黃銅角柱、上下黃銅帶、四面暖黃玻璃（每面一個鐵條小帳篷「Λ」＝ 營地特色）、白蠟燭、火焰、
#     鐵斜頂、煙囪蓋、黃銅提環（在 y–z 平面，橫桿沿 y ＝ 船首像左手的握軸）。
#   · 固定點：wick（火焰中心）、bail（提環頂、手握的地方）、base（底板中心底下）。
#   ⇒ masks/lantern.vox.txt、lantern_anchors.json、verify_lantern.json
import sys, os, json, math
import numpy as np


def main():
    design = sys.argv[1]
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    L, Lc = plan['lantern'], plan['lantern_build']
    H = plan['placement']['H_m'] / plan['work']['meters_per_voxel']      # 每 H 幾格
    W = 2 * int(round(L['body_w_H'] * H / 2)) + 1   # 燈身寬（格）—— 取奇數，中心才落在格心（偶數時燈身中心 29.5、蠟燭與提環 30 ⇒ 鏡像差 6,798）
    BH = int(round(L['body_h_H'] * H))         # 燈身高
    RH = int(round(L['roof_h_H'] * H))         # 斜頂高
    BA = int(round(L['bail_H'] * H))           # 提環高
    C = Lc['colors']
    size = Lc['size']
    cx = cy = size[0] // 2
    g = {}

    def put(x, y, z, c):
        if 0 <= x < size[0] and 0 <= y < size[1] and 0 <= z < size[2]:
            g[(x, y, z)] = c
    h0 = W // 2
    x0, x1 = cx - h0, cx - h0 + W - 1
    y0, y1 = cy - h0, cy - h0 + W - 1
    zb = Lc['base_thick']
    # 底板（比燈身寬 2 格）
    for x in range(x0 - 2, x1 + 3):
        for y in range(y0 - 2, y1 + 3):
            for z in range(zb):
                put(x, y, z, C['iron'])
    zt = zb + BH                                   # 燈身頂（不含）
    pt = Lc['post']
    for z in range(zb, zt):
        for (px, py) in ((x0, y0), (x1 - pt + 1, y0), (x0, y1 - pt + 1), (x1 - pt + 1, y1 - pt + 1)):
            for x in range(px, px + pt):
                for y in range(py, py + pt):
                    put(x, y, z, C['brass'])
        band = z < zb + Lc['band'] or z >= zt - Lc['band']
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                edge = x in (x0, x1) or y in (y0, y1)
                if not edge or (x, y, z) in g:
                    continue
                put(x, y, z, C['brass'] if band else C['glass'])
    # 每面玻璃的小帳篷 Λ（鐵條 2 格寬）：高 0.45 燈身、寬 0.6 燈身寬
    th, tw = int(BH * 0.45), int(W * 0.6)
    tz0 = zb + Lc['band'] + int(BH * 0.12)
    for k in range(th):
        half = tw / 2 * (1 - k / th)
        z = tz0 + k
        for s in (-1, 1):
            off = int(round(s * half))
            for dw in (0, s * -1):
                u = off + dw
                for (x, y) in ((cx + u, y0), (cx + u, y1), (x0, cy + u), (x1, cy + u)):
                    put(x, y, z, C['iron'])
    for u in range(-(tw // 2), tw // 2 + 1):          # 帳篷底邊（−tw // 2 對奇數往下取整會多一格）
        for (x, y) in ((cx + u, y0), (cx + u, y1), (x0, cy + u), (x1, cy + u)):
            if (x, y, tz0) in g and g[(x, y, tz0)] == C['glass']:
                put(x, y, tz0, C['iron'])
    # 蠟燭＋火焰
    cr, ch = Lc['candle_r'], int(BH * Lc['candle_h_frac'])
    for z in range(zb, zb + ch):
        for x in range(cx - cr, cx + cr + 1):
            for y in range(cy - cr, cy + cr + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= cr * cr:
                    put(x, y, z, C['candle'])
    fz0, fh, fr = zb + ch, Lc['flame_h'], Lc['flame_r']
    for k in range(fh):
        t = k / fh
        r = fr * math.sin(math.pi * min(1.0, t * 1.25)) if t < 0.8 else fr * (1 - t) * 2.5
        for x in range(cx - fr, cx + fr + 1):
            for y in range(cy - fr, cy + fr + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    put(x, y, fz0 + k, C['flame_core'] if (x - cx) ** 2 + (y - cy) ** 2 <= (r * 0.5) ** 2 else C['flame'])
    wick = [cx, cy, fz0 + fh // 3]
    # 斜頂（四角錐台）＋煙囪蓋
    for k in range(RH):
        half = (W / 2 + 1) * (1 - k / RH) + Lc['chimney_r'] * (k / RH)
        hw = int(half)                               # 左右各取一樣的格數（int(cx − half) 與 int(cx + half) 截尾方向不同 ⇒ 不對稱）
        for x in range(cx - hw, cx + hw + 1):
            for y in range(cy - hw, cy + hw + 1):
                put(x, y, zt + k, C['iron'])
    zc = zt + RH
    for k in range(Lc['cap_h']):
        r = Lc['chimney_r'] + (2 if k == Lc['cap_h'] - 1 else 0)
        for x in range(cx - r, cx + r + 1):
            for y in range(cy - r, cy + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    put(x, y, zc + k, C['iron'])
    # 提環：y–z 平面的圓環（橫桿沿 y），底接煙囪蓋頂
    zr0 = zc + Lc['cap_h']
    R = BA / 2.0
    rr = Lc['bail_r']
    ccz = zr0 + R - 1
    for x in range(cx - rr - 1, cx + rr + 2):
        for y in range(int(cy - R - rr - 1), int(cy + R + rr + 2)):
            for z in range(zr0 - 1, int(zr0 + 2 * R + rr + 1)):
                dy, dz = y - cy, z - ccz
                q = math.hypot(math.hypot(dy, dz) - R, x - cx)
                if q <= rr and (x, y, z) not in g:
                    put(x, y, z, C['brass'])
    bail = [cx, cy, int(round(ccz + R))]
    base = [cx, cy, 0]
    cells = sorted(g.items())
    os.makedirs(os.path.join(design, 'masks'), exist_ok=True)
    with open(os.path.join(design, 'masks', 'lantern.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 夜燈號 船首像的提燈（draft_lantern.py 產）—— x,y,z,color；stampvox at=0,0,0\n')
        for (x, y, z), c in cells:
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    zmax = max(z for (_, _, z) in g)
    anchors = {'wick': wick, 'bail': bail, 'base': base}
    json.dump(anchors, open(os.path.join(design, 'lantern_anchors.json'), 'w', encoding='utf-8'), indent=1)
    cols = {}
    for _, c in cells:
        cols[c] = cols.get(c, 0) + 1
    ver = {'cells': len(cells), 'colors': cols, 'body_w': W, 'body_h': BH, 'roof_h': RH, 'bail_h': BA,
           'height_cells': zmax + 1, 'height_m': (zmax + 1) * plan['work']['meters_per_voxel'], 'anchors': anchors,
           'mirror_y_missing': sum(1 for (x, y, z) in g if (x, 2 * cy - y, z) not in g),
           'mirror_x_missing': sum(1 for (x, y, z) in g if (2 * cx - x, y, z) not in g)}
    json.dump(ver, open(os.path.join(design, 'verify_lantern.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(ver)


if __name__ == '__main__':
    main()
