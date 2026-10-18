# 武器元件落地：開子作品（0.05 m）→ stampvox（讀回 placed）→ 固定點。
# 用法：python -I -X utf8 -B apply_weapons.py [名字 regex]
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli

D = os.path.dirname(os.path.abspath(__file__))
V = json.load(open(os.path.join(D, 'verify_weapons.json'), encoding='utf-8'))
flt = re.compile(sys.argv[1] if len(sys.argv) > 1 else '.')
TITLE = {'siphon': '持火號 希臘火噴筒（siphon：青銅藥槽＋壓力泵＋青銅管＋鍍金獅頭；0.05 m）',
         'ballista': '持火號 弩砲（toxoballistra；0.05 m）',
         'mangonel': '持火號 投石機（manganikon，牽引式；0.05 m）'}
for name, v in V.items():
    if not flt.search(name):
        continue
    wid = 'erina-dromon-01m-' + name
    print(name, wid)
    cli.ensure_work(wid, TITLE[name], v['size'], 'erina-dromon-01m', 0.05)
    rc, out = cli.run(['op=stats', 'work=' + wid], quiet=True)
    have = int((cli.val(out, 'total_voxels') or '0').replace(',', ''))
    if have == 0:
        cli.stamp(wid, os.path.join(D, v['file']), v['cells'])
    else:
        print('  已有 %d 格，不重貼' % have)
    for an, at in v['anchors'].items():
        cli.anchor(wid, an, at, 'draft_weapons.py')
    print('  anchors', len(v['anchors']))
