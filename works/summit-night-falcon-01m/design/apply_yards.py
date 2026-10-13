# 階段八：照 verify_yards.json 的 placements 下 CLI —— 帆桁子作品＋模型
# 用法：python -I -X utf8 -B apply_yards.py <design 資料夾> <步驟> [帆桁名 regex]
#   步驟：create（開子作品＋記 0.1 m）｜stamp（落帆桁，每刀讀回 placed）｜anchors（子作品固定點）｜models（桅杆子作品裡放模型）
#   · create 已存在 ⇒ 略過；anchors／models 用 overwrite=1 ⇒ 重跑一樣
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
PL = [p for p in json.load(open(os.path.join(D, 'verify_yards.json'), encoding='utf-8'))['placements'] if flt.search(p['member'])]
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗ rc=%d' % r.returncode, ' '.join(args[:4]), (r.stdout + r.stderr)[-600:])
    else:
        ok += 1
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%g' % c for c in v)


if step == 'create':
    for p in PL:
        rc, o = cli(['op=work', 'sub=show', 'work=' + p['work']])
        if rc == 0:
            print('已有', p['work'])
        else:
            bad -= 1
            cli(['op=work', 'sub=create', 'persona=summit', 'id=' + p['work'], 'title=' + p['title'], 'size=' + xyz(p['size']),
                 'parent_work=' + p['host'], 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + p['work'], 'meters_per_voxel=0.1'])
        print('create', p['work'], xyz(p['size']))

elif step == 'stamp':
    for p in PL:
        path = os.path.join(D, p['file']).replace('\\', '/')
        rc, o = cli(['op=stampvox', 'persona=summit', 'work=' + p['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % p['cells'], 'draft=0'])
        m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', o)
        print('stamp', p['member'], 'cells', p['cells'], 'placed', m.group(1) if m else '?')

elif step == 'anchors':
    for p in PL:
        for a in p['anchors']:
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + p['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
                 'note=%s（verify_yards.json；沒轉時的世界座標 %s）' % (a['kind'], xyz(a['world']))])
        print('anchors', p['member'], len(p['anchors']))

elif step == 'models':
    for p in PL:
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + p['host'], 'name=' + p['model'], 'source_work=' + p['work'],
             'at=' + xyz(p['at']), 'pivot=' + xyz(p['pivot']), 'rotate=' + xyz(p['rotate']), 'scale=1,1,1', 'overwrite=1',
             'meta=' + json.dumps(p['meta'], ensure_ascii=False, sort_keys=True),
             'note=帆桁（階段八：子作品＋模型引用；方帆桁繞自己的中心、gaff／boom 繞主桅軸心；轉 z 跟風、y 是 gaff／boom 的上翹）'])
        print('model', p['host'], p['model'], xyz(p['rotate']))
elif step == 'turn':
    # 試轉：python apply_yards.py <design> turn <帆桁名 regex> <rz 度> —— 只換 rotate 的 z（y 照 placement）；meta 不動（meta 記的是預設角）。
    # 轉回預設 ＝ 再跑一次 models（或 turn … 0）。
    rz = float(sys.argv[4])
    for p in PL:
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + p['host'], 'name=' + p['model'], 'source_work=' + p['work'],
             'at=' + xyz(p['at']), 'pivot=' + xyz(p['pivot']), 'rotate=' + xyz([0, p['rotate'][1], rz]), 'scale=1,1,1', 'overwrite=1',
             'meta=' + json.dumps(p['meta'], ensure_ascii=False, sort_keys=True),
             'note=帆桁（階段八：子作品＋模型引用；方帆桁繞自己的中心、gaff／boom 繞主桅軸心；轉 z 跟風、y 是 gaff／boom 的上翹）'])
        print('turn', p['model'], xyz([0, p['rotate'][1], rz]))
else:
    raise SystemExit('步驟？ create|stamp|anchors|models|turn')
print(step, 'ok', ok, 'bad', bad)
