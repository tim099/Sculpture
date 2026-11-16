"""威尼斯 galeazza（TASK-1302）步驟 9 落地：gun_layout.json 的 32 門 ⇒ 掛在所在甲板子作品裡的外部模型（meta kind=gun、gun=<代碼>；petriera 加 mount=turret、arc、rate）。
重跑安全：同名 overwrite=1。
"""
import json
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from apply_decks import HULL, cli

RECOIL = {'ven50': 9, 'ven6': 5}        # meadow galea 的兩種照她的設定


def main():
    lay = json.loads((D / 'gun_layout.json').read_text(encoding='utf-8'))
    assert not lay['bad'], lay['bad']
    for g in lay['layout']:
        host = f'{HULL}-{g["host"]}'
        meta = {'kind': 'gun', 'gun': g['gun']}
        if g['gun'] in RECOIL:
            meta['recoil'] = RECOIL[g['gun']]
        if g['gun'] == 'ven14p':
            meta.update(mount='turret', arc=f'-{g["arc"]},{g["arc"]}', rate=45)
        c = lambda v: ','.join(str(t) for t in v)
        s = g['scale']
        cli('work', sub='model', work=host, name=f'gun-{g["name"]}', source_work=g['work'], at=c(g['at']), pivot=c(g['pivot']),
            rotate=c(g['rotate']), scale=c([s, s, s]), meta=meta, overwrite=1)
    print(len(lay['layout']), 'guns placed', flush=True)


if __name__ == '__main__':
    main()
