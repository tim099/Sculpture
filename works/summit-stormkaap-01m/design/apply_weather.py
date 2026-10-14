# 階段十七：照 verify_weather.json 換色 —— 五件甲板子作品各一刀 stampvox overwrite。
# 守門：先匯出那件甲板，清單上每一格的現色要是 104（原色）或已經是目標色（重跑）；有一格不是 ⇒ 那一件整刀不換。只換跟目標不同的格。
# 用法：python -I -X utf8 -B apply_weather.py <design 資料夾>
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
V = json.load(open(os.path.join(D, 'verify_weather.json'), encoding='utf-8'))
tmp = os.path.join(os.path.dirname(D), 'exports', 'stage17_apply'); os.makedirs(tmp, exist_ok=True)
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1; print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


def rd(p):
    return {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}


for d in V['decks']:
    cur_p = os.path.join(tmp, d['work'] + '.list.txt').replace('\\', '/')
    cli(['op=export', 'format=list', 'work=' + d['work'], 'out=' + cur_p])
    cur, want = rd(cur_p), rd(os.path.join(D, d['file']))
    # 放行：原色 104、目標色、前一版風化用過的色（to_history；第一版 105 在燈下偏紫紅、看起來像糖果條紋 ⇒ 換掉重落）
    okc = {V['from']} | set(V.get('to_history', []))
    wrong = [k for k, c in want.items() if cur.get(k) not in okc and cur.get(k) != c]
    if wrong:
        print('✗ %s：%d 格的現色既不是 %d、前一版的色、也不是目標色（例 %s）⇒ 這一件不換' % (d['link'], len(wrong), V['from'], wrong[:3])); bad += 1
        continue
    todo = {k: c for k, c in want.items() if cur.get(k) != c}
    if not todo:
        print(d['link'], '全部已經是目標色'); continue
    tp = os.path.join(tmp, d['work'] + '.todo.vox.txt')
    with open(tp, 'w', encoding='utf-8', newline='\n') as f:
        for k, c in sorted(todo.items()):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c))
    if all(cur.get(k) == V['from'] for k in want):                # 第一次才標 begin；重跑 ⛔ 不把 begin 挪到上一版之後
        cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + d['work'], 'name=stage17', 'phase=begin', 'overwrite=1', 'note=階段十七 甲板風化之前'])
    rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + d['work'], 'voxels=' + tp.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(todo), 'overwrite=1', 'draft=0'])
    m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', out)
    cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + d['work'], 'name=stage17', 'phase=end', 'overwrite=1', 'note=階段十七 甲板風化之後'])
    print(d['link'], '換', len(todo), 'placed', m.group(1) if m else '?')
print('ok', ok, 'bad', bad)
