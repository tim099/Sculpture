# 新圖紙 09a 繫繩點（TASK-0547 階段九）：plan.json 的 belaying ⇒ 三根桅腳的 fife rails（一件子作品，框 ＝ 整艘船、at 0,0,0）＋ pin 固定點、
#   艉樓與艏樓舷牆頂的 kevel 固定點（船殼原有的格）、verify_belaying.json。
# 用法：python -I -X utf8 -B draft_belaying.py <design 資料夾>
#   · 從夜隼號 draft_belaying.py（TASK-0529 階段十）的 fife 那一段改；⛔ 舷牆 pin rails 不做（理由在 plan provenance belaying）。
#   · 現況：sk_world.World（船 ＋ 桅 ＋ channels v2；帆桁不算 —— fife 在甲板上，帆桁都在高處，量過再說）。
#   · 甲板面 zd(x) ＝ 中線外 10 格那一欄最上層甲板的頂面 ＋ 1（後甲板／艉樓／艏樓／上甲板取最高的）。
#   · fife：桅孔 x 後 aft 格一根橫 rail（rail_wide 寬）、兩側 ±half_width（2 寬）往前到桅孔前 fwd 格接 bitts（3×3、從每一欄自己的甲板面起、高到甲板面 ＋ bitt_tall）；
#     rail 在甲板面 ＋ above_deck；橫 rail 底下柱（兩角 2×2、中線 2×1）；bitts 頂下 2 格一根鐵 cross pin 前後各伸 1 格；
#     pins：橫 rail 後排 dy ＝ 每根桅的 aft_pins_dy（🩸 第一版三根共用 ±3、±6 ⇒ 後桅半寬 7、柱在 ±6，撞）、側 rail 內排每 pin_every 格；pin ＝ rail 上 up 格、下 down 格，固定點 ＝ pin 最上那一格。
#   · kevel：x ＝ kamp_x／bak_x，右舷：那一欄船殼最高那一格（舷牆頂）、最靠外那一格。左舷走船殼的鏡像格（船殼兩舷對稱 —— 量過）。
#   · 每一格都要落在空的格上、底下要接到甲板（assert）；重跑逐位元組相同。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_world import World


def main():
    d = sys.argv[1]
    w = World(d, with_yards=False)
    plan = w.plan; B = plan['belaying']; C = B['colors']; YC = w.YC
    Mp = {m['name']: m for m in plan['masts']['list']}
    fife = {}; anchors = []; rails = {}

    def put(c, col):
        assert not w.lab[c], ('撞到現況', w.at(c), c)
        assert c not in fife or fife[c] == col, ('自己重疊不同色', c)
        fife[c] = col

    def zd(x):
        t = w.deck_top(x); assert t, ('那一欄沒有甲板', x); return t[0] + 1, t[1]

    F = B['fife']; P = B['pin']
    for m in ('mizzen', 'main', 'fore'):
        G = F[m]; xm = int(Mp[m]['x'])
        z0, deck = zd(xm); zr = z0 + F['above_deck']
        xa, xf, hw = xm - G['aft_of_mast'], xm + G['fwd_of_mast'], G['half_width']
        for x in range(xa, xa + F['rail_wide']):
            for dy in range(-hw, hw + 1): put((x, YC + dy, zr), C['rail'])
        for sg in (1, -1):
            for x in range(xa, xf):
                for dy in (hw - 1, hw): put((x, YC + sg * dy, zr), C['rail'])
            for x in range(xf, xf + F['bitt']):
                for dy in (hw - 1, hw, hw + 1):
                    for z in range(zd(x)[0], z0 + F['bitt_tall']): put((x, YC + sg * dy, z), C['bitt'])
            for x in (xf - 1, xf + F['bitt']):
                put((x, YC + sg * hw, z0 + F['bitt_tall'] - 2), C['cross'])
        for x in range(xa, xa + F['rail_wide']):
            for dy in (-hw, -hw + 1, 0, hw - 1, hw):
                for z in range(zd(x)[0], zr): put((x, YC + dy, z), C['bitt'])
        pins = []
        def pin(x, y, tag):
            for z in list(range(zr + 1, zr + P['up'] + 1)) + list(range(zr - P['down'], zr)): put((x, y, z), C['pin'])
            pins.append((tag, (x, y, zr + P['up'])))
        for k, dy in enumerate(G['aft_pins_dy']):          # 後排避開柱（中線、±(hw−1)、±hw）
            pin(xa, YC + dy, 'fife-%s-aft%d' % (m, k + 1))
        for sg, sd in ((1, 'S'), (-1, 'P')):
            for k, x in enumerate(range(xa + 3, xf - 1, F['pin_every'])):
                pin(x, YC + sg * (hw - 1), 'fife-%s-%s%d' % (m, sd, k + 1))
        anchors += [(n, c, 'pin') for n, c in pins]
        # 每根柱、bitt 的最下面那一格底下要是甲板（接得到）
        for (x, y, z), col in list(fife.items()):
            if col == C['bitt'] and z == zd(x)[0] and xa - 1 <= x <= xf + F['bitt']:
                assert w.at((x, y, z - 1)) in ('kamp', 'half', 'bak', 'upper', 'hull'), ('柱腳沒有甲板', m, (x, y, z), w.at((x, y, z - 1)))
        rails['fife-' + m] = {'deck': deck, 'deck_z': z0, 'rail_z': zr, 'x': [xa, xf + F['bitt'] - 1], 'half_width': hw, 'pins': len(pins)}
    # kevels（船殼原有的格）
    # 🩸 第一版只看船殼 ⇒ 艏樓那個量到 z 97（比艏樓甲板 112 還低）—— 艏樓的舷牆是艏樓甲板那一件的，不是船殼的
    #    ⇒ 船殼與各層甲板裡找最高那一格；固定點登記在擁有那一格的那一件上
    kev = {}
    for tag, x in (('kevel-kamp', B['kevel']['kamp_x']), ('kevel-bak', B['kevel']['bak_x'])):
        best = None
        for k in ('hull', 'kamp', 'half', 'bak', 'upper'):
            col = w.color[k][x, YC:, :] > 0
            if not col.any(): continue
            zt = int(np.nonzero(col.any(0))[0].max())
            if best is None or zt > best[1]: best = (k, zt, YC + int(np.nonzero(col[:, zt])[0].max()))
        k, zt, y = best
        assert w.color[k][x, y, zt] and w.color[k][x, w.NY - 1 - y, zt], ('kevel 兩舷不對稱', tag)
        kev.setdefault(k, []).extend([(tag + '-S', (x, y, zt), 'kevel'), (tag + '-P', (x, w.NY - 1 - y, zt), 'kevel')])
    # 輸出
    a = np.array([[*k, v] for k, v in sorted(fife.items())])
    text = ''.join('%d,%d,%d,%d\n' % tuple(r) for r in a)
    od = os.path.join(d, 'masks', 'belaying'); os.makedirs(od, exist_ok=True)
    for f in os.listdir(od): os.remove(os.path.join(od, f))
    open(os.path.join(od, 'fiferails.vox.txt'), 'w', encoding='utf-8', newline='\n').write(text)
    g = np.zeros((w.NX, w.NY, 576), bool); g[tuple(a[:, :3].T)] = True
    allv = (w.lab > 0) | g
    lab, nc = ndimage.label(allv[:, :, :260])
    R = {'stamp_order': {'fiferails': [{'name': 'fiferails', 'op': 'stampvox', 'file': 'masks/belaying/fiferails.vox.txt', 'at': [0, 0, 0],
                                        'voxels': int(len(a)), 'origin_world': [0, 0, 0], 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}]},
         'counts': {'cells': int(len(a)), 'by_color': {str(int(c)): int((a[:, 3] == c).sum()) for c in np.unique(a[:, 3])},
                    'components_own': int(ndimage.label(g)[1]), 'components_ship_below_z260': int(nc),
                    'mirror_own': int((g != g[:, ::-1, :]).sum())},
         'rails': rails,
         'anchors': dict({'fife': [{'name': n, 'at': list(c), 'world': list(c), 'kind': k} for n, c, k in anchors]},
                         **{key: [{'name': n, 'at': list(c), 'world': list(c), 'kind': k} for n, c, k in L] for key, L in kev.items()})}
    with open(os.path.join(d, 'verify_belaying.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: R[k] for k in ('counts', 'rails')}, ensure_ascii=False))
    print({k: len(v) for k, v in R['anchors'].items()}, {k: [x['world'] for x in v] for k, v in R['anchors'].items() if k != 'fife'})


if __name__ == '__main__':
    main()
