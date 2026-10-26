# 直接出處：gura-pinas-01m/design/tools/build_deco.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成康塞普西翁號（TASK-0969）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/tools/build_deco.py（收穫號，照抄後改成康塞普西翁號 —— TASK-0969）
# 階段五落格：建裝飾子作品、貼清單、關聯進組裝件、船尾燈模型（沿用三叉戟號船尾燈）
#   用法：python -I -X utf8 tools/build_deco.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼；每一步讀回 exit 0 才往下
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'apex-two-galeon-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
V = json.load(open(os.path.join(design, 'verify_deco.json'), encoding='utf-8'))
PARTS = [('espolon', '船首喙', '康塞普西翁號 船首喙（espolón＋cutwater＋head rail）'),
         ('figurehead', '船首像', '康塞普西翁號 船首像「鍍金獅子」'),
         ('stern-deco', '船尾裝飾', '康塞普西翁號 船尾走廊與兩舷側廊（galerías）'),
         ('hackebort', '船尾拱形板', '康塞普西翁號 船尾拱形板（無原罪聖母與 CONCEPCION 名帶＋三盞船尾燈）')]


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


for key, link, title in PARTS:
    w = '%s-%s' % (HULL, key)
    path = os.path.join(design, 'masks', 'deco', key + '.vox.txt')
    if os.path.exists(os.path.join(WORKS, w, 'work.json')):
        print('· 已有', w)
        continue
    cli('op=work', 'sub=create', 'persona=apex-two', 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=900,320,700', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=apex-two', 'work=' + w, 'meters_per_voxel=0.1')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=apex-two', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, w))
    print('✓ %s：%d' % (w, n))
    cli('op=work', 'sub=link', 'persona=apex-two', 'work=' + ASM, 'name=' + link, 'source_work=' + w, 'at=0,0,0', 'note=步驟 6（TASK-0969）', ok=(0, 2))
LA = plan['stern_deco']['lanterns']
for lt in V['lanterns']:
    x, y, z = lt['at']
    if not (lt['on_solid'] and lt['air_above']):
        raise SystemExit('✗ 船尾燈腳下不是實心或頭上不是空的：%s' % lt)
    cli('op=work', 'sub=model', 'persona=apex-two', 'work=%s-hackebort' % HULL, 'name=lantern' + ('' if lt['dy'] == 0 else ('-P' if lt['dy'] < 0 else '-S')), 'source_work=' + LA['source'],
        'at=%g,%g,%g' % (x, y, z), 'pivot=8.5,8.5,0', 'scale=%g' % LA['scale'], 'meta={"kind":"light"}', 'note=步驟 6 船尾燈（沿用三叉戟號船尾燈）', ok=(0, 2))
print('✓ 船尾燈 %d 盞' % len(V['lanterns']))
print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-24:]))
