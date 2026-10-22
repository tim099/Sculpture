# 落格與組裝（TASK-0748 君士坦丁堡地標；抄大競技場 kaguya-hippodrome-1453 的（改：一份 manifest 好幾件成品、成品的 parent ＝ 委託作品、一格幾公尺照每一件的 mpv）；那支抄 kaguya-hagia-sophia-1453 的（那支抄 kaguya-galata-tower-1453）；抄 kaguya-roman-1453/design/apply.py，那支照 summit-bourg-fr-01m 的改：作者 kaguya、一格幾公尺照 manifest 的 mpv）：照 manifest.json 下 CLI。
# 用法：python -I -X utf8 -B apply.py <design 資料夾> <步驟> [作品 id 的子字串 …]（不給 ⇒ 全部）
#   create   建作品（已存在 ⇒ 只補 meters_per_voxel、tags）；parent_work ＝ 任務作品
#   stamp    匯出作品現在的格、跟清單比：多的 carvevox（帶原色守門）、少的或色不同的 stampvox overwrite ⇒ 第一次 ＝ 整份貼上，重跑只補差
#   anchors  登記固定點（同名同位置就跳過）
#   links    加關聯（同名同設定就跳過；位置、轉向、翻面不同 ⇒ overwrite=1；替換色、meta 直接改）
#   models   加外部模型（同上）
#   check    只讀：每件作品匯出跟清單逐格比（缺／多／色差）＋ stats structure；組裝件匯出跟 build.py 的組好清單比
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
filt = sys.argv[3:]
man = json.load(open(os.path.join(D, 'manifest.json'), encoding='utf-8'))
ROOT = man['root']
WORKS = os.path.dirname(os.path.dirname(D))          # …/Sculpture/works
TMP = os.path.join(os.path.dirname(D), 'exports', 'apply')
os.makedirs(TMP, exist_ok=True)
ok = bad = 0
P = 'kaguya'
MPV = man.get('mpv', 0.1)


def cli(args, quiet_fail=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        if not quiet_fail:
            bad += 1
            print('✗ rc=%d' % r.returncode, ' '.join(args[:6]))
            print((r.stdout + r.stderr)[-1200:])
    else:
        ok += 1
    return r.returncode, r.stdout


def rd(p):
    out = {}
    for l in open(p, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            a = l.split(',')
            out[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return out


def dump(path, cells, color=True):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for k, c in sorted(cells.items()):
            f.write(('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c)) if color else ('%d,%d,%d\n' % k))


def export(w):
    p = os.path.join(TMP, w + '.list.txt').replace('\\', '/')
    rc, _ = cli(['op=export', 'format=list', 'work=' + w, 'out=' + p])
    return rd(p) if rc == 0 else None


def jload(w, f):
    p = os.path.join(WORKS, w, f)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def fmt(v):
    return ','.join(('%g' % x) for x in v)


order = sorted(man['works'].items(), key=lambda kv: (kv[1]['order'], kv[0]))
sel = [(w, W) for w, W in order if not filt or any(f in w for f in filt)]

for w, W in sel:
    if step == 'create':
        rc, _ = cli(['op=work', 'sub=show', 'work=' + w], quiet_fail=True)
        if rc:
            cli(['op=work', 'sub=create', 'persona=' + P, 'id=' + w, 'title=' + W['title'], 'size=' + fmt(W['size']), 'parent_work=' + W.get('parent', ROOT)])
        else:
            card = jload(w, 'work.json')
            if card and [card.get('size_x'), card.get('size_y'), card.get('size_z')] != W['size']:
                cli(['op=work', 'sub=update', 'persona=' + P, 'work=' + w, 'size=' + fmt(W['size'])])
        cli(['op=work', 'sub=update', 'persona=' + P, 'work=' + w, 'meters_per_voxel=%g' % W.get('mpv', MPV), 'tags=' + W['tags'], 'title=' + W['title']])
        print('create', w)
    elif step == 'stamp':
        if not W['mask']:
            continue
        cur, want = export(w), rd(os.path.join(D, 'masks', W['mask']))
        carve = {k: c for k, c in cur.items() if k not in want}
        add = {k: c for k, c in want.items() if cur.get(k) != c}
        for nm, cells, args in (('carve', carve, ['op=carvevox']), ('stamp', add, ['op=stampvox', 'overwrite=1'])):
            if not cells:
                continue
            p = os.path.join(TMP, '%s.%s.vox.txt' % (w, nm))
            dump(p, cells)
            rc, out = cli(args + ['persona=' + P, 'work=' + w, 'voxels=' + p.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(cells), 'draft=0', 'share=0'])
            m = re.search(r'placed\s*=\s*(\d+)', out)
            print(w, nm, len(cells), 'rc', rc, 'placed', m.group(1) if m else '?')
        print(w, '現況 %d → 清單 %d｜刻 %d、補／換色 %d' % (len(cur), len(want), len(carve), len(add)))
    elif step == 'anchors':
        have = {}
        rc, out = cli(['op=work', 'sub=anchors', 'work=' + w])
        for m in re.finditer(r'`([^`]+)` ← \S+ @(-?\d+),(-?\d+),(-?\d+)', out):
            have[m.group(1)] = [int(m.group(2)), int(m.group(3)), int(m.group(4))]
        for nm, at in W['anchors'].items():
            if have.get(nm) == list(at):
                continue
            note = {'door': '前門外第一格（門檻那一層、門洞正前方：遊戲從路上走到這裡）', 'lot-0': '地塊原點：臨路左前角、整平面（格 0,0,0 的角）',
                    'smoke': '煙囪口（遊戲從這裡冒煙）'}.get(nm, '')
            args = ['op=work', 'sub=anchor', 'persona=' + P, 'work=' + w, 'name=' + nm, 'at=' + fmt(at)]
            if note:
                args.append('note=' + note)
            if nm in have:
                cli(['op=work', 'sub=unanchor', 'persona=' + P, 'work=' + w, 'name=' + nm])
            cli(args)
            print(w, 'anchor', nm, at)
    elif step == 'links':
        cur = {l['name']: l for l in (jload(w, 'links.json') or {}).get('links', [])}
        for L in W['links']:
            rc_s = ','.join('%s:%s' % (a, b) for a, b in sorted(L['recolor'].items()))
            c = cur.get(L['name'])
            same_geo = c and c.get('source_work', c.get('work')) == L['source'] and list(c.get('at', [])) == L['at'] and int(c.get('turn', 0)) == L['turn'] and (c.get('mirror') or '') == L['mirror']
            same_rest = c and (c.get('recolor') or '') == rc_s and (c.get('meta') or {}) == L['meta']
            if same_geo and same_rest:
                continue
            args = ['op=work', 'sub=link', 'persona=' + P, 'work=' + w, 'name=' + L['name'], 'source_work=' + L['source'], 'at=' + fmt(L['at']), 'turn=%d' % L['turn']]
            if L['mirror']:
                args.append('mirror=' + L['mirror'])
            if rc_s:
                args.append('recolor=' + rc_s)
            if L['meta']:
                args.append('meta=' + json.dumps(L['meta'], ensure_ascii=False, sort_keys=True))
            if c and not same_geo:
                args.append('overwrite=1')
            cli(args)
        print(w, 'links', len(W['links']))
    elif step == 'models':
        cur = {m['name']: m for m in (jload(w, 'models.json') or {}).get('models', [])}
        for m in W.get('models', []):
            c = cur.get(m['name'])
            rot = m.get('rotate', [0, 0, 0])
            if c and c.get('work') == m['source'] and list(c['at']) == list(m['at']) and list(c['pivot']) == list(m['pivot']) and list(c['rotate']) == list(rot) and (c.get('meta') or {}) == m['meta']:
                continue
            args = ['op=work', 'sub=model', 'persona=' + P, 'work=' + w, 'name=' + m['name'], 'source_work=' + m['source'],
                    'at=' + fmt(m['at']), 'pivot=' + fmt(m['pivot']), 'rotate=' + fmt(rot)]
            if m['meta']:
                args.append('meta=' + json.dumps(m['meta'], ensure_ascii=False, sort_keys=True))
            if c and c.get('work') != m['source']:
                args.append('overwrite=1')
            cli(args)
        print(w, 'models', len(W.get('models', [])))
    elif step == 'check':
        want = rd(os.path.join(D, 'masks', W['mask'])) if W['mask'] else (rd(os.path.join(D, 'masks', W['expect'])) if W.get('expect') else None)
        if want is None:
            continue
        cur = export(w)
        miss = sum(1 for k in want if k not in cur)
        extra = sum(1 for k in cur if k not in want)
        diff = sum(1 for k, c in want.items() if k in cur and cur[k] != c)
        rc, out = cli(['op=stats', 'work=' + w, 'structure=1'])
        nums = dict(re.findall(r'🔢 (\w+) = (\S+)', out))
        keys = [k for k in nums if re.search(r'compon|cavit|overlap|clip', k)]
        print(w, '作品 %d 格｜缺 %d 多 %d 色差 %d｜' % (len(cur), miss, extra, diff) + '  '.join('%s=%s' % (k, nums[k]) for k in keys))
    else:
        raise SystemExit('步驟？ create|stamp|anchors|links|models|check')
print(step, 'ok', ok, 'bad', bad)
