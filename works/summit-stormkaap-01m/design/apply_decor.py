# 階段十六：照 verify_decor.json 下 CLI —— 子作品 -decor（浮雕：牙、眉、海草、藤壺）＋組裝件關聯 `裝飾` ＋ 船殼換色（眼窩）
# 用法：python -I -X utf8 -B apply_decor.py <design 資料夾> <步驟>
#   步驟：create（已存在 ⇒ 略過）｜link｜relief｜eyes（先匯出船殼、眼窩每一格的現色要等於 verify 記的原色，對不上一格都不換）
#   · ⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_decor.json'), encoding='utf-8'))
PRE = 'summit-stormkaap-01m'
ASM = PRE + '-assembly'
ok = bad = 0


def cli(args, quiet_fail=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        if not quiet_fail:
            bad += 1; print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


def placed(out):
    m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', out)
    return m.group(1) if m else '?'


if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + V['work']], quiet_fail=True)
    if rc == 0:
        print('已有', V['work'])
    else:
        cli(['op=work', 'sub=create', 'persona=summit', 'id=' + V['work'], 'title=' + V['title'], 'size=736,261,576', 'parent_work=' + PRE, 'tags=sub'])
        print('建立', V['work'])
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + V['work'], 'meters_per_voxel=0.1'])
elif step == 'link':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=' + V['link'], 'source_work=' + V['work'], 'at=0,0,0', 'overwrite=1', 'note=階段十六 裝飾'])
elif step == 'relief':
    path = os.path.join(D, V['relief']['file']).replace('\\', '/')
    rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + V['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % V['relief']['cells'], 'draft=0'])
    print('relief', V['relief']['cells'], 'placed', placed(out))
elif step == 'eyes':
    tmp = os.path.join(os.path.dirname(D), 'exports', 'stage16_pre'); os.makedirs(tmp, exist_ok=True)
    hp = os.path.join(tmp, 'hull.list.txt').replace('\\', '/')
    cli(['op=export', 'format=list', 'work=' + PRE, 'out=' + hp])
    cur = {}
    for l in open(hp, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            cur[(x, y, z)] = c
    # 守門：每一格的現色要是原色（verify 記的）或本階段自己漆過的色（重跑時）—— 其餘一格對不上就整刀不換
    want = {}
    for l in open(os.path.join(D, V['eyes']['file']), encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            want[(x, y, z)] = c
    mine = set(V['eyes']['palette'])
    diff = [w for w in V['eyes']['was'] if cur.get(tuple(w[:3])) != w[3] and cur.get(tuple(w[:3])) not in mine]
    if diff:
        raise SystemExit('✗ 眼窩有 %d 格的現色既不是原色、也不是本階段的色（例 %s）⇒ 一格都不換' % (len(diff), diff[:3]))
    first = all(cur.get(tuple(w[:3])) == w[3] for w in V['eyes']['was'])
    todo = {k: c for k, c in want.items() if cur.get(k) != c}
    print('眼窩 %d 格：已經是目標色 %d、要換 %d（%s）' % (len(want), len(want) - len(todo), len(todo), '第一次' if first else '重跑：stage16 begin 不動'))
    if not todo:
        raise SystemExit('沒有要換的')
    tp = os.path.join(tmp, 'eyes_todo.vox.txt')
    with open(tp, 'w', encoding='utf-8', newline='\n') as f:
        for k, c in sorted(todo.items()):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c))
    if first:
        cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + PRE, 'name=stage16', 'phase=begin', 'overwrite=1', 'note=階段十六 眼窩換色之前'])
    rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + PRE, 'voxels=' + tp.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(todo), 'overwrite=1', 'draft=0'])
    print('eyes 換 %d 格 placed %s（換色前逐格對過：原色或本階段色）' % (len(todo), placed(out)))
    cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + PRE, 'name=stage16', 'phase=end', 'overwrite=1', 'note=階段十六 眼窩換色之後'])
else:
    raise SystemExit('步驟？ create|link|relief|eyes')
print(step, 'ok', ok, 'bad', bad)
