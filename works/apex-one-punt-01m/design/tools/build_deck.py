# 階段二落格（TASK-0754）：建子作品、貼清單、梯子固定點、關聯（組裝件 → 甲板／平台／叉柱；甲板-main → 梯子 meta kind=ladders）、甲板 meta、船殼 meta
#   用法：python -I -X utf8 tools/build_deck.py [--skip=<步驟,…>]   步驟：create stamp anchors links meta
#   · 每一刀讀回（stamp_lists.py 對 placed）；已經做過的步驟可以 --skip 掉（建子作品重跑會被擋：同 ID 已存在）。
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'apex-one-punt-01m'
ASM = HULL + '-assembly'
P = 'persona=apex-one'
SUBS = [  # (後綴, 名稱, 清單, 組裝件裡的關聯名)
    ('deck-main', '蓬特號 甲板（橫樑穿出船殼、艙口）', 'deck_main', '甲板-main'),
    ('deck-hold', '蓬特號 貨艙地板（壓艙）', 'deck_hold', '甲板-hold'),
    ('platform-aft', '蓬特號 艉台（欄杆、舵柱）', 'platform_aft', '平台-aft'),
    ('platform-fwd', '蓬特號 艏台（欄杆）', 'platform_fwd', '平台-fwd'),
    ('truss', '蓬特號 truss 叉柱', 'crutches', 'truss叉柱'),
    ('ladders', '蓬特號 梯子（貨艙、艉台、艏台；兩邊扶手）', 'ladders', None),
]
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
PL = json.load(open(os.path.join(HERE, 'deck_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


if 'create' not in skip:
    for suf, title, _, _ in SUBS:
        w = '%s-%s' % (HULL, suf)
        cli('op=work', 'sub=create', P, 'id=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=280,201,140', 'tags=sub')
        cli('op=work', 'sub=update', P, 'work=' + w, 'meters_per_voxel=0.1')

if 'stamp' not in skip:
    for suf, _, lst, _ in SUBS:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), '%s-%s' % (HULL, suf), '0',
                            os.path.join(HERE, 'masks', 'deck', lst + '.vox.txt')], text=True, encoding='utf-8')
        if r.returncode:
            sys.exit(1)

if 'anchors' not in skip:
    for nm, p4 in PL['ladders'].items():
        for k in ('foot', 'lo', 'hi', 'head'):
            cli('op=work', 'sub=anchor', P, 'work=%s-ladders' % HULL, 'name=%s.%s' % (nm, k), 'at=%d,%d,%d' % tuple(p4[k]), 'note=階段二 梯子 %s %s' % (nm, k))

if 'links' not in skip:
    for suf, _, _, link in SUBS:
        if link:
            cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=' + link, 'source_work=%s-%s' % (HULL, suf), 'at=0,0,0', 'note=階段二')
    cli('op=work', 'sub=link', P, 'work=%s-deck-main' % HULL, 'name=梯子', 'source_work=%s-ladders' % HULL, 'at=0,0,0',
        'meta={"kind":"ladders"}', 'note=階段二：貨艙、艉台、艏台三座梯子')

if 'meta' not in skip:
    for link, m in PL['decks'].items():
        cli('op=work', 'sub=meta', P, 'work=' + ASM, 'part=link', 'name=' + link, 'meta=' + json.dumps(m, ensure_ascii=False))
    cli('op=work', 'sub=meta', P, 'work=' + ASM, 'part=link', 'name=船殼', 'meta={"kind":"ship","waterline_z":12}')
