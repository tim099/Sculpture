# 光榮號 機艙讀數：① 每件子作品結果帳（匯出 vs 清單）② 組裝件結果帳：現在 vs 藏機艙關聯 ＋ 三份清單搬到 at
#   ③ 遊戲讀的那一份（export format=parts）：關聯／模型的 meta、固定點（世界、格心）vs draft ④ 引擎 stats（元件、空腔、link_overlap、鏡像差）
#   ⑤ 反向對照：真的拿掉 機艙-主機 的 kind ⇒ 讀數要報那一件；再加回
#   抄自拿破崙號 kotoko-napoleon-01m/design/tools/check_engine.py（kotoko）；光榮號改：曲柄是模型（不進組裝件的格子）、persona。
#   用法：python -I -X utf8 tools/check_engine.py <design>
import json, os, re, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
sys.path.insert(0, design)
import mio  # noqa: E402

PL = json.load(open(os.path.join(design, 'engine_placement.json'), encoding='utf-8'))


def key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


def ledger(now, want):
    dn = dict(zip(key(now).tolist(), now[:, 3].tolist()))
    dw = dict(zip(key(want).tolist(), want[:, 3].tolist()))
    return len(set(dw) - set(dn)), len(set(dn) - set(dw)), sum(1 for k in set(dn) & set(dw) if dn[k] != dw[k])


def cli(*a):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace(os.sep, '/')
        r = cli('op=export', 'format=parts', 'work=' + mio.ASM, 'out=' + out)
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))


moved = []
for k, P in sorted(PL.items()):
    L = np.loadtxt(os.path.join(design, 'masks', 'engine', k + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    N = mio.export_list(P['work'], None)
    print('① %s 結果帳：清單 %d ↔ 子作品 %d，缺 %d、多 %d、色差 %d' % ((P['work'], len(L), len(N)) + ledger(N, L)))
    if not P.get('model'):
        W = L.copy()
        W[:, :3] += np.array(P['at'], np.int32)
        moved.append(W)
links = ','.join(P['link'] for P in PL.values() if not P.get('model'))
B = mio.export_list(mio.ASM, 'all', ('hide_links=' + links,))
NOW = mio.export_list(mio.ASM, 'all')
E = np.concatenate([B] + moved)
print('② 組裝件結果帳：藏機艙 %d ＋ 三件 %s ↔ 現在 %d，缺 %d、多 %d、色差 %d；設計那一份自己重疊 %d' % (
    (len(B), [len(m) for m in moved], len(NOW)) + ledger(NOW, E) + (len(E) - len(np.unique(key(E))),)))

PJ = parts()
lk = {l['path']: l for l in PJ['links']}
mk = {m['path']: m for m in PJ['models']}
for k, P in sorted(PL.items()):
    l = (mk if P.get('model') else lk).get(P['link'])
    if l is None:
        print('③ %s：parts 裡找不到' % P['link'])
        continue
    md = l.get('meta') != P['meta']
    worst = max(abs(l['points'][nm][i] - (v[i] + 0.5)) for nm, v in P['anchors_world'].items() for i in range(3))
    print('③ %s：meta 相同 %s（%s）、固定點 %d 個、跟 draft 最大差 %.4f%s' % (P['link'], not md, l.get('meta'), len(l['points']), worst,
                                                               '、state %s' % l.get('state') if P.get('model') else ''))

st = {k: v for k, v in re.findall(r'🔢 (\w+) = (\S+)', cli('op=stats', 'work=' + mio.ASM, 'structure=1', 'mirror=y:200', 'hide_links=船名板,機艙-主機').stdout)}
print('④ 引擎（hide 船名板、機艙-主機 —— 主機本來就不對稱）：格 %s、元件 %s、空腔 %s、link_overlap %s、鏡像差 %s／%s' % (
    st.get('total_voxels'), st.get('components'), st.get('cavities'), st.get('link_overlap'), st.get('mirror_diff_a'), st.get('mirror_diff_b')))
st2 = {k: v for k, v in re.findall(r'🔢 (\w+) = (\S+)', cli('op=stats', 'work=' + mio.ASM, 'structure=1').stdout)}
print('④ 引擎（全部）：格 %s、元件 %s、空腔 %s、link_overlap %s' % (st2.get('total_voxels'), st2.get('components'), st2.get('cavities'), st2.get('link_overlap')))

# ⑤ 反向對照（真的改，再改回）
P = PL['engine']
cli('op=work', 'sub=meta', 'persona=kaguya', 'work=' + mio.ASM, 'part=link', 'name=' + P['link'], 'meta={"kind":null}')
m1 = {l['path']: l for l in parts()['links']}[P['link']].get('meta')
cli('op=work', 'sub=meta', 'persona=kaguya', 'work=' + mio.ASM, 'part=link', 'name=' + P['link'], 'meta=' + json.dumps({'kind': P['meta']['kind']}))
m2 = {l['path']: l for l in parts()['links']}[P['link']].get('meta')
eng = [l['path'] for l in parts()['links'] if (l.get('meta') or {}).get('kind') == 'engine']
print('⑤ 反向對照：拿掉 %s 的 kind ⇒ meta 不同 %s（kind=%s）；加回 ⇒ 相同 %s；kind=engine 的關聯 %s' % (P['link'], m1 != P['meta'], (m1 or {}).get('kind'), m2 == P['meta'], eng))
