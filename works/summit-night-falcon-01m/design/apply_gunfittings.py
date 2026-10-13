# 階段十四：照 verify_gunfittings.json 下 CLI —— 砲具子作品（一舷）＋兩條關聯（S、P mirror=y）＋ 60 條砲索
# 用法：python -I -X utf8 -B apply_gunfittings.py <design 資料夾> <步驟> [繩名 regex]
#   步驟：create（開子作品，parent 甲板-主、記 0.1 m）｜stamp（每刀印 placed）｜anchors｜links（組裝件）｜ropes（組裝件，分組 guns/…）
#   · create 已存在 ⇒ 略過；anchors／links／ropes 用 overwrite=1 ⇒ 重跑一樣；⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
V = json.load(open(os.path.join(D, 'verify_gunfittings.json'), encoding='utf-8'))
PRE = 'summit-night-falcon-01m'
ASM = PRE + '-assembly'
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


xyz = lambda v: ','.join('%d' % c for c in v)
if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + V['work']])
    if rc == 0:
        print('已有', V['work'])
    else:
        bad -= 1
        cli(['op=work', 'sub=create', 'persona=summit', 'id=' + V['work'], 'title=夜隼號 砲具（一舷：船牆與甲板的環首螺栓）',
             'size=' + xyz(V['frame_size']), 'parent_work=' + PRE + '-deck-main', 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + V['work'], 'meters_per_voxel=0.1'])
    print('create', V['work'])
elif step == 'stamp':
    for o in V['stamp_order']['fittings']:
        path = os.path.join(D, o['file']).replace('\\', '/')
        rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + V['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % o['voxels'], 'draft=0'])
        m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', out)
        print('stamp', o['voxels'], 'placed', m.group(1) if m else '?')
elif step == 'anchors':
    for a in V['anchors']:
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + V['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
             'note=%s（階段十四 verify_gunfittings.json；世界座標 %s）' % (a['kind'], xyz(a['world']))])
    print('anchors', len(V['anchors']))
elif step == 'links':
    for l in V['links']:
        args = ['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=' + l['name'], 'source_work=' + V['work'], 'at=' + xyz(l['at']), 'overwrite=1',
                'note=階段十四 砲具']
        if l['mirror']:
            args.append('mirror=' + l['mirror'])
        cli(args); print('link', l['name'], xyz(l['at']), l['mirror'])
elif step == 'ropes':
    for r in V['ropes']:
        if not flt.search(r['name']):
            continue
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=砲索（階段十四）'])
    print('ropes', sum(1 for r in V['ropes'] if flt.search(r['name'])))
else:
    raise SystemExit('步驟？ create|stamp|anchors|links|ropes')
print(step, 'ok', ok, 'bad', bad)
