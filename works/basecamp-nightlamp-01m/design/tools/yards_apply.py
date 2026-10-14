# 階段十四：照 design/yards_placement.json、rig_points_yards.json 下 CLI —— 帆桁子作品＋桅杆子作品裡的模型
# 用法：python -I yards_apply.py <design 資料夾> <步驟> [帆桁名 regex]
#   步驟：create（開子作品＋記 0.1 m）｜stamp（落沒轉的帆桁）｜anchors（子作品固定點）｜models（桅杆子作品裡放模型＋meta）｜readback（讀回對拍）
#   · 每一步重跑一樣（create 已存在 ⇒ 略過；stamp 子作品已有格 ⇒ 擋下、照實印；anchors／models overwrite=1）
import sys, os, json, re, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
WORKS = os.path.dirname(os.path.dirname(D))
PL = [p for p in json.load(open(os.path.join(D, 'yards_placement.json'), encoding='utf-8'))['placements'] if flt.search(p['member'])]
ok = bad = 0


def cli(args, show=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:4]), (r.stdout + r.stderr)[-500:])
    else:
        ok += 1
        if show:
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('🔢 placed') or l.startswith('✓'))[-600:])
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%g' % c for c in v)


if step == 'create':
    for p in PL:
        if os.path.exists(os.path.join(WORKS, p['work'], 'work.json')):
            print('已有', p['work'])
        else:
            cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + p['work'], 'title=' + p['title'], 'size=' + xyz(p['size']),
                 'parent_work=' + p['host'], 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + p['work'], 'meters_per_voxel=0.1'])

elif step == 'stamp':
    for p in PL:
        path = os.path.join(D, 'masks', 'yards', p['member'] + '.vox.txt').replace('\\', '/')
        cli(['op=stampvox', 'persona=basecamp', 'work=' + p['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % p['cells'], 'share=0'], show=True)

elif step == 'anchors':
    pts = json.load(open(os.path.join(D, 'rig_points_yards.json'), encoding='utf-8'))['points']
    W = {p['work'] for p in PL}
    for a in pts:
        if a['owner'] not in W:
            continue
        cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + a['owner'], 'name=' + a['name'], 'at=' + xyz(a['local']), 'overwrite=1',
             'note=%s（rig_points_yards.json；沒轉時的組裝件座標 %s）' % (a['kind'], xyz(a['world']))])

elif step == 'models':
    for p in PL:
        cli(['op=work', 'sub=model', 'persona=basecamp', 'work=' + p['host'], 'name=' + p['model'], 'source_work=' + p['work'],
             'at=' + xyz(p['at']), 'pivot=' + xyz(p['pivot']), 'rotate=' + xyz(p['rotate']), 'scale=1,1,1', 'overwrite=1',
             'meta=' + json.dumps(p['meta'], ensure_ascii=False), 'note=帆桁（階段十四：子作品＋模型引用，繞 pivot 那一格的 z 軸轉）'], show=True)

elif step == 'readback':
    pts = json.load(open(os.path.join(D, 'rig_points_yards.json'), encoding='utf-8'))['points']
    for p in PL:
        w = os.path.join(WORKS, p['work'])
        A = {a['name']: a for a in json.load(open(os.path.join(w, 'anchors.json'), encoding='utf-8'))['anchors']}
        want = {a['name']: a['local'] for a in pts if a['owner'] == p['work']}
        miss = [n for n in want if n not in A]
        diff = [n for n in want if n in A and [round(c) for c in A[n]['at']] != want[n]]
        M = {m['name']: m for m in json.load(open(os.path.join(WORKS, p['host'], 'models.json'), encoding='utf-8'))['models']}
        m = M.get(p['model'])
        mok = m is not None and m.get('meta') == p['meta'] and m.get('work') == p['work']
        print(p['member'], 'anchors', len(A), '/', len(want), 'missing', len(miss), 'diff', len(diff), 'model', 'ok' if mok else ('✗ ' + json.dumps(m, ensure_ascii=False)[:300]))
else:
    raise SystemExit('步驟？ create|stamp|anchors|models|readback')
print(step, 'ok', ok, 'bad', bad)
