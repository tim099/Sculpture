# 階段五落格：照 <placement>.json 建子作品（自己的框）、貼清單、掛到組裝件（一舷的另一舷 mirror=y）
#   用法：python -I -X utf8 tools/build_stage5.py <design> <部件名…>（部件定義在下面 PARTS；placement 檔由產生程式寫）
#   · 子作品已存在、而且格數 ＝ 清單 ⇒ 不重貼；已存在但格數不同 ⇒ 停（要重貼先 undo 掉，免得疊兩份）
#   · 關聯已存在 ⇒ 跳過（exit 2）
#   · --redo：清單改過之後重貼 —— undo 到 0 格、框照 placement 改、重貼、關聯先 unlink 再照 placement 的 at 重接
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'gura-tridente-01m'
ASM = HULL + '-assembly'
# 部件：子作品 id 尾巴、名稱、清單、placement 檔與鍵、組裝件裡的關聯（名, 鏡像?）
PARTS = {
    'walk': ('stern-walk', '三叉戟號 船尾陽台', 'masks/stern/walk.vox.txt', 'stern_placement.json', [('船尾陽台', False)]),
    'gallery': ('quarter-gallery', '三叉戟號 quarter gallery（右舷一件）', 'masks/stern/gallery.vox.txt', 'stern_placement.json', [('後廊-S', False), ('後廊-P', True)]),
    'deco': ('stern-deco', '三叉戟號 船尾名牌與徽', 'masks/stern/deco.vox.txt', 'stern_placement.json', [('船尾名牌與徽', False)]),
    'rudder': ('rudder', '三叉戟號 舵', 'masks/rudder/rudder.vox.txt', 'rudder_placement.json', [('舵', False)]),
    'knee': ('head-knee', '三叉戟號 船頭 knee', 'masks/head/knee.vox.txt', 'head_placement.json', [('船頭-knee', False)]),
    'side': ('head-side', '三叉戟號 船頭裝飾（右舷一件）', 'masks/head/side.vox.txt', 'head_placement.json', [('船頭裝飾', False), ('船頭裝飾-鏡像', True)]),
    'figurehead': ('figurehead', '三叉戟號 船首像', 'masks/head/figurehead.vox.txt', 'head_placement.json', [('船首像', False)]),
}


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return r.returncode, out


def count(work):
    _, out = cli('op=stats', 'work=' + work, 'links=none')
    m = re.search(r'🔢 total_voxels = (\d+)', out)
    return int(m.group(1)) if m else None


REDO = '--redo' in sys.argv
for key in [a for a in sys.argv[2:] if not a.startswith('--')]:
    if key == 'anchor':                                               # 錨：直接關聯憲法號的 -anchor（子物件能重複用就重複用）
        an = json.load(open(os.path.join(design, 'head_placement.json'), encoding='utf-8'))['anchor']
        for name, mir in (('錨-S', False), ('錨-P', True)):
            at = an['P'] if mir else an['S']
            args = ['op=work', 'sub=link', 'persona=gura', 'work=' + ASM, 'name=' + name, 'source_work=' + an['work'], 'at=%d,%d,%d' % tuple(at),
                    'note=階段五（TASK-0558）：吊環頂在 cathead 端正下方']
            if mir:
                args.append('mirror=y')
            rc, _ = cli(*args, ok=(0, 2))
            print('  關聯 %s at %s %s' % (name, at, '✓' if rc == 0 else '已有'))
        continue
    tail, title, lst, pfile, links = PARTS[key]
    work = '%s-%s' % (HULL, tail)
    pl = json.load(open(os.path.join(design, pfile), encoding='utf-8'))[key]
    path = os.path.join(design, lst)
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    size = ','.join(str(v) for v in pl['size'])
    wdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(design))), work)   # works/<子作品>
    if not os.path.exists(os.path.join(wdir, 'work.json')):
        cli('op=work', 'sub=create', 'persona=gura', 'id=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=' + size, 'tags=sub')
        cli('op=work', 'sub=update', 'persona=gura', 'work=' + work, 'meters_per_voxel=0.1')
        print('✓ 建立 %s（%s）' % (work, size))
    have = count(work)
    if REDO and have:
        for _ in range(5):
            cli('op=work', 'sub=undo', 'persona=gura', 'work=' + work)
            have = count(work)
            if have == 0:
                break
        if have:
            raise SystemExit('✗ %s undo 之後還有 %d 格' % (work, have))
        cli('op=work', 'sub=update', 'persona=gura', 'work=' + work, 'size=' + size)
        print('  undo → 0、框 %s' % size)
        for name, _ in links:
            cli('op=work', 'sub=unlink', 'persona=gura', 'work=' + ASM, 'name=' + name, ok=(0, 2))
    if have == 0:
        _, out = cli('op=stampvox', 'persona=gura', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0',
                     'expect_pixels=%d' % n, 'share=0')
        m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
        got = int(m.group(1).replace(',', '')) if m else None
        if got != n:
            print(out[-1500:])
            raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
        print('  stampvox %s：%d' % (os.path.basename(path), n))
    elif have != n:
        raise SystemExit('✗ %s 已有 %d 格 ≠ 清單 %d —— 先 undo 掉再重貼' % (work, have, n))
    else:
        print('· %s 已貼（%d）' % (work, n))
    for nm, xyz in sorted((pl.get('anchors') or {}).items()):
        cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + work, 'name=' + nm, 'at=%d,%d,%d' % tuple(xyz), 'note=階段五：cutwater 前緣中線那一格（之後 bobstay 綁這裡）')
        print('  固定點 %s %s' % (nm, xyz))
    for name, mir in links:
        at = pl['at_mirror'] if mir else pl['at']
        args = ['op=work', 'sub=link', 'persona=gura', 'work=' + ASM, 'name=' + name, 'source_work=' + work, 'at=%d,%d,%d' % tuple(at),
                'note=階段五（TASK-0558）']
        if mir:
            args.append('mirror=y')
        rc, out = cli(*args, ok=(0, 2))
        print('  關聯 %s at %s%s %s' % (name, at, '（mirror=y）' if mir else '', '✓' if rc == 0 else '已有'))
