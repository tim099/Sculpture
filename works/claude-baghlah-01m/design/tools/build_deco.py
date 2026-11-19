# Source: calli-cosecha-01m/design/tools/build_deco.py (Harvest) -- adapted for the Star (TASK-0019 step 6)
# Step 6 placement: hull recolour + sashes, decoration sub-works, links (glass material=glass, galleries P + mirror S,
#   helm rail), external models (stern carving, stem head; meta deco=1).
#   Usage: python -X utf8 tools/build_deco.py <design> <stage>   stage = hull | parts | links   (SENATE = wrapper path)
#   * Stops at the first non-zero exit; a sub-work that already exists is neither recreated nor restamped.
#   * placed must equal the list length for every stampvox (overwrite=1 for the hull recolour).
#   * What actually ran on 2026-11-18: the galleries were first created 420x160x120 and stamped with absolute y; the
#     mirror link was blocked (frame + at.y 1 > 160) => work move delta=0,-30,0, size 420,40,120, links re-made at y 30 / 91.
#     This file now does the end state directly (frame-local lists, 420x40x120 works).
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
stage = sys.argv[2]
HULL = 'claude-baghlah-01m'
ASM = HULL + '-assembly'
PERSONA = 'Claude-Ojousama'
SENATE = os.environ.get('SENATE', 'senate')
WORKS = os.path.dirname(os.path.dirname(design))
SIZE = '420,160,120'
FR = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['deco']['quarter_gallery']['frame']
GSIZE = ','.join(str(v) for v in FR['size'])      # gallery + its glass: frame-local lists (draft_deco.py shifts y by -at_y)
PARTS = [('stern-glass', 'stern_glass', '星辰號 船尾窗玻璃'),
         ('quarter-gallery', 'quarter_gallery', '星辰號 船尾側廊（左舷；右舷 mirror=y）'),
         ('quarter-gallery-glass', 'gallery_glass', '星辰號 側廊窗玻璃'),
         ('quarter-rail', 'quarter_rail', '星辰號 舵手台欄杆與舷牆布'),
         ('stern-carving', 'stern_carving', '星辰號 船尾雕花（裝飾模型）'),
         ('stem-head', 'stem_head', '星辰號 艏柱頭頂飾（裝飾模型）')]
NOTE = '步驟 6（TASK-0019；design/draft_deco.py）'


def cli(*args, ok=(0,)):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args)))
    return out


def stamp(work, path, overwrite=False):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    args = ['op=stampvox', 'persona=' + PERSONA, 'work=' + work, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0']
    if overwrite:
        args.append('overwrite=1')
    out = cli(*args)
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s != %d (%s %s)' % (got, n, work, os.path.basename(path)))
    print('  stampvox %s %s: %d%s' % (work, os.path.basename(path), n, ' (overwrite)' if overwrite else ''))


if stage == 'hull':
    stamp(HULL, os.path.join(design, 'masks', 'step6', 'hull_recolor.vox.txt'), overwrite=True)
    stamp(HULL, os.path.join(design, 'masks', 'step6', 'hull_add.vox.txt'))
elif stage == 'parts':
    for key, fn, title in PARTS:
        w = '%s-%s' % (HULL, key)
        if os.path.exists(os.path.join(WORKS, w, 'work.json')):
            print('· exists', w)
            continue
        size = GSIZE if key.startswith('quarter-gallery') else SIZE
        cli('op=work', 'sub=create', 'persona=' + PERSONA, 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=' + size, 'tags=sub')
        cli('op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + w, 'meters_per_voxel=0.1')
        print('✓ created', w)
        stamp(w, os.path.join(design, 'masks', 'deco', fn + '.vox.txt'))
elif stage == 'links':
    G = HULL + '-quarter-gallery'
    cli('op=work', 'sub=link', 'persona=' + PERSONA, 'work=' + G, 'name=窗玻璃', 'source_work=' + HULL + '-quarter-gallery-glass',
        'at=0,0,0', 'meta={"material":"glass"}', 'note=' + NOTE + '：側廊窗玻璃（Ship_Materials：玻璃一律獨立關聯、只寫 material=glass）')
    L = [('船尾窗玻璃', HULL + '-stern-glass', '0,0,0', None, {'material': 'glass'}, '船尾五扇窗的玻璃'),
         ('側廊-P', G, '0,%d,0' % FR['at_y'], None, None, '左舷船尾側廊（側廊作品框 420×40×120、放在 y %d）' % FR['at_y']),
         ('側廊-S', G, '0,%d,0' % (161 - FR['at_y'] - FR['size'][1]), 'y', None,
          '右舷船尾側廊（左舷 mirror=y；at.y ＝ 161 − %d − %d ＝ %d）' % (FR['at_y'], FR['size'][1], 161 - FR['at_y'] - FR['size'][1])),
         ('舵手台欄杆', HULL + '-quarter-rail', '0,0,0', None, None, '舵手台兩舷的舷牆布＋扶手、前緣小柱')]
    for name, src, at, mir, meta, note in L:
        args = ['op=work', 'sub=link', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + name, 'source_work=' + src, 'at=' + at, 'note=%s：%s' % (NOTE, note)]
        if mir:
            args.append('mirror=' + mir)
        if meta:
            args.append('meta=' + json.dumps(meta, separators=(',', ':')))
        cli(*args)          # 2026-11-18: ok=(0, 2) hid a blocked mirror link (exit 2) -- only 0 counts
        print('✓ link', name)
    for name, src, note in (('船尾雕花', HULL + '-stern-carving', '船尾雕花（P3：尖拱、窗框、方格板十字花、八角星）'),
                            ('艏柱頭', HULL + '-stem-head', '艏柱頭瓜形頂飾（P2 fig. 7 g）')):
        cli('op=work', 'sub=model', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + name, 'source_work=' + src, 'at=0,0,0', 'pivot=0,0,0',
            'scale=1', 'meta={"deco":1}', 'note=%s：%s；deco=1（Ship_Fittings §9.9）' % (NOTE, note))
        print('✓ model', name)
    print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-30:]))
else:
    raise SystemExit('stage = hull | parts | links')
