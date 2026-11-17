# 突尼斯湖淺水轉運划艇 Sandal 新圖紙 01（TASK-1301 步驟 3）：線形＋挖空船殼
#   出處：basecamp-piragua-01m/design/draft_lines.py —— 改為突尼斯平底駁運艇比例、追加船尾翹底、傳統赭黃舷飾帶與貨艙空間讀數。
#   用法：python -I -X utf8 draft_lines.py [--probe=half_beam=+3]
import sys, os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
EXTRA = 20
WOOD_T_PER_M3 = 0.55  # 地中海松／橡木船殼密度約 0.55 t/m³〔設計估〕


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def build(plan, probe=None):
    SX, SY, SZ = plan['space']['hull']
    X0, X1, ZMAX = 0, SX - 1, SZ - 1
    L = HL.Lines(plan, probe)
    hb = plan['hull_build']
    C = {k: V(v) for k, v in hb['colors'].items()}
    wall = V(hb['wall'])
    wl = plan['waterline']['z']

    S = L.solid(X0, X1, ZMAX, 0)
    Sx = np.pad(L.solid(X0, X1, ZMAX, EXTRA), 1)
    core = Sx
    for _ in range(wall):
        core = ndimage.binary_erosion(core, structure=np.ones((3, 3, 3), bool))
    shell = S & ~core[1:-1, 1:-1, 1:-1]

    G = np.zeros((SX, SY, SZ), np.uint8)
    G[shell] = C['hull']

    touch_out = ndimage.binary_dilation(~Sx, structure=ndimage.generate_binary_structure(3, 1))[1:-1, 1:-1, 1:-1]
    zz = np.arange(SZ)[None, None, :]
    G[shell & ~touch_out] = C['inner']
    G[shell & touch_out & (zz < wl)] = C['below']

    up_hollow = np.zeros_like(shell)
    up_hollow[:, :, :-1] = (S & ~shell)[:, :, 1:]
    G[shell & up_hollow] = C['inner']

    xs = np.arange(X0, X1 + 1) + 0.5
    ztop = np.floor(L.zs(xs) - 0.5).astype(int)
    for x in range(X0, X1 + 1):
        if L.xa <= x + 0.5 <= L.xf and 0 <= ztop[x] <= ZMAX:
            zt = int(ztop[x])
            if zt - 1 >= wl:
                sub = G[x, :, zt - 1]
                mask_ext = (sub > 0) & touch_out[x, :, zt - 1]
                sub[mask_ext] = C['trim']
            col = G[x, :, zt]
            col[col > 0] = C['band']
    # 地中海小艇常見微揚短艏柱頭（x=xf-1..xf, z=sh_fwd..sh_fwd+2）與深木色艉柱緣
    if probe is None:
        xf_top = int(np.floor(L.xf)) - 1
        zt_bow = int(np.floor(L.sh_fwd))
        for zz_p in range(zt_bow, min(zt_bow + 2, SZ)):
            if G[xf_top, L.YC, zz_p] == 0:
                G[xf_top, L.YC, zz_p] = C['band']
    return L, G, S


def readings(L, G, S, plan):
    wl = plan['waterline']['z']
    occ = G > 0
    R = {}
    lay = S[:, :, wl - 1]
    xs = np.where(lay.any(axis=1))[0]
    R['lwl_cells'] = int(xs.max() - xs.min() + 1) if len(xs) else 0
    R['bwl_cells'] = int(lay.any(axis=0).sum())
    R['beam_cells'] = int(S.any(axis=(0, 2)).sum())
    xo = np.where(occ.any(axis=(1, 2)))[0]
    R['loa_cells'] = int(xo.max() - xo.min() + 1)
    R['loa_x'] = [int(xo.min()), int(xo.max())]
    R['z_max'] = int(np.where(occ.any(axis=(0, 1)))[0].max())
    R['transom_width_cells'] = int(occ[int(L.xa)].any(axis=1).sum())
    R['bow_tip_x'] = int(xo.max())
    R['cells'] = int(occ.sum())
    R['color_counts'] = {str(int(c)): int((G == c).sum()) for c in np.unique(G[occ])}
    lab, n = ndimage.label(occ)
    R['components'] = int(n)
    la, na = ndimage.label(~occ)
    border = set(np.unique(np.r_[la[0].ravel(), la[-1].ravel(), la[:, 0].ravel(), la[:, -1].ravel(), la[:, :, 0].ravel(), la[:, :, -1].ravel()]))
    R['cavities'] = len([i for i in range(1, na + 1) if i not in border])
    R['mirror_diff'] = int((occ != occ[:, ::-1, :]).sum())
    R['hull_mass_t'] = round(R['cells'] * 0.001 * WOOD_T_PER_M3, 2)
    R['displacement_t'] = round(float(S[:, :, :wl].sum()) * 0.001 * 1.025, 2)
    R['free_payload_t'] = round(R['displacement_t'] - R['hull_mass_t'], 2)
    floor = S[:, :, 1] & ~occ[:, :, 1]
    R['floor_cells'] = int(floor.sum())
    bay = plan['layout']['cargo_bay']['v']
    R['cargo_bay_floor_cells'] = int(floor[bay['x0']:bay['x1'] + 1, :].sum())
    R['midship'] = {'x': int(L.xm), 'sheer_z': round(float(L.zs(L.xm)), 2), 'half_beam_at_sheer': round(float(L.Bs(L.xm)), 2)}
    return R


def sheet(L, G, plan, R, path):
    SX, SY, SZ = plan['space']['hull']
    sc = 8
    W = SX * sc + 40
    H = 60 + SZ * sc + 30 + SY * sc // 2 + 30 + 18 * sc + 80
    im = Image.new('RGB', (W, H), (246, 240, 226))
    d = ImageDraw.Draw(im)
    f, fs = font(22), font(15)
    d.text((20, 10), '突尼斯湖轉運艇 Sandal 新圖紙 01：線形與平底船殼（0.1 m/格；側面、平面、三站剖面）', fill=(40, 30, 20), font=f)

    oy = 50
    for x in range(SX):
        for z in range(SZ):
            nz = np.nonzero(G[x, :, z])[0]
            if len(nz):
                d.rectangle([20 + x * sc, oy + (SZ - 1 - z) * sc, 20 + x * sc + sc - 1, oy + (SZ - z) * sc - 1], fill=rgb(int(G[x, nz[0], z])))
    wl = plan['waterline']['z']
    d.line([20, oy + (SZ - wl) * sc, 20 + SX * sc, oy + (SZ - wl) * sc], fill=(30, 90, 200), width=2)
    d.text((24, oy + (SZ - wl) * sc + 4), f'DWL z={wl} (0.40 m)', fill=(30, 90, 200), font=fs)
    for x in range(0, SX, 10):
        d.text((20 + x * sc, oy + SZ * sc + 2), str(x), fill=(90, 80, 70), font=fs)

    oy2 = oy + SZ * sc + 30
    sc_y = max(sc // 2, 4)
    for x in range(SX):
        for y in range(SY):
            nz = np.nonzero(G[x, y, :])[0]
            if len(nz):
                d.rectangle([20 + x * sc, oy2 + y * sc_y, 20 + x * sc + sc - 1, oy2 + (y + 1) * sc_y - 1], fill=rgb(int(G[x, y, nz[-1]])))

    oy3 = oy2 + SY * sc_y + 30 + 15 * sc
    s2 = sc
    stations = ((int(L.xa), f'艉鏡 x={int(L.xa)}'), (int(L.xm), f'舯貨艙 x={int(L.xm)}'), (96, '前段 x=96'))
    for k, (x, lab) in enumerate(stations):
        ox = 20 + k * 42 * s2
        for y in range(32, 69):
            for z in range(0, 15):
                if G[x, y, z]:
                    d.rectangle([ox + (y - 32) * s2, oy3 - z * s2, ox + (y - 32) * s2 + s2 - 1, oy3 - z * s2 + s2 - 1], fill=rgb(int(G[x, y, z])))
        d.text((ox, oy3 + s2 + 4), lab, fill=(40, 30, 20), font=fs)

    txt = (f"LOA {R['loa_cells']} 格 (x {R['loa_x'][0]}-{R['loa_x'][1]}) | 寬 {R['beam_cells']} | "
           f"LWL {R['lwl_cells']} | BWL {R['bwl_cells']} | 艉寬 {R['transom_width_cells']} | "
           f"排水量 {R['displacement_t']:.2f} t (殼 {R['hull_mass_t']:.2f} t, 淨負載 {R['free_payload_t']:.2f} t) | "
           f"貨艙底 {R['cargo_bay_floor_cells']} 格 | 元件 {R['components']} | 空腔 {R['cavities']} | 鏡像差 {R['mirror_diff']}")
    d.text((20, H - 35), txt, fill=(40, 30, 20), font=fs)
    im.save(path)


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan()
    L, G, S = build(plan, probe or None)
    R = readings(L, G, S, plan)
    if probe:
        print(json.dumps({'probe': probe, **R}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'hull'), exist_ok=True)
    pts = np.argwhere(G > 0)
    with open(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 突尼斯湖轉運艇 Sandal 船殼（draft_lines.py）x,y,z,color —— at 0,0,0\n')
        f.write('\n'.join(f'{x},{y},{z},{G[x, y, z]}' for x, y, z in pts) + '\n')
    with open(os.path.join(HERE, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(L, G, plan, R, os.path.join(HERE, 'sheet01_lines_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
