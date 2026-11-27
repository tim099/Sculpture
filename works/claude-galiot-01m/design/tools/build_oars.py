# 蠍子號 步驟 13 落格（TASK-0023）：舷外槳架子作品（船殼的框，stampvox 讀回）＋組裝件關聯「舷外槳架」；兩件槳元件（0.05 m，同一份格子、seat 不同）＋固定點 pivot／blade／seat；
#   40 支槳的模型掛在舷外槳架子作品裡（皇家號同一個做法）。
#   出處：海鷗號 claude-felucca-01m/design/tools/build_oars.py（模型那一段、mirror）；建子作品、落格照本船 tools/build_magazine.py。
#   用法：python -I -X utf8 tools/build_oars.py   · 只認 exit 0；已經有格的子作品不重貼（讀回格數 ＝ 清單才算數）；模型、固定點、關聯 overwrite=1 ⇒ 重跑安全。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
P = 'persona=Claude-Ojousama'
HULL = 'claude-galiot-01m'
ASM = HULL + '-assembly'
NOTE = '步驟 13（TASK-0023；design/draft_oars.py）'
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
OP = json.load(open(os.path.join(HERE, 'oars_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return r.returncode, out


def ensure(work, title, size, mpv, fn):
    n = sum(1 for l in open(fn, encoding='utf-8') if l.strip() and not l.startswith('#'))
    rc, out = cli('op=work', 'sub=show', 'work=' + work, ok=(0, 1, 2))
    if rc != 0:
        cli('op=work', 'sub=create', P, 'id=' + work, 'title=' + title, 'size=' + ','.join(str(v) for v in size), 'parent_work=' + HULL, 'tags=sub')
        cli('op=work', 'sub=update', P, 'id=' + work, 'meters_per_voxel=%g' % mpv)
    rc, out = cli('op=stats', P, 'work=' + work)
    have = int(re.search(r'total_voxels = (\d+)', out).group(1))
    if have == 0:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), work, '0', fn], capture_output=True, text=True, encoding='utf-8')
        print(r.stdout.strip())
        if r.returncode:
            sys.exit(1)
    elif have != n:
        sys.exit('✗ %s 已有 %d 格 ≠ 清單 %d' % (work, have, n))
    else:
        print('· %s 已經落過（%d 格）' % (work, n))


ensure(OP['host'], '蠍子號 舷外槳架（apostis）與槳栓', PLAN['space']['hull'], 0.1, os.path.join(HERE, 'masks', 'oars', 'apostis.vox.txt'))
cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=舷外槳架', 'source_work=' + OP['host'], 'at=0,0,0', 'overwrite=1', 'note=' + NOTE)
for w, c in OP['components'].items():
    ensure(w, c['title'], OP['component_size'], 0.05, os.path.join(HERE, 'masks', 'oars', 'oar.vox.txt'))
    for an, at in c['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE)
for m in OP['models']:
    cli('op=work', 'sub=model', P, 'work=' + OP['host'], 'name=' + m['name'], 'source_work=' + m['work'], 'at=%g,%g,%g' % tuple(m['at']),
        'pivot=%g,%g,%g' % tuple(m['pivot']), 'scale=%g' % m['scale'], 'rotate=%g,%g,%g' % tuple(m['rotate']), 'mirror=' + (m['mirror'] or 'none'),
        'meta=' + json.dumps(m['meta'], ensure_ascii=False, separators=(',', ':')), 'overwrite=1', 'note=' + NOTE)
