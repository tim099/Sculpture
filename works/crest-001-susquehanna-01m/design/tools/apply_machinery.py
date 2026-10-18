# 蘇士奎哈納號（crest-001，TASK-0697）階段九落格：機艙 —— 照 machinery_placement.json（draft_machinery.py）
#   子作品（框收緊、0.1 m、parent 船殼、tags sub）→ 固定點 → 組裝件關聯（右舷＋鏡像）＋ meta；砲甲板開軸縫、住艙甲板開梯子口（carvevox 守門）
#   用法：python -I -X utf8 tools/apply_machinery.py <design>   （子作品已存在而且格數對 ⇒ 不重貼）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL, ASM = 'crest-001-susquehanna-01m', 'crest-001-susquehanna-01m-assembly'
WORKS = os.path.dirname(os.path.dirname(D))
PL = json.load(open(os.path.join(D, 'machinery_placement.json'), encoding='utf-8'))
MT = PL['meta']


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args[:6])))
    return out


def nlines(p):
    return sum(1 for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#'))


# (清單, 子作品尾巴, 標題, [(關聯名, 鏡像?, 掛在哪)], meta)
PARTS = [('engine_S', 'engine', '蘇士奎哈納號 主機（右舷一具；斜置直動式、汽缸 70 in × 10 ft；左舷鏡像）', [('主機-S', False, ASM), ('主機-P', True, ASM)], MT['engine']),
         ('boilers_aft', 'boilers-aft', '蘇士奎哈納號 後鍋爐兩座（銅、爐門朝後）＋煙箱', [('鍋爐-後', False, ASM)], MT['boiler']),
         ('boilers_fore', 'boilers-fore', '蘇士奎哈納號 前鍋爐兩座（銅、爐門朝前）＋煙箱', [('鍋爐-前', False, ASM)], MT['boiler']),
         ('shaft_S', 'paddle-shaft', '蘇士奎哈納號 明輪軸（右舷段；左舷鏡像）', [('明輪軸-S', False, ASM), ('明輪軸-P', True, ASM)], MT['shaft']),
         ('floor', 'deck-engine', '蘇士奎哈納號 甲板 機艙（鐵地板）', [('甲板-engine', False, ASM)], None),
         ('ladder', 'ladders-engine', '蘇士奎哈納號 梯子（機艙地板上住艙甲板）', [('梯子-機艙', False, HULL + '-deck-berth')], {'kind': 'ladders', 'engine-berth.decks': 'engine,berth'}),
         ('casing', 'shaft-casing', '蘇士奎哈納號 砲甲板上的明輪軸罩（木）', [('軸罩', False, ASM)], None)]
for k, tail, title, links, meta in PARTS:
    P = PL['parts'][k]
    w = '%s-%s' % (HULL, tail)
    path = os.path.join(D, 'masks', 'machinery', k + '.vox.txt')
    n = nlines(path)
    if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
        cli('op=work', 'sub=create', 'persona=crest-001', 'id=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=%d,%d,%d' % tuple(P['size']), 'tags=sub')
        cli('op=work', 'sub=update', 'persona=crest-001', 'work=' + w, 'meters_per_voxel=0.1')
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli('op=stats', 'work=' + w, 'links=none')).group(1))
    if have == 0:
        out = cli('op=stampvox', 'persona=crest-001', 'work=' + w, 'voxels=' + path.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
        got = int(re.search(r'🔢 placed = (\d+)', out).group(1))
        if got != n:
            raise SystemExit('✗ %s placed %d ≠ %d' % (w, got, n))
    elif have != n:
        raise SystemExit('✗ %s 已有 %d ≠ %d' % (w, have, n))
    for nm, xyz in sorted(P['anchors_local'].items()):
        cli('op=work', 'sub=anchor', 'persona=crest-001', 'work=' + w, 'name=' + nm, 'at=%d,%d,%d' % tuple(xyz), 'overwrite=1', 'note=階段九（draft_machinery.py）')
    for nm, mir, host in links:
        at = P['at_mirror'] if mir else P['at']
        a = ['op=work', 'sub=link', 'persona=crest-001', 'work=' + host, 'name=' + nm, 'source_work=' + w, 'at=%d,%d,%d' % tuple(at), 'note=階段九：機艙']
        if mir:
            a.append('mirror=y')
        cli(*a, ok=(0, 2))
        if meta:
            cli('op=work', 'sub=meta', 'persona=crest-001', 'work=' + host, 'part=link', 'name=' + nm, 'meta=' + json.dumps(meta, ensure_ascii=False))
    print('✓ %s %d 格、關聯 %s' % (w, n, [l[0] for l in links]))
# 甲板開口（carvevox；第 4 欄 ＝ 現在的色，守門）
for f, w in (('deck_gun_carve', HULL + '-deck-gun'), ('deck_berth_hole', HULL + '-deck-berth')):
    p = os.path.join(D, 'masks', 'machinery', f + '.vox.txt')
    n = nlines(p)
    if n == 0:
        continue
    out = cli('op=carvevox', 'persona=crest-001', 'work=' + w, 'voxels=' + p.replace('\\', '/'), 'at=0,0,0', 'share=0', ok=(0, 5))
    m = re.search(r'🔢 placed = (\d+)', out)
    print('  刻 %s：%s／%d' % (f, m.group(1) if m else out[-300:], n))
