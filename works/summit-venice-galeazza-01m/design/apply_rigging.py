"""威尼斯 galeazza（TASK-1302）步驟 8：帆、靜索、ratlines、動索、旗（Ship_Rigging §6／§7／§9.1）。

出處：meadow-venice-galea-01m/design/apply_rig.py 的 apply() 後半（三角帆三角、tack／sheet／halyard、shrouds）與 apply_ends.py 的 ensign（貼圖 venice-ensign.png 照抄）。
- 三面三角帆：peak、tack 釘在帆桁模型的 peak／fore，clew free（sheet 拉住）；帆布素白 #f2ead8（Tim 附圖的紅白條紋查不到出處）。
  帆裝三段（Ship_Rigging §9.1）：前帆 set 1（收帆）、主帆 set 2（戰鬥帆）、後帆 set 3（滿帆）。
- 靜索：每根桅每舷 3 條 shroud，從桅的 hound 到舷牆頂（|dy| 57 那層的頂格）；ratlines 橫繩組每根桅每舷一組（step 4、不標 climb：桅上沒有站得住的平台）。
- 動索：tack（帆桁 fore → corsia／艏樓頂）、sheet（clew → 甲板）、halyard（hound → 帆桁轉軸）。
- 旗：艉樓平台的旗桿（子作品 -flagstaff，關聯）掛聖馬可國旗 ensign（nation=venice）；三根帆桁 peak 各一面紅色長旗 pennant（Grevenbroeck 帆桁頂的長飄帶，nation=none）。
重跑安全：繩 overwrite=1、帆與固定點同名覆寫。
"""
import json
from pathlib import Path
import sys

import numpy as np

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import apply_decks as A
from apply_decks import ASM, HULL, cli

YC = 160
SET = {'fore': 1, 'main': 2, 'mizzen': 3}
c = lambda v: ','.join(str(round(t, 2)) for t in v)
TAR, RUN, CANVAS = '#2b2620', '#a08458', '#f2ead8'


def rope(name, a, b, group, slack=1.0, thick=0.5, color=TAR):
    cli('work', sub='rope', work=ASM, name=name, **{'from': a, 'to': b}, slack=slack, thickness=thick, color=color, group=group, overwrite=1)


def main():
    rig = json.loads((D / 'rig.json').read_text(encoding='utf-8'))
    plan = json.loads((D / 'plan.json').read_text(encoding='utf-8'))
    OUT = plan['lines']['half_beam']['v'] + plan['layout']['postizza_out']['v']   # 58
    bw_top = plan['layout']['bulwark_top_z']['v']                                  # 48
    meta = []
    shroud_x = {'main': (300, 318, 336), 'fore': (440, 452, 464), 'mizzen': (156, 168, 180)}
    tack_to = {'main': (432.5, 160.5, 37.5), 'fore': (560.5, 160.5, 51.5), 'mizzen': (236.5, 160.5, 37.5)}
    sheet_to = {'main': (196.5, 160.5, 37.5), 'fore': (396.5, 160.5, 37.5), 'mizzen': (92.5, 160.5, 82.5)}
    for name, r in rig.items():
        ml, ym = f'mast-{name}', f'model:mast-{name}/yard-{name}/'
        yard = f'{HULL}-yard-{name}'
        # pennant 固定點：從 peak 沿帆桁往 fore 走 10 格
        pk, fo = np.array(r['peak'], float), np.array(r['fore'], float)
        pn = pk + (fo - pk) / np.linalg.norm(fo - pk) * 10
        cli('work', sub='anchor', work=yard, name='pennant', at=c([int(round(v)) for v in pn]))
        sail = f'{name}-lateen'
        cli('work', sub='sail', work=ASM, name=sail, corners=f'{ym}peak|{ym}fore|{c(r["clew_w"])}',
            corner_names='peak|tack|clew', bind='0', free='clew', color=CANVAS, fullness=1.07)
        meta.append(('sail', sail, dict(kind='sail', mast=name, sail='gaff', set=SET[name])))
        for i, x in enumerate(shroud_x[name], 1):
            for side, sgn in (('P', -1), ('S', 1)):
                rn = f'{name}-shroud-{side}{i}'
                rope(rn, f'{ml}/hound', c([x + 0.5, YC + sgn * (OUT - 1) + 0.5, bw_top + 0.5]), f'standing/{name}', thick=0.6)
                meta.append(('rope', rn, dict(kind='shroud')))
        for side in ('P', 'S'):
            cli('work', sub='ratlines', work=ASM, name=f'{name}-lower-{side}', rope_a=f'{name}-shroud-{side}3', rope_b=f'{name}-shroud-{side}1',
                step=4, start=6, stop=12, min_span=5, thickness=0.3, color=TAR, group=f'ratlines/{name}')
        tack, sheet, hal = f'{sail}.tack', f'{sail}.sheet', f'{sail}.halyard'
        rope(tack, f'{ym}fore', c(tack_to[name]), f'running/{name}', slack=1.02, thick=0.5, color=RUN)
        rope(sheet, f'sail:{sail}/clew', c(sheet_to[name]), f'running/{name}', slack=1.02, thick=0.45, color=RUN)
        rope(hal, f'{ml}/hound', c(r['model_at']), f'running/{name}', slack=1.0, thick=0.6, color=RUN)
        for ln, k in ((tack, 'tack'), (sheet, 'sheet'), (hal, 'halyard')):
            meta.append(('rope', ln, dict(kind=k, sail=sail)))
        # 長旗：peak 與 pennant 兩點釘住、旗尾往後下飄
        pen = f'{name}-pennant'
        fly = [r['peak_w'][0] - 60, YC, r['peak_w'][1] - 12]
        cli('work', sub='sail', work=ASM, name=pen, corners=f'{ym}peak|{ym}pennant|{c(fly)}', corner_names='head|foot|fly',
            bind='0', free='fly', color='#b3202a', fullness=1.02)
        meta.append(('sail', pen, dict(kind='flag', flag='pennant', nation='none', mast=name)))
        print(name, 'rig', flush=True)

    # 旗桿：艉樓平台 x 58、中線十字截面、z 52..105；固定點 ensign-head／foot／cleat
    sx = 58
    cells = {}
    for z in range(52, 106):
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            if z < 100 or (dx, dy) == (0, 0):
                cells[(sx + dx, YC + dy, z)] = 212 if z >= 104 else 104
    mask = D / 'masks/rig/flagstaff.vox.txt'
    mask.write_bytes(''.join(f'{x},{y},{z},{v}\n' for (x, y, z), v in sorted(cells.items())).encode('ascii'))
    A.SIZE = '660,321,160'
    fs = A.component('flagstaff', '威尼斯加萊賽戰船 艉旗桿', [mask])
    for nm, pt in (('ensign-head', (sx - 1, YC, 104)), ('ensign-foot', (sx - 1, YC, 84)), ('ensign-cleat', (sx + 1, YC, 54))):
        cli('work', sub='anchor', work=fs, name=nm, at=c(pt))
    cli('work', sub='link', work=ASM, name='艉旗桿', source_work=fs, at='0,0,0')
    cli('work', sub='sail', work=ASM, name='ensign', corners=f'艉旗桿/ensign-head|{sx - 33},{YC},103|{sx - 33},{YC},85|艉旗桿/ensign-foot',
        corner_names='head|fly-top|fly-foot|foot', bind='3', free='fly-top,fly-foot', color='#ffffff',
        texture=str(D / 'masks/rig/venice-ensign.png').replace('\\', '/'), fullness=1.04)
    rope('ensign-halyard', '艉旗桿/ensign-cleat', '艉旗桿/ensign-head', 'standing/ensign', thick=0.3, color=RUN)
    rope('ensign-downhaul', '艉旗桿/ensign-cleat', '艉旗桿/ensign-foot', 'standing/ensign', thick=0.3, color=RUN)
    meta.append(('sail', 'ensign', dict(kind='flag', flag='ensign', nation='venice')))
    tsv = D / 'galeazza_rig.tsv'
    tsv.write_text(''.join(f'{p}\t{n}\t{json.dumps(m, ensure_ascii=False)}\n' for p, n, m in meta), encoding='utf-8')
    cli('work', sub='meta', work=ASM, file=str(tsv).replace('\\', '/'))
    print(cli('work', sub='ropecheck', work=ASM)[-1500:], flush=True)


if __name__ == '__main__':
    main()
