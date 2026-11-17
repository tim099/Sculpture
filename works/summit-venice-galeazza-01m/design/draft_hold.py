"""威尼斯 galeazza（TASK-1302）步驟 10：底艙地板、艏部彈藥庫、底艙梯口艙蓋，以及甲板上的模型位置（Ship_Magazine §8、Ship_Fittings §9.7）。

- 底艙地板（子作品 -hold，關聯 meta kind=deck、deck=hold、level −1）：船殼裡 z ≤ floor_top_z 的空氣全填實（壓艙，深色），
  每一柱最上一格鋪板；中線那道一格寬的縫一起填掉。x0..mag_x−1。
- 彈藥庫（子作品 -magazine，關聯 meta kind=magazine、powder_lb ＝ 桶數 × 100）：x mag_x、mag_x+1 兩格厚艙壁（後面橡木 136、
  裡面銅皮 168），門洞 5 格寬（|dy| ≤ door_half_w）、門檻在彈藥庫地板那一層；x ≥ mag_x 的底艙空氣 z ≤ mag_floor_top_z 填實、
  最上一格松木 177。固定點 blast（房間空氣重心最近的空氣格）、door（門洞地板中線、艙壁後面那一格）。
  火藥桶：憲法號 powder-barrel（0.02 m、scale 0.2、pivot 11,11,0），兩排、每格量腳下實心、桶身 5×5×6 格是空氣。
- 底艙梯口艙蓋（子作品 -hold-hatch，局部座標，外部模型掛在 -deck 裡，meta kind=door、open=up）：梯井外框每邊大一格、
  平貼在 corsia 頂上一格；鉸鏈 hinge-a → hinge-b 沿 +x、板往 +y ⇒ 往上掀。
- 甲板上的模型（不是格子，只量位置）：三盞艉燈（plan layout.lanterns）、羅經櫃（艉樓平台中線）—— 量腳下有沒有實心、身體在不在現況裡。
讀：船殼 01＋02（扣掉 hull_cut_01）、甲板、裝飾、桅；輸出 masks/hold/*.vox.txt、hold_meta.json、verify_hold.json。
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy import ndimage

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from lines import load_plan

PLANK, BALLAST, OAK, COPPER, PINE = 141, 68, 136, 168, 177
KEG = dict(work='basecamp-frigate-constitution-01m-powder-barrel', size=(22, 22, 27), mpv=0.02, scale=0.2, pivot=(11, 11, 0))
BINNACLE = dict(work='summit-night-falcon-01m-binnacle', size=(18, 26, 52), mpv=0.02, scale=0.2, pivot=(9, 13, 0))
LANTERN = dict(work='gura-tridente-01m-lantern', size=(17, 17, 36), mpv=0.05, pivot=(8.5, 8.5, 0))


def load(occ, p, val=None):
    a = np.loadtxt(p, delimiter=',', dtype=np.int32, ndmin=2)
    occ[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3] if val is None else val


def box_cells(at, piv, size, k):
    """模型外框蓋到的格（格心在框裡）：at ＝ pivot 落點（格座標，可帶小數），k ＝ 來源一格是幾個本作品格。"""
    lo = [at[i] - piv[i] * k for i in range(3)]
    hi = [lo[i] + size[i] * k for i in range(3)]
    rng = [range(int(np.floor(lo[i] + 0.5)), int(np.ceil(hi[i] - 0.5))) for i in range(3)]
    return lo, hi, rng


def main():
    plan = load_plan(D)
    NX, NY, NZ = plan['space']['hull']
    YC = plan['space']['yc']
    lay = {k: v['v'] for k, v in plan['layout'].items()}
    H = lay['hold']
    DZ = lay['deck_top_z']
    cor = lay['corsia']
    NZ = 360                                   # 組裝件的高（桅在船殼框 160 以上）
    occ = np.zeros((NX, NY, NZ), np.uint8)
    load(occ, D / 'masks/hull/hull_01.vox.txt')
    load(occ, D / 'masks/upper/upper_01.vox.txt')
    load(occ, D / 'masks/upper/hull_cut_01.vox.txt', 0)
    for sub in ('decks', 'deco', 'rig'):
        for p in sorted((D / 'masks' / sub).glob('*.vox.txt')):
            load(occ, p)
    # P 舷鏡像梯子
    for p in ('ladder_bow', 'ladder_stern'):
        a = np.loadtxt(D / f'masks/decks/{p}.vox.txt', delimiter=',', dtype=np.int32)
        occ[a[:, 0], 2 * YC - a[:, 1], a[:, 2]] = a[:, 3]

    # ── 底艙空氣：z 0..DZ−1 裡的空氣，連到外框（x、y 兩端、z 0）的是船外 ──
    sub = occ[:, :, :DZ] == 0
    lab, n = ndimage.label(sub)
    edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel()])))
    probe = lab[300, YC, 10]
    assert probe and probe not in edge, ('底艙空氣連到船外', probe)
    hold = lab == probe
    hold_full = np.zeros_like(occ, bool)
    hold_full[:, :, :DZ] = hold

    parts = {'floor': {}, 'magazine': {}}
    FZ, MX, MZ = H['floor_top_z'], H['mag_x'], H['mag_floor_top_z']
    # 地板（x0..MX−1）與彈藥庫地板（x ≥ MX）：填實，每一柱最上一格鋪板
    for x in range(H['x0'], H['x1'] + 1):
        top = FZ if x < MX else MZ
        part = 'floor' if x < MX else 'magazine'
        for y in range(NY):
            zs = [z for z in range(top + 1) if hold_full[x, y, z]]
            for z in zs:
                parts[part][(x, y, z)] = (PLANK if part == 'floor' else PINE) if z == zs[-1] else BALLAST
    # 艙壁：x MX（橡木）、MX+1（銅皮），門洞 |dy| ≤ dhw、z MZ+1..door_top_z
    dhw = H['door_half_w']
    for x, c in ((MX, OAK), (MX + 1, COPPER)):
        for y in range(NY):
            for z in range(MZ + 1, DZ):
                if not hold_full[x, y, z]:
                    continue
                if abs(y - YC) <= dhw and z <= H['door_top_z']:
                    continue
                parts['magazine'][(x, y, z)] = c

    union = occ > 0
    for cells in parts.values():
        for k in cells:
            union[k] = True
    # 封閉空腔（≤ 50 格填實，Ship_Magazine 最後一條）
    voids = ndimage.binary_fill_holes(np.pad(union, 1))[1:-1, 1:-1, 1:-1] & ~union
    vl, nv = ndimage.label(voids)
    filled = 0
    big = []
    for i in range(1, nv + 1):
        cells = np.argwhere(vl == i)
        if len(cells) <= 50:
            for x, y, z in cells:
                part = 'magazine' if x >= MX else 'floor'
                parts[part][(int(x), int(y), int(z))] = BALLAST
                union[x, y, z] = True
            filled += len(cells)
        else:
            big.append([len(cells)] + [int(v) for v in cells.min(0)] + [int(v) for v in cells.max(0)])

    # ── 彈藥庫房間空氣、固定點 ──
    room = hold_full.copy()
    room[:MX + 2] = False
    room &= ~union
    rl, rn = ndimage.label(room)
    sizes = ndimage.sum(room, rl, range(1, rn + 1))
    main_lab = int(np.argmax(sizes)) + 1
    rc = np.argwhere(rl == main_lab)
    cen = rc.mean(0)
    blast = [int(v) for v in rc[np.argmin(((rc - cen) ** 2).sum(1))]]
    door = [MX, YC, MZ + 1]
    assert not union[tuple(door)] and union[MX, YC, MZ], door

    # ── 火藥桶：候選位置照順序試，取前 kegs 個「腳下全實心、桶身全空氣」的（底是 V 形：x 474 在 z 8 只剩 |dy| ≤ 3）——
    #    先沿兩舷靠門那兩排（中間讓出門口進來的走道），放不下再往前排中線 ──
    k = KEG['scale']                          # scale ＝ 來源一格是幾個本作品格（22 × 0.2 ＝ 4.4 格 ＝ 0.44 m ＝ 22 × 0.02 m）
    cand = [(MX + 5, YC - 6), (MX + 5, YC + 5), (MX + 10, YC - 6), (MX + 10, YC + 5),
            (MX + 10, YC), (MX + 15, YC - 6), (MX + 15, YC + 5), (MX + 15, YC), (MX + 20, YC)]
    kegs, tried = [], []
    for x, y in cand:
        at = [x + 0.5, y + 0.5, MZ + 1]
        lo, hi, rng = box_cells(at, KEG['pivot'], KEG['size'], k)
        body = [(a, b, c) for a in rng[0] for b in rng[1] for c in rng[2]]
        foot = [(a, b, MZ) for a in rng[0] for b in rng[1]]
        clash = sum(1 for q in body if union[q])
        unsup = sum(1 for q in foot if not union[q])
        near = any(abs(at[0] - g['at'][0]) < 4.6 and abs(at[1] - g['at'][1]) < 4.6 for g in kegs)
        tried.append(dict(at=at, clash=clash, unsupported=unsup, overlaps_keg=near))
        if not clash and not unsup and not near and len(kegs) < H['kegs']:
            kegs.append(dict(name=f'keg-{len(kegs) + 1}', at=at))
    bad = [] if len(kegs) == H['kegs'] else [f'只放得下 {len(kegs)} 桶']

    # ── 底艙梯口艙蓋 ──
    deck_main = {tuple(r[:3]) for r in np.loadtxt(D / 'masks/decks/deck_main.vox.txt', delimiter=',', dtype=np.int32)}
    corsia = {tuple(r[:3]) for r in np.loadtxt(D / 'masks/decks/corsia.vox.txt', delimiter=',', dtype=np.int32)}
    xa, xb = lay['stern_castle']['x_front'], lay['bow_castle']['x_back']
    well = [(x, y) for x in range(xa + 6, xb - 7) for y in range(YC - cor['half_w'], YC + cor['half_w'] + 1)
            if (x, y, cor['top_z']) not in corsia and (x, y, DZ) not in deck_main]
    wx = [w[0] for w in well]
    wy = [w[1] for w in well]
    hx0, hx1, hy0, hy1 = min(wx) - 1, max(wx) + 1, min(wy) - 1, max(wy) + 1
    hz = cor['top_z'] + 1
    hatch = {}
    for x in range(hx0, hx1 + 1):
        for y in range(hy0, hy1 + 1):
            rim = x in (hx0, hx1) or y in (hy0, hy1)
            hatch[(x - hx0, y - hy0, 0)] = BALLAST if rim else PLANK
    hatch_clash = sum(1 for (x, y, z) in hatch if union[x + hx0, y + hy0, z + hz])
    under_open = sum(1 for (x, y) in well if not union[x, y, cor['top_z']])

    # ── 甲板上的模型：艉燈三盞、羅經櫃 ──
    def check_model(m, at, scale):
        kk = scale
        lo, hi, rng = box_cells(at, m['pivot'], m['size'], kk)
        body = [(a, b, c) for a in rng[0] for b in rng[1] for c in rng[2]]
        clash = sum(1 for q in body if union[q])
        foot = union[int(at[0]), int(at[1]), int(at[2]) - 1]
        return dict(at=at, scale=scale, clash=clash, foot_solid=bool(foot), box=[[round(v, 2) for v in lo], [round(v, 2) for v in hi]])

    L = lay['lanterns']
    lanterns = {'艉燈-中': check_model(LANTERN, L['centre'], L['scale'])}
    for nm, at in zip(('艉燈-P', '艉燈-S'), L['sides']):        # +y 是 S 舷（艏樓梯 bow-S 在 y 172–176）
        lanterns[nm] = check_model(LANTERN, at, L['scale'])
    binnacle = check_model(BINNACLE, [140.5, YC + 0.5, lay['stern_castle']['deck_z'] + 1], 0.2)

    out = D / 'masks/hold'
    out.mkdir(parents=True, exist_ok=True)
    shas = {}
    for name, cells in (('floor', parts['floor']), ('magazine', parts['magazine']), ('hatch', hatch)):
        body = ''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(cells.items())).encode('ascii')
        (out / f'{name}.vox.txt').write_bytes(body)
        shas[name] = hashlib.sha256(body).hexdigest()[:16]
    floor_meta = f'{H["x0"]}:{FZ + 1},{MX - 1}:{FZ + 1}'
    meta = dict(
        hold=dict(kind='deck', deck='hold', level=-1, name='底艙', floor=floor_meta, thick=1),
        magazine=dict(kind='magazine', powder_lb=100 * len(kegs)),
        anchors=dict(blast=blast, door=door),
        kegs=[dict(name=g['name'], at=g['at']) for g in kegs],
        keg=KEG,
        hatch=dict(at=[hx0, hy0, hz], size=[hx1 - hx0 + 1, hy1 - hy0 + 1, 1], hinge_a=[0, 0, 0], hinge_b=[hx1 - hx0, 0, 0]),
        lanterns={k2: dict(at=v['at'], scale=v['scale']) for k2, v in lanterns.items()},
        lantern=LANTERN,
        binnacle=dict(at=binnacle['at'], **BINNACLE),
    )
    stats = dict(parts={k2: len(v) for k2, v in parts.items()}, hatch=len(hatch), voids_filled=filled, voids_big=big,
                 room_air=int(len(rc)), blast=blast, door=door, kegs=kegs, kegs_tried=tried, kegs_bad=bad,
                 well_cells=len(well), well_open_at_corsia_top=under_open, hatch_clash=hatch_clash,
                 lanterns=lanterns, binnacle=binnacle, sha16=shas)
    (D / 'hold_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (D / 'verify_hold.json').write_text(json.dumps(stats, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    main()
