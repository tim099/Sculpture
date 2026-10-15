# 抄自三叉戟號 gura-tridente-01m/design/tools/check_stage7.py（gura）；改：作品、「階段七之前」＝ 組裝件全部關聯藏掉 channels 兩條。
# 階段七讀數（TASK-0612）：① channels 子作品結果帳（匯出 vs 清單）② 組裝件結果帳：現在（全部關聯）vs 階段七之前 ＋ channels 兩條關聯（右舷＋鏡像，照清單自己算）
#   ③ 固定點：各作品 anchors.json vs plan ④ 繩、帆：組裝件 ropes.json／sails.json 逐條逐欄 vs plan ⑤ 帆自己的繩（端點 sail:）的 meta：沒有、kind 不是 sheet／tack、sail 跟端點那面帆不同
#   ⑥ 引擎讀數（sub=ropes／sails 的 broken）⑦ 反向對照：同一套比對拿動過手腳的副本跑，每一種都要報 1（鏡像錯 1 格 ⇒ 缺、多都不是 0）
#   用法：python -I -X utf8 tools/check_stage7.py <design>
import copy, json, os, re, subprocess, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, design)
import tempfile  # noqa: E402


class DB:
    ASM = 'kotoko-napoleon-01m-assembly'

    @staticmethod
    def export_list(work, links, extra=()):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, 'a.txt').replace(os.sep, '/')
            r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out]
                               + (['--arg', 'links=' + links] if links else []) + [a for kv in extra for a in ('--arg', kv)],
                               capture_output=True, text=True, encoding='utf-8', errors='replace')
            if r.returncode != 0 or not os.path.exists(out):
                raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-800:])
            return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')

WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
P = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
C = P['channels']


def jl(work, f):
    return json.load(open(os.path.join(WORKS, work, f), encoding='utf-8'))


def read(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


def ledger(now, want):
    """回 (缺, 多, 色差)：want 有 now 沒有 ／ now 有 want 沒有 ／ 兩邊都有但色不同。"""
    dn = dict(zip(key(now).tolist(), now[:, 3].tolist()))
    dw = dict(zip(key(want).tolist(), want[:, 3].tolist()))
    return len(set(dw) - set(dn)), len(set(dn) - set(dw)), sum(1 for k in set(dn) & set(dw) if dn[k] != dw[k])


def place(local, at, mirror):
    """子作品清單 ⇒ 組裝件座標；mirror=y 在自己的框裡翻（框高 C['size'][1]，⛔ 不是格子的 max ＋ 1）。"""
    w = local.copy()
    if mirror:
        w[:, 1] = C['size'][1] - 1 - w[:, 1]
    w[:, :3] += np.array(at, np.int32)
    return w


# ---- 比對函式（反向對照拿同一支跑）----
def diff_anchors(plan, have):
    """plan：{part: {名: xyz}}；have：{part: {名: xyz}} ⇒ (缺, 多, 位置不同)。"""
    m = e = d = 0
    for part, items in plan.items():
        h = have.get(part, {})
        m += len(set(items) - set(h))
        d += sum(1 for k in set(items) & set(h) if list(items[k]) != list(h[k]))
    for part, h in have.items():
        e += len(set(h) - set(plan.get(part, {})))
    return m, e, d


ROPE_F = ('from', 'to', 'group', 'thickness', 'slack', 'color')


def diff_ropes(plan, have):
    """⇒ (缺, 多, 欄位不同的條數, meta 不同的條數)；欄位照 rigging_apply.py 寫進去的那幾格。"""
    pw = {r['name']: r for r in plan}
    hv = {r['name']: r for r in have}
    fd = sum(1 for n in set(pw) & set(hv) if any(pw[n][f] != hv[n][f] for f in ROPE_F) or not hv[n].get('enabled', True))
    md = sum(1 for n in set(pw) & set(hv) if (pw[n].get('meta') or None) != (hv[n].get('meta') or None))
    return len(set(pw) - set(hv)), len(set(hv) - set(pw)), fd, md


def sail_fields(s, plan_side):
    if plan_side:
        free = {str(f) for f in (s['free'] or [])}                    # 旗寫序號（int）、方帆寫角名 ⇒ 一律當字串比
        names = s['corner_names'] or [str(i) for i in range(len(s['corners']))]
        corners = [(n, a, n not in free and str(i) not in free) for i, (n, a) in enumerate(zip(names, s['corners']))]
        return corners, list(s['bind']), s['color'], s['fullness'], bool(s.get('texture'))
    corners = [(c.get('name') or str(i), c['at'], c['pin']) for i, c in enumerate(s['corners'])]
    return corners, list(s.get('bind') or []), s['color'], s['fullness'], bool(s.get('texture'))


def diff_sails(plan, have):
    pw = {s['name']: s for s in plan}
    hv = {s['name']: s for s in have}
    fd = sum(1 for n in set(pw) & set(hv) if sail_fields(pw[n], True) != sail_fields(hv[n], False) or not hv[n].get('enabled', True))
    md = sum(1 for n in set(pw) & set(hv) if (pw[n].get('meta') or None) != (hv[n].get('meta') or None))
    return len(set(pw) - set(hv)), len(set(hv) - set(pw)), fd, md


def sail_rope_meta(ropes, sail_names):
    """帆自己的繩（任一端 sail:帆名/角）⇒ (條數, 沒有 meta, kind 不是 sheet／tack, meta 的 sail ≠ 端點的帆, 端點的帆不存在)。"""
    n = no = badk = bads = ghost = 0
    for r in ropes:
        ends = [x for x in (r['from'], r['to']) if x.startswith('sail:')]
        if not ends:
            continue
        n += 1
        sail = ends[0][5:].split('/')[0]
        ghost += sail not in sail_names
        m = r.get('meta')
        if not m:
            no += 1
            continue
        badk += m.get('kind') not in ('sheet', 'tack')
        bads += m.get('sail') != sail
    return n, no, badk, bads, ghost


def engine(sub):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=' + sub, '--arg', 'work=' + DB.ASM],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {k: v for k, v in re.findall(r'🔢 (\w+) = (\S+)', r.stdout)}


# ① channels 子作品
CL = read(os.path.join(design, 'masks', 'rigging', 'channels.vox.txt'))
CH = DB.export_list(C['work'], None)
print('① channels 結果帳：清單 %d ↔ 子作品 %d，缺 %d、多 %d、色差 %d' % ((len(CL), len(CH)) + ledger(CH, CL)))

# ② 組裝件
BEFORE = DB.export_list(DB.ASM, 'all', ('hide_links=channels,channels-鏡像',))
S_ = place(CL, C['at'], False)
P_ = place(CL, C['at_mirror'], True)
E = np.concatenate([BEFORE, S_, P_])
dup = len(E) - len(np.unique(key(E)))
NOW = DB.export_list(DB.ASM, 'all')
links = {l['name']: l for l in jl(DB.ASM, 'links.json')['links']}
lk = [(n, links.get(n, {}).get('at'), links.get(n, {}).get('mirror')) for n in C['links']]
print('② 組裝件結果帳：設計 %d（階段七之前 %d ＋ channels 右 %d ＋ 左 %d）↔ 組裝件 %d，缺 %d、多 %d、色差 %d；設計那一份自己重疊 %d' % (
    (len(E), len(BEFORE), len(S_), len(P_), len(NOW)) + ledger(NOW, E) + (dup,)))
print('   關聯：%s；鏡像 y：右 %d..%d、左 %d..%d（中線 y 200 對稱 ⇒ 兩邊加起來 %d、%d 要都是 400）' % (
    lk, S_[:, 1].min(), S_[:, 1].max(), P_[:, 1].min(), P_[:, 1].max(), S_[:, 1].min() + P_[:, 1].max(), S_[:, 1].max() + P_[:, 1].min()))

# ③ 固定點
have_a = {part: {a['name']: a['at'] for a in jl(w, 'anchors.json')['anchors'] if a['name'] in P['anchors'][part] or '階段七' in (a.get('note') or '')}
          for part, w in P['anchor_works'].items()}
print('③ 固定點：plan %d（%s），缺 %d、多（階段七寫的、plan 沒有）%d、位置不同 %d' % (
    (sum(len(v) for v in P['anchors'].values()), '、'.join('%s %d' % (k, len(v)) for k, v in P['anchors'].items())) + diff_anchors(P['anchors'], have_a)))

# ④ 繩、帆
R = jl(DB.ASM, 'ropes.json')['ropes']
SA = jl(DB.ASM, 'sails.json')
print('④ 繩：plan %d ↔ 組裝件 %d，缺 %d、多 %d、欄位不同 %d、meta 不同 %d' % ((len(P['ropes']), len(R)) + diff_ropes(P['ropes'], R)))
print('   帆：plan %d ↔ 組裝件 %d，缺 %d、多 %d、欄位不同 %d、meta 不同 %d；預設風 %s／%s 秒（plan %s／%s）' % (
    (len(P['sails']), len(SA['sails'])) + diff_sails(P['sails'], SA['sails']) + (SA.get('wind'), SA.get('seconds'), P['wind'], P['sail_seconds'])))

# ⑤ 帆自己的繩
names = {s['name'] for s in SA['sails']}
print('⑤ 帆自己的繩：%d 條，沒有 meta %d、kind 不是 sheet／tack %d、meta 的 sail ≠ 端點的帆 %d、端點的帆不存在 %d' % sail_rope_meta(R, names))
flags = [s['name'] for s in SA['sails'] if (s.get('meta') or {}).get('kind') == 'flag']
print('   旗：%s；帆沒有 meta %d' % (flags, sum(1 for s in SA['sails'] if not s.get('meta'))))

# ⑥ 引擎讀數
er, es = engine('ropes'), engine('sails')
print('⑥ 引擎：ropes %s 條（子繩 %s）broken %s、ungrouped %s；sails %s 面 broken %s、帆自己的繩 broken %s、最鼓 %s' % (
    er.get('rope_count'), er.get('ropes_child'), er.get('ropes_broken'), er.get('ropes_ungrouped'),
    es.get('sail_count'), es.get('sails_broken'), es.get('ropes_broken'), es.get('sail_max_billow')))

# ⑦ 反向對照（同一支比對、拿副本動手腳）
r1 = copy.deepcopy(R)
sheet = next(r for r in r1 if (r.get('meta') or {}).get('kind') == 'sheet')
sheet['meta'] = None
r2 = copy.deepcopy(R)
next(r for r in r2 if (r.get('meta') or {}).get('kind') == 'tack')['meta']['sail'] = 'nope'
r3 = copy.deepcopy(R)
r3[7]['slack'] = r3[7]['slack'] + 0.01
s1 = copy.deepcopy(SA['sails'])
s1[0]['corners'][2]['pin'] = not s1[0]['corners'][2]['pin']
s2 = copy.deepcopy(SA['sails'])
fl = next(s for s in s2 if s['name'] == 'ensign')                     # free 寫序號的那一種也要抓得到
fl['corners'][1]['pin'] = not fl['corners'][1]['pin']
a1 = copy.deepcopy(have_a)
k0 = sorted(a1['channels'])[0]
a1['channels'][k0] = [a1['channels'][k0][0], a1['channels'][k0][1] + 1, a1['channels'][k0][2]]
NOW1 = NOW.copy()
NOW1[0, 3] = (NOW1[0, 3] % 255) + 1
P1 = place(CL, [C['at_mirror'][0], C['at_mirror'][1] + 1, C['at_mirror'][2]], True)
m1 = ledger(NOW, np.concatenate([BEFORE, S_, P1]))
print('⑦ 反向對照：拿掉 sheet %s 的 meta ⇒ 沒有 meta %d；tack 的 sail 改錯 ⇒ %d；繩 %s 鬆緊 +0.01 ⇒ 欄位不同 %d；帆 %s 一角釘／不釘對調 ⇒ %d、ensign ⇒ %d；'
      'channels 固定點 %s 偏 1 ⇒ %d；組裝件一格改色 ⇒ 色差 %d；鏡像那件 y 錯 1 ⇒ 缺 %d、多 %d' % (
          sheet['name'], sail_rope_meta(r1, names)[1], sail_rope_meta(r2, names)[3], r3[7]['name'], diff_ropes(P['ropes'], r3)[2],
          s1[0]['name'], diff_sails(P['sails'], s1)[2], diff_sails(P['sails'], s2)[2], k0, diff_anchors(P['anchors'], a1)[2], ledger(NOW1, E)[2], m1[0], m1[1]))
