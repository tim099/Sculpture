# 炎羽號（kiara-phoenix-01m）新圖紙 02 骨架與肋骨（Phase 2: Framing & Backbone）
# 龍骨、艏柱、艉柱、死木、肋骨站與橫向艉板
# 用法：python -I -X utf8 -B draft_hull.py <design 資料夾>

import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC, FONT

NX, NY, NZ = 576, 181, 100


def build(plan):
    H = Hull(plan)
    F = plan['framing']
    x = np.arange(NX) + 0.5; z = np.arange(NZ) + 0.5
    X, Z = np.meshgrid(x, z, indexing='ij')
    hb = H.hb(X, Z)                                                     # (NX, NZ)
    dy = np.abs(np.arange(NY) - YC).astype(float)
    hbn = np.nan_to_num(hb, nan=-1)
    solid = (hbn[:, None, :] >= 0) & (dy[None, :, None] <= hbn[:, None, :])

    # 頂面開口：每一欄最上面那一層往上複製
    top_ext = 8
    ext = np.concatenate([solid, np.zeros((NX, NY, top_ext), bool)], axis=2)
    for xi in range(NX):
        col = solid[xi]
        if not col.any(): continue
        zt = np.where(col.any(axis=0))[0].max()
        for k in range(1, top_ext + 1):
            if zt + k < NZ + top_ext: ext[xi, :, zt + k] |= col[:, zt]
    d = ndimage.distance_transform_edt(ext)[:, :, :NZ]

    Y = np.arange(NY)[None, :, None]
    Xc = (np.arange(NX) + 0.5)[:, None, None]; Zc = (np.arange(NZ) + 0.5)[None, None, :]
    DY = np.abs(Y - YC)
    own = np.zeros((NX, NY, NZ), np.int16)        # 0 空；>0 木料編號
    names = [None]

    def claim(name, mask):
        m = mask & solid & (own == 0)
        names.append(name); own[m] = len(names) - 1
        return int(m.sum())

    # ── 骨架 ──
    claim('keel', (Zc < H.rab) & (Xc >= H.kx0) & (Xc <= H.kx1) & (DY <= F['backbone_half']))
    claim('stem', (DY <= F['backbone_half']) & (Xc >= H.stem_face(Zc) - H.st_sid))
    claim('sternpost', (DY <= F['backbone_half']) & (Xc <= H.post_face(Zc) + H.sp_sid) & (Zc <= H.deck_side(Xc)))
    dw = np.nan_to_num(hb, nan=99)[:, None, :] <= F['deadwood_hb']
    claim('deadwood_aft', dw & (Xc < H.xm))
    claim('deadwood_fwd', dw & (Xc >= H.xm))

    # deadwood 碎片貼在相鄰柱子上
    for dn, host in (('deadwood_aft', 'sternpost'), ('deadwood_fwd', 'stem')):
        m = own == names.index(dn)
        lab_, n_ = ndimage.label(m)
        if n_ > 1:
            sz = ndimage.sum(m, lab_, range(1, n_ + 1)); keep = int(np.argmax(sz)) + 1
            own[m & (lab_ != keep)] = names.index(host)

    # ── 肋骨層 ──
    layer = solid & (d > 1.0) & (d <= 1.0 + F['moulded']) & (own == 0)
    st_ = F['stern']
    aft = np.broadcast_to(np.arange(NX)[:, None, None] < st_['x'], (NX, NY, NZ))
    sp, sd, x0 = F['spacing'], F['sided'], F['station_x']
    xi = np.arange(NX)[:, None, None]
    stations = sorted(set(((np.arange(NX) - x0) // sp).tolist()))
    for k in stations:
        xs = x0 + k * sp
        m = layer & ~aft & (xi >= xs) & (xi < xs + sd)
        if m.any(): claim('f%+03d' % k, m)
    zi = np.arange(NZ)[None, None, :]
    for k in range(-10, 20):
        zs = H.trz + k * st_['spacing']
        m = layer & aft & (zi >= zs) & (zi < zs + st_['sided'])
        if m.any(): claim('tr%+03d' % k, m)

    # 確保 6 連通
    lab, n = ndimage.label(own > 0)
    main = lab[tuple(np.argwhere(own == names.index('keel'))[0])]
    stray = (own > 0) & (lab != main)
    dropped = {}
    for i in np.unique(own[stray]):
        dropped[names[i]] = int((stray & (own == i)).sum())
    own[stray] = 0
    return H, solid, d, own, names, layer, aft, dropped


def piece_lists(own, names, colors):
    out = []
    for i in range(1, len(names)):
        name = names[i]
        coords = np.argwhere(own == i)
        if coords.size == 0: continue
        coords = sorted(coords.tolist(), key=lambda t: (t[0], t[1], t[2]))
        if name in ('keel', 'stem', 'sternpost', 'deadwood_aft', 'deadwood_fwd'):
            c = colors['backbone']
        elif name.startswith('tr'):
            c = colors.get('counter', colors['frame'])
        else:
            c = colors['frame']
        out.append((name, coords, c))
    return out


def main():
    design_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    plan_path = os.path.join(design_dir, "plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    H, solid, d, own, names, layer, aft, dropped = build(plan)
    pieces = piece_lists(own, names, plan['framing']['colors'])

    work_dir = os.path.dirname(os.path.abspath(plan_path))
    parent_dir = os.path.dirname(work_dir)
    masks_dir = os.path.join(parent_dir, "masks", "frames")
    os.makedirs(masks_dir, exist_ok=True)

    manifest = []
    total_vox = 0
    for name, coords, color in pieces:
        fn = os.path.join(masks_dir, f"{name}.vox.txt")
        with open(fn, "w", encoding="utf-8") as f:
            for x, y, z in coords:
                f.write(f"{x},{y},{z},{color}\n")
        manifest.append({
            "name": name,
            "count": len(coords),
            "color": color,
            "path": fn
        })
        total_vox += len(coords)

    verify_path = os.path.join(work_dir, "verify_hull.json")
    with open(verify_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_pieces": len(pieces),
            "total_voxels": total_vox,
            "dropped_fragments": dropped,
            "manifest": manifest
        }, f, indent=2, ensure_ascii=False)

    print(f"✓ 骨架已生成: 共 {len(pieces)} 根木料，{total_vox} 格 voxel，已寫入 {masks_dir}")
    print(f"✓ 驗證檔已保存: {verify_path}")


if __name__ == "__main__":
    main()
