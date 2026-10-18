# 落地：子作品 → 落格（每刀讀回 placed）→ 關聯 → 固定點 → 模型 → meta。每一步重跑都安全（已有格的不重貼；關聯／固定點／模型 overwrite）。
# 用法：python -I -X utf8 -B apply_all.py <步驟>   步驟：works｜stamp｜links｜anchors｜models｜meta｜all
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli, dro

D = dro.D
step = sys.argv[1]
VH = json.load(open(os.path.join(D, 'verify_hull.json'), encoding='utf-8')); ZAIR = VH['zair']
VU = json.load(open(os.path.join(D, 'verify_upper.json'), encoding='utf-8'))
VR = json.load(open(os.path.join(D, 'verify_rig.json'), encoding='utf-8'))
VS = json.load(open(os.path.join(D, 'verify_steer.json'), encoding='utf-8'))
VM = json.load(open(os.path.join(D, 'verify_models.json'), encoding='utf-8'))
HULL, ASM = 'erina-dromon-01m', 'erina-dromon-01m-assembly'
FULL = dro.PLAN['frame']['size']
geo = VU['_geo']

# 子作品：(id 尾巴, 標題, 清單, 關聯名, 框)
SUBS = [
    ('deck-main', '持火號 主甲板（katastrōma：甲板板＋橫樑；兩個艙口）', 'lists/deck_main.txt', '甲板-main', FULL),
    ('deck-hold', '持火號 艙底走道（下層槳手的地板）', 'lists/deck_hold.txt', '甲板-hold', FULL),
    ('forecastle', '持火號 艏樓（pseudopation：siphon 上面的木板平台與胸牆）', VU['forecastle']['file'], '艏樓', FULL),
    ('castles', '持火號 木塔（xylokastra：中線兩側各一座）', VU['castles']['file'], '木塔', FULL),
    ('fittings', '持火號 艉舵橫樑與舵箱、艏錨架、帆腳繫柱', VU['fittings']['file'], '舵橫樑與吊架', FULL),
    ('magazine', '持火號 希臘火藥庫（艙底隔間）', VU['magazine']['file'], '藥庫', FULL),
    ('ladders', '持火號 梯子（艙口兩座、艏樓、木塔兩座）', VU['ladders']['file'], '梯子', FULL),
    ('mast-fore', '持火號 前桅（前傾 13°、11.85 m）', VR['masts']['fore']['file'], '桅-fore', FULL),
    ('mast-main', '持火號 中桅（8.3 m）', VR['masts']['main']['file'], '桅-main', FULL),
    ('rudder', '持火號 舷側舵（pēdalion：舵葉、舵桿、舵柄；S 舷，P 舷用鏡像；整船的框）', VS['file'], None, FULL),
    ('yard-fore', '持火號 前三角帆桁（20.17 m；沒轉、沿 x）', VR['yards']['fore']['file'], None, VR['yards']['fore']['size']),
    ('yard-main', '持火號 中三角帆桁（15.43 m；沒轉、沿 x）', VR['yards']['main']['file'], None, VR['yards']['main']['size']),
]


def has(wid):
    rc, out = cli.run(['op=stats', 'work=' + wid], quiet=True)
    return int((cli.val(out, 'total_voxels') or '0').replace(',', ''))


def count(path):
    return sum(1 for ln in open(os.path.join(D, path), encoding='utf-8') if ln.strip() and ln[0] != '#')


if step in ('works', 'all'):
    for tail, title, f, ln, size in SUBS:
        cli.ensure_work(HULL + '-' + tail, title, size, HULL, 0.1)

if step in ('stamp', 'all'):
    for wid, f in [(HULL, 'lists/hull.txt')] + [(HULL + '-' + t, f) for t, _, f, _, _ in SUBS]:
        n = count(f)
        h = has(wid)
        if h == n:
            print('  %s 已有 %d 格' % (wid, h)); continue
        if h:
            raise SystemExit('%s 已有 %d 格、清單 %d 格 —— 不一樣，先處理（⛔ 不疊貼）' % (wid, h, n))
        cli.stamp(wid, os.path.join(D, f), n)

if step in ('links', 'all'):
    for tail, title, f, ln, size in SUBS:
        if ln:
            cli.run(['op=work', 'sub=link', 'persona=erina', 'work=' + ASM, 'name=' + ln, 'source_work=' + HULL + '-' + tail, 'at=0,0,0', 'overwrite=1'])

if step in ('anchors', 'all'):
    A = []
    A += [(HULL + '-fittings', k, v) for k, v in VU['fittings']['anchors'].items()]
    A += [(HULL + '-magazine', k, v) for k, v in VU['magazine']['anchors'].items()]
    A += [(HULL + '-ladders', k, v) for k, v in VU['ladders']['anchors'].items()]
    for m in ('fore', 'main'):
        A += [(HULL + '-mast-' + m, k, v) for k, v in VR['masts'][m]['anchors'].items()]
        A += [(HULL + '-yard-' + m, k, v) for k, v in VR['yards'][m]['anchors'].items()]
    A += [(HULL + '-rudder', k, v) for k, v in VS['anchors'].items()]
    for wid, k, v in A:
        cli.anchor(wid, k, v, 'erina design（draft_*.py）')
    print('  anchors', len(A))

if step in ('models', 'all'):
    host = {'assembly': ASM, 'fittings': HULL + '-fittings', 'forecastle': HULL + '-forecastle', 'castles': HULL + '-castles', 'magazine': HULL + '-magazine',
            'mast-fore': HULL + '-mast-fore', 'mast-main': HULL + '-mast-main'}
    for m in VM:
        sc = m['scale'] if isinstance(m['scale'], list) else [m['scale']] * 3
        args = ['op=work', 'sub=model', 'persona=erina', 'work=' + host[m['host']], 'name=' + m['name'], 'source_work=' + m['source_work'],
                'at=' + cli.xyz(m['at']), 'pivot=' + cli.xyz(m['pivot']), 'rotate=' + cli.xyz(m['rotate']), 'scale=' + cli.xyz(sc),
                'overwrite=1', 'meta=' + json.dumps(m['meta'], ensure_ascii=False, sort_keys=True)]
        if m.get('mirror'):
            args.append('mirror=' + m['mirror'])
        cli.run(args, quiet=True)
        print('  model', m['host'], m['name'])

if step in ('meta', 'all'):
    def floor_of(xs, zf):
        return ','.join('%d:%d' % (x, zf(x)) for x in xs)
    main_xs = list(range(44, 351, 10)) + [350]
    LM = {
        '船殼': {'kind': 'ship', 'waterline_z': dro.PLAN['waterline_z']},
        '甲板-hold': {'kind': 'deck', 'deck': 'hold', 'level': 0, 'name': '艙底（下層槳手）', 'floor': '%d:%d,%d:%d' % (dro.PLAN['deck_hold']['x0'], dro.PLAN['deck_hold']['z'] + 1, dro.PLAN['deck_hold']['x1'], dro.PLAN['deck_hold']['z'] + 1), 'thick': 1},
        '甲板-main': {'kind': 'deck', 'deck': 'main', 'level': 1, 'name': '主甲板', 'floor': floor_of(main_xs, lambda x: ZAIR[x]), 'thick': 2},
        '艏樓': {'kind': 'deck', 'deck': 'forecastle', 'level': 2, 'name': '艏樓（pseudopation）', 'floor': '%d:%d,%d:%d' % (geo['forecastle'][0], geo['forecastle'][2] + 1, geo['forecastle'][1], geo['forecastle'][2] + 1), 'thick': 2},
        '木塔': {'kind': 'deck', 'deck': 'castle', 'level': 2, 'name': '木塔（xylokastra）', 'floor': '%d:%d,%d:%d' % (geo['castles'][0], geo['castles'][4] + 1, geo['castles'][1], geo['castles'][4] + 1), 'thick': 2},
        '梯子': {'kind': 'ladders'},
        '藥庫': {'kind': 'magazine', 'powder_lb': 600, 'pos': 'aft'},
    }
    for ln, meta in LM.items():
        cli.run(['op=work', 'sub=meta', 'persona=erina', 'work=' + ASM, 'part=link', 'name=' + ln, 'meta=' + json.dumps(meta, ensure_ascii=False, sort_keys=True)], quiet=True)
        print('  meta link', ln, meta.get('kind'))
print(step, 'done')
