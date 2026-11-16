"""威尼斯 galeazza（TASK-1302）步驟 5 落地：draft_decks.py 的清單 ⇒ 子作品、組裝件關聯（含 meta）、梯子固定點。

出處：meadow-venice-galea-01m/design/apply_upper.py 的 cli()／component()（persona 改 summit、加鏡像關聯與每刀讀回）。
重跑安全：子作品有 events 就不再落格；關聯同名覆寫；固定點同名覆寫。
"""
import json
from pathlib import Path
import re
import subprocess
import sys

D = Path(__file__).resolve().parent
HULL = D.parent.name
ASM = HULL + '-assembly'
SIZE = '660,321,160'


def cli(op, **args):
    cmd = ['senate', 'cmd', 'sculpture', '--arg', 'op=' + op, '--arg', 'persona=summit']
    for k, v in args.items():
        if isinstance(v, dict):
            v = json.dumps(v, ensure_ascii=False, separators=(',', ':'))
        cmd += ['--arg', f'{k}={v}']
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
    if r.returncode:
        raise RuntimeError(f'{cmd!r}\n{r.stdout[-3000:]}')
    return r.stdout


def component(suffix, title, lists):
    work = f'{HULL}-{suffix}'
    where = D.parent.parent / work
    if not (where / 'work.json').exists():
        cli('work', sub='create', work=work, title=title, size=SIZE, parent_work=HULL, tags='sub')
        cli('work', sub='update', work=work, meters_per_voxel=0.1, tags='sub')
    if not list((where / 'events').rglob('*.json')) if (where / 'events').exists() else True:
        for p in lists:
            n = sum(1 for l in p.read_text().splitlines() if l.strip())
            out = cli('stampvox', work=work, voxels=str(p).replace('\\', '/'), at='0,0,0', expect_pixels=n, share=0)
            m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
            placed = int(m.group(1).replace(',', '')) if m else None
            print(f'  {work} ← {p.name}: {n} cells, placed {placed}', flush=True)
            if placed != n:
                raise RuntimeError(out[-2000:])
    return work


def main():
    M = D / 'masks/decks'
    meta = json.loads((D / 'deck_meta.json').read_text(encoding='utf-8'))
    lad = json.loads((D / 'ladders.json').read_text(encoding='utf-8'))
    deck = component('deck', '威尼斯加萊賽戰船 主甲板（划槳甲板）與 corsia', [M / 'deck_main.vox.txt', M / 'corsia.vox.txt'])
    cli('work', sub='link', work=ASM, name='甲板-main', source_work=deck, at='0,0,0', meta=meta['deck_main'])
    benches = component('benches', '威尼斯加萊賽戰船 划凳（每舷 25 張）', [M / 'benches.vox.txt'])
    cli('work', sub='link', work=ASM, name='划凳', source_work=benches, at='0,0,0')
    bow = component('deck-bow', '威尼斯加萊賽戰船 艏樓頂（圓形砲樓）', [M / 'deck_bow.vox.txt'])
    cli('work', sub='link', work=ASM, name='甲板-forecastle', source_work=bow, at='0,0,0', meta=meta['deck_bow'])
    stern = component('deck-stern', '威尼斯加萊賽戰船 艉樓平台', [M / 'deck_stern.vox.txt'])
    cli('work', sub='link', work=ASM, name='甲板-quarter', source_work=stern, at='0,0,0', meta=meta['deck_stern'])
    for suffix, title, lname, key, decks in (
            ('ladder-bow', '威尼斯加萊賽戰船 艏樓梯（S 舷；P 舷鏡像）', '梯子-艏樓', 'bow-S', 'main,forecastle'),
            ('ladder-stern', '威尼斯加萊賽戰船 艉樓梯（S 舷；P 舷鏡像）', '梯子-艉樓', 'stern-S', 'main,quarter'),
            ('ladder-hold', '威尼斯加萊賽戰船 底艙梯（corsia 中線）', '梯子-底艙', 'hold', None)):
        w = component(suffix, title, [M / (suffix.replace('-', '_') + '.vox.txt')])
        for pt in ('foot', 'lo', 'hi', 'head'):
            cli('work', sub='anchor', work=w, name=f'{key}.{pt}', at=','.join(map(str, lad[key][pt])))
        m = {'kind': 'ladders'}
        if decks:
            m[f'{key}.decks'] = decks
        cli('work', sub='link', work=ASM, name=lname, source_work=w, at='0,0,0', meta=m)
        if key != 'hold':
            cli('work', sub='link', work=ASM, name=lname + '-鏡像', source_work=w, at='0,0,0', mirror='y', meta=m)
        print('  linked', lname, flush=True)


if __name__ == '__main__':
    main()
