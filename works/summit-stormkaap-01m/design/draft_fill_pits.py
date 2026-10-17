# 階段二十 d 填掉「掉得進去、爬不出來」的坑（TASK-0685；Tim 2026-10-17「船頭頭欄底下的坑直接填掉，外觀改一點沒關係」）
#   階段二十之後 walkback（basecamp 餘燼號 design/tools/walkback.py；框 ＝ 整艘；起點 ＝ head ≥ z 100 的四座梯子）還剩 63 格：
#     船頭 galjoen 格柵上、頭欄底下的坑 58（坑 2 格寬、頭頂的欄木壓到 7 格以內 ⇒ 從欄頂跳 7–8 格下去掉得進去、旁邊太矮、上面太高）；
#     船長室的兩個角落凹槽（船殼）、側窗廊一對凹槽（鏡像關聯）、右舷船外水線上 0.1 m 的一根海草尖（裝飾）。
#   ⇒ 一輪一輪：量出回不來的格子 ⇒ 每格填一層（顏色 ＝ 坑底那一格、歸 坑底那一格所屬的子作品；鏡像關聯換回子作品座標）⇒ 再量，直到 0。
#     例外：水線附近（z ≤ 55）、在船殼外的那一格（海草尖）⇒ 刻掉它腳下那一格（往上填會越長越高，那裡本來就是海）。
# 用法：python -I -X utf8 -B draft_fill_pits.py <design> <exports 資料夾：assembly.list.txt、各子作品 <work>.list.txt> <walkback_dump.py>
#   walkback_dump.py ＝ walkback.py 加一個參數 dump=<檔>：把回不來的站位格寫出來（sha256 記進 verify）
#   ⇒ masks/fill_pits/<work>.fill.vox.txt（stampvox）／<work>.carve.vox.txt（carvevox）、verify_fill_pits.json
import sys, os, json, glob, hashlib, subprocess, tempfile

D, EX, WB = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
WORKS = os.path.dirname(os.path.dirname(D))
NYM = 260                                                              # 鏡像 y：世界 y ＝ 260 − 子作品 y（框 261）
MIRRORED = {'summit-stormkaap-01m-quarter-gallery', 'summit-stormkaap-01m-channels'}


def read(p):
    d = {}
    for ln in open(p, encoding='utf-8'):
        if ln[0] == '#' or not ln.strip():
            continue
        x, y, z, c = map(int, ln.split(','))
        d[(x, y, z)] = c
    return d


A = read(os.path.join(EX, 'assembly.list.txt'))
own = {}                                                               # 世界格 → (子作品, 子作品座標)
for f in sorted(glob.glob(os.path.join(EX, 'summit-stormkaap-01m*.list.txt'))):
    w = os.path.basename(f)[:-len('.list.txt')]
    for (x, y, z) in read(f):
        own.setdefault((x, y, z), (w, (x, y, z)))
        if w in MIRRORED:
            own.setdefault((x, NYM - y, z), (w, (x, y, z)))
cur = dict(A)
fill, carve, rounds = {}, {}, []
tmp = tempfile.mkdtemp(prefix='fillpits_')
for rnd in range(12):
    lp, tp = os.path.join(tmp, 'cur.list.txt'), os.path.join(tmp, 'trap.txt')
    with open(lp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 量用\n' + ''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(cur.items())))
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', WB, 'summit-stormkaap-01m-assembly', lp, 'summit-stormkaap-01m-ladders',
                        'summit-stormkaap-01m-ladders,summit-stormkaap-01m-ladders-hold', 'startz=100', 'dump=' + tp], capture_output=True, text=True, encoding='utf-8', cwd=WORKS)
    assert r.returncode == 0, r.stderr[-800:]
    out = json.loads(r.stdout[r.stdout.find('{'):])
    T = [tuple(map(int, ln.split(','))) for ln in open(tp) if ln.strip()]
    rounds.append({'round': rnd, 'reachable_not_back': out['reachable_not_back'], 'reachable': out['reachable'], 'back': out['back']})
    print('第 %d 輪：回不來 %d' % (rnd, out['reachable_not_back']))
    if not T:
        break
    for (x, y, z) in T:
        below = (x, y, z - 1)
        w, sk = own[below]
        if z <= 55 and w == 'summit-stormkaap-01m-decor':           # 船外水線附近的海草尖 ⇒ 刻掉腳下那一格
            carve.setdefault(w, {})[sk] = cur[below]; del cur[below]
            continue
        c = cur[below]
        k = (sk[0], sk[1], sk[2] + 1)                                  # 子作品座標：坑底那一格往上一格（鏡像關聯的 sk 已經是子作品那一側）
        fill.setdefault(w, {})[k] = c; cur[(x, y, z)] = c; own[(x, y, z)] = (w, k)
        if w in MIRRORED:                                              # 子作品填一格 ⇒ 兩舷都有：世界那一格也補上
            cur[(x, NYM - y, z)] = c; own[(x, NYM - y, z)] = (w, k)
else:
    raise SystemExit('12 輪還沒到 0')
v = {'assembly_list_sha256': hashlib.sha256(open(os.path.join(EX, 'assembly.list.txt'), 'rb').read()).hexdigest(),
     'walkback_dump_sha256': hashlib.sha256(open(WB, 'rb').read()).hexdigest(), 'rounds': rounds,
     'fill': {w: len(c) for w, c in fill.items()}, 'carve': {w: len(c) for w, c in carve.items()},
     'expect_assembly_after': len(cur), 'files': {}}
out = os.path.join(D, 'masks', 'fill_pits'); os.makedirs(out, exist_ok=True)
NL = chr(10)
for kind, M in (('fill', fill), ('carve', carve)):
    for w, cs in sorted(M.items()):
        txt = '# 填坑（draft_fill_pits.py）—— %s %s，子作品座標 x,y,z,色（%d 格）' % (w, '加' if kind == 'fill' else '刻掉', len(cs)) + NL + ''.join('%d,%d,%d,%d' % (k + (c,)) + NL for k, c in sorted(cs.items()))
        p = os.path.join(out, '%s.%s.vox.txt' % (w, kind))
        open(p, 'w', encoding='utf-8', newline=NL).write(txt)
        v['files']['%s.%s' % (w, kind)] = {'work': w, 'op': 'stampvox' if kind == 'fill' else 'carvevox', 'path': 'masks/fill_pits/%s.%s.vox.txt' % (w, kind),
                                          'cells': len(cs), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()}
with open(os.path.join(D, 'verify_fill_pits.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(v, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
print(json.dumps({k: v[k] for k in ('fill', 'carve', 'expect_assembly_after')}, ensure_ascii=False))
