# 抄自三叉戟號 gura-tridente-01m/design/tools/build_masts.py（gura）；改：作品、persona、尺寸、帆桁不建子作品（直接引用三叉戟號的帆桁、模型帶 scale x,y,z）、船殼沒有要刻就跳過。
# 階段六落格：船殼刻艏斜桅開口（標記 艏斜桅開口:begin／end）、桅子作品（整船的框、at 0,0,0）、組裝件關聯、帆桁子作品＋固定點、帆桁模型（放在它的桅子作品裡）—— 照 masts_placement.json
#   用法：python -I -X utf8 tools/build_masts.py <design> [hull] [masts] [yards] [models]（不給 ⇒ 全部，照順序）
#   · 每一步讀回 exit 0／格數對上才往下；已經做過的跳過（標記 艏斜桅開口:end 已有 ⇒ 不再刻；子作品格數 ＝ 清單 ⇒ 不重貼）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
steps = [a for a in sys.argv[2:] if not a.startswith('--')] or ['hull', 'masts', 'models']
HULL = 'kotoko-napoleon-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))


def cli(*args, ok=(0,)):
    for _ in range(3):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = r.stdout + r.stderr
        if r.returncode in ok or 'IOException' not in out:
            break
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return r.returncode, out


def count(work):
    return int(re.search(r'🔢 total_voxels = (\d+)', cli('op=stats', 'work=' + work, 'links=none')[1]).group(1))


def nlines(p):
    return sum(1 for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#'))


def stamp(work, path):
    n = nlines(path)
    have = count(work)
    if have == n:
        print('· %s 已貼（%d）' % (work, n))
        return
    if have:
        raise SystemExit('✗ %s 已有 %d 格 ≠ 清單 %d' % (work, have, n))
    _, out = cli('op=stampvox', 'persona=kotoko', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        print(out[-1500:])
        raise SystemExit('✗ placed ≠ %d（%s）' % (n, work))
    print('  stampvox %s：%d' % (os.path.basename(path), n))


def create(work, title, parent, size, mpv=0.1):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        return
    cli('op=work', 'sub=create', 'persona=kotoko', 'id=' + work, 'title=' + title, 'parent_work=' + parent, 'size=' + ','.join(str(v) for v in size), 'tags=sub')
    cli('op=work', 'sub=update', 'persona=kotoko', 'work=' + work, 'meters_per_voxel=%g' % mpv)
    print('✓ 建立 %s（%s）' % (work, size))


pl = json.load(open(os.path.join(design, 'masts_placement.json'), encoding='utf-8'))
if 'hull' in steps:
    _, marks = cli('op=work', 'sub=marks', 'work=' + HULL)
    path = os.path.join(design, 'masks', 'masts', 'hull_carve.vox.txt')
    if not os.path.exists(path) or nlines(path) == 0:
        print('· 艏斜桅沒有穿過船殼（清單 0 格），不刻')
    elif '艏斜桅開口:end' in marks:
        print('· 船殼已刻艏斜桅開口')
    else:
        if '艏斜桅開口:begin' not in marks:
            cli('op=work', 'sub=mark', 'persona=kotoko', 'work=' + HULL, 'name=艏斜桅開口', 'phase=begin', 'note=階段六（TASK-0611）艏斜桅穿過船頭舷牆頂')
        n = nlines(path)
        _, out = cli('op=carvevox', 'persona=kotoko', 'work=' + HULL, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'share=0')
        m = re.search(r'🔢 placed = (\d+)', out)                     # carvevox 也回 placed（刻掉的格數）
        got = int(m.group(1).replace(',', '')) if m else None
        if got != n:
            print(out[-1500:])
            raise SystemExit('✗ carved %s ≠ %d' % (got, n))
        cli('op=work', 'sub=mark', 'persona=kotoko', 'work=' + HULL, 'name=艏斜桅開口', 'phase=end', 'note=刻 %d 格（顏色守門）' % n)
        print('✓ 船殼刻艏斜桅開口 %d' % n)
if 'masts' in steps:
    for key, m in pl['masts'].items():
        create(m['work'], m['title'], HULL, [1200, 400, 800])
        stamp(m['work'], os.path.join(design, 'masks', 'masts', key + '.vox.txt'))
        rc, _ = cli('op=work', 'sub=link', 'persona=kotoko', 'work=' + ASM, 'name=' + m['link'], 'source_work=' + m['work'], 'at=0,0,0', 'note=階段六（TASK-0611）', ok=(0, 2))
        print('  關聯 %s %s' % (m['link'], '✓' if rc == 0 else '已有'))
if 'yards' in steps:
    for yd in pl['yards']:
        create(yd['work'], yd['title'], yd['parent'], yd['frame'])
        stamp(yd['work'], os.path.join(design, 'masks', 'yards', yd['name'] + '.vox.txt'))
        for nm, xyz in sorted(yd['anchors'].items()):
            cli('op=work', 'sub=anchor', 'persona=kotoko', 'work=' + yd['work'], 'name=' + nm, 'at=%d,%d,%d' % tuple(xyz), 'note=階段六（draft_masts.py）')
        print('  固定點 %d' % len(yd['anchors']))
if 'models' in steps:
    for yd in pl['yards']:
        md = yd['model']
        cli('op=work', 'sub=unmodel', 'persona=kotoko', 'work=' + yd['parent'], 'name=' + md['name'], ok=(0, 2))
        cli('op=work', 'sub=model', 'persona=kotoko', 'work=' + yd['parent'], 'name=' + md['name'], 'source_work=' + yd['source_work'],
            'at=%g,%g,%g' % tuple(md['at']), 'pivot=%g,%g,%g' % tuple(md['pivot']), 'rotate=%g,%g,%g' % tuple(md['rotate']), 'scale=%g,%g,%g' % tuple(md['scale']),
            'meta=' + json.dumps(md['meta'], ensure_ascii=False), 'note=階段六（TASK-0611）')
        print('  模型 %s/%s rotate %s' % (yd['parent'].split('-')[-1], md['name'], md['rotate'][2]))
