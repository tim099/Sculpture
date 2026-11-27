# 出處：claude-baghlah-01m/design/tools/build_decks.py（星辰號）。改：作品 id 利劍號、框 540,261,110、標題中文、senate 預設用離線包裝絕對路徑。
# Source: calli-cosecha-01m/design/tools/build_decks.py (Harvest) -- adapted for the Star (TASK-0019 step 5)
# Step 5 placement: deck / ladder sub-works, stamp the lists, ladder anchors, links (assembly -> deck -> ladders kind=ladders),
#   deck meta on the assembly links (decks_meta.tsv via sub=meta).
#   Usage: python -X utf8 tools/build_decks.py <design>   (SENATE = path of the senate wrapper; default: the offline wrapper)
#   * Stops at the first non-zero exit; a sub-work that already exists is neither recreated nor restamped.
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
HULL = 'claude-xebec-01m'
ASM = HULL + '-assembly'
PERSONA = 'Claude-Ojousama'
SENATE = os.environ.get('SENATE', '/paperclip/instances/default/projects/482d2c24-3be9-40fc-8ec9-1a7a02dd4f3f/1ea1d409-d2dd-45dc-b44e-35e83e49b833/_default/.work/senate/bin/senate')
WORKS = os.path.dirname(os.path.dirname(design))
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
G = plan['decks_build']['groups']
TITLE = {g['key']: g['name'] for g in G}
SIZE = '540,261,110'


def cli(*args, ok=(0,)):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args)))
    return out


def make(work, title):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· exists', work)
        return False
    cli('op=work', 'sub=create', 'persona=' + PERSONA, 'work=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=' + SIZE, 'tags=sub')
    cli('op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + work, 'meters_per_voxel=0.1')
    print('✓ created', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=' + PERSONA, 'work=' + work, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s != %d (%s)' % (got, n, work))
    print('  stampvox %s: %d' % (os.path.basename(path), n))


pts = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
ups = sorted({v['group_up'] for v in pts.values()})
for g in G:
    k = g['key']
    w = '%s-deck-%s' % (HULL, k)
    if make(w, '利劍號 甲板 ' + TITLE[k]):
        stamp(w, os.path.join(design, 'masks', 'decks', k + '.vox.txt'))
for k in ups:
    w = '%s-ladders-%s' % (HULL, k)
    if make(w, '利劍號 梯子（上到%s）' % TITLE[k]):
        stamp(w, os.path.join(design, 'masks', 'ladders', k + '.vox.txt'))
        for nm, v in sorted(pts.items()):
            if v['group_up'] != k:
                continue
            for pk in ('foot', 'lo', 'hi', 'head'):
                x, y, z = v['points'][pk]
                cli('op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + w, 'name=%s.%s' % (nm, pk), 'at=%d,%d,%d' % (x, y, z),
                    'note=梯子點（draft_decks.py：腳踩的那一格）')
        print('  anchors %d' % sum(4 for v in pts.values() if v['group_up'] == k))
for k in ups:
    meta = {'kind': 'ladders'}
    for nm, v in sorted(pts.items()):
        if v['group_up'] == k and v.get('decks'):
            meta[nm + '.decks'] = v['decks']
    cli('op=work', 'sub=link', 'persona=' + PERSONA, 'work=%s-deck-%s' % (HULL, k), 'name=梯子', 'source_work=%s-ladders-%s' % (HULL, k), 'at=0,0,0',
        'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')), 'note=步驟 5：從下一層上來的梯子', ok=(0, 2))
for g in G:
    k = g['key']
    cli('op=work', 'sub=link', 'persona=' + PERSONA, 'work=' + ASM, 'name=甲板-' + k, 'source_work=%s-deck-%s' % (HULL, k), 'at=0,0,0',
        'note=步驟 5', ok=(0, 2))
print(cli('op=work', 'sub=meta', 'persona=' + PERSONA, 'work=' + ASM, 'file=' + os.path.join(design, 'decks_meta.tsv'))[-800:])
print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-30:]))
