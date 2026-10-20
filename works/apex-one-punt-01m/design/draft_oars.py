# 蓬特號 新圖紙 04（TASK-0754）：槳 —— 每舷 15 支（浮雕；C09／W10），引用持火號上層槳（erina-dromon-01m-oar-upper：4.7 m、1 人、0.05 m、scale 0.5）
#   ⇒ oars_placement.json（每支 at／rotate／mirror／meta）、verify_oars.json
#   用法：python -I -X utf8 draft_oars.py [--drop=S3] [--sink=S5:3]   （反向對照：少擺一支／一支往下沉幾格）
#   · 槳座 pivot ＝ 那一站舷頂最外面那一格的上一格（槳柄靠在舷緣上；埃及船沒有槳架、槳手站著划 C09）。
#   · 每支照舷弧補傾角（造船規格 §9.10.2 第 3 點）：rotate x ＝ 右舷 −δ、左舷 mirror=y 時 ＋δ；δ 用元件裡 pivot → 槳葉中心那兩格的實際角度算。
#   · 量：模型格心＋八角不落在船的實心（船殼、甲板、平台、叉柱、梯子、桅）；槳葉中心離水線；槳手照遊戲的找法站得住（seat 往下 6 格內：那一格空、腳下實心、頭上 14 格空）。
import sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio
from draft_lines import SX, SY, V
from draft_deck import load_list

sys.stdout.reconfigure(encoding='utf-8')
SRC = 'erina-dromon-01m-oar-upper'
PIV = np.array([3.5, 26.5, 40.5])            # 元件的 pivot 格心（持火號同一個）
SCALE = 0.5
SEAT = np.array([2.5, 4.5, 29.5])
SZ2 = 180


def occupancy(plan):
    G = load_list(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'))
    occ = np.zeros((SX, SY, SZ2), bool)
    occ[:, :, :G.shape[2]] = G > 0
    for f in ('deck/deck_main', 'deck/deck_hold', 'deck/platform_aft', 'deck/platform_fwd', 'deck/crutches', 'deck/ladders', 'rig/mast'):
        a = np.loadtxt(os.path.join(HERE, 'masks', f + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
        occ[a[:, 0], a[:, 1], a[:, 2]] = True
    return occ


def rotx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def world(q, at, rot, mirror):
    v = (np.asarray(q, float) - PIV) * SCALE
    if mirror:
        v[..., 1] = -v[..., 1]
    return np.asarray(at) + v @ rotx(rot).T


def main():
    args = sys.argv[1:]
    drop = next((a.split('=')[1] for a in args if a.startswith('--drop=')), None)
    sink = next((a.split('=')[1] for a in args if a.startswith('--sink=')), None)
    plan = HL.load_plan()
    K = {k: V(v) for k, v in plan['oars'].items()}
    YC = plan['space']['yc']
    wl = plan['waterline']['z']
    occ = occupancy(plan)
    hull = load_list(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt')) > 0
    cells = wio.export_list(SRC, None)
    # 槳葉中心：槳葉那一段（y ≥ blade_y0）格心的平均
    bl = cells[cells[:, 1] >= K['blade_y0']][:, :3] + 0.5
    bc = bl.mean(axis=0)
    ang0 = math.degrees(math.atan2(PIV[2] - bc[2], bc[1] - PIV[1]))     # 元件裡 pivot → 槳葉中心往下的角度
    Lb = math.hypot(bc[1] - PIV[1], PIV[2] - bc[2]) * SCALE
    corners = np.array([[dx, dy, dz] for dx in (-.5, .5) for dy in (-.5, .5) for dz in (-.5, .5)])
    pts_local = np.concatenate([cells[:, :3] + 0.5] + [cells[:, :3] + 0.5 + c for c in corners])
    out, R = [], {'component': SRC, 'blade_center_local': bc.round(2).tolist(), 'angle0_deg': round(ang0, 2), 'pivot_to_blade_m': round(Lb * 0.1, 2), 'oars': []}
    xs = [K['x0'] + K['pitch'] * i for i in range(K['per_side'])]
    for side, s in (('S', 1), ('P', -1)):
        for i, x in enumerate(xs, 1):
            nm = 'oar-%s%02d' % (side, i)
            if drop == '%s%d' % (side, i):
                continue
            # 舷頂最外面那一格：這一站船殼最高那一層裡 |dy| 最大的
            col = np.argwhere(hull[x, :, :])
            zt = col[:, 1].max()
            ys = col[col[:, 1] == zt][:, 0]
            yo = ys.max() if s > 0 else ys.min()
            pz = zt + 1
            if sink and sink.split(':')[0] == '%s%d' % (side, i):
                pz -= int(sink.split(':')[1])
            at = [float(x + 0.5), float(yo + 0.5), float(pz + 0.8)]            # 槳柄下緣在 pivot 下 0.75 格 ⇒ 抬 0.3 格才不咬進舷頂（v1 每支 2–3 點）
            want = math.degrees(math.asin(min(1, (at[2] - (wl + 0.5)) / Lb)))
            d = want - ang0
            rot = round(-d if s > 0 else d, 2)
            W = world(pts_local, at, rot, s < 0)
            ci = np.floor(W).astype(int)
            ok = (ci[:, 0] >= 0) & (ci[:, 0] < SX) & (ci[:, 1] >= 0) & (ci[:, 1] < SY) & (ci[:, 2] >= 0) & (ci[:, 2] < SZ2)
            hit = int(occ[ci[ok, 0], ci[ok, 1], ci[ok, 2]].sum())
            bcw = world(bc, at, rot, s < 0)
            st = np.floor(world(SEAT, at, rot, s < 0)).astype(int)
            stand = None
            for dz in range(0, 7):
                z = st[2] - dz
                if not occ[st[0], st[1], z] and occ[st[0], st[1], z - 1] and not occ[st[0], st[1], z:z + 14].any():
                    stand = [int(st[0]), int(st[1]), int(z)]
                    break
            # 遊戲的掛點：pivot 旁 8 格內有船殼
            p = np.floor(at).astype(int)
            near = bool(hull[p[0] - 8:p[0] + 9, max(0, p[1] - 8):p[1] + 9, max(0, p[2] - 8):p[2] + 9].any())
            out.append({'name': nm, 'at': at, 'pivot': PIV.tolist(), 'rotate': [rot, 0, 0], 'scale': SCALE, 'mirror': 'y' if s < 0 else '',
                        'meta': {'kind': 'oar', 'rowers': 1, 'side': side, 'stroke_deg': 30, 'dip_deg': 12}})
            R['oars'].append({'name': nm, 'pivot_z': int(pz), 'rot': rot, 'collide': hit, 'blade_center_z_m': round((bcw[2] - (wl + 0.5)) * 0.1, 3),
                              'seat': st.tolist(), 'stand': stand, 'hang': near})
    R['count'] = {'S': sum(1 for o in out if o['meta']['side'] == 'S'), 'P': sum(1 for o in out if o['meta']['side'] == 'P')}
    R['collide_total'] = sum(o['collide'] for o in R['oars'])
    R['stand_ok'] = sum(1 for o in R['oars'] if o['stand'])
    R['blade_z_range_m'] = [min(o['blade_center_z_m'] for o in R['oars']), max(o['blade_center_z_m'] for o in R['oars'])]
    R['hang_ok'] = sum(1 for o in R['oars'] if o['hang'])
    if drop or sink:
        print(json.dumps({'drop': drop, 'sink': sink, 'count': R['count'], 'collide_total': R['collide_total'],
                          'collide_by': {o['name']: o['collide'] for o in R['oars'] if o['collide']}}, ensure_ascii=False))
        return
    with open(os.path.join(HERE, 'oars_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_oars.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'oars'}, ensure_ascii=False))
    for o in R['oars']:
        print(o)


if __name__ == '__main__':
    main()
