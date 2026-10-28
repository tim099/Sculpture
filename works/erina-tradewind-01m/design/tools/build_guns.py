# 出處：erina-oxford-01m/design/tools/build_guns.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 來源：calli-cosecha-01m/design/tools/build_guns.py（照抄後改：persona erina、本船的砲名）
# 步驟 9 落格（TASK-1097）：照 guns_placement.json 每門砲一個外部模型，掛在所在甲板的子作品上（藏甲板就一起藏；Ship_Guns §4.2）；
#   迴旋砲另外補一個「座」雙生（kind=gunmount、mount_of ＝ 那門砲的 id；Ship_Guns §4.2.1）
#   用法：python -I -X utf8 tools/build_guns.py <design>（重跑：overwrite=1）
#   · P 舷 mirror=y；meta ＝ 砲種的 meta（kind、gun）＋ deck、side、port
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
GB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['guns_build']
PL = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']
NAMES = {'4l': '3 磅砲 ⇒ 4 磅砲（pinnacle 的 4 磅專用元件 ×0.5）', 'pierrier': '½ 磅旋轉砲 ⇒ 迴旋砲 pierrier（皇家號共用件 ×0.5）'}


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD = {}
for w in set(GB['deck_works'].values()):
    p = os.path.join(WORKS, w, 'models.json')
    if os.path.exists(p):
        for m in json.load(open(p, encoding='utf-8'))['models']:
            OLD[(w, m['name'])] = m.get('meta') or {}
ok = bad = 0
for r in PL:
    t = GB['types'][r['type']]
    s = float(t['scale'])
    meta = dict(t['meta'])
    meta.update({'deck': r['deck'], 'side': r['side'], 'port': r['port'], 'id': r['id']})
    old = OLD.get((GB['deck_works'][r['deck']], r['name']), {})
    if 'id' in old and old['id'] != r['id']:
        print('⚠ %s 原本的 id %s ≠ 擺法表的 %s（照擺法表）' % (r['name'], old['id'], r['id']))
    note = '%s（步驟 9 TASK-1097；%s 舷、%s %s；draft_guns.py back %s、砲口伸出 %s）' % (
        NAMES[r['type']], r['side'], r['deck'], ('第 %d 個砲門' % r['port']) if isinstance(r['port'], int) else '舷頂 ' + str(r['port']), num(float(r['back'])), num(float(r['muzzle_beyond'])))
    args = ['op=work', 'sub=model', 'persona=erina', 'work=' + GB['deck_works'][r['deck']], 'name=' + r['name'], 'source_work=' + t['work'],
            'at=' + xyz(r['at']), 'pivot=' + xyz(t['pivot']), 'rotate=0,0,' + num(float(r['phi'])), 'scale=' + xyz([s, s, s]), 'overwrite=1',
            'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')), 'note=' + note]
    if r['side'] == 'P':
        args.append('mirror=y')
    todo = [args]
    if t.get('mount_work'):
        twin = ['op=work', 'sub=model', 'persona=erina', 'work=' + GB['deck_works'][r['deck']], 'name=' + r['name'] + '座', 'source_work=' + t['mount_work'],
                'at=' + xyz(r['at']), 'pivot=' + xyz(t['pivot']), 'rotate=0,0,' + num(float(r['phi'])), 'scale=' + xyz([s, s, s]), 'overwrite=1',
                'meta=' + json.dumps({'kind': 'gunmount', 'mount_of': r['id'], 'id': r['id'].replace('gun-', 'gunmount-')}, ensure_ascii=False, separators=(',', ':')),
                'note=迴旋砲的座（叉架＋插銷；Ship_Guns §4.2.1 雙生，擺法照抄 ' + r['name'] + '）']
        if r['side'] == 'P':
            twin.append('mirror=y')
        todo.append(twin)
    for a_ in todo:
        p = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in a_ for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if p.returncode:
            bad += 1
            print('✗', r['name'], (p.stdout + p.stderr)[-500:])
        else:
            ok += 1
print('模型 ok %d／bad %d（設計 %d）' % (ok, bad, len(PL)))
