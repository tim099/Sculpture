# 越嶺號 階段五落格（TASK-0762）：舵（子作品＋組裝件模型）、艙底（甲板-hold）、彈藥庫（甲板-hold/彈藥庫，火藥桶與箭箱模型）、
#   艙口梯（甲板-main/梯子）、四爪錨（新通用部件＋甲板-bow 的兩個模型）、每層甲板的 meta
#   用法：python -I -X utf8 tools/build_hold.py
import os, sys, json, re, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
T = 'kotoko-fusta-01m'
ASM = T + '-assembly'
P = 'persona=kotoko'
HP = json.load(open(os.path.join(HERE, 'hold_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


def ensure(work, title, size, mpv):
    if subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=show', '--arg', 'work=' + work], capture_output=True).returncode:
        cli('op=work', 'sub=create', P, 'id=' + work, 'title=' + title, 'parent_work=' + T, 'size=%d,%d,%d' % tuple(size), 'tags=sub')
        cli('op=work', 'sub=update', P, 'work=' + work, 'meters_per_voxel=%g' % mpv)
    f = os.path.join(HERE, 'masks', 'hold', {'-rudder': 'rudder', '-hold': 'hold', '-magazine': 'magazine', '-ladders': 'ladder', '-anchor-grapnel': 'anchor'}[work[len(T):]] + '.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    have = int(re.search(r'total_voxels = (\d+)', cli('op=stats', 'work=' + work, 'links=none')).group(1))   # 只數自己的格（艙底底下掛著彈藥庫）
    if have == 0:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), work, '0', f], text=True, encoding='utf-8')
        if r.returncode:
            sys.exit(1)
    elif have != n:
        sys.exit('✗ %s 已有 %d 格 ≠ 清單 %d' % (work, have, n))


ensure(T + '-rudder', '越嶺號 舵（尾柱舵 timon bavonescho＋舵柄）', (360, 161, 80), 0.1)
ensure(T + '-hold', '越嶺號 艙底（地板＋壓艙碎石）', (360, 161, 80), 0.1)
ensure(T + '-magazine', '越嶺號 彈藥庫（銅皮牆；火藥桶與箭箱）', (360, 161, 80), 0.1)
ensure(T + '-ladders', '越嶺號 艙口梯（船尾艙口 → 艙底）', (360, 161, 80), 0.1)
ac = HP['anchor_component']
ensure(ac['work'], '四爪錨（grapnel，地中海槳帆船的錨；通用部件，0.05 m）', ac['size'], 0.05)
NOTE = {'ring': '錨環頂：鐵鍊綁的地方', 'crown': '錨冠最低那一格：落地那一點', 'fluke-a': '錨爪尖', 'fluke-b': '錨爪尖（對面那一支）'}
for nm, at in ac['anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + ac['work'], 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE[nm])

# 舵：組裝件的模型（at ＝ pivot ＝ 鉸鏈下端）；舵頭 stock-top
r = HP['rudder']
cli('op=work', 'sub=anchor', P, 'work=%s-rudder' % T, 'name=stock-top', 'at=%d,%d,%d' % tuple(r['stock_top']), 'overwrite=1', 'note=舵頭（遊戲在它旁邊 8 格內找掛住的船尾格）')
cli('op=work', 'sub=model', P, 'work=' + ASM, 'name=舵', 'source_work=%s-rudder' % T, 'at=%g,%g,%g' % tuple(r['at']), 'pivot=%g,%g,%g' % tuple(r['pivot']),
    'scale=1', 'rotate=0,0,0', 'mirror=none', 'overwrite=1', 'meta=' + json.dumps(r['meta'], ensure_ascii=False), 'note=階段五 尾柱舵')

# 艙底、彈藥庫（巢狀關聯）、火藥桶與箭箱
cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=甲板-hold', 'source_work=%s-hold' % T, 'at=0,0,0', 'overwrite=1', 'note=階段五')
cli('op=work', 'sub=link', P, 'work=%s-hold' % T, 'name=彈藥庫', 'source_work=%s-magazine' % T, 'at=0,0,0', 'overwrite=1',
    'meta=' + json.dumps(HP['magazine_meta'], ensure_ascii=False), 'note=階段五')
for s in HP['stores']:
    cli('op=work', 'sub=model', P, 'work=%s-magazine' % T, 'name=' + s['name'], 'source_work=' + s['work'], 'at=%g,%g,%g' % tuple(s['at']),
        'pivot=%g,%g,%g' % tuple(s['pivot']), 'scale=%g' % s['scale'], 'rotate=%g,%g,%g' % tuple(s['rotate']), 'mirror=none', 'overwrite=1',
        'meta=' + json.dumps(s['meta'], ensure_ascii=False), 'note=階段五 補給')

# 艙口梯：甲板-main 底下的關聯 梯子（kind=ladders），固定點 hold.foot／lo／hi／head
cli('op=work', 'sub=link', P, 'work=%s-deck-main' % T, 'name=梯子', 'source_work=%s-ladders' % T, 'at=0,0,0', 'overwrite=1', 'meta={"kind":"ladders"}', 'note=階段五')
for L in HP['ladders']:
    for k, at in L['points'].items():
        cli('op=work', 'sub=anchor', P, 'work=%s-ladders' % T, 'name=%s.%s' % (L['name'], k), 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=階段五 梯子點（腳踩的那一格）')

# 四爪錨：甲板-bow 的兩個模型
for a in HP['anchors']:
    cli('op=work', 'sub=model', P, 'work=%s-bow' % T, 'name=' + a['name'], 'source_work=' + a['work'], 'at=%g,%g,%g' % tuple(a['at']),
        'pivot=%g,%g,%g' % tuple(a['pivot']), 'scale=%g' % a['scale'], 'rotate=%g,%g,%g' % tuple(a['rotate']), 'mirror=none', 'overwrite=1',
        'meta=' + json.dumps(a['meta'], ensure_ascii=False), 'note=階段五 四爪錨（掛在船首平台前緣外側）')

# 甲板 meta
f = os.path.join(HERE, 'decks_meta.tsv')
with open(f, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(''.join('%s\t%s\t%s\n' % (a, b, json.dumps(c, ensure_ascii=False)) for a, b, c in HP['decks']))
cli('op=work', 'sub=meta', P, 'work=' + ASM, 'file=' + f.replace('\\', '/'))
