# 沙船 新圖紙 01（TASK-1313 步驟 3）：線形 ⇒ 圖紙 sheet01_lines_v1.png、讀數 verify_lines.json、船殼清單 masks/hull/hull_01.vox.txt
#   出處：kiara-tunis-sandal-01m/design/draft_lines.py ＋ calli-cosecha-01m/design/draft_lines.py
#   用法：python -I -X utf8 draft_lines.py <design 資料夾> [--probe=half_beam=+3]
#   · 只讀 plan.json、不碰作品。--probe 時只算讀數不寫清單或圖。
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
EXTRA = 35
WOOD_T_PER_M3 = 0.60  # 松／杉傳統船殼密度約 0.60 t/m³〔設計估〕


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
    L = HL.Lines(plan, probe)
    zmax = int(math.ceil(L.top_max)) + 2
    x0 = int(math.floor(L.x_aft(L.top_max))) - 3
    x1 = int(math.ceil(L.x_fwd(L.sh_fwd))) + 3
    half = int(math.ceil(L.B)) + 6
    ylo = L.YC - half
    yhi = L.YC + half

    hb = plan['hull_build']
    C = {k: V(v) for k, v in hb['colors'].items()}
    wall = int(V(hb['wall']))
    wl = plan['waterline']['z']

    S = L.solid(x0, x1, zmax, 0)[:, ylo:yhi + 1, :]
    Sx = np.pad(L.solid(x0, x1, zmax + EXTRA, EXTRA)[:, ylo:yhi + 1, :], 1)
    core = Sx
    for _ in range(wall):
        core = ndimage.binary_erosion(core, structure=np.ones((3, 3, 3), bool))
    shell = S & ~core[1:-1, 1:-1, 1:zmax + 2]

    G = np.zeros(S.shape, np.uint8)
    G[shell] = C['hull']

    # touch_out：只看「會露到船外」的表面格（往外相鄰非 Sx）
    touch_out = ndimage.binary_dilation(~Sx, structure=ndimage.generate_binary_structure(3, 1))[1:-1, 1:-1, 1:zmax + 2]
    zz = np.arange(zmax + 1)[None, None, :]
    G[shell & ~touch_out] = C['inner']
    G[shell & touch_out & (zz < wl)] = C['below']

    # 貼著舷頂、方艏／方艉緣的深木壓條與朱紅飾帶
    xs = np.arange(x0, x1 + 1) + 0.5
    ztop = np.floor(L.top_z(xs) - 0.5).astype(int)
    for xi, x in enumerate(range(x0, x1 + 1)):
        zt = int(ztop[xi])
        if 0 <= zt <= zmax:
            row_top = G[xi, :, zt]
            row_top[row_top > 0] = C['trim']
            if zt - 1 >= wl:
                sub = G[xi, :, zt - 1]
                sub[(sub > 0) & touch_out[xi, :, zt - 1]] = C['red'] if (x <= 88 or x >= 216) else C['trim']
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
    R['flat_bottom_cells'] = int(S[:, :, 0].any(axis=1).sum())
    R['flat_bottom_max_w_cells'] = int(S[:, :, 0].sum(axis=1).max())
    R['bow_transom_w_cells'] = int(occ[int(L.xf) - x0, :, :].any(axis=1).sum())
    R['stern_transom_w_cells'] = int(occ[int(L.xa) - x0, :, :].any(axis=1).sum())
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
    # 代表站讀數（船尾 60、中段 148、船首 220）
    stations = []
    for x in (60, 100, 148, 196, 224):
        xi = x - x0
        row = {'x': x}
        for tag, z in (('bot', 0), ('wl', wl), ('main', 23), ('top', int(L.top_z(x + 0.5)) - 1)):
            ys = np.nonzero(S[xi, :, z])[0]
            row[tag] = int(np.max(np.abs(ys + ylo - L.YC))) if len(ys) else None
        stations.append(row)
    R['stations'] = stations
    return R


def draw(L, G, S, x0, ylo, plan, R, path):
    sc = 4
    nx, ny, nz = G.shape
    padL, padT = 50, 75
    side_h = nz * sc
    plan_h = (ny // 2) * sc + 24
    body_h = nz * sc
    W = max(nx * sc + padL * 2 + 120, 1060)
    H = padT + side_h + 50 + plan_h + 50 + body_h + 150
    im = Image.new('RGB', (W, H), (248, 244, 234))
    d = ImageDraw.Draw(im)
    f20, f14, f12 = font(20), font(14), font(12)
    d.text((padL, 14), plan['title'] + '　(0.1 m/格；船頭在右)', fill=(25, 20, 15), font=f20)
    d.text((padL, 42), f"LOA {R['loa_m']} m ({R['loa_cells']} 格, x {R['loa_x'][0]}..{R['loa_x'][1]}) | 寬 {R['beam_m']} m | 吃水 {plan['waterline']['z']*0.1:.1f} m | 排水量 {R['displacement_t_at_wl']} t | 元件 {R['components_6']} | 空腔 {R['cavities']}", fill=(60, 50, 40), font=f14)

    # ① 側面剪影
    oy = padT
    for xi in range(nx):
        for z in np.nonzero(G[xi].any(axis=0))[0]:
            ys = np.nonzero(G[xi, :, z])[0]
            c = rgb(int(G[xi, ys[0], z]))
            X0, Y0 = padL + xi * sc, oy + (nz - 1 - z) * sc
            d.rectangle([X0, Y0, X0 + sc - 1, Y0 + sc - 1], fill=c)
    wl = plan['waterline']['z']
    yw = oy + (nz - wl) * sc
    d.line([padL, yw, padL + nx * sc, yw], fill=(20, 90, 200), width=2)
    d.text((padL + nx * sc + 6, yw - 8), f'DWL z={wl} (1.4 m)', fill=(20, 90, 200), font=f12)
    for nm, zd in plan['decks_preview'].items():
        yd = oy + (nz - zd) * sc
        d.line([padL, yd, padL + nx * sc, yd], fill=(190, 40, 20))
        d.text((padL + nx * sc + 6, yd - 8), f'{nm} z={zd}', fill=(190, 40, 20), font=f12)
    for x in range((x0 // 20 + 1) * 20, x0 + nx, 20):
        X = padL + (x - x0) * sc
        d.line([X, oy + side_h, X, oy + side_h + 5], fill=(40, 40, 40))
        d.text((X - 8, oy + side_h + 7), str(x), fill=(60, 60, 60), font=f12)
    d.text((padL, oy - 18), '① 側面（白底＝桐油灰 z<14，紅邊＝艏艉飾帶）', fill=(0, 0, 0), font=f14)

    # ② 半寬圖（右舷）
    oy2 = oy + side_h + 45
    d.text((padL, oy2 - 18), '② 半寬圖（右舷：平底／水線／主甲板／舷頂）', fill=(0, 0, 0), font=f14)
    cy = oy2 + 12
    d.line([padL, cy, padL + nx * sc, cy], fill=(0, 0, 0))
    yc_local = L.YC - ylo
    for z, col_line, lbl in ((0, (120, 120, 120), '底 z=0'), (wl - 1, (20, 90, 200), '水線'), (23, (180, 90, 0), '主甲板')):
        pts = []
        for xi in range(nx):
            ys = np.nonzero(S[xi, yc_local:, z])[0]
            if len(ys):
                pts.append((padL + xi * sc, cy + ys[-1] * sc))
        if len(pts) > 1:
            d.line(pts, fill=col_line, width=2)
    # 舷頂外緣
    pts_top = []
    for xi in range(nx):
        zt = min(nz - 1, max(0, int(L.top_z(x0 + xi + 0.5)) - 1))
        ys = np.nonzero(S[xi, yc_local:, zt])[0]
        if len(ys):
            pts_top.append((padL + xi * sc, cy + ys[-1] * sc))
    if len(pts_top) > 1:
        d.line(pts_top, fill=(180, 0, 0), width=2)

    # ③ 五站橫剖面（平底硬舭外張驗證）
    oy3 = oy2 + plan_h + 40
    d.text((padL, oy3 - 18), '③ 五站橫剖面（外板＋內襯 wall=2；平底無龍骨、外張舷側）', fill=(0, 0, 0), font=f14)
    st_xs = (60, 100, 148, 196, 224)
    for k, sx in enumerate(st_xs):
        ox = padL + k * 190
        xi = sx - x0
        for y in range(ny):
            for z in range(nz):
                if G[xi, y, z]:
                    d.rectangle([ox + y * 3, oy3 + (nz - 1 - z) * 3, ox + y * 3 + 2, oy3 + (nz - z) * 3 - 1], fill=rgb(int(G[xi, y, z])))
        d.line([ox, oy3 + (nz - wl) * 3, ox + ny * 3, oy3 + (nz - wl) * 3], fill=(20, 90, 200))
        d.text((ox + 20, oy3 + nz * 3 + 6), f'x={sx}', fill=(20, 20, 20), font=f12)

    d.text((padL, H - 34), f"平底最寬 {R['flat_bottom_max_w_cells']*0.1:.1f} m | 方艏寬 {R['bow_transom_w_cells']*0.1:.1f} m | 方艉寬 {R['stern_transom_w_cells']*0.1:.1f} m | 格數 {R['cells']} | 鏡像差 {R['mirror_diff']}", fill=(40, 30, 20), font=f14)
    im.save(path)


def main():
    design = HERE
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=')
            probe[k] = float(v)
        elif not a.startswith('--'):
            design = a
    plan = HL.load_plan(design)
    L, G, S, x0, ylo = build(plan, probe or None)
    R = readings(L, G, S, x0, ylo, plan)
    if probe:
        print(json.dumps({'probe': probe, **R}, ensure_ascii=False))
        return

    os.makedirs(os.path.join(design, 'masks', 'hull'), exist_ok=True)
    pts = np.argwhere(G > 0)
    mask_path = os.path.join(design, 'masks', 'hull', 'hull_01.vox.txt')
    with open(mask_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 沙船船殼 hull_01（draft_lines.py）x,y,z,color —— at 0,0,0\n')
        for x, y, z in pts:
            f.write(f'{x + x0},{y + ylo},{z},{G[x, y, z]}\n')
    sha = hashlib.sha256(open(mask_path, 'rb').read()).hexdigest()
    R['mask_file'] = 'masks/hull/hull_01.vox.txt'
    R['mask_sha256'] = sha
    with open(os.path.join(design, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    draw(L, G, S, x0, ylo, plan, R, os.path.join(design, 'sheet01_lines_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
