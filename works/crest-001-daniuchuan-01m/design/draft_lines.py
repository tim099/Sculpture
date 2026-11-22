# 明鄭一號大鳥船 新圖紙 01（TASK-1316 步驟 3）：線形 ⇒ 圖紙 sheet01_lines_v1.png、讀數 verify_lines.json、船殼清單 masks/hull/hull_*.vox.txt
#   出處：kotoko-ganzengchuan-01m/design/draft_lines.py（改寫為 40 m 旗艦級尖底圓舭高尾大鳥船）
#   用法：python -I -X utf8 draft_lines.py <design 資料夾> [--probe=half_beam=+3]
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
EXTRA = 35
WOOD_T_PER_M3 = 0.60
CHUNK_MAX = 200000


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
    L = HL.Lines(plan, probe)
    zmax = int(math.ceil(L.top_max)) + 2
    x0 = int(math.floor(L.xa_min)) - 3
    x1 = int(math.ceil(L.xf_max)) + 3
    half = int(math.ceil(L.B)) + 6
    ylo = L.YC - half
    yhi = L.YC + half

    hb = plan['hull_build']
    C = {k: V(v) for k, v in hb['colors'].items()}
    wall = int(V(hb['wall']))
    wl = int(plan['waterline']['z'])

    S = L.solid(x0, x1, zmax, 0)[:, ylo:yhi + 1, :]
    Sx = np.pad(L.solid(x0, x1, zmax + EXTRA, EXTRA)[:, ylo:yhi + 1, :], 1)
    core = Sx
    for _ in range(wall):
        core = ndimage.binary_erosion(core, structure=np.ones((3, 3, 3), bool))
    shell = S & ~core[1:-1, 1:-1, 1:zmax + 2]

    G = np.zeros(S.shape, np.uint8)
    G[shell] = C['hull']

    touch_out = ndimage.binary_dilation(~Sx, structure=ndimage.generate_binary_structure(3, 1))[1:-1, 1:-1, 1:zmax + 2]
    zz = np.arange(zmax + 1)[None, None, :]
    G[shell & ~touch_out] = C['inner']
    G[shell & touch_out & (zz < wl)] = C['below']

    xs = np.arange(x0, x1 + 1) + 0.5
    ztop = np.floor(L.top_z(xs) - 0.5).astype(int)
    for xi in range(x1 - x0 + 1):
        zt = int(ztop[xi])
        if 0 <= zt <= zmax:
            row_top = G[xi, :, zt]
            row_top[row_top > 0] = C['trim']
    return L, G, S, x0, ylo


def readings(L, G, S, x0, ylo, plan):
    m = plan['meters_per_cell']
    wl = int(plan['waterline']['z'])
    occ = G > 0
    R = {}
    lay = S[:, :, wl - 1]
    xs_wl = np.where(lay.any(axis=1))[0]
    R['lwl_cells'] = int(xs_wl.max() - xs_wl.min() + 1) if len(xs_wl) else 0
    R['lwl_m'] = round(R['lwl_cells'] * m, 2)
    R['bwl_cells'] = int(lay.any(axis=0).sum())
    R['bwl_m'] = round(R['bwl_cells'] * m, 2)
    R['beam_cells'] = int(S.any(axis=(0, 2)).sum())
    R['beam_m'] = round(R['beam_cells'] * m, 2)
    xo = np.where(occ.any(axis=(1, 2)))[0]
    R['loa_cells'] = int(xo.max() - xo.min() + 1)
    R['loa_m'] = round(R['loa_cells'] * m, 2)
    R['loa_x'] = [int(x0 + xo.min()), int(x0 + xo.max())]
    R['keel_w_cells'] = int(S[:, :, 0].sum(axis=1).max())
    R['cells'] = int(occ.sum())
    R['solid_cells'] = int(S.sum())
    R['color_counts'] = {str(int(c)): int((G == c).sum()) for c in np.unique(G[occ])}
    lab, n = ndimage.label(occ)
    R['components_6'] = int(n)
    filled = ndimage.binary_fill_holes(occ)
    R['cavities'] = int((filled & ~occ).sum())
    R['mirror_diff'] = int((occ != occ[:, ::-1, :]).sum())
    R['displacement_t_at_wl'] = round(float(S[:, :, :wl].sum()) * (m ** 3) * 1.025, 2)
    R['hull_mass_t_est'] = round(R['cells'] * (m ** 3) * WOOD_T_PER_M3, 2)
    stations = []
    for x in plan['lines']['stations']:
        xi = x - x0
        row = {'x': x}
        for tag, z in (('bot', int(round(float(L.zb(x + 0.5))))), ('wl', wl), ('main', 48), ('upper', 70), ('top', int(L.top_z(x + 0.5)) - 1)):
            if 0 <= z < S.shape[2]:
                ys = np.nonzero(S[xi, :, z])[0]
                row[tag] = int(np.max(np.abs(ys + ylo - L.YC))) if len(ys) else None
            else:
                row[tag] = None
        stations.append(row)
    R['stations'] = stations
    return R


def draw_sheet(L, G, S, x0, ylo, plan, out_png):
    f18, f13, f11 = font(18), font(13), font(11)
    im = Image.new('RGB', (1920, 1200), (248, 244, 234))
    d = ImageDraw.Draw(im)
    d.text((36, 18), '明鄭一號大鳥船（1666 亞洲船⑤）新圖紙 01 — 40m 戰座大福船線形與橫剖面', fill=(25, 25, 25), font=f18)

    ox, oy = 60, 440
    sc = 3
    gx_arr, gy_arr, gz_arr = np.nonzero(G > 0)
    proj_xz = {}
    for xi, yi, zi in zip(gx_arr.tolist(), gy_arr.tolist(), gz_arr.tolist()):
        k = (xi, zi)
        if k not in proj_xz or yi > proj_xz[k][0]:
            proj_xz[k] = (yi, int(G[xi, yi, zi]))
    for (xi, zi), (_, c) in proj_xz.items():
        px = ox + xi * sc
        py = oy - zi * sc
        d.rectangle([px, py, px + sc - 1, py + sc - 1], fill=rgb(c))

    wl = int(plan['waterline']['z'])
    d.line([ox, oy - wl * sc, ox + G.shape[0] * sc, oy - wl * sc], fill=(30, 100, 210), width=2)
    d.text((ox + G.shape[0] * sc + 8, oy - wl * sc - 8), f'DWL z={wl} (4.2 m)', fill=(30, 100, 210), font=f11)
    for label, dz in (('底艙 z=12', 12), ('主砲甲板 z=48', 48), ('上戰棚 z=70', 70), ('尾樓 z=92', 92)):
        d.line([ox, oy - dz * sc, ox + G.shape[0] * sc, oy - dz * sc], fill=(140, 60, 40), width=1)
        d.text((ox + G.shape[0] * sc + 8, oy - dz * sc - 7), label, fill=(140, 60, 40), font=f11)
    for x in range(60, 460, 40):
        px = ox + (x - x0) * sc
        d.line([px, oy + 6, px, oy + 12], fill=(40, 40, 40), width=1)
        d.text((px - 8, oy + 14), str(x), fill=(40, 40, 40), font=f11)

    oy2 = 640
    d.text((ox, oy2 - 115), '半寬平面圖（水線下尖底收斂 vs 高尾樓與高昂艏端）', fill=(30, 30, 30), font=f13)
    for (xi, yi) in np.argwhere(S.any(axis=2)):
        px = ox + int(xi) * sc
        py = oy2 + (int(yi) + ylo - L.YC) * 2
        d.rectangle([px, py, px + sc - 1, py + 1], fill=(160, 120, 75))
    d.line([ox, oy2, ox + G.shape[0] * sc, oy2], fill=(60, 60, 60), width=1)

    oy3 = 1080
    d.text((ox, 780), '代表橫剖面（7 站：尖底龍骨、圓舭、雙戰棚與高尾樓）', fill=(30, 30, 30), font=f13)
    for idx, st in enumerate(plan['lines']['stations']):
        cx = 140 + idx * 250
        d.line([cx, 810, cx, oy3], fill=(40, 110, 200), width=1)
        d.line([cx - 105, oy3 - wl * 2, cx + 105, oy3 - wl * 2], fill=(40, 110, 200), width=1)
        xi = st - x0
        for yi, zi in np.argwhere(G[xi] > 0):
            c = int(G[xi, yi, zi])
            px = cx + (int(yi) + ylo - L.YC) * 2
            py = oy3 - int(zi) * 2
            d.rectangle([px, py, px + 1, py + 1], fill=rgb(c))
        d.text((cx - 18, oy3 + 10), f'x={st}', fill=(30, 30, 30), font=f11)

    im.save(out_png)


def main():
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a.split('=', 1)[1].split('=')
            probe = {k: float(v)}
        elif not a.startswith('--'):
            design = a

    plan = HL.load_plan(design)
    L, G, S, x0, ylo = build(plan, probe)
    R = readings(L, G, S, x0, ylo, plan)
    if probe:
        print(json.dumps({'probe': probe, 'readings': R}, ensure_ascii=False, indent=2))
        return

    hdir = os.path.join(design, 'masks', 'hull')
    os.makedirs(hdir, exist_ok=True)
    for old in os.listdir(hdir):
        if old.startswith('hull_') and old.endswith('.vox.txt'):
            os.remove(os.path.join(hdir, old))

    pts = np.argwhere(G > 0)
    n_tot = len(pts)
    n_chunks = max(1, (n_tot + CHUNK_MAX - 1) // CHUNK_MAX)
    chunks = []
    for ci in range(n_chunks):
        sub = pts[ci * CHUNK_MAX:(ci + 1) * CHUNK_MAX]
        fn = f'hull_{ci + 1:02d}.vox.txt'
        vp = os.path.join(hdir, fn)
        with open(vp, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 明鄭一號大鳥船 步驟 4：船殼清單 {ci + 1}/{n_chunks} x,y,z,color\n')
            for xi, yi, zi in sub.tolist():
                f.write(f'{xi + x0},{yi + ylo},{zi},{int(G[xi, yi, zi])}\n')
        chunks.append({'file': fn, 'cells': len(sub), 'sha256': hashlib.sha256(open(vp, 'rb').read()).hexdigest()})

    png_path = os.path.join(design, 'sheet01_lines_v1.png')
    draw_sheet(L, G, S, x0, ylo, plan, png_path)
    R['hull_chunks'] = chunks
    R['sheet01_sha256'] = hashlib.sha256(open(png_path, 'rb').read()).hexdigest()
    ver_path = os.path.join(design, 'verify_lines.json')
    with open(ver_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    print(json.dumps(R, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
