# 階段四落格：建甲板／梯子子作品、貼清單、梯子固定點、關聯（組裝件 → 甲板 → 梯子 meta kind=ladders）
#   用法：python -I -X utf8 tools/build_decks.py <design>
#   · 每一步讀回 exit 0 才往下；子作品已存在 ⇒ 不重建、不重貼（清單已落過的那件跳過；看 placed 對不上就停）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'gura-tridente-01m'
ASM = HULL + '-assembly'
DECKS = ['orlop', 'lower', 'middle', 'upper', 'spar', 'poop']
TITLE = {'orlop': 'orlop', 'lower': '下砲甲板', 'middle': '中砲甲板', 'upper': '上砲甲板', 'spar': '上甲板', 'poop': 'poop'}


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def exists(work):
    return os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(design)))), work, 'work.json'))


def make(work, title):
    if exists(work):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=gura', 'id=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=1100,400,800', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=gura', 'work=' + work, 'meters_per_voxel=0.1')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=gura', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  stampvox %s：%d' % (os.path.basename(path), n))


pts = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
for k in DECKS:
    w = '%s-deck-%s' % (HULL, k)
    if make(w, '三叉戟號 甲板 ' + TITLE[k]):
        stamp(w, os.path.join(design, 'masks', 'decks', k + '.vox.txt'))
for k in DECKS[1:]:
    w = '%s-ladders-%s' % (HULL, k)
    if make(w, '三叉戟號 梯子（上到%s）' % TITLE[k]):
        stamp(w, os.path.join(design, 'masks', 'ladders', k + '.vox.txt'))
        for nm, v in sorted(pts.items()):
            if v['up'] != k:
                continue
            for pk in ('foot', 'lo', 'hi', 'head'):
                x, y, z = v['points'][pk]
                cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + w, 'name=%s.%s' % (nm, pk), 'at=%d,%d,%d' % (x, y, z),
                    'note=梯子點（draft_decks.py：腳踩的那一格）')
        print('  固定點 %d' % sum(4 for v in pts.values() if v['up'] == k))
# 關聯：甲板 → 梯子（meta kind=ladders）；組裝件 → 甲板
for k in DECKS[1:]:
    cli('op=work', 'sub=link', 'persona=gura', 'work=%s-deck-%s' % (HULL, k), 'name=梯子', 'source_work=%s-ladders-%s' % (HULL, k), 'at=0,0,0',
        'meta={"kind":"ladders"}', 'note=階段四：從下一層上來的梯子', ok=(0, 2))
for k in DECKS:
    cli('op=work', 'sub=link', 'persona=gura', 'work=' + ASM, 'name=甲板-' + k, 'source_work=%s-deck-%s' % (HULL, k), 'at=0,0,0',
        'note=階段四', ok=(0, 2))
print(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-25:])
