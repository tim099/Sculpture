# 新圖紙 07 船頭船尾骨架 v1（階段六，TASK-0538）：plan.json ends ⇒ 兩頭的肋骨、wing transom、stern timbers 的 3D 格子清單、對照圖、verify_ends.json。
# 用法：python -I draft_ends.py <design 資料夾>
#   · 清單給 `sculpture op=stampvox at=0,0,0`；片片互不重疊，也不跟階段一～五重疊。
#   · 兩頭的肋骨跟階段五同一套（frame_cells），但沒有底肋頭條件（兩頭沒有底肋，肋骨腳直接貼 deadwood／apron）。
#   · 落地順序：肋骨（船尾、船頭）→ wing transom → stern timbers（後面的跳過前面已經有的格）。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_frames import Ctx, frame_cells, load_prev   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def main():
    design = sys.argv[1]
    ctx = Ctx(design)
    plan, R, B, ship = ctx.plan, ctx.R, ctx.B, ctx.ship
    cpm, X0, Zk, zs = ctx.cpm, ctx.X0, ctx.Zk, ctx.zs
    E, Fr = plan['ends'], plan['frames']
    occ = load_prev(design)
    for fn in sorted(os.listdir(os.path.join(design, 'masks', 'frames'))):
        for ln in open(os.path.join(design, 'masks', 'frames', fn), encoding='utf-8'):
            if ln[0] != '#':
                occ.add(tuple(int(v) for v in ln.split(',')[:3]))
    stage5 = set(occ)

    parts = {}                                             # 名字 → 格清單（照落地順序）
    info = {}
    for lo, hi in (E['aft_n'], E['fore_n']):
        for n in range(lo, hi + 1):
            cells, xf, i0 = frame_cells(ctx, n, Fr['sided_cells'], Fr['color'], occ, use_head=False, segments=True)
            if not cells:
                info['r%+03d' % n] = {'x_frame_plate': round(xf, 4), 'cells': 0, 'note': '這個肋位船殼外（沒有格）'}
                continue
            name = 'r%+03d' % n
            parts[name] = cells
            occ |= {(a, b, c) for a, b, c, _ in cells}
            info[name] = {'x_frame_plate': round(xf, 4), 'X_cells': [i0, i0 + Fr['sided_cells'] - 1]}

    # 船尾輪廓（tuck 以上）：每一層 z 的船尾端 x
    tuck = ship.tuck_z
    so = ship.stern_outline
    z_hi = float(ship.top(float(so[-1, 0])))
    WT, ST = E['wing_transom'], E['stern_timbers']

    def stern_cells(kind):
        out = []
        for Zc in range(int(Zk + tuck * cpm), int(Zk + z_hi * cpm) + 2):
            z = (Zc + 0.5 - Zk) / cpm
            if z < tuck or z > z_hi:
                continue
            xa = float(ship.stern_x_of_z(min(z, so[-1, 1])))
            if kind == 'wing_transom':
                if z > tuck + WT['depth_m']:
                    continue
                thick = WT['thick_m']
            else:
                thick = ST['thick_m']
            for Xc in range(int(np.floor(X0 + xa * cpm)) - 1, int(X0 + (xa + thick) * cpm) + 2):
                x = (Xc + 0.5 - X0) / cpm
                if not (xa <= x < xa + thick):
                    continue
                if z > float(ship.top(x)):
                    continue
                col = ctx.hg.column(x)
                okz = col >= 0
                if not okz.any() or z > zs[okz].max() or z < zs[okz].min():
                    continue
                hb_z = float(np.interp(z, zs[okz], col[okz]))
                for dy in range(0, int(hb_z * cpm) + 2):
                    if dy / cpm > hb_z:
                        continue
                    if kind == 'stern_timbers':
                        r = dy % ST['spacing_cells']
                        if not (r <= 2 or r >= ST['spacing_cells'] - 2):
                            continue
                    for y in {160 + dy, 160 - dy}:
                        if (Xc, y, Zc) not in occ:
                            out.append((Xc, y, Zc, WT['color'] if kind == 'wing_transom' else ST['color']))
        return out

    for kind in ('wing_transom', 'stern_timbers'):
        cl = stern_cells(kind)
        parts[kind] = cl
        occ |= {(a, b, c) for a, b, c, _ in cl}

    mdir = os.path.join(design, 'masks', 'ends')
    os.makedirs(mdir, exist_ok=True)
    ver = {'k': round(ctx.k, 5), 'order': list(parts), 'parts': {}}
    seen = set()
    for name, cl in parts.items():
        xyz = {(a, b, c) for a, b, c, _ in cl}
        assert len(xyz) == len(cl), name + ' 有重複格'
        assert not (xyz & seen) and not (xyz & stage5), name + ' 重疊'
        seen |= xyz
        with open(os.path.join(mdir, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 夜燈號 {name}（新圖紙 07 v1，draft_ends.py 產）—— x,y,z,color；stampvox at=0,0,0\n')
            for c in cl:
                f.write('%d,%d,%d,%d\n' % c)
        a = np.array(sorted(xyz))
        mir = sum(1 for (x, y, z) in xyz if (x, 320 - y, z) not in xyz)
        d = {'file': f'masks/ends/{name}.vox.txt', 'cells': len(cl), 'x': [int(a[:, 0].min()), int(a[:, 0].max())],
             'z': [int(a[:, 2].min()), int(a[:, 2].max())], 'mirror_missing': mir}
        d.update(info.get(name, {}))
        ver['parts'][name] = d
    ver['empty_frames'] = {k_: v for k_, v in info.items() if v.get('cells') == 0}
    ver['total_cells'] = len(seen)
    # 連通（含封閉空腔之前的粗看：元件數）
    allc = seen | stage5
    from collections import deque
    comps = []
    left = set(allc)
    while left:
        s0 = left.pop()
        q, comp = deque([s0]), [s0]
        while q:
            c = q.popleft()
            for dd in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nb = (c[0] + dd[0], c[1] + dd[1], c[2] + dd[2])
                if nb in left:
                    left.discard(nb)
                    q.append(nb)
                    comp.append(nb)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    ver['components'] = {'count': len(comps), 'sizes': [len(c) for c in comps[:5]],
                         'small': [sorted(c)[:6] for c in comps[1:6]]}

    # 對照圖一：落在船尾站上的四片（16、20、22、24 ＝ 肋位 −16、−20、−22、−24）中間那一欄疊橫切面圖左半
    base = Image.open(os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768',
                                   'PlLI_Engelsk_Ostindiefarare.tif')).convert('L')
    pxm = R['px_per_m']
    bpc, bpk = B['body_plan']['centre_px'], B['body_plan']['keel_top_py']
    bx0, by0, bx1, by1, s3 = 7450, 1750, 8720, 4130, 0.45
    Bm = base.crop((bx0, by0, bx1, by1)).resize((int((bx1 - bx0) * s3), int((by1 - by0) * s3)), Image.LANCZOS).convert('RGBA')
    ov = Image.new('RGBA', Bm.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cols = {-16: (220, 0, 0, 130), -20: (0, 120, 220, 130), -22: (0, 160, 60, 130), -24: (200, 120, 0, 150)}
    for n, colr in cols.items():
        name = 'r%+03d' % n
        Xc = info[name]['X_cells'][0] + 1
        for (x, y, z, c) in parts[name]:
            if x != Xc or y > 160:
                continue
            h0 = (160 - y) / cpm - 0.5 / cpm
            z0 = (z - Zk) / cpm
            d.rectangle([(bpc - (h0 + 1 / cpm) * pxm - bx0) * s3, (bpk - (z0 + 1 / cpm) * pxm - by0) * s3,
                         (bpc - h0 * pxm - bx0) * s3, (bpk - z0 * pxm - by0) * s3], fill=colr)
    Bm = Image.alpha_composite(Bm, ov).convert('RGB')
    Bm.save(os.path.join(design, 'compare07_ends_body_v1.png'))
    # 對照圖二：側面投影（整件作品 y ≤ 160 的格，最外那層）疊 Pl. LI 船尾、船頭
    x0p, kt = R['px_per_m'] and R['datum']['x0_px'], R['datum']['keel_top_py']
    toP = lambda Xc, Zc: (x0p + (Xc - X0) / cpm * pxm, kt - (Zc - Zk) / cpm * pxm)
    prof = {}
    for (x, y, z) in allc:
        prof[(x, z)] = 1 if (x, y, z) in seen else prof.get((x, z), 0)
    outs = ['compare07_ends_body_v1.png']
    for name, (px0, py0, px1, py1, sc) in {'stern': (900, 3500, 3600, 7000, 0.3), 'bow': (8600, 3800, 11000, 7000, 0.3)}.items():
        Aim = base.crop((px0, py0, px1, py1)).resize((int((px1 - px0) * sc), int((py1 - py0) * sc)), Image.LANCZOS).convert('RGBA')
        ov = Image.new('RGBA', Aim.size, (0, 0, 0, 0))
        dd = ImageDraw.Draw(ov)
        for (x, z), new in prof.items():
            a0, a1 = toP(x, z + 1), toP(x + 1, z)
            dd.rectangle([(a0[0] - px0) * sc, (a0[1] - py0) * sc, (a1[0] - px0) * sc, (a1[1] - py0) * sc],
                         fill=(220, 0, 0, 70) if new else (0, 90, 230, 45))
        Aim = Image.alpha_composite(Aim, ov).convert('RGB')
        p = os.path.join(design, f'compare07_ends_{name}_v1.png')
        Aim.save(p)
        outs.append(os.path.basename(p))
    ver['outputs'] = outs
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1, default=lambda v: v.item())
    open(os.path.join(design, 'verify_ends.json'), 'w', encoding='utf-8').write(dump(ver))
    print(json.dumps({'total_cells': ver['total_cells'], 'components': ver['components'], 'empty': list(ver['empty_frames'])}, ensure_ascii=False))
    for n_, v in ver['parts'].items():
        print(n_, v['cells'], 'x', v['x'], 'z', v['z'], 'mir', v['mirror_missing'])


if __name__ == '__main__':
    main()
