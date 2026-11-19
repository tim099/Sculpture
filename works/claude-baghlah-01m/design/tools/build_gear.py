# Source: calli-cosecha-01m/design/tools/build_gear.py (Harvest) + apex-two-barbados-01m/design/tools/build_gear.py
#   (Barbados) -- rewritten for the Star (TASK-0019 step 10).
# Step 10 placement from gear_placement.json:
#   works  : the magazine, the boat skids (420x160x120, 0.1 m, world lists at 0,0,0) and the hearth (its own 24x20x16 frame,
#            0.05 m) -- create + stampvox (expect_pixels; placed must equal the list) + anchors (blast, door; smoke)
#   links  : assembly links 彈藥庫 (meta kind=magazine, pos, powder_lb, hoist) and 小艇架
#   models : barrels in the magazine work; boat, hearth, hatch covers, cabin door on deck-main; binnacle on deck-poop
#   Usage: python -X utf8 tools/build_gear.py <design> <stage>   stage = works | links | models   (SENATE = wrapper path)
#   * Stops at the first non-zero exit (only 0 counts: step 6 learned exit 2 hides a blocked link).
#   * A work that already exists is neither recreated nor restamped (cell changes go through delta_apply); anchors, links
#     and models use overwrite=1 where the CLI has it.
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
stage = sys.argv[2]
HULL = 'claude-baghlah-01m'
PERSONA = 'Claude-Ojousama'
SENATE = os.environ.get('SENATE', 'senate')
WORKS = os.path.dirname(os.path.dirname(design))
NOTE = '步驟 10（TASK-0019；design/draft_gear.py）'
GB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['gear_build']
PL = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))
ASM = GB['assembly']
HOST = dict(GB['deck_works'], magazine=GB['magazine']['work'])


def cli(*args):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode:
        print(out[-2000:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args[:6])))
    return out


def num(v):
    return ('%.7f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=' + PERSONA, 'work=' + work, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s != %d (%s)' % (got, n, work))
    print('  stampvox %s: %d' % (work, n), flush=True)


if stage == 'works':
    H = GB['hearth']
    todo = [(GB['magazine']['work'], GB['magazine']['title'], '420,160,120', 0.1, 'magazine', PL['magazine']['anchors'], '彈藥庫'),
            (GB['skids']['work'], GB['skids']['title'], '420,160,120', 0.1, 'skids', {}, '小艇架'),
            (H['work'], H['title'], ','.join(str(v) for v in H['size']), H['mpv'], 'hearth', PL['hearth']['anchors'], '沙箱灶')]
    for w, title, size, mpv, fn, anchors, what in todo:
        if os.path.exists(os.path.join(WORKS, w, 'work.json')):
            print('· exists', w)
        else:
            cli('op=work', 'sub=create', 'persona=' + PERSONA, 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=' + size, 'tags=sub')
            cli('op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + w, 'meters_per_voxel=%g' % mpv)
            print('✓ created', w, flush=True)
            stamp(w, os.path.join(design, 'masks', 'gear', fn + '.vox.txt'))
        for an, at in sorted(anchors.items()):
            cli('op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1',
                'note=%s：%s的固定點 %s' % (NOTE, what, an))
            print('  anchor %s %s %s' % (w, an, at), flush=True)
elif stage == 'links':
    links = json.load(open(os.path.join(WORKS, ASM, 'links.json'), encoding='utf-8'))
    have = {l['name'] for l in (links if isinstance(links, list) else links.get('links', []))}
    MP = PL['magazine']
    for name, w, meta, note in ((MP['link'], MP['work'], MP['meta'], '彈藥庫（Ship_Magazine §8；hoist ＝ 主甲板 orlop 梯、舵手台 quarter-S 梯）'),
                                (PL['skids']['link'], PL['skids']['work'], None, '主艙口上的小艇架（三座橫架）')):
        if name in have:
            if meta:
                cli('op=work', 'sub=meta', 'persona=' + PERSONA, 'part=link', 'work=' + ASM, 'name=' + name, 'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
            print('· link exists', name)
            continue
        args = ['op=work', 'sub=link', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + name, 'source_work=' + w, 'at=0,0,0', 'note=%s：%s' % (NOTE, note)]
        if meta:
            args.append('meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
        cli(*args)
        print('✓ link', name, flush=True)
    print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-12:]))
elif stage == 'models':
    ONLY = os.environ.get('GEAR_ONLY')
    ok = 0
    src = {m['name']: m.get('src', '') for m in GB['models']}
    for r in PL['models']:
        if ONLY and r['name'] != ONLY:
            continue
        what = src.get(r['name']) or '火藥桶（憲法號 -powder-barrel × 0.2；第 %d 層）' % (r.get('tier', 0) + 1)
        cli('op=work', 'sub=model', 'persona=' + PERSONA, 'work=' + HOST[r['host']], 'name=' + r['name'], 'source_work=' + r['work'],
            'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=0,0,' + num(float(r['rotate'])), 'scale=' + xyz(r['scale']), 'overwrite=1',
            'meta=' + json.dumps(r['meta'], ensure_ascii=False, separators=(',', ':')), 'note=%s：%s' % (NOTE, what[:180]))
        ok += 1
        if ok % 10 == 0:
            print('  models %d' % ok, flush=True)
    print('✓ models %d' % ok)
else:
    raise SystemExit('stage = works | links | models')
