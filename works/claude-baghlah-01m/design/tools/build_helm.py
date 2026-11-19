# Source: calli-cosecha-01m/design/tools/build_rudder_anchor.py (Harvest, TASK-0619) -- rewritten for the Star (TASK-0019 step 11).
# Step 11 placement from helm_placement.json:
#   carve  : the trunk -- carvevox the step-11 carve lists on the hull, the poop deck and the stern carving (expect_pixels;
#            carved must equal the list)
#   works  : rudder, tiller, helm fittings (collar), stem rollers -- 420x160x120, 0.1 m, world lists at 0,0,0: create +
#            stampvox (placed must equal the list); rudder anchor stock-top
#   links  : assembly links 舵頭圈, 艏柱滾輪 (at 0,0,0)
#   models : assembly models 舵 (kind=rudder), 舵柄 (kind=tiller) at = pivot = hinge; deck-main models 錨-S, 錨-P (P mirror=y)
#   hawse  : hull anchors hawse-S / hawse-P (roller tops)
#   Usage: python -X utf8 tools/build_helm.py <design> <stage>   stage = carve | works | links | models | hawse   (SENATE = wrapper path)
#   * Stops at the first non-zero exit (only 0 counts). A work that already exists is neither recreated nor restamped
#     (cell changes go through delta_apply); anchors and models use overwrite=1; a link that exists is not re-added.
import glob, json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
stage = sys.argv[2]
HULL = 'claude-baghlah-01m'
PERSONA = 'Claude-Ojousama'
SENATE = os.environ.get('SENATE', 'senate')
WORKS = os.path.dirname(os.path.dirname(design))
NOTE = '步驟 11（TASK-0019；design/draft_helm.py）'
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
HB = plan['helm_build']
DECK = plan['gear_build']['deck_works']
PL = json.load(open(os.path.join(design, 'helm_placement.json'), encoding='utf-8'))
ASM = HB['assembly']
CARVE_WORK = {'hull': HULL, 'deck-poop': HULL + '-deck-poop', 'stern-carving': HULL + '-stern-carving'}


def cli(*args):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode != 0:
        print(out[-2000:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args)[:300]))
    return out


def num(v):
    return ('%.4f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


def count(path):
    return sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))


def meta(d):
    return 'meta=' + json.dumps(d, ensure_ascii=False, separators=(',', ':'))


def replay(work_dir):
    cells = {}
    for p in sorted(glob.glob(os.path.join(work_dir, 'events', '*', '*.json'))):
        e = json.load(open(p, encoding='utf-8'))
        if 'placed_colored' in e:
            for x, y, z, c in e['placed_colored']:
                cells[(x, y, z)] = c
        elif e.get('op') == 'box':
            for x, y, z in e.get('placed_voxels', []):
                cells[(x, y, z)] = e['color']
        if 'carved_voxels' in e:
            for v in e['carved_voxels']:
                cells.pop(tuple(v[:3]), None)
        if e.get('op') == 'workedit':
            for a in e['edit'].get('after', []):
                k = (a['x'], a['y'], a['z'])
                if a['color']:
                    cells[k] = a['color']
                else:
                    cells.pop(k, None)
    return cells


if stage == 'carve':
    for w, rel in PL['carve'].items():
        path = os.path.join(design, 'masks', rel + '.vox.txt')
        n = count(path)
        lst = {tuple(map(int, l.split(',')[:3])) for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#')}
        left = len(lst & set(replay(os.path.join(WORKS, CARVE_WORK[w]))))
        if left == 0:
            print('· %s: all %d already carved (events replay)' % (CARVE_WORK[w], n))
            continue
        if left != n:
            raise SystemExit('✗ %s: %d of %d still there (partly carved?)' % (CARVE_WORK[w], left, n))
        out = cli('op=carvevox', 'persona=' + PERSONA, 'work=' + CARVE_WORK[w], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n)
        got = {k: int(v) for k, v in re.findall(r'🔢 (placed|already_empty|list_count) = (\d+)', out)}
        print('✓ carvevox %s: list %d, engine placed %s, already empty %s' % (CARVE_WORK[w], n, got.get('placed'), got.get('already_empty')), flush=True)
        if not (got.get('list_count') == n and (got.get('placed') == n or (got.get('placed') == 0 and got.get('already_empty') == n))):
            print(out[-1500:])
            raise SystemExit('✗ carvevox counts %s, list %d' % (got, n))      # a rerun after a full carve reads placed 0, already_empty n
elif stage == 'works':
    for part, rel in (('rudder', 'helm/rudder'), ('tiller', 'helm/tiller'), ('fittings', 'helm/fittings'), ('rollers', 'helm/rollers')):
        P = HB[part]
        w = P['work']
        if os.path.exists(os.path.join(WORKS, w, 'work.json')):
            print('· exists', w)
            continue
        path = os.path.join(design, 'masks', rel + '.vox.txt')
        n = count(path)
        cli('op=work', 'sub=create', 'persona=' + PERSONA, 'work=' + w, 'title=' + P['title'], 'parent_work=' + HULL, 'size=420,160,120', 'tags=sub')
        cli('op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + w, 'meters_per_voxel=0.1')
        out = cli('op=stampvox', 'persona=' + PERSONA, 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
        m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
        got = int(m.group(1).replace(',', '')) if m else None
        if got != n:
            print(out[-1500:])
            raise SystemExit('✗ placed %s != %d (%s)' % (got, n, w))
        print('✓ created %s, stampvox %d' % (w, n), flush=True)
    R = PL['rudder']
    for an, at in R['anchors'].items():
        cli('op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + R['work'], 'name=' + an, 'at=' + xyz(at), 'overwrite=1',
            'note=%s：舵頭（遊戲在它旁邊 8 格內找掛住的船尾格；Ship_Game §9 rudder）' % NOTE)
    print('✓ anchor stock-top', R['anchors']['stock-top'])
elif stage == 'links':
    links = json.load(open(os.path.join(WORKS, ASM, 'links.json'), encoding='utf-8'))
    have = {l['name'] for l in (links if isinstance(links, list) else links.get('links', []))}
    for l in PL['links']:
        if l['link'] in have:
            print('· link exists', l['link'])
            continue
        cli('op=work', 'sub=link', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + l['link'], 'source_work=' + l['work'], 'at=0,0,0', 'note=%s：%s' % (NOTE, l['title']))
        print('✓ link', l['link'])
elif stage == 'models':
    for key, what in (('rudder', '舵（at ＝ pivot ＝ 鉸鏈下端 ⇒ 子作品的世界座標原樣；spin 照舵角轉）'), ('tiller', '舵柄（繞舵的鉸鏈軸轉；kind=tiller 是操舵鏈的操作端）')):
        M = PL[key]
        cli('op=work', 'sub=model', 'persona=' + PERSONA, 'work=' + M['host'], 'name=' + M['model'], 'source_work=' + M['work'], 'at=' + xyz(M['at']),
            'pivot=' + xyz(M['pivot']), 'rotate=0,0,0', 'scale=1,1,1', 'overwrite=1', meta(M['meta']), 'note=%s：%s' % (NOTE, what))
        print('✓ model', M['model'])
    for a in PL['anchors']:
        s = float(a['scale'])
        args = ['op=work', 'sub=model', 'persona=' + PERSONA, 'work=' + DECK[a['host']], 'name=' + a['name'], 'source_work=' + a['work'], 'at=' + xyz(a['at']),
                'pivot=' + xyz(a['pivot']), 'rotate=0,0,' + num(float(a['rotate'])), 'scale=' + xyz([s, s, s]), 'overwrite=1', meta(a['meta']),
                'note=%s：共用四爪錨 × %g、出海收在船頭水槽甲板上（PT）' % (NOTE, s)]
        if a['mirror']:
            args.append('mirror=' + a['mirror'])
        cli(*args)
        print('✓ model', a['name'])
elif stage == 'hawse':
    for nm, at in PL['hawse'].items():
        cli('op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + HULL, 'name=' + nm, 'at=' + xyz(at), 'overwrite=1',
            'note=%s：錨鏈孔 ＝ 艏柱滾輪頂（PT：巴格拉沒有錨鏈孔，錨纜壓在艏柱的滾輪上）' % NOTE)
        print('✓ hull anchor', nm, at)
else:
    raise SystemExit('stage = carve | works | links | models | hawse')
