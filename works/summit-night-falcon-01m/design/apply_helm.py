# 階段十五：照 verify_helm.json 下 CLI —— 舵輪兩件子作品＋模型；舵：gudgeon 搬回船殼、組裝件拿掉關聯「舵」、改成外部模型
# 用法：python -I -X utf8 -B apply_helm.py <design 資料夾> <步驟>
#   步驟：create（-wheel、-helm-stand，parent 甲板-後、0.02 m）｜stamp（兩件各一刀）｜anchors（兩件＋舵）｜
#         rudder（船殼 mark stage15 begin → 貼 gudgeon → end；舵子作品刻 gudgeon）｜unlink（組裝件拿掉關聯 舵）｜models（舵、舵輪、舵輪座）
#   · create 已存在 ⇒ 略過；anchors／models 用 overwrite=1 ⇒ 重跑一樣；rudder／unlink 只跑一次；⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_helm.json'), encoding='utf-8'))
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


xyz = lambda v: ','.join('%g' % c for c in v)
parts = [('wheel', '夜隼號 舵輪（會轉的：輪、輪幅、輪轂與隼的疤、輪軸、鼓輪；0.02 m）'), ('stand', '夜隼號 舵輪座（底座、兩根支柱；0.02 m）')]
if step == 'create':
    for key, title in parts:
        w = V[key]['work']
        rc, _ = cli(['op=work', 'sub=show', 'work=' + w])
        if rc == 0:
            print('已有', w)
        else:
            bad -= 1
            cli(['op=work', 'sub=create', 'persona=summit', 'id=' + w, 'title=' + title, 'size=' + xyz(V['size']), 'parent_work=' + PRE + '-deck-quarter', 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + w, 'meters_per_voxel=%g' % V['mpv']])
        print('create', w)
elif step == 'stamp':
    for key, _ in parts:
        path = os.path.join(D, V[key]['file']).replace('\\', '/')
        rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + V[key]['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % V[key]['cells'], 'draft=0'])
        m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', out)
        print('stamp', key, V[key]['cells'], 'placed', m.group(1) if m else '?')
elif step == 'anchors':
    for key, _ in parts:
        for name, at in V[key]['anchors'].items():
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + V[key]['work'], 'name=' + name, 'at=' + xyz(at), 'overwrite=1', 'note=階段十五 draft_helm.py'])
    for name, at in V['rudder']['anchors'].items():
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + V['rudder']['work'], 'name=' + name, 'at=' + xyz(at), 'overwrite=1', 'note=階段十五 舵頭（之後舵柄／舵索用）'])
    print('anchors')
elif step == 'rudder':
    so = V['stamp_order']
    cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + PRE, 'name=stage15', 'phase=begin', 'note=階段十五：gudgeon 從舵搬回船殼'])
    for o in so['hull']:
        rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + PRE, 'voxels=' + os.path.join(D, o['file']).replace('\\', '/'), 'at=0,0,0',
                       'expect_pixels=%d' % o['voxels'], 'draft=0'])
        m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', out); print('hull gudgeons', o['voxels'], 'placed', m.group(1) if m else '?')
    cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + PRE, 'name=stage15', 'phase=end', 'note=階段十五'])
    cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + V['rudder']['work'], 'name=stage15', 'phase=begin', 'note=階段十五：舵改外部模型；gudgeon 搬去船殼'])
    for o in so['rudder']:
        rc, out = cli(['op=carvevox', 'persona=summit', 'work=' + V['rudder']['work'], 'voxels=' + os.path.join(D, o['file']).replace('\\', '/'), 'at=0,0,0',
                       'expect_pixels=%d' % o['voxels'], 'draft=0'])
        print('rudder carve', o['voxels'], 'rc', rc, re.findall(r'🔢 (?:carved|removed|placed) = \d+', out))
    cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + V['rudder']['work'], 'name=stage15', 'phase=end', 'note=階段十五'])
elif step == 'unlink':
    cli(['op=work', 'sub=unlink', 'persona=summit', 'work=' + ASM, 'name=' + V['rudder']['unlink']])
    print('unlink', V['rudder']['unlink'])
elif step == 'models':
    r = V['rudder']
    cli(['op=work', 'sub=model', 'persona=summit', 'work=' + ASM, 'name=' + r['model'], 'source_work=' + r['work'], 'at=' + xyz(r['at']),
         'pivot=' + xyz(r['pivot']), 'rotate=0,0,0', 'scale=1', 'overwrite=1', 'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True),
         'note=舵（階段十五：外部模型；轉軸 ＝ 舵柱中心線，見 meta hinge_*／axis_*）'])
    for m in V['models']:
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + V['host'], 'name=' + m['name'], 'source_work=' + m['work'], 'at=' + xyz(V['at']),
             'pivot=' + xyz(V['pivot']), 'rotate=0,0,0', 'scale=%g' % V['scale'], 'overwrite=1', 'meta=' + json.dumps(m['meta'], ensure_ascii=False, sort_keys=True),
             'note=舵輪（階段十五：pivot ＝ 輪軸中心）'])
    print('models')
else:
    raise SystemExit('步驟？ create|stamp|anchors|rudder|unlink|models')
print(step, 'ok', ok, 'bad', bad)
