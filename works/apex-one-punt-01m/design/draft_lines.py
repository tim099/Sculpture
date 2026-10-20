# 蓬特號 新圖紙 01（TASK-0754）：線形＋船殼外板＋兩頭柱與柱頭 ⇒ 圖紙 sheet01_lines_v1.png、讀數 verify_lines.json、清單 masks/hull/hull.vox.txt
#   用法：python -I -X utf8 draft_lines.py [--probe=half_beam=+3]
#   · 只讀 plan.json、不碰作品。船殼 ＝ 線形圍出來的實心往裡留 wall 格；舷頂以上多算 EXTRA 層再量距離 ⇒ 舷頂不會變成一層蓋子。
#   · 兩頭的柱：沿 plan.json 的折線掃一串球（半徑照表內插）；柱頂一朵往外張的柱頭（圓錐）＋一道綁帶。
#   · --probe：反向對照（拿某個線形參數加減重算讀數，⛔ 不寫清單與圖）。
import sys, os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
EXTRA = 30
SX, SY, SZ = 280, 201, 140
X0, X1, ZMAX = 0, SX - 1, 90


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def tube(G, path, radii, yc, color, overwrite=False):
    """沿 (x, z) 折線掃球：每 0.25 格取一點，半徑沿長度內插。"""
    P = np.array(path, float)
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    for s in np.arange(0, seg[-1] + 1e-9, 0.25):
        x = np.interp(s, seg, P[:, 0])
        z = np.interp(s, seg, P[:, 1])
        r = np.interp(s, seg, radii)
        ball(G, x, yc + 0.5, z, r, color, overwrite)


def ball(G, cx, cy, cz, r, color, overwrite=False):
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 + (z + 0.5 - cz) ** 2 <= r * r and 0 <= x < SX and 0 <= y < SY and 0 <= z < SZ:
                    if overwrite or G[x, y, z] == 0:
                        G[x, y, z] = color


def umbel(G, base, axis, length, r0, r1, yc, color):
    """柱頭：從 base 沿 axis（x, z 平面）張開的實心圓錐（紙莎草傘形花序的樣子），口緣一圈。"""
    ax = np.array(axis, float)
    ax /= np.linalg.norm(ax)
    for s in np.arange(0, length + 1e-9, 0.25):
        r = r0 + (r1 - r0) * (s / length) ** 1.6
        ball(G, base[0] + ax[0] * s, yc + 0.5, base[1] + ax[1] * s, max(r, 0.8), color, overwrite=True)


def build(plan, probe=None):
    L = HL.Lines(plan, probe)
    hb = plan['hull_build']
    C = {k: V(v) for k, v in hb['colors'].items()}
    wall = V(hb['wall'])
    wl = plan['waterline']['z']
    YC = L.YC
    S = L.solid(X0, X1, ZMAX, 0)
    Sx = np.pad(L.solid(X0, X1, ZMAX, EXTRA), 1)
    dist = ndimage.distance_transform_edt(Sx)[1:-1, 1:-1, 1:-1]
    shell = S & (dist <= wall)
    G = np.zeros((SX, SY, SZ), np.uint8)
    G[:, :, :ZMAX + 1][shell] = C['hull']
    # 內面（離外面 > 1 格的殼）塗內板色；水線下塗深褐；舷頂兩格塗深色帶
    inner = shell & (dist > 1.5)
    G[:, :, :ZMAX + 1][inner] = C['inner']
    zz = np.arange(ZMAX + 1)[None, None, :]
    outer = shell & ~inner
    G[:, :, :ZMAX + 1][outer & (zz < wl)] = C['below']
    xs = np.arange(X0, X1 + 1) + 0.5
    ztop = np.floor(L.zs(xs) - 0.5).astype(int)          # 每一站舷頂那一格
    for i, x in enumerate(range(X0, X1 + 1)):
        if L.xa <= x + 0.5 <= L.xf:
            for z in (ztop[i], ztop[i] - 1):
                if 0 <= z <= ZMAX:
                    col = G[x, :, z]
                    col[(col == C['hull']) | (col == C['inner'])] = C['band']
    # 兩頭的柱與柱頭
    posts = {}
    for k in ('stern_post', 'bow_post'):
        p = V(hb[k])
        tube(G, p['path'], p['r'], YC, C['hull'])
        tip = p['path'][-1]
        umbel(G, tip, p['umbel_axis'], p['umbel_len'], p['umbel_r'][0], p['umbel_r'][1], YC, C['umbel'])
        bx, bz = p['path'][-1 - p['binding_at']] if p['binding_at'] < len(p['path']) else p['path'][0]
        ball(G, bx, YC + 0.5, bz, p['r'][-1 - p['binding_at']] + 0.6, C['binding'], overwrite=True)
        posts[k] = {'tip': tip}
    # 小封閉空腔填實（造船規格 §8 最後一條：≤ 50 格；柱與船殼接縫會夾出一兩格）
    la, na = ndimage.label(G == 0)
    border = set(np.unique(np.r_[la[0].ravel(), la[-1].ravel(), la[:, 0].ravel(), la[:, -1].ravel(), la[:, :, 0].ravel(), la[:, :, -1].ravel()]))
    filled = 0
    for i in range(1, na + 1):
        if i not in border:
            m = la == i
            if m.sum() <= 50:
                G[m] = C['hull']
                filled += int(m.sum())
    posts['cavity_filled'] = filled
    return L, G, posts


def readings(L, G, plan):
    wl = plan['waterline']['z']
    YC = L.YC
    occ = G > 0
    R = {}
    # 水線長、水線寬（照線形：z wl 那一層船裡的格）
    S = L.solid(X0, X1, ZMAX, 0)
    lay = S[:, :, wl]
    xs = np.where(lay.any(axis=1))[0] + X0
    R['lwl_cells'] = int(xs.max() - xs.min() + 1) if len(xs) else 0
    R['lwl_x'] = [int(xs.min()), int(xs.max())] if len(xs) else None
    R['bwl_cells'] = int(lay.any(axis=0).sum())
    R['beam_cells'] = int(S.any(axis=(0, 2)).sum())
    xo = np.where(occ.any(axis=(1, 2)))[0]
    R['loa_cells'] = int(xo.max() - xo.min() + 1)
    R['loa_x'] = [int(xo.min()), int(xo.max())]
    R['z_max'] = int(np.where(occ.any(axis=(0, 1)))[0].max())
    R['cells'] = int(occ.sum())
    lab, n = ndimage.label(occ)
    R['components'] = int(n)
    air = ~occ
    la, na = ndimage.label(air)
    border = set(np.unique(np.r_[la[0].ravel(), la[-1].ravel(), la[:, 0].ravel(), la[:, -1].ravel(), la[:, :, 0].ravel(), la[:, :, -1].ravel()]))
    cav = [i for i in range(1, na + 1) if i not in border]
    R['cavities'] = len(cav)
    R['mirror_diff'] = int((occ != occ[:, ::-1, :]).sum())
    # 排水量（線形水線下的體積 × 1.025）
    sub = S[:, :, :wl].sum()
    R['displacement_t'] = round(float(sub) * 0.001 * 1.025, 2)
    R['midship'] = {'x': int(L.xm), 'sheer_z': float(L.zs(L.xm)), 'half_beam_at_wl': float(L.hb(L.xm, wl + 0.5))}
    return R


def sheet(L, G, plan, R, path):
    sc = 4
    W, H = SX * sc + 40, (SZ - 40) * sc + SY * sc // 2 + 340
    im = Image.new('RGB', (W, H), (246, 240, 226))
    d = ImageDraw.Draw(im)
    f, fs = font(22), font(15)
    d.text((20, 10), '蓬特號 新圖紙 01：線形、船殼、兩頭柱頭（0.1 m／格；側面、平面、船中剖面）', fill=(40, 30, 20), font=f)
    oy = 50
    # 側面（最靠近看的人那一格的顏色：沿 +y 看，取 y 最小的非空）
    occ = G > 0
    ztop = SZ - 40
    for x in range(SX):
        for z in range(ztop):
            col = G[x, :, z]
            nz = np.nonzero(col)[0]
            if len(nz):
                c = rgb(int(col[nz[0]]))
                d.rectangle([20 + x * sc, oy + (ztop - 1 - z) * sc, 20 + x * sc + sc - 1, oy + (ztop - z) * sc - 1], fill=c)
    wl = plan['waterline']['z']
    d.line([20, oy + (ztop - wl) * sc, 20 + SX * sc, oy + (ztop - wl) * sc], fill=(30, 90, 200), width=2)
    d.text((24, oy + (ztop - wl) * sc + 4), 'DWL z %d（吃水 1.2 m）' % wl, fill=(30, 90, 200), font=fs)
    for x in range(0, SX, 20):
        d.text((20 + x * sc, oy + ztop * sc + 2), str(x), fill=(90, 80, 70), font=fs)
    # 平面（俯視：最高那一格的顏色）
    oy2 = oy + ztop * sc + 30
    for x in range(SX):
        for y in range(0, SY, 2):
            col = G[x, y, :]
            nz = np.nonzero(col)[0]
            if len(nz):
                c = rgb(int(col[nz[-1]]))
                d.rectangle([20 + x * sc, oy2 + y // 2 * sc, 20 + x * sc + sc - 1, oy2 + y // 2 * sc + sc - 1], fill=c)
    # 讀數
    txt = 'LOA %d 格（x %d–%d）｜LWL %d｜BWL %d｜寬 %d｜排水量 %.1f t｜元件 %d｜空腔 %d｜鏡像差 %d' % (
        R['loa_cells'], R['loa_x'][0], R['loa_x'][1], R['lwl_cells'], R['bwl_cells'], R['beam_cells'], R['displacement_t'], R['components'], R['cavities'], R['mirror_diff'])
    d.text((20, H - 30), txt, fill=(40, 30, 20), font=fs)
    # 船中剖面（平面圖底下）
    x = int(L.xm)
    s2 = 5
    ox, oy3 = 20, oy2 + SY * sc // 2 + 20 + 40 * s2
    for y in range(50, 151):
        for z in range(0, 40):
            if G[x, y, z]:
                d.rectangle([ox + (y - 50) * s2, oy3 - z * s2, ox + (y - 50) * s2 + s2 - 1, oy3 - z * s2 + s2 - 1], fill=rgb(int(G[x, y, z])))
    d.text((ox + 110 * s2 // 2, oy3 - 20 * s2), '← 船中剖面 x %d' % x, fill=(40, 30, 20), font=fs)
    im.save(path)


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan()
    L, G, posts = build(plan, probe or None)
    R = readings(L, G, plan)
    R['posts'] = posts
    if probe:
        print(json.dumps({'probe': probe, **R}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'hull'), exist_ok=True)
    pts = np.argwhere(G > 0)
    with open(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蓬特號 船殼（draft_lines.py）x,y,z,color —— at 0,0,0\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, G[x, y, z]) for x, y, z in pts) + '\n')
    with open(os.path.join(HERE, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(L, G, plan, R, os.path.join(HERE, 'sheet01_lines_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
