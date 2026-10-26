# 直接出處：gura-pinas-01m/design/tools/check_stage6.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成康塞普西翁號（TASK-0969）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/tools/check_stage6.py（收穫號，照抄後改成康塞普西翁號 —— TASK-0969）
# 階段六（TASK-0595）讀數：桅／艏斜桅／lateen 帆桁子作品匯出 vs 清單（結果帳）、船殼 ＝ 砲門:end − 艏斜桅孔、帆桁模型的 meta 與固定點
#   用法：python -I -X utf8 tools/check_stage6.py <design>
import json, os, sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key
HULL = 'apex-two-galeon-01m'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))


def ledger(work, path, label):
    W = export_list(work, None)
    D = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
    print('%-22s 作品 %6d、設計 %6d、缺 %d、多 %d、色差 %d' % (label, len(cw), len(cd), len(set(cd) - set(cw)), len(set(cw) - set(cd)), sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])))


for nm in ('mast-fore', 'mast-main', 'mast-mizzen', 'bowsprit'):
    ledger('%s-%s' % (HULL, nm), os.path.join(design, 'masks', 'masts', nm + '.vox.txt'), nm)
for k in ('mizzen',):
    ledger('%s-yard-%s-lateen' % (HULL, k), os.path.join(design, 'masks', 'yards', 'lateen-%s.vox.txt' % k), 'yard-%s-lateen' % k)
# 船殼 ＝ 窗玻璃:end − 艏斜桅孔（康塞普西翁號的艏斜桅從船頭舷牆上面過去 ⇒ 孔 0 格、船殼不變）
B = export_list(HULL, json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['rig_build']['hull_mark'])
N = export_list(HULL, None)
rows = [l for l in open(os.path.join(design, 'masks', 'bowsprit_hole', 'carve.vox.txt'), encoding='utf-8') if l.strip() and not l.startswith('#')]
H = np.array([list(map(int, l.split(','))) for l in rows], np.int32).reshape(-1, 4)
want = dict(zip(key(B).tolist(), B[:, 3].tolist()))
for k in key(H).tolist():
    want.pop(k, None)
got = dict(zip(key(N).tolist(), N[:, 3].tolist()))
print('船殼（窗玻璃:end − 艏斜桅孔 %d）：作品 %d、設計 %d、缺 %d、多 %d、色差 %d' % (len(H), len(got), len(want), len(set(want) - set(got)), len(set(got) - set(want)),
      sum(1 for k in set(want) & set(got) if want[k] != got[k])))
# 帆桁模型：meta 齊全、來源作品有 pivot／earing（方帆）或 fore／peak（lateen）
P = json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))
bad = []
for p in P:
    host = '%s-%s' % (HULL, 'bowsprit' if p['mast'] == 'bowsprit' else 'mast-' + p['mast'])
    ms = {m['name']: m for m in json.load(open(os.path.join(WORKS, host, 'models.json'), encoding='utf-8'))['models']}
    m = ms.get(p['name'])
    if not m:
        bad.append((p['name'], '模型不在 ' + host)); continue
    for fk in ('at', 'pivot', 'rotate', 'scale'):
        if [round(float(a), 2) for a in m[fk]] != [round(float(a), 2) for a in p[fk]]:
            bad.append((p['name'], '%s 作品 %s ≠ 設計 %s' % (fk, m[fk], p[fk])))
    mt = m.get('meta', {})
    for k in ('kind', 'mast', 'yard', 'sail', 'pivot_anchor'):
        if not mt.get(k):
            bad.append((p['name'], '少 meta ' + k))
    an = {a['name'] for a in json.load(open(os.path.join(WORKS, m['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
    need = ('pivot', 'fore', 'peak') if p['name'].endswith('lateen') else ('pivot', 'earing-P', 'earing-S', 'arm-P', 'arm-S')
    for k in need:
        if k not in an:
            bad.append((p['name'], '來源少固定點 ' + k))
print('帆桁模型 %d 根；問題 %s' % (len(P), bad or 0))
