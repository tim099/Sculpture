# 蠍子號 步驟 7 落格（TASK-0023）：甲板-main 刻桅孔、主桅子作品、三角帆桁子作品（＋固定點）、帆桁模型放在桅子作品裡、組裝件關聯（meta kind=mast＋mast=main）
#   出處：海鷗號 claude-felucca-01m/design/tools/build_masts.py（parts／yards／links）＋越嶺號 kotoko-fusta-01m/design/tools/build_rig.py 的桅孔（mark 桅孔 begin／end 夾一刀 carvevox）。
#   用法：python -I -X utf8 tools/build_masts.py <stage>   stage = hole | mast | yard | links
#   · 只認 exit 0；第一個不是 0 就停。已經做過的不重做：桅孔看甲板-main 的格數、子作品看有沒有格。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
SENATE = wio.SENATE
P = 'persona=Claude-Ojousama'
T = 'claude-galiot-01m'
ASM = T + '-assembly'
DECK = T + '-deck-main'
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
ASIZE = ','.join(str(v) for v in PLAN['space']['assembly'])
NOTE = '步驟 7（TASK-0023；design/draft_masts.py）'
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
        print('· exists', w)
        return
    cli('op=work', 'sub=create', P, 'id=' + w, 'title=' + title, 'size=' + size, 'parent_work=' + T, 'tags=sub')
    cli('op=work', 'sub=update', P, 'id=' + w, 'meters_per_voxel=0.1')
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


if stage == 'hole':
    f = os.path.join(HERE, 'masks', 'masts', 'deck_hole.vox.txt')
    n = count(f)
    deck_n = count(os.path.join(HERE, 'masks', 'decks', 'deck_main.vox.txt'))
    have = voxels(DECK)
    if have == deck_n - n:
        print('· 桅孔已經刻過（%s 有 %d 格）' % (DECK, have))
    elif have == deck_n:
        cli('op=work', 'sub=mark', P, 'work=' + DECK, 'name=桅孔', 'phase=begin', 'note=' + NOTE + '：主桅穿過甲板板、橫樑、中央走道')
        out = cli('op=carvevox', P, 'work=' + DECK, 'voxels=' + f, 'at=0,0,0', 'expect_pixels=%d' % n, 'draft=0', 'share=0')
        cli('op=work', 'sub=mark', P, 'work=' + DECK, 'name=桅孔', 'phase=end')
        print('✓ 桅孔 carvevox %d 格；%s 現在 %s 格' % (n, DECK, voxels(DECK)))
    else:
        raise SystemExit('✗ %s 有 %s 格，不是 %d（還沒刻）也不是 %d（刻過）' % (DECK, have, deck_n, deck_n - n))
elif stage == 'mast':
    w = T + '-mast-main'
    create(w, '蠍子號 主桅（直立，甲板以上 16 m，calcet 滑輪箱）', ASIZE)
    stamp(w, os.path.join(HERE, 'masks', 'masts', 'main.vox.txt'))
elif stage == 'yard':
    LAT = json.load(open(os.path.join(HERE, 'yards_lateen.json'), encoding='utf-8'))['main']
    w = T + '-yard-main'
    create(w, '蠍子號 三角帆桁（antenna，%.1f m，兩段綁成）' % LAT['len_m'], '%d,%d,%d' % tuple(LAT['size']))
    stamp(w, os.path.join(HERE, 'masks', 'yards', 'lateen-main.vox.txt'))
    for an, at in sorted(LAT['anchors'].items()):
        cli('op=work', 'sub=anchor', P, 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE + '：帆桁固定點')
    print('✓ anchors %s: %d' % (w, len(LAT['anchors'])))
elif stage == 'links':
    cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=主桅', 'source_work=' + T + '-mast-main', 'at=0,0,0', 'overwrite=1',
        'meta=' + json.dumps({'kind': 'mast', 'mast': 'main'}, separators=(',', ':')), 'note=' + NOTE + '：主桅（下桅，kind=mast）')
    print('✓ link 主桅')
    for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
        cli('op=work', 'sub=model', P, 'work=%s-%s' % (T, p['host']), 'name=' + p['name'], 'source_work=' + p['work'],
            'at=%g,%g,%g' % tuple(p['at']), 'pivot=%g,%g,%g' % tuple(p['pivot']), 'rotate=%g,%g,%g' % tuple(p['rotate']),
            'scale=%g,%g,%g' % tuple(p['scale']), 'mirror=none', 'overwrite=1', 'meta=' + json.dumps(p['meta'], ensure_ascii=False, separators=(',', ':')),
            'note=%s：三角帆桁（rig=lateen；yard=gaff；掛在桅的左舷側）' % NOTE)
        print('✓ model', p['host'], p['name'])
else:
    raise SystemExit('stage = hole | mast | yard | links')
