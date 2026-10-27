# 澤漢號 步驟 6（TASK-0966）落格：船首喙（子作品＋關聯）、紅獅（子作品＋外部模型 deco=1）、船殼換色（海公雞、假砲門）、
#   船尾窗玻璃（從船殼拆出、雙生關聯 material=glass、後面的內板刻穿）、艉燈（外部模型 kind=light）
#   用法：python -I -X utf8 tools/build_deco.py <design> [--only=<步驟,…>]（步驟：head figure paint glass behind lamp）
#   · 每一刀讀回 exit 0／placed 才往下；子作品已存在 ⇒ 不重建、不重貼
#   · 出處：tools/build_decks.py（cli、make、stamp 照抄）；拉貝爾號步驟 6 是手打的 CLI，本船寫成程式
import json, os, re, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
only = next((a.split('=', 1)[1].split(',') for a in sys.argv[2:] if a.startswith('--only=')), None)
HULL = 'abigail-fluyt-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
YC = plan['space']['yc']
NOTE = 'note=步驟 6'
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list


def want(k):
    return only is None or k in only


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def make(work, title):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=Abigail', 'work=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=480,192,384', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=Abigail', 'work=' + work, 'meters_per_voxel=0.1')
    print('✓ 建立', work)
    return True


def stamp(work, path, extra=()):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=Abigail', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0', *extra)
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  stampvox %s：%d' % (os.path.basename(path), n))


def carve(work, cells):
    d = tempfile.mkdtemp()
    f = os.path.join(d, 'c.vox.txt')
    with open(f, 'w', encoding='utf-8', newline='\n') as h:
        h.write('# 澤漢號 船尾窗玻璃後面的內板（carvevox，第 4 欄守門）\n')
        for (x, y, z), c in sorted(cells.items()):
            h.write('%d,%d,%d,%d\n' % (x, y, z, c))
    out = cli('op=carvevox', 'persona=Abigail', 'work=' + work, 'voxels=' + f.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(cells), 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != len(cells):
        print(out[-1500:])
        raise SystemExit('✗ carved %s ≠ %d' % (got, len(cells)))
    print('  carvevox %d' % len(cells))
    return f


mk = lambda name, phase: cli('op=work', 'sub=mark', 'persona=Abigail', 'work=' + HULL, 'name=' + name, 'phase=' + phase)
masks = os.path.join(design, 'masks', 'deco')

if want('head'):
    w = HULL + '-head'
    if make(w, '澤漢號 船首喙（knee of head＋head rails）'):
        stamp(w, os.path.join(masks, 'head.vox.txt'))
    cli('op=work', 'sub=link', 'persona=Abigail', 'work=' + ASM, 'name=船首喙', 'source_work=' + w, 'at=0,0,0', 'note=步驟 6：knee of head＋head rails', ok=(0, 2))

if want('figure'):
    w = HULL + '-figurehead'
    if make(w, '澤漢號 船首像（紅獅 leeuw）'):
        stamp(w, os.path.join(masks, 'figurehead.vox.txt'))
    cli('op=work', 'sub=model', 'persona=Abigail', 'work=' + ASM, 'name=船首像', 'source_work=' + w, 'at=0,0,0', 'scale=1,1,1', 'overwrite=1',
        'meta={"deco":1}', 'note=步驟 6：紅獅（deco=1）')

if want('paint'):
    mk('裝飾', 'begin')
    stamp(HULL, os.path.join(masks, 'paint.vox.txt'), ('overwrite=1',))

if want('glass'):
    out = cli('op=work', 'sub=split', 'persona=Abigail', 'work=' + HULL, 'into=' + HULL + '-stern-glass', 'colors=%d' % plan['paint']['glass'],
              'twin={name}-窗玻璃', 'twin_meta={"material":"glass"}', 'confirm=1')
    print('\n'.join(l for l in out.splitlines() if l.startswith(('✓', '✗', '⚠', '🔢 moved', '🔢 twin'))))

if want('behind'):
    # 玻璃後面（往船頭）那幾層船殼牆刻穿到艙裡：每格玻璃 (x, y, z) 往 +x 數，船殼的格一直刻到空氣為止（顏色守門）
    G = export_list(HULL + '-stern-glass', None)
    Hc = {(x, y, z): c for x, y, z, c in export_list(HULL, None).tolist()}
    cells = {}
    for x, y, z, _ in G.tolist():
        xx = x + 1
        while (xx, y, z) in Hc:
            cells[(xx, y, z)] = Hc[(xx, y, z)]
            xx += 1
    os.makedirs(os.path.join(design, 'masks', 'glass'), exist_ok=True)
    p = os.path.join(design, 'masks', 'glass', 'carve_behind.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write('# 澤漢號 船尾窗玻璃後面的船殼牆（carvevox，第 4 欄守門）—— 刻穿看得進船長室（Ship_Materials §9.5）\n')
        for (x, y, z), c in sorted(cells.items()):
            h.write('%d,%d,%d,%d\n' % (x, y, z, c))
    out = cli('op=carvevox', 'persona=Abigail', 'work=' + HULL, 'voxels=' + p.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(cells), 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    print('  玻璃 %d 格、後面刻 %d（placed %s）' % (len(G), len(cells), m.group(1) if m else None))
    mk('裝飾', 'end')

if want('glassfill'):
    # 斜的 hek 面：上下兩排玻璃差 1 格 ⇒ 只在斜角相碰（4 片、看得到縫、水灌得過去）⇒ 往下一排補 1 格（Ship_Materials：玻璃要 6 連通整片接起來）
    #   補在下一排、上一排那個 x（那一格是刻掉的窗洞 ⇒ 空氣）；只補空氣格
    G = export_list(HULL + '-stern-glass', None)
    gs = {(x, y, z): c for x, y, z, c in G.tolist()}
    Hc = {(x, y, z) for x, y, z, _ in export_list(HULL, None).tolist()}
    add = {}
    for (x, y, z), c in gs.items():
        if (x, y, z - 1) not in gs and (x + 1, y, z - 1) in gs and (x, y, z - 1) not in Hc:
            add[(x, y, z - 1)] = c
    p = os.path.join(design, 'masks', 'glass', 'fill.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write('# 澤漢號 船尾窗玻璃：斜面上下兩排的接縫往下一排補 1 格（stampvox 進 -stern-glass）\n')
        for (x, y, z), c in sorted(add.items()):
            h.write('%d,%d,%d,%d\n' % (x, y, z, c))
    stamp(HULL + '-stern-glass', p)

if want('lamp'):
    # hek 頂中線：船殼在 y=YC 那一欄最高那一格的最後面
    Hc = export_list(HULL, None)
    col = Hc[(Hc[:, 1] == YC) & (Hc[:, 0] < plan['paint']['stern_x_max'])]      # 只看船尾那一段（v1 整條中線 ⇒ 船頭船尾一樣高，燈放到 x 217 的半空中）
    ztop = int(col[:, 2].max())
    xs = col[col[:, 2] == ztop][:, 0]
    lx = (int(xs.min()) + int(xs.max())) / 2.0 + 0.5
    lp = plan['deco']['lantern']
    cli('op=work', 'sub=model', 'persona=Abigail', 'work=' + ASM, 'name=艉燈', 'source_work=' + lp['source'], 'at=%g,%g,%d' % (lx, YC + 0.5, ztop + 1),
        'pivot=8.5,8.5,0', 'scale=%g' % lp['scale'], 'overwrite=1', 'meta={"kind":"light"}', 'note=步驟 6：hek 頂中間的艉燈')
    print('  艉燈 at %g,%g,%d（hek 頂 x %d–%d）' % (lx, YC + 0.5, ztop + 1, xs.min(), xs.max()))
