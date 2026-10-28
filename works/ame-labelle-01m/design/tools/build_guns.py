# 拉貝爾號 步驟 9（TASK-0965）；出處 calli-cosecha-01m/design/tools/build_guns.py（砲種名、迴旋砲的 port 換本船）。
# 原檔頭：階段八落格：照 guns_placement.json 每門砲一個外部模型，掛在所在甲板的子作品上（藏甲板就一起藏；造船規格 §4.2）
#   用法：python -I -X utf8 tools/build_guns.py <design>（重跑：overwrite=1）
#   · P 舷 mirror=y；meta ＝ 砲種的 meta（kind、gun）＋ deck、side、port
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
GB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['guns_build']
PL = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']
NAMES = {'4l': '4 磅砲（4 磅砲通用部件 pinnacle-patache-01m-gun-4l 縮 0.443；Tim 2026-10-28 換）', 'pierrier': '迴旋砲 pierrier（皇家號 -gun-pierrier 縮 0.39）'}


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


ok = bad = 0
for r in PL:
    t = GB['types'][r['type']]
    s = float(t['scale'])
    meta = dict(t['meta'])
    meta.update({'deck': r['deck'], 'side': r['side'], 'port': r['port']})
    note = '%s（步驟 9 TASK-0965；%s 舷%s；draft_guns.py back %s、砲口伸出 %s）' % (
        NAMES[r['type']], r['side'], ('、%s 第 %d 個砲門' % (r['deck'], r['port'])) if isinstance(r['port'], int) else '、舷牆頂 x %s' % r['port'][2:], num(float(r['back'])), num(float(r['muzzle_beyond'])))
    args = ['op=work', 'sub=model', 'persona=ame', 'work=' + GB['deck_works'][r['deck']], 'name=' + r['name'], 'source_work=' + t['work'],
            'at=' + xyz(r['at']), 'pivot=' + xyz(t['pivot']), 'rotate=0,0,' + num(float(r['phi'])), 'scale=' + xyz([s, s, s]), 'overwrite=1',
            'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')), 'note=' + note]
    if r['side'] == 'P':
        args.append('mirror=y')
    p = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        bad += 1
        print('✗', r['name'], (p.stdout + p.stderr)[-500:])
    else:
        ok += 1
print('模型 ok %d／bad %d（設計 %d）' % (ok, bad, len(PL)))
