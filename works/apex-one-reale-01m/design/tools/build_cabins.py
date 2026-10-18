# 艙底分間落格（TASK-0694 傘；Tim 2026-10-18「可以試著加一些艙室嗎」「送藥手&其他問題…一起修復」）：
#   艙底分間子作品（地板、隔艙壁＋艙房的框）、艙口梯子作品（固定點、kind=ladders）、甲板-main 刻艙口、甲板 meta（甲板-hold floor、甲板-main walk）
#   用法：python -I -X utf8 tools/build_cabins.py [--skip=<步驟,…>]   步驟：create stamp carve anchors links meta
import os, sys, json, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.stdout.reconfigure(encoding='utf-8')
import wio

HULL = 'apex-one-reale-01m'
ASM = HULL + '-assembly'
P = 'persona=apex-one'
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
PL = json.load(open(os.path.join(HERE, 'cabins_placement.json'), encoding='utf-8'))
SUBS = [('cabins', '皇家號 艙底分間（compagne、paillot、taverne、chambre de proue）', 'cabins'), ('ladders-cabins', '皇家號 艙口梯（中央走道 → 艙底各間）', 'ladders')]


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
                            os.path.join(HERE, 'masks', 'cabins', lst + '.vox.txt')], text=True, encoding='utf-8')
        if r.returncode:
            sys.exit(1)

if 'carve' not in skip:                                    # 甲板-main：目標 ＝ 現在的格 − 艙口 ⇒ delta_apply（帶顏色守門刻）
    w = wio.export_list(HULL + '-deck-main', None)
    cv = np.loadtxt(os.path.join(HERE, 'masks', 'cabins', 'deck_carve.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    kw, kc = wio.key(w), wio.key(cv)
    miss = np.setdiff1d(kc, kw)
    print('  艙口 %d 格；不在甲板-main 的 %d 格（⛔ 要是 0）' % (len(kc), len(miss)), flush=True)
    if len(miss):
        sys.exit(1)
    keep = w[~np.isin(kw, kc)]
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, 'deck_main_target.vox.txt')
        np.savetxt(f, keep, fmt='%d', delimiter=',', header='甲板-main 刻掉艙口之後', encoding='utf-8')
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'delta_apply.py'), HULL + '-deck-main', f], text=True, encoding='utf-8')
        if r.returncode:
            sys.exit(1)

if 'anchors' not in skip:
    for nm, p4 in PL['ladder_points'].items():
        for k in ('foot', 'lo', 'hi', 'head'):
            cli('op=work', 'sub=anchor', P, 'work=%s-ladders-cabins' % HULL, 'name=%s.%s' % (nm, k), 'at=%d,%d,%d' % tuple(p4[k]), 'note=艙口梯（%s）' % nm)
    for nm, b in PL['rooms'].items():
        for k in ('min', 'max', 'door'):
            cli('op=work', 'sub=anchor', P, 'work=%s-cabins' % HULL, 'name=%s.%s' % (nm, k), 'at=%d,%d,%d' % tuple(b[k]), 'note=空艙房（§9.2）%s' % nm)

if 'links' not in skip:
    cli('op=work', 'sub=link', P, 'work=%s-deck-hold' % HULL, 'name=艙房', 'source_work=%s-cabins' % HULL, 'at=0,0,0',
        'meta={"kind":"rooms"}', 'note=艙底分間（Marteilhe 1757）：compagne、paillot、taverne、chambre de proue')
    cli('op=work', 'sub=link', P, 'work=%s-deck-main' % HULL, 'name=梯子-艙房', 'source_work=%s-ladders-cabins' % HULL, 'at=0,0,0',
        'meta={"kind":"ladders"}', 'note=中央走道開艙口下艙底各間（艙口墊高到中央走道的高度，Marteilhe）')

if 'meta' not in skip:
    f = os.path.join(HERE, 'decks_meta.tsv')
    rows = [l.rstrip('\n').split('\t') for l in open(f, encoding='utf-8') if l.strip()]
    out = []
    for part, name, js in rows:
        m = json.loads(js)
        if name == '甲板-hold':
            m['floor'] = PL['hold_floor']
            m['name'] = '艙底（彈藥庫、各間）'
        elif name == '甲板-main':
            m['walk'] = PL['walk']
        out.append((part, name, m))
    with open(f, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(''.join('%s\t%s\t%s\n' % (a, b, json.dumps(c, ensure_ascii=False)) for a, b, c in out))
    cli('op=work', 'sub=meta', P, 'work=' + ASM, 'file=' + f.replace('\\', '/'))
