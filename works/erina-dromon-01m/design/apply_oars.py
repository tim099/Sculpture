# 槳落地（造船規格 §9.10.1）：兩件槳元件（下層／上層，子作品 0.05 m）→ stampvox（讀回 placed）→ 固定點 pivot／blade／seat；
# 再照 oars_placement.json 擺每一支（外部模型，掛在船殼作品裡 —— 槳口開在船殼上；左舷 mirror=y、上層 rotate x ＝ 照舷弧補的傾角）。
# 用法：python -I -X utf8 -B apply_oars.py [comp|models|all]
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli

D = os.path.dirname(os.path.abspath(__file__))
HULL = 'erina-dromon-01m'
step = sys.argv[1] if len(sys.argv) > 1 else 'all'
V = json.load(open(os.path.join(D, 'verify_oars.json'), encoding='utf-8'))
PL = json.load(open(os.path.join(D, 'oars_placement.json'), encoding='utf-8'))
TITLE = {'lower': '槳（dromon 下層，3.85 m、1 人划、入水 12°；通用部件 0.05 m）',
         'upper': '槳（dromon 上層，4.7 m、1 人划、入水 28°；通用部件 0.05 m）'}
NOTE = {'pivot': '槳座：槳靠在槳口下緣的那一點 ＝ 划槳轉的中心、推力作用點、掛點',
        'blade': '槳葉末端',
        'seat': '槳手站的那一格（下層：艙底走道上；上層：主甲板上）'}

if step in ('comp', 'all'):
    for b, c in V['components'].items():
        wid = '%s-oar-%s' % (HULL, b)
        cli.ensure_work(wid, TITLE[b], c['size'], HULL, 0.05)
        rc, out = cli.run(['op=stats', 'work=' + wid], quiet=True)
        have = int((cli.val(out, 'total_voxels') or '0').replace(',', ''))
        if have == 0:
            cli.stamp(wid, os.path.join(D, c['file']), c['cells'])
        elif have != c['cells']:
            raise SystemExit('%s 已有 %d 格、清單 %d 格 ⇒ 用 restamp.py' % (wid, have, c['cells']))
        else:
            print('  %s 已有 %d 格，不重貼' % (wid, have))
        for an, at in c['anchors'].items():
            cli.anchor(wid, an, at, NOTE[an])
        print('  anchors', b, c['anchors'])

if step in ('models', 'all'):
    n = 0
    for o in PL['oars']:
        args = ['op=work', 'sub=model', 'persona=erina', 'work=' + HULL, 'name=' + o['name'], 'source_work=%s-oar-%s' % (HULL, o['bank']),
                'at=' + cli.xyz(o['at']), 'pivot=' + cli.xyz(PL['pivot'][o['bank']]), 'rotate=' + cli.xyz(o['rotate']), 'scale=0.5,0.5,0.5',
                'overwrite=1', 'meta=' + json.dumps(o['meta'], ensure_ascii=False, sort_keys=True), 'note=draft_oars.py（槳口 x %d z %d）' % (o['port_x'], o['port_z'])]
        if o['mirror']:
            args.append('mirror=' + o['mirror'])
        cli.run(args, quiet=True)
        n += 1
    print('  models', n)
print(step, 'done')
