"""威尼斯 galeazza（TASK-1302）步驟 10 落地：draft_decks.py（底艙梯改站在底艙地板上）＋ draft_hold.py 的清單 ⇒ 作品。

- 甲板（-deck：主甲板＋corsia）、底艙梯（-ladder-hold）：已落過格 ⇒ 照「現況匯出 vs 新清單」差分，carvevox 多的（帶顏色守門）、
  stampvox 缺的；改完再匯出一次，逐格要等於新清單。
- 新子作品：-hold（底艙地板，關聯 甲板-hold）、-magazine（彈藥庫，關聯 彈藥庫 meta kind=magazine＋固定點 blast／door＋6 個火藥桶模型）、
  -hold-hatch（底艙梯口艙蓋，局部座標；固定點 hinge-a／hinge-b；外部模型掛在 -deck）。
- 模型：三盞艉燈（組裝件，kind=light）、羅經櫃（-deck-stern，kind=binnacle）。
重跑安全：差分為空就不動；子作品有 events 就不再落格；關聯、模型、固定點同名覆寫。
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from apply_decks import ASM, HULL, cli, component


def read_list(p):
    out = {}
    for line in Path(p).read_text(encoding='utf-8').splitlines():
        if line.strip() and not line.startswith('#'):
            x, y, z, c = (int(v) for v in line.split(',')[:4])
            out[(x, y, z)] = c
    return out


def export(work):
    out = cli('export', work=work, format='list')
    return read_list(re.search(r'path = (\S+)', out).group(1))


def sync(work, lists, tmp):
    want = {}
    for p in lists:
        want.update(read_list(p))
    got = export(work)
    carve = {k: c for k, c in got.items() if want.get(k) != c}
    stamp = {k: c for k, c in want.items() if got.get(k) != c}
    if carve:
        f = tmp / f'{work}.carve.txt'
        f.write_text(''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(carve.items())), encoding='ascii')
        cli('carvevox', work=work, voxels=str(f).replace('\\', '/'), at='0,0,0', expect_pixels=len(carve), share=0)
    if stamp:
        f = tmp / f'{work}.stamp.txt'
        f.write_text(''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(stamp.items())), encoding='ascii')
        cli('stampvox', work=work, voxels=str(f).replace('\\', '/'), at='0,0,0', expect_pixels=len(stamp), share=0)
    after = export(work)
    assert after == want, (work, len(after), len(want))
    print(f'  {work}: carved {len(carve)}, stamped {len(stamp)} ⇒ {len(after)} = 新清單', flush=True)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    M, H = D / 'masks/decks', D / 'masks/hold'
    meta = json.loads((D / 'hold_meta.json').read_text(encoding='utf-8'))
    lad = json.loads((D / 'ladders.json').read_text(encoding='utf-8'))
    c = lambda v: ','.join(str(t) for t in v)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # ① 甲板＋corsia、底艙梯：差分
        sync(f'{HULL}-deck', [M / 'deck_main.vox.txt', M / 'corsia.vox.txt'], tmp)
        sync(f'{HULL}-ladder-hold', [M / 'ladder_hold.vox.txt'], tmp)
    lh = f'{HULL}-ladder-hold'
    for pt in ('foot', 'lo', 'hi', 'head'):
        cli('work', sub='anchor', work=lh, name=f'hold.{pt}', at=c(lad['hold'][pt]), overwrite=1)
    cli('work', sub='link', work=ASM, name='梯子-底艙', source_work=lh, at='0,0,0', meta={'kind': 'ladders', 'hold.decks': 'hold,main'}, overwrite=1)

    # ② 底艙地板
    hold = component('hold', '威尼斯加萊賽戰船 底艙地板（壓艙＋鋪板）', [H / 'floor.vox.txt'])
    cli('work', sub='link', work=ASM, name='甲板-hold', source_work=hold, at='0,0,0', meta=meta['hold'], overwrite=1)

    # ③ 彈藥庫＋火藥桶
    mag = component('magazine', '威尼斯加萊賽戰船 彈藥庫（艏樓下底艙；銅皮艙壁、松木地板）', [H / 'magazine.vox.txt'])
    for nm in ('blast', 'door'):
        cli('work', sub='anchor', work=mag, name=nm, at=c(meta['anchors'][nm]), overwrite=1)
    K = meta['keg']
    for g in meta['kegs']:
        cli('work', sub='model', work=mag, name=g['name'], source_work=K['work'], at=c(g['at']), pivot=c(K['pivot']),
            scale=c([K['scale']] * 3), meta={'kind': 'powder', 'powder_lb': 100}, overwrite=1)
    cli('work', sub='link', work=ASM, name='彈藥庫', source_work=mag, at='0,0,0', meta=meta['magazine'], overwrite=1)

    # ④ 底艙梯口艙蓋（局部座標）
    h = meta['hatch']
    hatch = f'{HULL}-hold-hatch'
    where = D.parent.parent / hatch
    if not (where / 'work.json').exists():
        cli('work', sub='create', work=hatch, title='威尼斯加萊賽戰船 底艙梯口艙蓋（corsia 上；門 kind=door）', size=c(h['size']), parent_work=HULL, tags='sub')
        cli('work', sub='update', work=hatch, meters_per_voxel=0.1, tags='sub')
    with tempfile.TemporaryDirectory() as td:
        sync(hatch, [H / 'hatch.vox.txt'], Path(td))
    cli('work', sub='anchor', work=hatch, name='hinge-a', at=c(h['hinge_a']), overwrite=1)
    cli('work', sub='anchor', work=hatch, name='hinge-b', at=c(h['hinge_b']), overwrite=1)
    cli('work', sub='model', work=f'{HULL}-deck', name='底艙艙蓋', source_work=hatch, at=c(h['at']), pivot='0,0,0', scale='1,1,1',
        meta={'kind': 'door', 'open': 'up', 'open_deg': 100}, overwrite=1)

    # ⑤ 艉燈三盞（組裝件）、羅經櫃（艉樓平台）
    Lt = meta['lantern']
    for nm, v in meta['lanterns'].items():
        cli('work', sub='model', work=ASM, name=nm, source_work=Lt['work'], at=c(v['at']), pivot=c(Lt['pivot']),
            scale=c([v['scale']] * 3), meta={'kind': 'light'}, overwrite=1)
    B = meta['binnacle']
    cli('work', sub='model', work=f'{HULL}-deck-stern', name='羅經櫃', source_work=B['work'], at=c(B['at']), pivot=c(B['pivot']),
        scale=c([B['scale']] * 3), meta={'kind': 'binnacle'}, overwrite=1)
    print('ok', flush=True)


if __name__ == '__main__':
    main()
