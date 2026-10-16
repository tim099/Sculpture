# 哨兵號：建子作品（沒有才建）＋把格子同步成 gen_sentinel.py 的清單＋外部模型＋組裝件的關聯（原船那一條另外設，見 notes.md）。
# 用法：python -I -X utf8 apply_sentinel.py <gen_sentinel 的輸出資料夾>
import sys, os, json, subprocess, shutil, tempfile
out = sys.argv[1]
S = shutil.which('senate'); W = 'meadow-sentinel-01m'; PER = 'meadow'
WORKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
M = json.load(open(os.path.join(out, 'sentinel_meta.json'), encoding='utf-8'))


def run(*a, ok_codes=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok_codes: print((p.stdout + p.stderr)[-1200:]); sys.exit(1)
    return p.stdout


def fwd(p): return p.replace(os.sep, '/')


FRAME = '544,131,128'
PARTS = [  # 部件 → (作品 ID, 名稱, 清單檔, 尺寸, 關聯名（None ＝ 不關聯：遮罩）, 關聯 meta)
    ('carve', W + '-carve', '哨兵號 挖格子的遮罩（原船＝莫尼特號組裝件的座標：五座速射砲的砲井）', 'part_carve.txt', '544,131,80', None, None),
    ('conning', W + '-conning', '哨兵號 司令塔（圓、加高，取代方形駕駛塔）', 'part_conning.txt', FRAME, '司令塔', {'material': 'iron'}),
    ('mounts', W + '-mounts', '哨兵號 速射砲台（五座：砲座圍欄＋三管速射砲）', 'part_mounts.txt', FRAME, '速射砲台', {'material': 'iron'}),
    ('mast', W + '-mast', '哨兵號 訊號桅', 'part_mast.txt', FRAME, '訊號桅', {'material': 'iron'}),
    ('locker', W + '-locker', '哨兵號 備便彈藥櫃（速射砲的火藥，4 桶；關聯兩次：前、後）', 'part_locker.txt', '14,14,9', None, None),
]


def exists(wid): return os.path.exists(os.path.join(WORKS, wid, 'work.json'))


def load(f):
    d = {}
    for l in open(f, encoding='utf-8'):
        l = l.strip()
        if not l or l[0] == '#': continue
        a = l.split(','); d[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return d


def sync(wid, listfile):
    tmp = tempfile.mkdtemp(prefix='ssync_'); cur = fwd(os.path.join(tmp, 'cur.txt'))
    run(('op', 'export'), ('format', 'list'), ('work', wid), ('out', cur), ('links', 'none'))
    old = load(cur) if os.path.exists(cur) else {}
    new = load(listfile)
    rm = [k for k, c in old.items() if new.get(k) != c]
    add = [k for k, c in new.items() if old.get(k) != c]
    print('%s：現在 %d、新的 %d ⇒ 刻 %d、補 %d' % (wid, len(old), len(new), len(rm), len(add)))
    for name, lst, op in (('rm', rm, 'carvevox'), ('add', add, 'stampvox')):
        if not lst: continue
        fn = fwd(os.path.join(tmp, '%s.txt' % name))
        with open(fn, 'w') as f:
            f.write('\n'.join('%d,%d,%d,%d' % (k[0], k[1], k[2], old[k] if op == 'carvevox' else new[k]) for k in lst) + '\n')
        run(('op', op), ('persona', PER), ('work', wid), ('at', '0,0,0'), ('voxels', fn), ('expect_pixels', str(len(lst))), ('share', '0'))
        print('  %s %d ✓' % (op, len(lst)))


for key, wid, title, lf, size, lname, lmeta in PARTS:
    if not exists(wid):
        run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', wid), ('title', title), ('parent_work', W), ('size', size), ('tags', 'sub'))
        print('＋ 建立', wid)
    run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', wid), ('meters_per_voxel', '0.1'), ('size', size), ('tags', 'sub'), ('title', title))
    sync(wid, os.path.join(out, lf))


def model(wid, m):
    a = [('op', 'work'), ('sub', 'model'), ('persona', PER), ('work', wid), ('name', m['name']), ('source_work', m['work']),
         ('at', ','.join(str(v) for v in m['at'])), ('scale', ','.join(str(v) for v in m['scale'])), ('meta', json.dumps(m['meta'], ensure_ascii=False))]
    if 'pivot' in m: a.append(('pivot', ','.join(str(v) for v in m['pivot'])))
    if 'rotate' in m: a.append(('rotate', ','.join(str(v) for v in m['rotate'])))
    have = os.path.exists(os.path.join(WORKS, wid, 'models.json')) and any(x['name'] == m['name'] for x in json.load(open(os.path.join(WORKS, wid, 'models.json'), encoding='utf-8'))['models'])
    if have: a.append(('overwrite', '1'))
    run(*a)
    print('  模型 %s ✓' % m['name'])


for m in M['wheel']: model(W + '-conning', m)
for m in M['guns']: model(W + '-mounts', m)
for m in M['kegs']: model(W + '-locker', m)

lf = os.path.join(WORKS, W, 'links.json')
have = [l['name'] for l in json.load(open(lf, encoding='utf-8'))['links']] if os.path.exists(lf) else []
for key, wid, title, lfile, size, lname, lmeta in PARTS:
    if not lname: continue
    a = [('op', 'work'), ('sub', 'link'), ('persona', PER), ('work', W), ('name', lname), ('source_work', wid), ('at', '0,0,0'), ('meta', json.dumps(lmeta, ensure_ascii=False))]
    if lname in have: a.append(('overwrite', '1'))
    run(*a)
    print('  關聯 %s ✓' % lname)
for L in M['lockers']:                                                  # 彈藥櫃：同一件小作品關聯兩次
    a = [('op', 'work'), ('sub', 'link'), ('persona', PER), ('work', W), ('name', L['name']), ('source_work', W + '-locker'), ('at', ','.join(str(v) for v in L['at'])), ('meta', json.dumps(L['meta'], ensure_ascii=False))]
    if L['name'] in have: a.append(('overwrite', '1'))
    run(*a)
    print('  關聯 %s ✓' % L['name'])
print('done')
