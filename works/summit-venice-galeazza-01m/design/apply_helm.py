"""威尼斯 galeazza（TASK-1302）步驟 11 落地：draft_helm.py 的清單 ⇒ 作品。

- 船殼刻舵柄口（masks/upper/hull_cut_02.vox.txt，carvevox 帶顏色守門）。
- 子作品 -rudder（舵葉＋舵桿＋舵柄，跟組裝件同框）＋固定點 stock-top ⇒ 組裝件外部模型「舵」（pivot ＝ at ＝ 鉸鏈點，meta kind=rudder＋spin）。
- 兩隻四爪錨 ⇒ 組裝件外部模型「錨-S」「錨-P」（meta kind=anchor、anchor=bower、hawse）。
重跑安全：刻過的格不在了就不再刻；子作品有 events 就不再落格；模型、固定點同名覆寫。
"""
import json
from pathlib import Path
import sys
import tempfile

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from apply_decks import ASM, HULL, cli, component
from apply_hold import export, read_list


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    meta = json.loads((D / 'helm_meta.json').read_text(encoding='utf-8'))
    c = lambda v: ','.join(str(t) for t in v)
    # ① 舵柄口
    cut = read_list(D / 'masks/upper/hull_cut_02.vox.txt')
    got = export(HULL)
    todo = {k: v for k, v in cut.items() if got.get(k) == v}
    if todo:
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / 'cut.txt'
            f.write_text(''.join(f'{x},{y},{z},{v}\n' for (x, y, z), v in sorted(todo.items())), encoding='ascii')
            cli('carvevox', work=HULL, voxels=str(f).replace('\\', '/'), at='0,0,0', expect_pixels=len(todo), share=0)
    after = export(HULL)
    left = [k for k in cut if k in after]
    assert not left, left[:5]
    print(f'  {HULL}: carved {len(todo)} ⇒ {len(after)}（舵柄口 {len(cut)} 格都不在了）', flush=True)

    # ② 舵
    rud = component('rudder', '威尼斯加萊賽戰船 舵（舵葉、舵桿、舵柄；沿斜艉柱）', [D / 'masks/helm/rudder.vox.txt'])
    cli('work', sub='anchor', work=rud, name='stock-top', at=c(meta['stock_top']), overwrite=1)
    P = meta['pivot']
    cli('work', sub='model', work=ASM, name='舵', source_work=rud, at=c(P), pivot=c(P), scale='1,1,1', meta=meta['rudder'], overwrite=1)

    # ③ 錨
    G = meta['grapnel']
    for name, a in meta['anchors'].items():
        cli('work', sub='model', work=ASM, name=name, source_work=G['work'], at=c(a['at']), pivot=c(G['pivot']),
            rotate=c(a['rotate']), scale=c([a['scale']] * 3), meta={'kind': 'anchor', 'anchor': 'bower', 'hawse': c(a['hawse'])}, overwrite=1)
    print('ok', flush=True)


if __name__ == '__main__':
    main()
