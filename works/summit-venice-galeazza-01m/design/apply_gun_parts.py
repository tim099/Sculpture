"""通用部件落地：draft_guns_venice.py 的六種威尼斯砲 ⇒ 子作品（0.05 m、tags=sub）、固定點、作品預設 meta（kind=gun、gun=<代碼>；petriera 加 mount=turret）。"""
import json
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import apply_decks as A
from apply_decks import HULL, cli

KINDS = {'cannone': '短重砲 cannone', 'colubrina': '長砲 colubrina', 'falcone': '輕砲 falcone', 'petriera': '叉架石彈迴旋砲 petriera'}


def main():
    plan = json.loads((D / 'plan.json').read_text(encoding='utf-8'))
    v = json.loads((D / 'verify_guns_venice.json').read_text(encoding='utf-8'))
    for code, T in plan['guns']['types'].items():
        r = v[code]
        A.SIZE = ','.join(map(str, r['size']))
        w = A.component(f'gun-{code}', f'{T["lb"]} 威尼斯磅{KINDS[T["kind"]]}（gun {code}，青銅，通用部件，0.05 m）', [D / f'masks/guns/gun-{code}.vox.txt'])
        cli('work', sub='update', work=w, meters_per_voxel=0.05, tags='sub')
        for k, p in r['anchors'].items():
            cli('work', sub='anchor', work=w, name=k, at=','.join(map(str, p)))
        meta = {'kind': 'gun', 'gun': code}
        if T['kind'] == 'petriera':
            meta['mount'] = 'turret'
        cli('work', sub='meta', part='work', work=w, meta=meta)
        print(code, w, flush=True)


if __name__ == '__main__':
    main()
