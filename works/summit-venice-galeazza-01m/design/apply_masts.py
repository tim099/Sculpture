"""威尼斯 galeazza（TASK-1302）步驟 7 落地：draft_masts.py ⇒ 每根下桅一件子作品（組裝件關聯 kind=mast）、每根帆桁一件子作品（桅子作品裡的外部模型 kind=yard、yard=gaff、rig=lateen）。

出處：meadow-venice-galea-01m/design/apply_rig.py 的 apply() 前半（帆、索在步驟 8）。重跑安全：有 events 不再落格、固定點同名覆寫、模型與關聯同名覆寫。
"""
import json
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import apply_decks as A
from apply_decks import ASM, HULL, cli

NAMES = {'main': '主桅 maestra', 'fore': '前桅 trinchetto', 'mizzen': '後桅 mezzana'}
c = lambda v: ','.join(str(round(t, 2)) for t in v)


def main():
    rig = json.loads((D / 'rig.json').read_text(encoding='utf-8'))
    for name, r in rig.items():
        A.SIZE = '660,321,360'
        mast = A.component(f'mast-{name}', f'威尼斯加萊賽戰船 {NAMES[name]}', [D / f'masks/rig/{name}-mast.vox.txt'])
        A.SIZE = c(r['yard_size'])
        yard = A.component(f'yard-{name}', f'威尼斯加萊賽戰船 {NAMES[name]} 三角帆桁（{r["yard_length_m"]} m）', [D / f'masks/rig/{name}-yard.vox.txt'])
        for pt in ('pivot', 'peak', 'fore'):
            cli('work', sub='anchor', work=yard, name=pt, at=c(r[pt]))
        cli('work', sub='anchor', work=mast, name='hound', at=c(r['hound']))
        cli('work', sub='model', work=mast, name=f'yard-{name}', source_work=yard, at=c(r['model_at']),
            pivot=c([v + 0.5 for v in r['pivot']]), scale=1,
            meta=dict(kind='yard', mast=name, yard='gaff', rig='lateen', length_m=r['yard_length_m'],
                      pivot_anchor='pivot', turn_axis='z', rotate_z_deg=0, sail=f'{name}-lateen'))
        cli('work', sub='link', work=ASM, name=f'mast-{name}', source_work=mast, at='0,0,0', meta=dict(kind='mast', mast=name))
        print(name, 'mast + yard', flush=True)


if __name__ == '__main__':
    main()
