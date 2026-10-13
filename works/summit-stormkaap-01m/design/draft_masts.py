# 新圖紙 06b 桅、船首斜桅、桅頂平台、channels（TASK-0547 階段六）：plan.json 的 masts ⇒ 四件桅子作品＋ channels 子作品（右舷一份、左舷走 mirror=y）
#   的清單、固定點、verify_masts.json、sheet06_masts_v1.png。
# 用法：python -I -X utf8 -B draft_masts.py <design 資料夾>
#   · 尺寸：Witsen 1671（1690 版 DBNL 抄本查證）× 1.194；見 references/history_voc_retourschip.md「查證」那一節。桅位沿用階段四的甲板開孔。
#   · 桅是直的（不傾斜）。下桅：圓截面（直徑 d_low）從桅腳（量現況：腳下那一格的上面）到 下桅頂；桅頂段（head）在上；
#     上桅：直徑 d_top，從 hounds（下桅頂 − head）起、往船頭偏 off_top 格（doubling：上桅在下桅頭的前面），長 L_top；上上桅同理。
#     cap：下桅頂那一層，把下桅頭與上桅接起來的一塊。
#   · 桅頂平台（top）：hounds 那一層，圓、半徑 top_r，一格厚＋外緣一圈 1 格高的欄；中間留桅與上桅的位置。
#   · 船首斜桅：從桅腳點沿仰角 steeve 往前上方的圓柱（直徑 d），尖端立一根垂直的斜桅頂桅。
#   · channels（右舷）：每根桅一塊，x 範圍照階段四留給它的 channels_avoid，z ＝ floor(sheer) − 2，往外伸 width 格，1 格厚；外緣一排加厚 1 格。
#   · 所有格都只放在現況（sk_state 重播到 stage6a）空的地方；跟任何一件重疊 ⇒ 讀數報出來。
#   · 固定點（給帆桁、繩）：每根桅 hounds（平台那一層的桅心）、cap、上桅頂、上上桅頂；斜桅尖端。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, font
from sk_state import state_after

NZ6 = 576


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def pal(k):
    return (int(((k >> 5) & 7) * 255 / 7), int(((k >> 2) & 7) * 255 / 7), int((k & 3) * 255 / 3))


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    M = plan['masts']; C = M['colors']
    H = Hull(plan); NX, NY, YC = H.NX, H.NY, H.YC
    W = state_after(d, 'stage6a', nz=200)
    occ200 = np.zeros(W['hull'].shape, bool)
    for k, v in W.items():
        if not k.endswith('_model'): occ200 |= v > 0
    occ = np.zeros((NX, NY, NZ6), bool); occ[:, :, :200] = occ200
    yc = YC + 0.5
    works, anchors, info = {}, {}, {}

    def disk(arr, xc, yc_, z, r, col):
        for x in range(int(math.floor(xc - r)), int(math.ceil(xc + r)) + 1):
            for y in range(int(math.floor(yc_ - r)), int(math.ceil(yc_ + r)) + 1):
                if (x + 0.5 - xc) ** 2 + (y + 0.5 - yc_) ** 2 <= r * r and not occ[x, y, z]:
                    arr[x, y, z] = col

    for m in M['list']:
        arr = np.zeros((NX, NY, NZ6), np.int16)
        xm = m['x']; r_low = m['d_low'] / 2
        # 桅腳：腳印裡現況最高的那一格（z < 60）的上面一格
        fp = [(x, y) for x in range(int(xm - r_low) - 1, int(xm + r_low) + 2) for y in range(YC - 6, YC + 7)
              if (x + 0.5 - xm) ** 2 + (y + 0.5 - yc) ** 2 <= r_low * r_low]
        heel = 1 + max(int(np.nonzero(occ[x, y, :60])[0].max()) if occ[x, y, :60].any() else -1 for x, y in fp)
        if m.get('step_z'): heel = m['step_z']
        top_low = heel + m['L_low']
        hounds = top_low - m['head']
        for z in range(heel, top_low):
            disk(arr, xm, yc, z, r_low, C['mast'] if (z - heel) % m['hoop_every'] else C['hoop'])
        # 上桅（在下桅頭前面）
        xt = xm + m['off_top']; r_top = m['d_top'] / 2
        top_top = hounds + m['L_top']
        for z in range(hounds, top_top):
            disk(arr, xt, yc, z, r_top, C['mast'])
        # cap：下桅頂那一層，把下桅頭跟上桅接起來
        for z in range(top_low, top_low + 2):
            for x in range(int(math.floor(xm - r_low)), int(math.ceil(xt + r_top)) + 1):
                for y in range(int(math.floor(yc - r_low)), int(math.ceil(yc + r_low)) + 1):
                    if abs(y + 0.5 - yc) <= r_low and not occ[x, y, z] and arr[x, y, z] == 0: arr[x, y, z] = C['iron']
        # 上上桅（在上桅頭前面）
        top_tg = None
        if m.get('L_tg'):
            xg = xt + m['off_tg']; r_tg = m['d_tg'] / 2
            hounds_t = top_top - m['head_top']
            top_tg = hounds_t + m['L_tg']
            for z in range(hounds_t, top_tg):
                disk(arr, xg, yc, z, r_tg, C['mast'])
            for z in range(top_top, top_top + 1):
                for x in range(int(math.floor(xt - r_top)), int(math.ceil(xg + r_tg)) + 1):
                    for y in range(int(math.floor(yc - r_top)), int(math.ceil(yc + r_top)) + 1):
                        if abs(y + 0.5 - yc) <= r_top and arr[x, y, z] == 0: arr[x, y, z] = C['iron']
            # 上桅頭的小平台（crosstrees）
            for x in range(int(xt - m['xtree']), int(xt + m['xtree']) + 1):
                for y in range(YC - m['xtree'], YC + m['xtree'] + 1):
                    if (abs(x + 0.5 - xt) < 1.0 or abs(y - YC) < 1) and arr[x, y, hounds_t - 1] == 0: arr[x, y, hounds_t - 1] = C['top']
        # 桅頂平台（top）：hounds 那一層下面一格，圓、外緣一圈欄
        zt_ = hounds - 1
        tr = m['top_r']
        for x in range(int(xm - tr) - 1, int(xm + tr) + 2):
            for y in range(int(yc - tr) - 1, int(yc + tr) + 2):
                rr = math.hypot(x + 0.5 - xm, y + 0.5 - yc)
                if rr <= tr and arr[x, y, zt_] == 0: arr[x, y, zt_] = C['top']
                if tr - 1.0 < rr <= tr and arr[x, y, zt_ + 1] == 0: arr[x, y, zt_ + 1] = C['top_rim']
        works[m['name']] = arr
        anchors[m['name']] = {'hounds': [int(math.floor(xm)), YC, hounds], 'cap': [int(math.floor(xm)), YC, top_low],
                              'topmast_head': [int(math.floor(xt)), YC, top_top - 1]}
        if top_tg: anchors[m['name']]['tgmast_head'] = [int(math.floor(xt + m['off_tg'])), YC, top_tg - 1]
        info[m['name']] = {'heel_z': heel, 'lower_top_z': top_low, 'hounds_z': hounds, 'topmast_top_z': top_top, 'tg_top_z': top_tg,
                           'height_above_dwl_m': round(((top_tg or top_top) - H.dwl) * 0.1, 2)}
    # ── 船首斜桅 ──（也要躲開剛長出來的桅：🩸 第一版只躲船上原有的格 ⇒ 跟前桅重疊 1 格）
    B = M['bowsprit']
    for k_, a_ in works.items(): occ |= a_ > 0
    arr = np.zeros((NX, NY, NZ6), np.int16)
    th = math.radians(B['steeve']); ux, uz = math.cos(th), math.sin(th)
    x0b, z0b = B['heel']
    r_b = B['d'] / 2
    n = int(B['L'] * 2)
    for i in range(n + 1):
        s = i / 2
        cx, cz = x0b + ux * s, z0b + uz * s
        rr = r_b * (1 - 0.3 * s / B['L'])
        for x in range(int(cx - rr) - 1, int(cx + rr) + 2):
            for z in range(int(cz - rr) - 1, int(cz + rr) + 2):
                for y in range(int(yc - rr) - 1, int(yc + rr) + 2):
                    # 到軸的距離（軸在 x–z 平面裡）
                    px, pz = x + 0.5 - x0b, z + 0.5 - z0b
                    t = px * ux + pz * uz
                    if t < 0 or t > B['L']: continue
                    dd = math.hypot(px - t * ux, pz - t * uz)
                    if math.hypot(dd, y + 0.5 - yc) <= rr and not occ[x, y, z] and arr[x, y, z] == 0:
                        arr[x, y, z] = C['mast'] if int(t) % 24 else C['hoop']
    tipx, tipz = x0b + ux * B['L'], z0b + uz * B['L']
    for z in range(int(tipz) - 2, int(tipz) + B['L_sprit_top']):
        disk(arr, tipx, yc, z, B['d_sprit_top'] / 2, C['mast'])
    works['bowsprit'] = arr
    occ[:, :, :] = False; occ[:, :, :200] = occ200          # channels 照舊只躲船上原有的格（桅不會長到船殼外面）
    anchors['bowsprit'] = {'tip': [int(tipx), YC, int(tipz)], 'sprit_top_head': [int(tipx), YC, int(tipz) + B['L_sprit_top'] - 1]}
    info['bowsprit'] = {'heel': B['heel'], 'tip_xz': [round(tipx, 2), round(tipz, 2)], 'sprit_top_z': int(tipz) + B['L_sprit_top']}
    # ── channels（右舷）──
    Ch = M['channels']
    ch = np.zeros((NX, NY, NZ6), np.int16)
    side = (occ200[:, YC:, :]).copy()
    zch = lambda x: int(math.floor(H.sheer(x + 0.5))) + Ch['dz']
    for name, (xa, xb) in plan['decks']['masts_provisional']['channels_avoid'].items():
        for x in range(xa, xb + 1):
            z = zch(x)
            ys = np.nonzero(side[x, :, z])[0]
            if len(ys) == 0: continue
            y0 = YC + int(ys.max())
            # 舷弧升階的地方往下補一格（跟兩旁較低那一欄齊）—— 🩸 第一版前桅那塊散成 5 段，段與段只靠邊角相接（階段四甲板的同一個病）
            zlo = min(z, zch(max(x - 1, xa)), zch(min(x + 1, xb)))
            for zz in range(zlo, z + 1):
                for k in range(1, Ch['width'] + 1):
                    if not occ[x, y0 + k, zz]: ch[x, y0 + k, zz] = C['channel']
            for zz in (z + 1,):
                if not occ[x, y0 + Ch['width'], zz]: ch[x, y0 + Ch['width'], zz] = C['channel']
    works['channels'] = ch

    # ── 讀數 ──
    od = os.path.join(d, 'masks', 'masts'); os.makedirs(od, exist_ok=True)
    for f in os.listdir(od): os.remove(os.path.join(od, f))
    order = {}
    for k, arr in works.items():
        pts = np.argwhere(arr > 0)
        text = lst(pts, arr[tuple(pts.T)])
        fn = k + '.vox.txt'
        open(os.path.join(od, fn), 'w', encoding='utf-8', newline='\n').write(text)
        order[k] = [{'name': k, 'op': 'stampvox', 'file': 'masks/masts/' + fn, 'at': [0, 0, 0], 'expect_pixels': int(len(pts)),
                     'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}]
    chP = works['channels'][:, ::-1, :]
    parts = {'ship': occ}
    for k, arr in works.items(): parts[k] = arr > 0
    parts['channels_P'] = chP > 0
    ks = list(parts); pair = {}
    for i, a_ in enumerate(ks):
        for b_ in ks[i + 1:]:
            n_ = int((parts[a_] & parts[b_]).sum())
            if n_: pair[a_ + '×' + b_] = n_
    allv = np.zeros((NX, NY, NZ6), bool)
    for v in parts.values(): allv |= v
    lab, ncomp = ndimage.label(allv)
    comps = {k: int(ndimage.label(arr > 0)[1]) for k, arr in works.items()}
    R = {'stamp_order': order, 'anchors': anchors, 'info': info,
         'counts': {k: int((arr > 0).sum()) for k, arr in works.items()},
         'checks': {'pair_overlap_all_parts': pair, 'components_assembly': int(ncomp), 'components_each': comps,
                    'mirror_each': {k: int((arr != arr[:, ::-1, :]).sum()) for k, arr in works.items() if k != 'channels'}}}
    with open(os.path.join(d, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    # 圖：側面（右舷看）整艘＋桅
    allc = np.zeros((NX, NY, NZ6), np.int16)
    for k, v in W.items():
        if not k.endswith('_model'): allc[:, :, :200] = np.where(v > 0, v, allc[:, :, :200])
    for k, arr in works.items(): allc = np.where(arr > 0, arr, allc)
    S = 1.6; Wd, Hh = 1240, 1000
    im = Image.new('RGB', (Wd, Hh), (250, 248, 242)); g = ImageDraw.Draw(im); ink = (30, 30, 30)
    g.text((20, 10), "風暴角號 Stormkaap　新圖紙 06　桅、船首斜桅、桅頂平台、channels（從右舷看）　0.1 m／格　summit 2026-10-14　（Witsen × 1.194）", fill=ink, font=font(18))
    half = allc[:, YC:, :]
    hasv = (half > 0).any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    ox, base = 20, Hh - 20
    for x, z in np.argwhere(hasv):
        g.rectangle([ox + x * S, base - (z + 1) * S, ox + x * S + S, base - z * S], fill=pal(int(half[x, last[x, z], z])))
    g.line([(ox, base - H.dwl * S), (ox + NX * S, base - H.dwl * S)], fill=(30, 90, 200), width=1)
    ty = 50
    for k, v in info.items():
        g.text((Wd - 520, ty), k + "：" + json.dumps(v, ensure_ascii=False), fill=ink, font=font(13)); ty += 20
    im.save(os.path.join(d, 'sheet06_masts_v1.png'), optimize=False)
    print(json.dumps({k: R[k] for k in ('info', 'counts', 'checks')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
