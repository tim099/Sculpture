# 階段五落格（TASK-0610）：建裝飾子作品、貼清單、關聯進組裝件、船尾燈（外部模型，沿用三叉戟號船尾燈）
#   用法：python -I -X utf8 tools/build_deco.py <design>
#   · 結構照三叉戟號 tools/build_decks.py（gura）；子作品已存在 ⇒ 不重建、不重貼（看 placed 對不上就停）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'kotoko-napoleon-01m'
ASM = HULL + '-assembly'
PARTS = [('head', '船頭', '拿破崙號 船頭（knee of the head、head rails、trailboard）'),
         ('figurehead', '船首像', '拿破崙號 船首像（帝國鷹）'),
         ('stern', '船尾裝飾', '拿破崙號 船尾陽台與船尾燈'),
         ('name', '船名板', '拿破崙號 船名板'),
         ('funnels', '煙囪', '拿破崙號 煙囪（兩根）'),
         ('screw', '螺旋槳', '拿破崙號 螺旋槳（固定式、3 葉）')]
SUBID = {'head': 'head', 'figurehead': 'figurehead', 'stern': 'stern-deco', 'name': 'name-board', 'funnels': 'funnels', 'screw': 'screw'}


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def exists(work):
    return os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(design)))), work, 'work.json'))


plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
for k, link, title in PARTS:
    w = '%s-%s' % (HULL, SUBID[k])
    if exists(w):
        print('· 已有', w)
        continue
    cli('op=work', 'sub=create', 'persona=kotoko', 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=1200,400,800', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=kotoko', 'work=' + w, 'meters_per_voxel=0.1')
    path = os.path.join(design, 'masks', 'deco', k + '.vox.txt')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=kotoko', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, w))
    print('✓ %s：%d' % (w, n))
    cli('op=work', 'sub=link', 'persona=kotoko', 'work=' + ASM, 'name=' + link, 'source_work=' + w, 'at=0,0,0', 'note=階段五（TASK-0610）', ok=(0, 2))
LA = plan['deco']['lanterns']
V = json.load(open(os.path.join(design, 'deco_placement.json'), encoding='utf-8'))
for lt, side in zip(V['lanterns'], ('P', 'C', 'S')):
    x, y, z = lt['at']
    cli('op=work', 'sub=model', 'persona=kotoko', 'work=%s-stern-deco' % HULL, 'name=lantern-' + side, 'source_work=' + LA['source'],
        'at=%g,%g,%g' % (x, y, z), 'pivot=8.5,8.5,0', 'scale=%g' % LA['scale'], 'meta={"kind":"light"}', 'note=階段五 船尾燈（沿用三叉戟號船尾燈）', ok=(0, 2))
print('✓ 船尾燈 3 盞')
print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-20:]))
