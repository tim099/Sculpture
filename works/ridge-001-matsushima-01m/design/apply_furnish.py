# 松島號 裝飾落格 —— 照 draft_furnish.py 的 furnish_placement.json 下 CLI（寫法照拿破崙號 tools/apply_furnish.py，kotoko）
#   新做的件：子作品（0.05 m、parent 船殼、tags sub；已在且格數對 ⇒ 不重落）；引用的件（拿破崙號的繫纜柱）不建。
#   每一列掛一個外部模型（meta deco=1，造船規格 §9.9；overwrite=1 ⇒ 重跑結果一樣）。
#   用法：python -I -X utf8 -B apply_furnish.py <draft_furnish 輸出>
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL = 'ridge-001-matsushima-01m'; PER = 'ridge-001'
WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # Sculpture/works
TITLE = {'crest': '松島號 菊花紋章（艏柱頂、十六八重表菊、直徑 1.2 m；0.05 m，外部模型的來源，裝飾 deco）',
         'bollard': '雙柱繫纜樁（鋼船時代的 double bollard，柱徑 0.36 m；通用部件，0.05 m，裝飾 deco）',
         'rack': '12 cm 速射砲備便彈架（定裝彈八發直立；通用部件，0.05 m，裝飾 deco）'}
ok = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, retried
    for k in range(5):
        r = run(args)
        out = r.stdout + r.stderr
        if r.returncode and any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 4:
            retried += 1; time.sleep(0.5); continue
        break
    if r.returncode:
        print('✗ rc=%d' % r.returncode, ' '.join(args[:6])); print(out[-1200:]); raise SystemExit(1)
    ok += 1
    return r.stdout


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


PL = json.load(open(os.path.join(D, 'furnish_placement.json'), encoding='utf-8'))
for k, P in sorted(PL['pieces'].items()):
    if k not in TITLE: continue                                           # 引用別艘的元件
    W = HULL + '-' + k
    vox = os.path.join(D, 'furnish', k + '.vox.txt').replace('\\', '/')
    if run(['op=work', 'sub=show', 'work=' + W]).returncode != 0:
        cli(['op=work', 'sub=create', 'persona=' + PER, 'id=' + W, 'title=' + TITLE[k], 'size=' + xyz(P['size']), 'parent_work=' + HULL, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=' + PER, 'work=' + W, 'meters_per_voxel=0.05'])
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
    if have == 0:
        out = cli(['op=stampvox', 'persona=' + PER, 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % P['cells'], 'share=0'])
        n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
        if n != P['cells']: raise SystemExit('✗ %s placed %d ≠ %d' % (W, n, P['cells']))
    elif have != P['cells']:
        raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (W, have, P['cells']))
    print('✓ 子作品', W, P['cells'], '格', P['size'])
def old_id(work, name):
    """那件作品裡同名模型已經發過的物件 id（admin.py ids；§12.2 改名挪位置都不變）⇒ 重落時帶上，⛔ meta= 是整份覆寫，不帶下一次 ids 就重發、換號。"""
    try:
        M = json.load(open(os.path.join(WORKS, work, 'models.json'), encoding='utf-8'))['models']
    except FileNotFoundError:
        return None
    return next(((m.get('meta') or {}).get('id') for m in M if m['name'] == name), None)


for r in PL['rows']:
    meta = dict(r['meta'])
    oid = old_id(r['work'], r['model'])
    if oid is not None:
        meta['id'] = oid
    a = ['op=work', 'sub=model', 'persona=' + PER, 'work=' + r['work'], 'name=' + r['model'], 'source_work=' + r['source_work'],
         'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=0,0,0', 'scale=%g' % r['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
         'meta=' + json.dumps(meta, sort_keys=True), 'note=松島號 裝飾 %s（draft_furnish.py；deco=1：遊戲畫質「裝飾」關著就不載入、不算重量）' % r['piece']]
    if r.get('recolor'): a.append('recolor=' + r['recolor'])
    cli(a)
    print('✓ 模型', r['path'], r['at'], r['mirror'])
print('furnish ok', ok, 'IOException 重試', retried)
