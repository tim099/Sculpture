# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/build_deco.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 階段五落格（kaguya 改寫自拿破崙號 tools/build_deco.py）：建裝飾子作品、貼清單、關聯進組裝件（帶給遊戲的 meta）、
#   煙囪的排煙點 smoke、船尾燈（外部模型，沿用三叉戟號船尾燈，掛在艉樓甲板子作品上）
#   用法：python -I -X utf8 tools/build_deco.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼（看 placed 對不上就停）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
HULL = 'crest-001-susquehanna-01m'
ASM = HULL + '-assembly'
# (清單, 子作品 id 尾巴, 關聯名, 標題, 關聯 meta)
PARTS = [('head', 'head', '船頭', '蘇士奎哈納號 船頭 knee of the head＋trailboard（金色花藤）', {}),   # 蘇士奎哈納號改：部件整份換掉
         ('figurehead', 'figurehead', '船首像', '蘇士奎哈納號 船首像（鷹；NARA c. 1850 設計圖）', {}),
         ('rails', 'head-rails', 'head-rails', '蘇士奎哈納號 head rails（每舷兩條）', {}),
         ('name', 'name-board', '船名板', '蘇士奎哈納號 船名板（SUSQUEHANNA）', {}),
         ('funnels', 'funnel', '煙囪', '蘇士奎哈納號 煙囪（一根，黑；從鍋爐頂接上來）', {'kind': 'funnel', 'material': 'iron', 'render': 'smooth'}),
         ('hammock', 'hammock', 'hammock', '蘇士奎哈納號 舷牆頂 hammock 白帆布', {}),
         ('catheads', 'catheads', '吊錨架', '蘇士奎哈納號 吊錨架 cathead（兩舷）', {})]


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def exists(work):
    return os.path.exists(os.path.join(os.path.dirname(os.path.dirname(design)), work, 'work.json'))


plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
for k, sid, link, title, meta in PARTS:
    w = '%s-%s' % (HULL, sid)
    if not exists(w):
        cli('op=work', 'sub=create', 'persona=crest-001', 'id=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=1300,400,800', 'tags=sub')
        cli('op=work', 'sub=update', 'persona=crest-001', 'work=' + w, 'meters_per_voxel=0.1')
        path = os.path.join(design, 'masks', 'deco', k + '.vox.txt')
        n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
        out = cli('op=stampvox', 'persona=crest-001', 'work=' + w, 'voxels=' + path.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
        m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
        got = int(m.group(1).replace(',', '')) if m else None
        if got != n:
            print(out[-1500:])
            raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, w))
        print('✓ %s：%d' % (w, n))
    else:
        print('· 已有', w)
    a = ['op=work', 'sub=link', 'persona=crest-001', 'work=' + ASM, 'name=' + link, 'source_work=' + w, 'at=0,0,0', 'note=階段五']
    if meta:
        a.append('meta=' + json.dumps(meta))
    cli(*a, ok=(0, 2))
    if meta:
        cli('op=work', 'sub=meta', 'persona=crest-001', 'work=' + ASM, 'part=link', 'name=' + link, 'meta=' + json.dumps(meta))
# 煙囪的排煙點（煙囪口中心；造船規格 §9 funnel）
for f in plan['funnels']['rows']:
    cli('op=work', 'sub=anchor', 'persona=crest-001', 'work=%s-funnel' % HULL, 'name=smoke', 'at=%d,%d,%d' % (f['x'], plan['space']['yc'], f['top_z']),
        'note=排煙點：煙囪口中心（遊戲從這裡冒煙）', ok=(0, 2))
print('✓ smoke')
LA = plan['deco']['lanterns']
V = json.load(open(os.path.join(design, 'deco_placement.json'), encoding='utf-8'))
for lt, side in zip(V['lanterns'], ('P', 'C', 'S')):
    x, y, z = lt['at']
    cli('op=work', 'sub=model', 'persona=crest-001', 'work=%s-deck-gun' % HULL,   # 蘇士奎哈納號改：船尾燈掛在砲甲板（露天）子作品
        'name=lantern-' + side, 'source_work=' + LA['source'],
        'at=%g,%g,%g' % (x, y, z), 'pivot=8.5,8.5,0', 'scale=%g' % LA['scale'], 'meta={"kind":"light"}', 'note=階段五 船尾燈（沿用三叉戟號船尾燈）', ok=(0, 2))
print('✓ 船尾燈 3 盞')
print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[4:22]))
