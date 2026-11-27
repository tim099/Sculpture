# 蠍子號 步驟 10 落格（TASK-0023）：藥艙子作品（船殼的框、0.1 m、parent 船殼、tags sub）⇒ stampvox room.vox.txt ⇒ 固定點 blast／door ⇒
#   組裝件關聯「彈藥庫」＋meta ⇒ 火藥桶模型（放在藥艙子作品裡）、艉燈模型（放在艉台子作品裡）、艙蓋（kind=door，放在甲板-main）。
#   出處：海鷗號 claude-felucca-01m/design/tools/build_magazine.py（固定點、關聯、模型那一段）；建子作品、落格照本船 tools/build_deco.py。
#   用法：python -I -X utf8 tools/build_magazine.py   · 只認 exit 0；已經有格的不重落（讀回格數 ＝ 清單才算數，不等就停）；關聯、模型 overwrite=1 ⇒ 重跑安全。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
P = 'persona=Claude-Ojousama'
T = 'claude-galiot-01m'
ASM = T + '-assembly'
NOTE = '步驟 10（TASK-0023；design/draft_magazine.py）'
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
MP = json.load(open(os.path.join(HERE, 'magazine_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return r.returncode, out


w = MP['hosts']['magazine']
f = os.path.join(HERE, 'masks', 'magazine', 'room.vox.txt')
n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
rc, out = cli('op=work', 'sub=show', 'work=' + w, ok=(0, 1, 2))
if rc != 0:
    cli('op=work', 'sub=create', P, 'id=' + w, 'title=蠍子號 藥艙（船首那段艙底；銅皮、松木地板）', 'size=' + ','.join(str(v) for v in PLAN['space']['hull']), 'parent_work=' + T, 'tags=sub')
    cli('op=work', 'sub=update', P, 'id=' + w, 'meters_per_voxel=0.1')
    print('· 建了', w)
rc, out = cli('op=stats', P, 'work=' + w)
have = int(re.search(r'total_voxels = (\d+)', out).group(1))
if have == 0:
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', f], capture_output=True, text=True, encoding='utf-8')
    print(r.stdout.strip())
    if r.returncode:
        sys.exit(1)
elif have != n:
    sys.exit('✗ %s 已有 %d 格 ≠ 清單 %d' % (w, have, n))
else:
    print('· 藥艙已經落過（%d 格）' % n)
for name, at in MP['anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + w, 'name=' + name, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE)
cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=' + MP['link']['name'], 'source_work=' + w, 'at=0,0,0',
    'meta=' + json.dumps(MP['link']['meta'], ensure_ascii=False, separators=(',', ':')), 'overwrite=1', 'note=' + NOTE + '：艙底的藥艙')
for m in MP['models']:
    cli('op=work', 'sub=model', P, 'work=' + MP['hosts'][m['host']], 'name=' + m['name'], 'source_work=' + m['work'],
        'at=%g,%g,%g' % tuple(m['at']), 'pivot=%g,%g,%g' % tuple(m['pivot']), 'scale=' + (','.join('%g' % v for v in m['scale']) if isinstance(m['scale'], list) else '%g' % m['scale']), 'rotate=%g,%g,%g' % tuple(m['rotate']),
        'mirror=none', 'meta=' + json.dumps(m['meta'], ensure_ascii=False, separators=(',', ':')), 'overwrite=1', 'note=' + NOTE)
