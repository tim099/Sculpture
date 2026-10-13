# 階段十：照 verify_belaying.json 下 CLI —— fife rails 與舷牆 pin rails 兩件子作品
# 用法：python -I -X utf8 -B apply_belaying.py <design 資料夾> <步驟>
#   步驟：create（開子作品＋記 0.1 m）｜stamp（每刀印 placed）｜anchors｜links（組裝件關聯；舷牆那件一舷＋鏡像）
#   · create 已存在 ⇒ 略過；anchors／links 用 overwrite=1 ⇒ 重跑一樣；⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_belaying.json'), encoding='utf-8'))
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['belaying']
PRE = 'summit-night-falcon-01m'
WK = {'fiferails': {'id': PRE + '-fiferails', 'parent': PRE + '-deck-main', 'title': '夜隼號 fife rails、bitts 與 main sheet horse', 'sub': plan['fife'], 'anc': 'fife',
                    'links': [('fife-rails', plan['fife']['frame_at'], '')]},
      'belaying_side': {'id': PRE + '-belaying-side', 'parent': PRE, 'title': '夜隼號 舷牆 pin rails（一舷）', 'sub': plan['side'], 'anc': 'side',
                        'links': [('繫繩欄', plan['side']['frame_at'], ''),
                                  ('繫繩欄-鏡像', [plan['side']['frame_at'][0], 161 - plan['side']['frame_at'][1] - plan['side']['frame_size'][1], plan['side']['frame_at'][2]], 'y')]}}
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
for key, w in WK.items():
    if step == 'create':
        rc, _ = cli(['op=work', 'sub=show', 'work=' + w['id']])
        if rc == 0: print('已有', w['id'])
        else:
            bad -= 1
            cli(['op=work', 'sub=create', 'persona=summit', 'id=' + w['id'], 'title=' + w['title'], 'size=' + xyz(w['sub']['frame_size']), 'parent_work=' + w['parent'], 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + w['id'], 'meters_per_voxel=0.1'])
        print('create', w['id'])
    elif step == 'stamp':
        for o in V['stamp_order'][key]:
            path = os.path.join(D, o['file']).replace('\\', '/')
            rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + w['id'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % o['voxels'], 'draft=0'])
            m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', out)
            print('stamp', key, o['voxels'], 'placed', m.group(1) if m else '?')
    elif step == 'anchors':
        for a in V['anchors'][w['anc']]:
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + w['id'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
                 'note=%s（verify_belaying.json；世界座標 %s）' % (a['kind'], xyz(a['world']))])
        print('anchors', w['id'], len(V['anchors'][w['anc']]))
    elif step == 'links':
        for name, at, mir in w['links']:
            args = ['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=' + name, 'source_work=' + w['id'], 'at=' + xyz(at), 'overwrite=1',
                    'note=階段十 繫繩點']
            if mir: args.append('mirror=' + mir)
            cli(args); print('link', name, xyz(at), mir)
    else:
        raise SystemExit('步驟？ create|stamp|anchors|links')
print(step, 'ok', ok, 'bad', bad)
