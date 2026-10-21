# 艙房落到作品（造船規格 §9.2）：gen_rooms.py 的 rooms.json ⇒ 每間的固定點 <房名>.min／.max／.door（艙房子作品裡）、
#   甲板子作品裡兩條關聯 艙房（右舷）／艙房-鏡像（mirror=y）meta kind=rooms（照憲法號：遊戲照關聯路徑把艙房歸到那一層甲板）。
# 用法：python -I -X utf8 -B apply_rooms.py <gen 輸出>   （先跑 gen_rooms.py、apply_build.py rooms-lower rooms-middle rooms-upper）
import sys, os, json, subprocess
out = sys.argv[1]
W = 'ridge-001-matsushima-01m'; PER = 'ridge-001'
HERE = os.path.dirname(os.path.abspath(__file__)); WORKS = os.path.join(HERE, '..', '..')
R = json.load(open(os.path.join(out, 'rooms.json'), encoding='utf-8'))['rooms']
DECK = {'rooms-lower': W + '-deck-lower', 'rooms-middle': W + '-deck-middle', 'rooms-upper': W + '-deck-upper'}


def run(*a):
    p = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for k, v in a for x in ('--arg', '%s=%s' % (k, v))], capture_output=True, text=True, encoding='utf-8')
    if p.returncode != 0:
        print('✗', a, (p.stdout + p.stderr)[-600:]); sys.exit(1)


def listed(wid, fn, key):
    f = os.path.join(WORKS, wid, fn)
    return [x['name'] for x in json.load(open(f, encoding='utf-8')).get(key, [])] if os.path.exists(f) else []


for key, rooms in R.items():
    wid = W + '-' + key
    have = set(listed(wid, 'anchors.json', 'anchors'))
    for r in rooms:
        for k in ('min', 'max', 'door'):
            nm = '%s.%s' % (r['name'], k)
            if nm in have: run(('op', 'work'), ('sub', 'unanchor'), ('work', wid), ('persona', PER), ('name', nm))
            run(('op', 'work'), ('sub', 'anchor'), ('work', wid), ('persona', PER), ('name', nm), ('at', '%d,%d,%d' % tuple(r[k])))
    deck = DECK[key]; links = listed(deck, 'links.json', 'links')
    for nm, mir in (('艙房', ''), ('艙房-鏡像', 'y')):
        a = [('op', 'work'), ('sub', 'link'), ('work', deck), ('persona', PER), ('name', nm), ('source_work', wid), ('at', '0,0,0'), ('meta', json.dumps({'kind': 'rooms'}))]
        if mir: a.append(('mirror', mir))
        if nm in links: a.append(('overwrite', '1'))
        run(*a)
    print('✓ %s：%d 間（固定點 %d）、%s/艙房＋艙房-鏡像' % (key, len(rooms), 3 * len(rooms), deck), flush=True)
