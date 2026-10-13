# 新圖紙 07 桅檣（TASK-0529 階段七）：plan.json 的 masts ⇒ 前桅、主桅、艏斜桅、channels（一舷）的清單、船殼的艏斜桅開口、verify_masts.json。
# 用法：python -I -X utf8 -B draft_masts.py <design 資料夾>
#   · 現況照 nf_state.state_after('stage6') 重建。
#   · 桅：軸過甲板那一點（桅孔中心、甲板面）往後傾 rake；下桅（桅座 → 桅頂）＋ top（trestletrees 緊貼那一層桅杆最外的格 ±1、crosstrees、平台）＋ cap
#     ＋ 中桅（軸往前 offset，從平台上一格到頂）＋ 中桅 crosstrees ＋ 頂桅＋ truck。每一節是沿軸的錐（半徑線性收）。
#     桅座：桅腳下 keel 上面那幾層船艙空氣補一塊（踩在龍骨與底肋上）。
#   · 艏斜桅：從甲板上的 heel 往前上 angle 度，半徑線性收；船殼跟它相交的格刻掉（舷牆頂、艏柱頭 —— carvevox 帶原色守門），船頭作品不准碰。
#     jib-boom 在艏斜桅前段上方平行；艏斜桅 cap。
#   · channels（一舷、固定框）：兩根桅旁，舷牆頂下 3 格起 2 格厚，從船殼外面往外 out 格，兩頭收圓角。
#   · 固定點（給下一階段的帆桁與繩）：寫在 verify_masts.json 的 rig_points（世界座標）。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC
from nf_state import state_after, occupancy, NX, NY, NZ


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def cone(p0, p1, r0, r1, shape):
    """p0→p1 的錐（半徑 r0→r1），格心在裡面的格。"""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); ab = p1 - p0; L2 = float(ab @ ab)
    rm = max(r0, r1)
    lo = np.maximum(np.floor(np.minimum(p0, p1) - rm - 1).astype(int), 0)
    hi = np.minimum(np.ceil(np.maximum(p0, p1) + rm + 2).astype(int), shape)
    gx, gy, gz = np.meshgrid(*[np.arange(lo[i], hi[i]) + 0.5 for i in range(3)], indexing='ij')
    t = ((gx - p0[0]) * ab[0] + (gy - p0[1]) * ab[1] + (gz - p0[2]) * ab[2]) / L2
    inside_t = (t >= 0) & (t <= 1)
    tc = np.clip(t, 0, 1)
    px, py, pz = p0[0] + tc * ab[0], p0[1] + tc * ab[1], p0[2] + tc * ab[2]
    r = r0 + (r1 - r0) * tc
    m = np.zeros(shape, bool)
    m[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] = inside_t & (((gx - px) ** 2 + (gy - py) ** 2 + (gz - pz) ** 2) <= r * r)
    return m


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    M = plan['masts']; C = M['colors']; H = Hull(plan)
    W = state_after(d, 'stage6'); occ = occupancy(W)
    shape = occ.shape
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(NZ)[None, None, :]
    xg = np.arange(NX) + 0.5; zg = np.arange(80) + 0.5
    hbv = H.hb(*np.meshgrid(xg, zg, indexing='ij'))
    vol = np.zeros(shape, bool)
    vol[:, :, :80] = (~np.isnan(hbv))[:, None, :] & (np.abs(Y - YC) <= np.nan_to_num(hbv, nan=-1)[:, None, :])
    out = {}; rig = {}
    # ── 桅 ──
    for name in ('fore', 'main'):
        S = M[name]; mx = S['x']; a = math.radians(S['rake_deg'])
        zdeck = int(np.nonzero(W['main'][mx, YC + 6, :])[0].max()) + 1          # 甲板面（板頂）—— 從甲板作品量
        ax = lambda z, off=0.0: (mx + 0.5 - (z - zdeck) * math.tan(a) + off, YC + 0.5, z)
        col = np.zeros(shape, np.int16)
        # 桅座
        step = (X >= mx - S['step_half_x']) & (X <= mx + S['step_half_x']) & (np.abs(Y - YC) <= S['step_half_y']) & (Z >= S['step_z'][0]) & (Z <= S['step_z'][1]) & vol & ~occ
        col[step] = C['step']
        z0 = S['step_z'][1] + 1
        lower = cone(ax(z0), ax(S['lower_head_z'] + 1), S['r_lower'][0], S['r_lower'][1], shape)
        col[lower & ~occ] = C['spar']
        zt = S['top_z']                                                       # top 平台那一層
        lay = np.argwhere(lower[:, :, zt - 1])
        ymin, ymax = lay[:, 1].min(), lay[:, 1].max(); xmin, xmax = lay[:, 0].min(), lay[:, 0].max()
        # trestletrees：緊貼那一層桅杆最外的格 ±1（憲法號 round(±4.56) 空一格、top 浮空的坑）
        cx = ax(zt)[0]
        tr = (X >= int(cx - S['top_x'] / 2)) & (X <= int(cx + S['top_x'] / 2)) & ((Y == ymin - 1) | (Y == ymax + 1)) & (Z == zt - 1)
        cr = ((X == int(cx - S['top_x'] / 2) + 1) | (X == int(cx + S['top_x'] / 2) - 1)) & (np.abs(Y - YC) <= S['top_y'] // 2) & (Z == zt - 1)
        plat = (X >= int(cx - S['top_x'] / 2)) & (X <= int(cx + S['top_x'] / 2)) & (np.abs(Y - YC) <= S['top_y'] // 2) & (Z == zt)
        col[(tr | cr) & ~lower & ~occ] = C['iron']
        col[plat & ~lower & ~occ] = C['top']
        # 中桅（往前 offset）
        rl = S['r_lower'][1]; rt = S['r_top'][0]
        off_t = rl + rt + 1.0
        tm = cone(ax(zt + 1, off_t), ax(S['topmast_head_z'] + 1, off_t), S['r_top'][0], S['r_top'][1], shape)
        # cap：下桅頂兩層，包住下桅頂與中桅
        hz = S['lower_head_z']
        cap = (X >= int(ax(hz)[0] - rl - 1)) & (X <= int(ax(hz, off_t)[0] + rt + 1)) & (np.abs(Y - YC) <= int(math.ceil(max(rl, rt))) + 1) & (Z >= hz - 1) & (Z <= hz)
        col[cap & ~lower & ~tm & ~occ] = C['iron']
        col[tm & ~occ & (col == 0)] = C['spar']
        # 中桅 crosstrees
        zc = S['topmast_head_z'] - S['tm_doubling']
        lay2 = np.argwhere(tm[:, :, zc])
        cx2 = ax(zc, off_t)[0]
        ct = (np.abs(X + 0.5 - cx2) <= S['tm_cross_x'] / 2) & ((Y == lay2[:, 1].min() - 1) | (Y == lay2[:, 1].max() + 1)) & (Z == zc)
        cc = (np.abs(X + 0.5 - cx2) <= 1) & (np.abs(Y - YC) <= S['tm_cross_y'] // 2) & (Z == zc + 1) & ~tm
        col[(ct | cc) & ~occ & (col == 0)] = C['iron']
        # 頂桅
        rt1 = S['r_top'][1]; rg = S['r_tg'][0]
        off_g = off_t + rt1 + rg + 1.0
        tg = cone(ax(zc + 1, off_g), ax(S['truck_z'], off_g), S['r_tg'][0], S['r_tg'][1], shape)
        # 中桅 cap：中桅頂兩層，從中桅後緣包到頂桅前緣 —— 🩸 第一版沒有：頂桅往前偏 3.1 格、兩節半徑和 2.1，中間空一格 ⇒ 頂桅浮在半空
        th = S['topmast_head_z']
        tcap = (X >= int(ax(th, off_t)[0] - rt1 - 1)) & (X <= int(ax(th, off_g)[0] + S['r_tg'][0] + 1)) & (np.abs(Y - YC) <= int(math.ceil(rt1)) + 1) & (Z >= th - 1) & (Z <= th)
        col[tcap & ~tm & ~tg & ~occ & (col == 0)] = C['iron']
        col[tg & ~occ & (col == 0)] = C['spar']
        truck = cone(ax(S['truck_z'], off_g), ax(S['truck_z'] + 2, off_g), 1.3, 1.3, shape)
        col[truck & ~occ & (col == 0)] = C['iron']
        out['mast_' + name] = col
        rig.setdefault('_dropped', {})[name] = int(((lower | tm | tg) & occ).sum())   # 桅身跟現況撞到被丟的格（桅孔夠大的話應為 0）
        rig[name] = {'deck': [round(v, 2) for v in ax(zdeck)], 'lower_head': [round(v, 2) for v in ax(hz + 1)], 'top_platform_z': zt,
                     'topmast_head': [round(v, 2) for v in ax(S['topmast_head_z'] + 1, off_t)], 'truck': [round(v, 2) for v in ax(S['truck_z'] + 2, off_g)],
                     'topmast_offset_x': round(off_t, 2), 'topgallant_offset_x': round(off_g, 2), 'zdeck': zdeck}
    # ── 艏斜桅 ──
    B = M['bowsprit']; ang = math.radians(B['angle_deg'])
    hx, hz0 = B['heel_x'], None
    zdk = int(np.nonzero(W['main'][hx, YC + 4, :])[0].max()) + 1
    p0 = np.array([hx + 0.5, YC + 0.5, zdk + B['r'][0]])
    dirv = np.array([math.cos(ang), 0.0, math.sin(ang)])
    p1 = p0 + dirv * B['length']
    bs = cone(p0, p1, B['r'][0], B['r'][1], shape)
    jb0 = p0 + dirv * B['jib_from'] + np.array([0, 0, 1]) * (B['r'][1] + B['jib_r'][0] + 0.6) / math.cos(ang)
    jb1 = jb0 + dirv * B['jib_length']
    jb = cone(jb0, jb1, B['jib_r'][0], B['jib_r'][1], shape)
    bcap = cone(p1 - dirv * 1.5, p1 + dirv * 0.5, B['r'][1] + 1.0, B['r'][1] + 1.0, shape) | cone(jb0 + dirv * (B['length'] - B['jib_from'] - 1.5), jb0 + dirv * (B['length'] - B['jib_from'] + 0.5), B['jib_r'][0] + 1.0, B['jib_r'][0] + 1.0, shape)
    hull_hits = bs & (W['hull'] > 0)
    other_hits = (bs | jb | bcap) & occ & ~(W['hull'] > 0)
    colb = np.zeros(shape, np.int16)
    colb[bs] = C['spar']; colb[jb & ~bs] = C['spar']; colb[bcap & ~bs & ~jb] = C['iron']
    colb[other_hits] = 0
    colb[(W['hull'] > 0) & ~bs] = 0
    out['bowsprit'] = colb
    rig['bowsprit'] = {'heel': [round(v, 2) for v in p0], 'end': [round(v, 2) for v in p1], 'jib_end': [round(v, 2) for v in jb1]}
    # ── channels（右舷，世界座標）──
    CH = M['channels']; chan = np.zeros(shape, np.int16)
    occ_now = occ.copy(); occ_now[hull_hits] = False
    for name in ('fore', 'main'):
        xa, xb = CH[name]['x']
        ztop = int(math.floor(min(float(H.top(x + 0.5)) for x in range(xa, xb + 1))))
        zs = range(ztop - CH['below_top'] - CH['thick'] + 1, ztop - CH['below_top'] + 1)
        for xx in range(xa, xb + 1):
            e = min(xx - xa, xb - xx)
            o = CH['out'] if e >= 2 else CH['out'] - (2 - e)
            for zz in zs:
                ys = np.nonzero(W['hull'][xx, YC:, zz])[0]
                if len(ys) == 0: continue
                yo = YC + ys.max()
                chan[xx, yo + 1:yo + 1 + o, zz] = C['channel']
        rig['channel_' + name] = {'x': [xa, xb], 'z': [zs[0], zs[-1]]}
    chan[occ_now & (chan > 0)] = 0
    for k in ('mast_fore', 'mast_main', 'bowsprit'):
        chan[(out[k] > 0) & (chan > 0)] = 0
    # ── 清單 ──
    subs = {'hull': [], 'mast_fore': [], 'mast_main': [], 'bowsprit': [], 'channels': []}
    for sub in subs:
        od = os.path.join(d, 'masks', 'masts', sub); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od): os.remove(os.path.join(od, f))
    def emit(sub, name, pts, cols, op='stampvox', origin=(0, 0, 0)):
        if len(pts) == 0: return
        text = lst(np.asarray(pts) - np.asarray(origin), cols)
        fn = name + '.vox.txt'
        open(os.path.join(d, 'masks', 'masts', sub, fn), 'w', encoding='utf-8', newline='\n').write(text)
        subs[sub].append({'name': name, 'op': op, 'file': 'masks/masts/' + sub + '/' + fn, 'at': [0, 0, 0], 'voxels': int(len(pts)),
                          'origin_world': list(origin), 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})
    hp = np.argwhere(hull_hits); emit('hull', 'bowsprit_opening_carve', hp, W['hull'][tuple(hp.T)], op='carvevox')
    for k in ('mast_fore', 'mast_main', 'bowsprit'):
        p = np.argwhere(out[k] > 0); emit(k, k, p, out[k][tuple(p.T)])
    cp = np.argwhere(chan > 0); emit('channels', 'channels', cp, chan[tuple(cp.T)], origin=tuple(CH['frame_at']))
    # ── 讀數 ──
    after = occ.copy(); after[hull_hits] = False
    newv = (out['mast_fore'] > 0) | (out['mast_main'] > 0) | (out['bowsprit'] > 0) | (chan > 0) | (chan[:, ::-1, :] > 0)
    ov = int((newv & after).sum())
    allv = after | newv
    lab, nc = ndimage.label(allv)
    holes = int((ndimage.binary_fill_holes(allv) & ~allv).sum())
    comp = {k: int(ndimage.label(out[k] > 0)[1]) for k in ('mast_fore', 'mast_main', 'bowsprit')}
    comp['channels'] = int(ndimage.label(chan > 0)[1])
    cl = np.argwhere(chan > 0) - np.asarray(CH['frame_at'])
    R = {'stamp_order': subs, 'rig_points': rig,
         'counts': {'hull_carve': int(hull_hits.sum()), 'mast_fore': int((out['mast_fore'] > 0).sum()), 'mast_main': int((out['mast_main'] > 0).sum()),
                    'bowsprit': int((out['bowsprit'] > 0).sum()), 'channels_one_side': int((chan > 0).sum()), 'other_hits_dropped': int(other_hits.sum()),
                    'assembly_after': int(allv.sum())},
         'structure': {'components_assembly': int(nc), 'enclosed_cavity_assembly': holes, 'mirror_shape_assembly': int((allv != allv[:, ::-1, :]).sum()),
                       'overlap_new_vs_now': ov, 'components_parts': comp},
         'channels_frame': {'at': CH['frame_at'], 'size': CH['frame_size'], 'local_min': cl.min(0).tolist() if len(cl) else None,
                            'local_max': cl.max(0).tolist() if len(cl) else None, 'mirror_at_y': 161 - CH['frame_at'][1] - CH['frame_size'][1]}}
    with open(os.path.join(d, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: R[k] for k in ('counts', 'structure', 'channels_frame', 'rig_points')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
