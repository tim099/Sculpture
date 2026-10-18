# 階段二落格（TASK-0698）：建子作品、貼清單、梯子固定點、關聯（組裝件 → 子作品；砲台 → 梯子 meta kind=ladders）、船尾燈模型、船尾塗裝
#   用法：python -I -X utf8 tools/build_upper.py [--skip=<步驟,…>]   步驟：create stamp anchors links lanterns paint
#   · 每一刀讀回（stamp_lists.py 對 placed）；已經做過的步驟可以 --skip 掉（建子作品重跑會被擋：同 ID 已存在）。
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'apex-one-reale-01m'
ASM = HULL + '-assembly'
SUBS = [  # (後綴, 名稱, 清單, 組裝件裡的關聯名, meta)
    ('deck-main', '皇家號 甲板（couverte）・中央走道・划手座', 'deck', '甲板-main', None),
    ('apostis', '皇家號 舷外槳架（apostis）', 'apostis', '舷外槳架', None),
    ('rambade', '皇家號 船頭砲台（rambade）與角落平台', 'rambade', '甲板-rambade', None),
    ('ladders-rambade', '皇家號 梯子（甲板 → 船頭砲台）', 'ladders', None, None),
    ('eperon', '皇家號 撞角（éperon）', 'eperon', '撞角', None),
    ('stern', '皇家號 船尾篷・翹尾・燈桿', 'stern', '船尾', None),
]
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


if 'create' not in skip:
    for suf, title, _, _, _ in SUBS:
        w = '%s-%s' % (HULL, suf)
        print('建', w)
        cli('op=work', 'sub=create', 'persona=apex-one', 'id=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=720,321,140', 'tags=sub')
        cli('op=work', 'sub=update', 'persona=apex-one', 'work=' + w, 'meters_per_voxel=0.1')

if 'stamp' not in skip:
    for suf, _, lst, _, _ in SUBS:
        w = '%s-%s' % (HULL, suf)
        f = os.path.join(HERE, 'masks', 'upper', lst + '.vox.txt')
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', f], text=True, encoding='utf-8')
        if r.returncode:
            sys.exit(1)

if 'anchors' not in skip:
    pts = json.load(open(os.path.join(HERE, 'ladder_points.json'), encoding='utf-8'))
    for nm, p4 in pts.items():
        for k in ('foot', 'lo', 'hi', 'head'):
            cli('op=work', 'sub=anchor', 'persona=apex-one', 'work=%s-ladders-rambade' % HULL, 'name=%s.%s' % (nm, k), 'at=%d,%d,%d' % tuple(p4[k]),
                'note=階段二 梯子 %s %s' % (nm, k))

if 'links' not in skip:
    for suf, _, _, link, _ in SUBS:
        if link:
            cli('op=work', 'sub=link', 'persona=apex-one', 'work=' + ASM, 'name=' + link, 'source_work=%s-%s' % (HULL, suf), 'at=0,0,0', 'note=階段二')
    cli('op=work', 'sub=link', 'persona=apex-one', 'work=%s-rambade' % HULL, 'name=梯子', 'source_work=%s-ladders-rambade' % HULL, 'at=0,0,0',
        'meta={"kind":"ladders"}', 'note=階段二：甲板上來的兩座梯子')

if 'lanterns' not in skip:
    for L in json.load(open(os.path.join(HERE, 'lanterns.json'), encoding='utf-8')):
        cli('op=work', 'sub=model', 'persona=apex-one', 'work=%s-stern' % HULL, 'name=' + L['name'], 'source_work=' + L['source'],
            'at=%g,%g,%g' % tuple(L['at']), 'pivot=8.5,8.5,0', 'scale=%g' % L['scale'], 'meta={"kind":"light"}',
            'note=階段二 船尾燈（Réale 三盞並排；沿用三叉戟號船尾燈）')

if 'paint' not in skip:
    f = os.path.join(HERE, 'masks', 'paint', 'stern.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    cli('op=work', 'sub=mark', 'persona=apex-one', 'work=' + HULL, 'name=船尾塗裝', 'phase=begin')
    out = cli('op=stampvox', 'persona=apex-one', 'work=' + HULL, 'voxels=' + f.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n,
              'overwrite=1', 'draft=0', 'share=0')
    cli('op=work', 'sub=mark', 'persona=apex-one', 'work=' + HULL, 'name=船尾塗裝', 'phase=end')
