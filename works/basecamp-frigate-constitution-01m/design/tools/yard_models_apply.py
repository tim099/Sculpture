# 階段三十三：照 design/yard_models_placement.json 下 CLI —— 帆桁改外部模型
# 用法：python -I yard_models_apply.py <design 資料夾> <步驟> [帆桁名 regex]
#   步驟：create（開子作品＋記 0.1 m）｜stamp（落沒轉的帆桁）｜anchors（子作品固定點）｜models（桅杆子作品裡放模型）｜
#         rebind（帆角與帆腳索改 model: 路徑）｜carve（從桅杆子作品刻掉舊帆桁，顏色守門）｜unanchor（拿掉桅杆子作品裡的舊帆桁固定點）
#   · 每一步重跑一樣（create 已存在 ⇒ 略過；stamp 子作品已有格 ⇒ 略過；其他 overwrite=1）
import sys, os, json, re, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
ASM = 'basecamp-frigate-constitution-01m-assembly'
PL = [p for p in json.load(open(os.path.join(D, 'yard_models_placement.json'), encoding='utf-8'))['placements'] if flt.search(p['member'])]
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['yards']
LABEL = {Y['name']: Y['label'] for Y in plan['yards']}
LABEL.update({'spanker-gaff': 'spanker gaff', 'spanker-boom': 'spanker boom', 'spritsail': 'spritsail yard'})
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
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('🔢') or l.startswith('✓'))[-1200:])
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
            cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + p['work'], 'title=憲法號 帆桁 %s（%g ft）' % (LABEL[p['member']], p['meta']['length_ft']),
                 'size=' + xyz(p['size']), 'parent_work=' + p['host'], 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + p['work'], 'meters_per_voxel=0.1'])

elif step == 'stamp':
    for p in PL:
        path = os.path.join(D, 'masks', 'yard_models', p['member'] + '.vox.txt').replace('\\', '/')
        cli(['op=stampvox', 'persona=basecamp', 'work=' + p['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % p['cells']], show=True)

elif step == 'anchors':
    pts = json.load(open(os.path.join(D, 'rig_points_yard_models.json'), encoding='utf-8'))['points']
    O = {p['work']: p['origin'] for p in PL}
    for a in pts:
        if a['owner'] not in O:
            continue
        loc = [a['world'][i] - O[a['owner']][i] for i in range(3)]
        note = '%s（rig_points_yard_models.json；沒轉時的組裝件座標 %s%s）' % (a['kind'], xyz(a['world']), '；舊名 ' + a['old'] if a['old'] else '')
        cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + a['owner'], 'name=' + a['name'], 'at=' + xyz(loc), 'overwrite=1', 'note=' + note])

elif step == 'models':
    for p in PL:
        cli(['op=work', 'sub=model', 'persona=basecamp', 'work=' + p['host'], 'name=' + p['model'], 'source_work=' + p['work'],
             'at=' + xyz(p['at']), 'pivot=' + xyz(p['pivot']), 'rotate=' + xyz(p['rotate']), 'scale=1,1,1', 'overwrite=1',
             'meta=' + json.dumps(p['meta'], ensure_ascii=False), 'note=帆桁（階段三十三：子作品＋模型引用，繞 pivot 那一格的 z 軸轉）'], show=True)

elif step == 'rebind':
    # 舊端點 `<桅關聯>/<帆桁>.<點>` → `model:<桅關聯>/yard-<帆桁>/<點>`
    M = {}
    for p in PL:
        M[p['link'] + '/' + p['member'] + '.'] = 'model:%s/%s/' % (p['link'], p['model'])

    def conv(s):
        for k, v in M.items():
            if s.startswith(k):
                return v + s[len(k):], True
        return s, False
    S = json.load(open(os.path.join(os.path.dirname(os.path.dirname(D)), ASM, 'sails.json'), encoding='utf-8'))['sails']
    for s in S:
        cs = [conv(c['at']) for c in s['corners']]
        if not any(f for _, f in cs):
            continue
        args = ['op=work', 'sub=sail', 'persona=basecamp', 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(c for c, _ in cs),
                'corner_names=' + '|'.join(c['name'] for c in s['corners']), 'bind=' + ','.join(str(b) for b in s['bind']),
                'fullness=%g' % s['fullness'], 'color=' + s['color'], 'overwrite=1', 'note=' + s['note']]
        fr = [c['name'] for c in s['corners'] if not c['pin']]
        if fr:
            args.append('free=' + ','.join(fr))
        if s.get('res'):
            args.append('res=%d' % s['res'])
        print('sail', s['name'], [c for c, f in cs if f])
        cli(args)
    R = json.load(open(os.path.join(os.path.dirname(os.path.dirname(D)), ASM, 'ropes.json'), encoding='utf-8'))['ropes']
    for r in R:
        a, fa = conv(r['from'])
        b, fb = conv(r['to'])
        if not (fa or fb):
            continue
        args = ['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=' + r['name'], 'from=' + a, 'to=' + b, 'overwrite=1',
                'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'note=' + r.get('note', '')]
        if r.get('group'):
            args.append('group=' + r['group'])
        print('rope', r['name'], a if fa else '', b if fb else '')
        cli(args)

elif step == 'carve':
    seen = set()
    for p in PL:
        if p['host'] in seen:
            continue
        seen.add(p['host'])
        m = [k for k, w in plan['works'].items() if w == p['host']][0]
        path = os.path.join(D, 'masks', 'yard_models', 'carve_' + m + '.vox.txt').replace('\\', '/')
        n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
        cli(['op=carvevox', 'persona=basecamp', 'work=' + p['host'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n], show=True)

elif step == 'unanchor':
    pts = json.load(open(os.path.join(D, 'rig_points_yard_models.json'), encoding='utf-8'))['points']
    H = {p['member']: p['host'] for p in PL}
    for a in pts:
        if a['old'] and a['member'] in H:
            cli(['op=work', 'sub=unanchor', 'persona=basecamp', 'work=' + H[a['member']], 'name=' + a['old']])
else:
    raise SystemExit('步驟？ create|stamp|anchors|models|rebind|carve|unanchor')
print(step, 'ok', ok, 'bad', bad)
