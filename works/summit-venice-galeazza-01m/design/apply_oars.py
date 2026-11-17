"""威尼斯 galeazza（TASK-1302）步驟 13 落地：oar_layout.json 的 50 支槳 ⇒ 組裝件外部模型 oar-S01…S25、oar-P01…P25
（來源 apex-one-reale-01m-oar、scale 照長度放大、pivot ＝ 元件的 pivot 格中心、at ＝ 槳門裡的槳座；P 舷 mirror=y）。
meta kind=oar、rowers 6、side、stroke_deg（每支照 draft_oars 量的：多數 30，兩頭幾支較小）、dip_deg 12。重跑安全：同名 overwrite=1。
"""
import json
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from apply_decks import ASM, cli


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    L = json.loads((D / 'oar_layout.json').read_text(encoding='utf-8'))
    c = lambda v: ','.join(str(t) for t in v)
    piv = [v + 0.5 for v in L['ref']['pivot']]
    s = L['scale']
    for o in L['oars']:
        meta = dict(L['meta'], side=o['side'], stroke_deg=o['stroke_deg'])      # 兩頭幾支掃不開 30°（樓的牆）⇒ 照 draft_oars 量的
        args = dict(sub='model', work=ASM, name=o['name'], source_work=L['ref']['work'], at=c(o['at']), pivot=c(piv),
                    scale=c([s, s, s]), meta=meta, overwrite=1)
        if o['mirror']:
            args['mirror'] = o['mirror']
        cli('work', **args)
    print(len(L['oars']), 'oars placed', flush=True)


if __name__ == '__main__':
    main()
