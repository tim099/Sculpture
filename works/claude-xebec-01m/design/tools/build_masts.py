# 利劍號 步驟 7 落格（TASK-0022）：三根桅子作品、三根三角帆桁子作品（＋固定點）、帆桁模型放在各自的桅子作品裡、組裝件關聯（meta kind=mast＋mast）
#   出處：蠍子號 claude-galiot-01m/design/tools/build_masts.py。改：三根桅（mizzen／main／fore，關聯名 後桅／主桅／前桅）；
#         桅孔步驟 5 就開好了 ⇒ 沒有 hole 這一段；子作品建立用 work=（不是 id=）。
#   用法：python -I -X utf8 tools/build_masts.py <stage>   stage = mast | yard | links
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
SENATE = wio.SENATE
P = 'persona=Claude-Ojousama'
T = 'claude-xebec-01m'
ASM = T + '-assembly'
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
ASIZE = ','.join(str(v) for v in PLAN['space']['assembly'])
YC = int(PLAN['space']['yc'])
NOTE = '步驟 7（TASK-0022；design/draft_masts.py）'
stage = sys.argv[1]


def cli(*args):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), '')
    print('  exit=%d %s' % (r.returncode, line[:160]), flush=True)
    if r.returncode != 0:
        print(out[-2000:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args)))
    return out


def count(path):
    return sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))


def voxels(work):
    r = subprocess.run([SENATE, 'cmd', 'sculpture', '--arg', 'op=stats', '--arg', 'work=' + work, '--arg', 'links=none'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        return None
    m = re.search(r'total_voxels = (\d+)', r.stdout + r.stderr)
    return int(m.group(1)) if m else None


def create(w, title, size):
    if voxels(w) is not None:
        cli('op=work', 'sub=update', P, 'work=' + w, 'title=' + title)      # 已經有了 ⇒ 只把標題換成現在的讀數
        print('· exists', w)
        return
    cli('op=work', 'sub=create', P, 'work=' + w, 'title=' + title, 'size=' + size, 'parent_work=' + T, 'tags=sub')
    cli('op=work', 'sub=update', P, 'work=' + w, 'meters_per_voxel=0.1')
    print('✓ created', w)


def stamp(w, path):
    n = count(path)
    have = voxels(w)
    if have == n:
        print('· %s already has %d cells' % (w, n))
        return
    if have != 0:
        raise SystemExit('✗ %s has %s cells ≠ 0 or %d' % (w, have, n))
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', path], capture_output=True, text=True, encoding='utf-8')
    print(r.stdout.strip())
    if r.returncode:
        raise SystemExit('✗ stamp ' + w)


NAMES = {'mizzen': '後桅', 'main': '主桅', 'fore': '前桅'}
VM = json.load(open(os.path.join(HERE, 'verify_masts.json'), encoding='utf-8'))['masts']
if stage == 'mast':
    for m, nm in NAMES.items():
        w = T + '-mast-' + m
        v = VM[m]
        create(w, '利劍號 %s（%.1f m，徑 %.1f m，傾 %s°，calcet 滑輪箱）' % (nm, v['length_along_axis_m'], (2 * int(v['r']) + 1) * 0.1, v['rake_deg']), ASIZE)
        stamp(w, os.path.join(HERE, 'masks', 'masts', m + '.vox.txt'))
elif stage == 'yard':
    LAT = json.load(open(os.path.join(HERE, 'yards_lateen.json'), encoding='utf-8'))
    for m, nm in NAMES.items():
        L = LAT[m]
        w = T + '-yard-' + m
        create(w, '利劍號 %s三角帆桁（%.1f m，兩段綁成）' % (nm[:1], L['len_m']), '%d,%d,%d' % tuple(L['size']))
        stamp(w, os.path.join(HERE, 'masks', 'yards', 'lateen-%s.vox.txt' % m))
        for an, at in sorted(L['anchors'].items()):
            cli('op=work', 'sub=anchor', P, 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE + '：帆桁固定點')
        print('✓ anchors %s: %d' % (w, len(L['anchors'])))
elif stage == 'links':
    for m, nm in NAMES.items():
        cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=' + nm, 'source_work=' + T + '-mast-' + m, 'at=0,0,0', 'overwrite=1',
            'meta=' + json.dumps({'kind': 'mast', 'mast': m}, separators=(',', ':')), 'note=' + NOTE + '：%s（下桅，kind=mast）' % nm)
        print('✓ link', nm)
    for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
        cli('op=work', 'sub=model', P, 'work=%s-%s' % (T, p['host']), 'name=' + p['name'], 'source_work=' + p['work'],
            'at=%g,%g,%g' % tuple(p['at']), 'pivot=%g,%g,%g' % tuple(p['pivot']), 'rotate=%g,%g,%g' % tuple(p['rotate']),
            'scale=%g,%g,%g' % tuple(p['scale']), 'mirror=none', 'overwrite=1', 'meta=' + json.dumps(p['meta'], ensure_ascii=False, separators=(',', ':')),
            'note=%s：三角帆桁（rig=lateen；yard=gaff；掛在桅的%s舷側）' % (NOTE, '右' if p['at'][1] > YC else '左'))
        print('✓ model', p['host'], p['name'])
else:
    raise SystemExit('stage = mast | yard | links')
