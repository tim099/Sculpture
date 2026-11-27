# 利劍號 步驟 9 落格（TASK-0022）：迴旋砲柱 stampvox 進它站的那一層甲板子作品（masks/guns/posts_<deck>.vox.txt）、每門砲一個外部模型掛在那一層甲板子作品上（guns_placement.json）。
#   出處：蠍子號 claude-galiot-01m/design/tools/build_guns.py（砲柱、模型）＋星辰號 claude-baghlah-01m/design/tools/build_guns.py（P 舷 mirror=y、meta 加 deck／side／port、
#         迴旋砲的叉架雙生 `<名>座` kind=gunmount；id 與 mount_of 等步驟 14 Blockside admin.py ids 發號才寫，Ship_Game §12）。
#   用法：python -I -X utf8 tools/build_guns.py   · 只認 exit 0；砲柱已經落過就不重落（讀回格數）；模型 overwrite=1 ⇒ 重跑安全。
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
P = 'persona=Claude-Ojousama'
NOTE = '步驟 9（TASK-0022；design/draft_guns.py）'
GB = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))['guns_build']
PL = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))['rows']
NAMES = {'6l': '6 磅長砲（風暴角號的通用部件，縮 0.5）', '12l': '12 磅長砲（風暴角號的通用部件，縮 0.5）', '3l': '3 磅砲（本船做的通用部件，縮 0.5 ＝ 原尺寸）',
         'pierrier': '迴旋砲 pierrier（補放不下的 12 磅、3 磅；皇家號的通用部件，縮 0.5）'}


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.')


def xyz(v):
    return ','.join(num(float(c)) for c in v)


def cli(*args):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:200]), flush=True)
    if r.returncode != 0:
        print(out[-1500:])
        sys.exit(1)
    return out


# ── 砲柱 ──
for dk, w in sorted(GB['deck_works'].items()):
    f = os.path.join(HERE, 'masks', 'guns', 'posts_%s.vox.txt' % dk)
    if not os.path.exists(f):
        continue
    want = [tuple(map(int, l.split(','))) for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#')]
    have = {tuple(r[:3]): int(r[3]) for r in wio.export_list(w, None).tolist()}
    todo = [p for p in want if have.get(p[:3]) != p[3]]
    if not todo:
        print('· %s 砲柱已經落過（%d 格）' % (w, len(want)))
        continue
    assert not any(p[:3] in have for p in todo), ('要落的砲柱位置上已經有格', w, len(todo), len(want))
    if len(todo) < len(want):                                           # v2（2026-11-27）加砲柱：已經落過的不重落，只落新的那幾柱
        f = os.path.join(HERE, 'masks', 'guns', 'posts_%s.todo.vox.txt' % dk)
        with open(f, 'w', encoding='utf-8', newline='\n') as fo:
            fo.write('# 還沒落的砲柱（build_guns.py 從 posts_%s.vox.txt 扣掉作品裡已經有的）\n' % dk)
            fo.write(''.join('%d,%d,%d,%d\n' % p for p in todo))
        print('· %s 砲柱 %d 格已經落過，這次落 %d 格' % (w, len(want) - len(todo), len(todo)))
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', f], capture_output=True, text=True, encoding='utf-8')
    print(r.stdout.strip())
    if r.returncode:
        sys.exit(1)
# ── 模型 ──
n = 0
for r in PL:
    t = GB['types'][r['type']]
    s = float(t['scale'])
    meta = dict(t['meta'])
    meta.update({'deck': r['deck'], 'side': r['side'], 'port': r['port'] if isinstance(r['port'], int) else r['group']})
    if r['swivel']:
        meta['arc'] = r['arc']
    where = ('%s 甲板第 %d 個砲門' % (r['deck'], r['port'])) if isinstance(r['port'], int) else ('%s 甲板 x %d（%s）' % (r['deck'], int(r['at'][0]), r['group']))
    note = '%s：%s（%s 舷、%s；draft_guns.py 退 %s 格%s）' % (NOTE, NAMES[r['type']], r['side'], where, num(float(r['back'])),
                                                        '、往船頭偏 %d°' % r['angle_fwd'] if r.get('angle_fwd') else '')
    base = ['op=work', 'sub=model', P, 'work=' + GB['deck_works'][r['deck']], 'at=' + xyz(r['at']), 'pivot=' + xyz(t['pivot']),
            'rotate=0,0,' + num(float(r['phi'])), 'scale=' + xyz([s, s, s]), 'mirror=' + ('y' if r['side'] == 'P' else 'none'), 'overwrite=1']
    todo = [(r['name'], t['work'], meta, note)]
    if t.get('mount_work'):
        todo.append((r['name'] + '座', t['mount_work'], {'kind': 'gunmount'}, '%s：%s的叉架（拆件雙生，Ship_Guns §4.2.1；mount_of 等步驟 14 發 id 後補）' % (NOTE, r['name'])))
    for nm, src, mt, nt in todo:
        cli(*(base + ['name=' + nm, 'source_work=' + src, 'meta=' + json.dumps(mt, ensure_ascii=False, separators=(',', ':')), 'note=' + nt]))
        n += 1
print('✓ 模型 %d 個（設計 %d）' % (n, sum(2 if GB['types'][r['type']].get('mount_work') else 1 for r in PL)))
