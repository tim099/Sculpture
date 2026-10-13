# 新圖紙 02 龍骨 v1（階段一，TASK-0538）：plan.json keel ⇒ 護龍骨與龍骨的 3D 格子清單、Pl. LI 對照圖、verify_keel.json。
# 用法：python -I draft_keel.py <design 資料夾>
#   · 清單給 `sculpture op=stampvox at=0,0,0`（每行 x,y,z,color）；先護龍骨、再龍骨（兩份不重疊）。
#   · 格 i 佔 [i, i+1)；格中心 i+0.5 落在 [X(後端), X(前端)] 之內才放。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_lines as DL   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def keel_cells(plan, ship, X, cpm):
    K = plan['keel']
    Zk = plan['scale']['Z_of_keel_top']
    y0, y1 = K['y']
    out = {}
    for part in ('shoe', 'keel'):
        P = K[part]
        cells = []
        for z in range(P['z'][0], P['z'][1] + 1):
            zc = (z + 0.5 - Zk) / cpm                     # 這層格中心的底圖高度（龍骨頂 ＝ 0，往下為負）
            xa = float(X(ship.sternpost_x(zc)))
            xf = float(X(P['fore_x']))
            i0 = math.ceil(xa - 0.5)
            i1 = math.floor(xf - 0.5)
            for x in range(i0, i1 + 1):
                for y in range(y0, y1 + 1):
                    cells.append((x, y, z, P['color']))
        out[part] = cells
    return out


def main():
    design = sys.argv[1]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    cells = keel_cells(plan, ship, X, cpm)

    mdir = os.path.join(design, 'masks', 'keel')
    os.makedirs(mdir, exist_ok=True)
    ver = {'k': round(k, 5), 'cells_per_m_plate': round(cpm, 4), 'parts': {}}
    allc = set()
    for part, cl in cells.items():
        path = os.path.join(mdir, part + '.vox.txt')
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 夜燈號 {part}（新圖紙 02 龍骨 v1，draft_keel.py 產）—— x,y,z,color；stampvox at=0,0,0\n')
            for c in cl:
                f.write('%d,%d,%d,%d\n' % c)
        xyz = {(a, b, c) for a, b, c, _ in cl}
        assert len(xyz) == len(cl), part + ' 清單有重複格'
        assert not (xyz & allc), part + ' 跟前一份重疊'
        allc |= xyz
        a = np.array([c[:3] for c in cl])
        rows = {}
        for x, y, z, _ in cl:
            r = rows.setdefault(z, [x, x])
            r[0], r[1] = min(r[0], x), max(r[1], x)
        ver['parts'][part] = {'file': f'masks/keel/{part}.vox.txt', 'cells': len(cl), 'color': cl[0][3],
                              'x': [int(a[:, 0].min()), int(a[:, 0].max())], 'y': [int(a[:, 1].min()), int(a[:, 1].max())],
                              'z': [int(a[:, 2].min()), int(a[:, 2].max())],
                              'rows_x': {str(z): rows[z] for z in sorted(rows)}}
    ver['total_cells'] = len(allc)
    ver['length_m'] = round((max(c[0] for c in allc) + 1 - min(c[0] for c in allc)) / 10, 2)

    # ── 對照圖：作品格（側面投影）換回底圖像素，疊在 Pl. LI 上（船尾一張、船頭一張、全長一張）
    base = Image.open(os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768',
                                   'PlLI_Engelsk_Ostindiefarare.tif')).convert('L')
    pxm, x0p, kt = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']
    Sc = plan['scale']
    # 作品 (X, Z) → 底圖 px：x = (X − X0)/cpm、z = (Z − Zk)/cpm
    toP = lambda Xc, Zc: (x0p + (Xc - Sc['X_of_x0']) / cpm * pxm, kt - (Zc - Sc['Z_of_keel_top']) / cpm * pxm)
    prof = {}
    for x, y, z, c in cells['shoe'] + cells['keel']:
        prof[(x, z)] = c
    outs = []
    for name, (px0, py0, px1, py1, sc) in {'aft': (1450, 6550, 2150, 6950, 1.4), 'fore': (9050, 6550, 9750, 6950, 1.4),
                                           'full': (1300, 6600, 10100, 6950, 0.2)}.items():
        A = base.crop((px0, py0, px1, py1)).resize((int((px1 - px0) * sc), int((py1 - py0) * sc)), Image.LANCZOS).convert('RGB')
        ov = Image.new('RGBA', A.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for (x, z), c in prof.items():
            a0 = toP(x, z + 1)
            a1 = toP(x + 1, z)
            box = [(a0[0] - px0) * sc, (a0[1] - py0) * sc, (a1[0] - px0) * sc, (a1[1] - py0) * sc]
            col = (230, 120, 0, 90) if c == 104 else (220, 0, 0, 70)
            d.rectangle(box, fill=col, outline=(160, 0, 0, 160) if sc > 1 else None)
        A = Image.alpha_composite(A.convert('RGBA'), ov).convert('RGB')
        p = os.path.join(design, f'compare02_keel_{name}_v1.png')
        A.save(p)
        outs.append(os.path.basename(p))
    ver['outputs'] = outs
    json.dump(ver, open(os.path.join(design, 'verify_keel.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k_: v for k_, v in ver.items() if k_ != 'parts'}, ensure_ascii=False))
    for part, v in ver['parts'].items():
        print(part, v['cells'], 'x', v['x'], 'z', v['z'], v['rows_x'])


if __name__ == '__main__':
    main()
