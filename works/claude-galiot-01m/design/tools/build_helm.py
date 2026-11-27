# 蠍子號 步驟 11 落格（TASK-0023）：舵、舵柄各一件子作品（船殼的框、0.1 m、parent 船殼、tags sub；stampvox 讀回）＋固定點、組裝件裡的模型（at ＝ pivot ＝ 鉸鏈點）、
#   兩隻四爪錨模型（掛在船首平台子作品）、舵頭鐵箍（stampvox 進艉台子作品）、吊錨木（stampvox 進船首平台子作品）、船殼的錨鏈孔固定點 hawse-S／P。
#   出處：海鷗號 claude-felucca-01m/design/tools/build_helm.py（順序：子作品 → 固定點 → 模型）；建子作品照本船 tools/build_magazine.py。
#   用法：python -I -X utf8 tools/build_helm.py   · 只認 exit 0；已經有格的子作品不重貼（讀回格數 ＝ 清單才算數）；模型、固定點 overwrite=1 ⇒ 重跑安全。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
P = 'persona=Claude-Ojousama'
HULL = 'claude-galiot-01m'
ASM = HULL + '-assembly'
NOTE = '步驟 11（TASK-0023；design/draft_helm.py）'
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
HP = json.load(open(os.path.join(HERE, 'helm_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return r.returncode, out


for key in ('rudder', 'tiller'):
    h = HP[key]
    f = os.path.join(HERE, 'masks', 'helm', key + '.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    rc, out = cli('op=work', 'sub=show', 'work=' + h['work'], ok=(0, 1, 2))
    if rc != 0:
        cli('op=work', 'sub=create', P, 'id=' + h['work'], 'title=' + h['title'], 'size=' + ','.join(str(v) for v in PLAN['space']['hull']), 'parent_work=' + HULL, 'tags=sub')
        cli('op=work', 'sub=update', P, 'id=' + h['work'], 'meters_per_voxel=0.1')
    rc, out = cli('op=stats', P, 'work=' + h['work'])
    have = int(re.search(r'total_voxels = (\d+)', out).group(1))
    if have == 0:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), h['work'], '0', f], capture_output=True, text=True, encoding='utf-8')
        print(r.stdout.strip())
        if r.returncode:
            sys.exit(1)
    elif have != n:
        sys.exit('✗ %s 已有 %d 格 ≠ 清單 %d' % (h['work'], have, n))
    for an, at in h['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + h['work'], 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE)
    cli('op=work', 'sub=model', P, 'work=' + ASM, 'name=' + h['model'], 'source_work=' + h['work'], 'at=%g,%g,%g' % tuple(h['at']),
        'pivot=%g,%g,%g' % tuple(h['pivot']), 'scale=1', 'rotate=0,0,0', 'mirror=none', 'meta=' + json.dumps(h['meta'], ensure_ascii=False, separators=(',', ':')),
        'overwrite=1', 'note=' + NOTE)
for a in HP['anchors']:
    cli('op=work', 'sub=model', P, 'work=' + HP['hosts'][a['host']], 'name=' + a['name'], 'source_work=' + a['work'], 'at=%g,%g,%g' % tuple(a['at']),
        'pivot=%g,%g,%g' % tuple(a['pivot']), 'scale=%g' % a['scale'], 'rotate=%g,%g,%g' % tuple(a['rotate']), 'mirror=none',
        'meta=' + json.dumps(a['meta'], ensure_ascii=False, separators=(',', ':')), 'overwrite=1', 'note=' + NOTE + '：四爪錨（FUR p.80：galeotta 兩個錨）')
# 舵頭鐵箍（艉台子作品）、吊錨木（船首平台子作品）：已經落過 ⇒ 不重落
for fn, host in (('strap', HP['hosts']['poop']), ('cathead', HP['hosts']['bow'])):
    f = os.path.join(HERE, 'masks', 'helm', fn + '.vox.txt')
    want = [tuple(map(int, l.split(','))) for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#')]
    have = {tuple(r[:3]): int(r[3]) for r in wio.export_list(host, None).tolist()}
    todo = [w for w in want if have.get(w[:3]) != w[3]]
    if todo:
        assert len(todo) == len(want), (fn + ' 只落了一部分？', len(todo), len(want))
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), host, '0', f], capture_output=True, text=True, encoding='utf-8')
        print(r.stdout.strip())
        if r.returncode:
            sys.exit(1)
    else:
        print('· %s 已經落過（%d 格）' % (fn, len(want)))
for an, at in HP['hull_anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + HULL, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE + '：錨鏈孔（錨纜過胸牆頂的地方）')
