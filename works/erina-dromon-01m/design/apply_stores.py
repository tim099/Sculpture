# 補給元件落地：開子作品（0.05 m）→ stampvox（讀回 placed）→ 固定點 pivot。擺法在 placements.py（藥庫 桶-001…006）、落地照 apply_all.py models。
# 用法：python -I -X utf8 -B apply_stores.py
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli

D = os.path.dirname(os.path.abspath(__file__))
V = json.load(open(os.path.join(D, 'verify_stores.json'), encoding='utf-8'))
TITLE = {'amphora': '持火號 希臘火陶罐（補給；遊戲當火藥桶；0.05 m）', 'boltbox': '持火號 弩箭箱（補給；遊戲當火藥桶；0.05 m）'}
for name, v in V.items():
    wid = 'erina-dromon-01m-store-' + name
    cli.ensure_work(wid, TITLE[name], v['size'], 'erina-dromon-01m', 0.05)
    rc, out = cli.run(['op=stats', 'work=' + wid], quiet=True)
    have = int((cli.val(out, 'total_voxels') or '0').replace(',', ''))
    if have == 0:
        cli.stamp(wid, os.path.join(D, v['file']), v['cells'])
    elif have != v['cells']:
        raise SystemExit('%s 已有 %d 格、清單 %d 格 ⇒ 用 restamp.py' % (wid, have, v['cells']))
    for an, at in v['anchors'].items():
        cli.anchor(wid, an, at, '底面正中（draft_stores.py）')
    print(name, 'ok')
