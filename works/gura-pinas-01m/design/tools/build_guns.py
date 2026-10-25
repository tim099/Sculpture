# 出處：calli-cosecha-01m/design/tools/build_guns.py（收穫號，照抄後改成藍鯊號 —— TASK-0967）
# 階段八落格：照 guns_placement.json 每門砲一個外部模型，掛在所在甲板的子作品上（藏甲板就一起藏；造船規格 §4.2）
#   用法：python -I -X utf8 tools/build_guns.py <design>（重跑：overwrite=1）
#   · P 舷 mirror=y；meta ＝ 砲種的 meta（kind、gun）＋ deck、side、port
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
GB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['guns_build']
PL = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']
NAMES = {'18l': '18 磅長砲（憲法號 -gun-long18）', '18chase': '18 磅追擊砲（憲法號 -gun-long18）', '12l': '12 磅長砲（風暴角號 -gun-12l）', '6l': '6 磅砲（風暴角號 -gun-6l）'}


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


ok = bad = 0
for r in PL:
    t = GB['types'][r['type']]
    s = float(t['scale'])
    meta = dict(t['meta'])
    meta.update({'deck': r['deck'], 'side': r['side'], 'port': r['port'] if isinstance(r['port'], int) else 'stern'})
    note = '%s（階段八 TASK-0597；%s 舷%s；draft_guns.py back %s、砲口伸出 %s）' % (
        NAMES[r['type']], r['side'], ('、%s 第 %d 個砲門' % (r['deck'], r['port'])) if isinstance(r['port'], int) else '、船尾', num(float(r['back'])), num(float(r['muzzle_beyond'])))
    args = ['op=work', 'sub=model', 'persona=gura', 'work=' + GB['deck_works'][r['deck']], 'name=' + r['name'], 'source_work=' + t['work'],
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
