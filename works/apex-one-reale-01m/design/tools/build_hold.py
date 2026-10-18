# 階段五落格（TASK-0704）：舵子作品＋模型、艙底甲板、彈藥庫＋火藥桶、艙口梯（固定點、kind=ladders）、錨、甲板 meta 重排
#   用法：python -I -X utf8 tools/build_hold.py [--skip=<步驟,…>]   步驟：create stamp anchors links models meta
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'apex-one-reale-01m'
ASM = HULL + '-assembly'
P = 'persona=apex-one'
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
PL = json.load(open(os.path.join(HERE, 'hold_placement.json'), encoding='utf-8'))
SUBS = [('rudder', '皇家號 舵（timon，含舵柄；22½ pi × 1.22）', 'rudder'), ('deck-hold', '皇家號 艙底地板與壓艙', 'hold'),
        ('magazine', '皇家號 彈藥庫（soute，銅皮）', 'magazine'), ('ladders-hold', '皇家號 梯子（艙底 → 甲板，espale 艙口）', 'ladder')]


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
    for suf, title, _ in SUBS:
        cli('op=work', 'sub=create', P, 'id=%s-%s' % (HULL, suf), 'title=' + title, 'parent_work=' + HULL, 'size=720,321,140', 'tags=sub')
        cli('op=work', 'sub=update', P, 'work=%s-%s' % (HULL, suf), 'meters_per_voxel=0.1')

if 'stamp' not in skip:
    for suf, _, lst in SUBS:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), '%s-%s' % (HULL, suf), '0',
                            os.path.join(HERE, 'masks', 'hold', lst + '.vox.txt')], text=True, encoding='utf-8')
        if r.returncode:
            sys.exit(1)

if 'anchors' not in skip:
    cli('op=work', 'sub=anchor', P, 'work=%s-rudder' % HULL, 'name=stock-top', 'at=%d,%d,%d' % tuple(PL['rudder']['stock_top']), 'note=舵頭：遊戲在它旁邊 8 格內找掛住的船尾格')
    for nm, p4 in PL['ladder_points'].items():
        for k in ('foot', 'lo', 'hi', 'head'):
            cli('op=work', 'sub=anchor', P, 'work=%s-ladders-hold' % HULL, 'name=%s.%s' % (nm, k), 'at=%d,%d,%d' % tuple(p4[k]), 'note=階段五 艙口梯')

if 'links' not in skip:
    cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=甲板-hold', 'source_work=%s-deck-hold' % HULL, 'at=0,0,0', 'note=階段五')
    cli('op=work', 'sub=link', P, 'work=%s-deck-hold' % HULL, 'name=彈藥庫', 'source_work=%s-magazine' % HULL, 'at=0,0,0',
        'meta=' + json.dumps(PL['magazine_meta'], ensure_ascii=False), 'note=階段五：船尾艙底的火藥艙（soute）')
    cli('op=work', 'sub=link', P, 'work=%s-deck-main' % HULL, 'name=梯子', 'source_work=%s-ladders-hold' % HULL, 'at=0,0,0',
        'meta={"kind":"ladders"}', 'note=階段五：艙底上來的梯子（espale 艙口）')

if 'models' not in skip:
    r = PL['rudder']
    cli('op=work', 'sub=model', P, 'work=' + ASM, 'name=舵', 'source_work=%s-rudder' % HULL, 'at=%g,%g,%g' % tuple(r['at']), 'pivot=%g,%g,%g' % tuple(r['pivot']),
        'scale=1', 'meta=' + json.dumps(r['meta'], ensure_ascii=False), 'note=階段五：舵（鉸鏈 ＝ 艉柱在 z 25 的切線）')
    for b in PL['barrels']:
        cli('op=work', 'sub=model', P, 'work=%s-magazine' % HULL, 'name=' + b['name'], 'source_work=' + PL['barrel_source'], 'at=%g,%g,%g' % tuple(b['at']),
            'pivot=%g,%g,%g' % tuple(PL['barrel_pivot']), 'scale=%g' % PL['barrel_scale'], 'meta={"kind":"powder","powder_lb":100}', 'note=階段五 火藥桶（沿用憲法號）')
    for a in PL['anchors']:
        cli('op=work', 'sub=model', P, 'work=%s-rambade' % HULL, 'name=' + a['name'], 'source_work=' + PL['anchor_source'], 'at=%g,%g,%g' % tuple(a['at']),
            'pivot=%g,%g,%g' % tuple(a['pivot']), 'scale=%g' % a['scale'], 'rotate=0,0,%g' % a['rotate'], 'meta=' + json.dumps(a['meta'], ensure_ascii=False),
            'note=階段五 錨（沿用憲法號的錨 × 0.4，掛在砲台前緣外側）')

if 'meta' not in skip:
    f = os.path.join(HERE, 'decks_meta.tsv')
    rows = [l.rstrip('\n').split('\t') for l in open(f, encoding='utf-8') if l.strip()]
    out = []
    for part, name, js in rows:
        m = json.loads(js)
        if name == '甲板-main':
            m['level'] = 1
        elif name == '甲板-rambade':
            m['level'] = 2
        out.append((part, name, m))
    if not any(n == '甲板-hold' for _, n, _ in out):
        out.insert(0, ('link', '甲板-hold', {'kind': 'deck', 'deck': 'hold', 'level': 0, 'name': '艙底（彈藥庫）', 'floor': '132:15,182:15', 'thick': 2}))
    with open(f, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(''.join('%s\t%s\t%s\n' % (a, b, json.dumps(c, ensure_ascii=False)) for a, b, c in out))
    cli('op=work', 'sub=meta', P, 'work=' + ASM, 'file=' + f.replace('\\', '/'))
