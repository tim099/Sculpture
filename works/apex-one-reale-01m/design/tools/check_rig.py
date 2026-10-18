# 階段三讀數（TASK-0701）：
#   ① 結果帳：兩根桅、兩根帆桁（export format=list）vs 清單；甲板-main（mark=桅孔:end）vs 階段二清單 − 桅孔 —— 缺／多／色差
#   ② CLI 讀數：繩、帆（broken）、模型（broken）、帆的 meta（沒有 meta 幾面）
#   用法：python -I -X utf8 tools/check_rig.py
import os, sys, re, subprocess
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.stdout.reconfigure(encoding='utf-8')
import wio

HULL = 'apex-one-reale-01m'
ASM = HULL + '-assembly'


def ld(p):
    return np.loadtxt(os.path.join(HERE, p), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def ledger(name, w, d):
    cw = dict(zip(wio.key(w).tolist(), w[:, 3].tolist()))
    cd = dict(zip(wio.key(d).tolist(), d[:, 3].tolist()))
    print('   %-12s 作品 %7d ／ 設計 %7d ⇒ 缺 %d、多 %d、色差 %d' % (name, len(cw), len(cd), len(set(cd) - set(cw)), len(set(cw) - set(cd)),
                                                          sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])))


print('① 結果帳')
for k in ('main', 'fore'):
    ledger('mast-' + k, wio.export_list('%s-mast-%s' % (HULL, k), None), ld('masks/masts/%s.vox.txt' % k))
    ledger('yard-' + k, wio.export_list('%s-yard-%s' % (HULL, k), None), ld('masks/yards/%s.vox.txt' % k))
deck = ld('masks/upper/deck.vox.txt')
holes = set(wio.key(ld('masks/masts/deck_holes.vox.txt')).tolist())
deck = deck[[k not in holes for k in wio.key(deck).tolist()]]
ledger('deck-main', wio.export_list(HULL + '-deck-main', '桅孔:end'), deck)


def cli(*a):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for s in a for x in ('--arg', s)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.stdout + r.stderr


def val(out, key):
    m = re.search(r'🔢 %s = (\S+)' % key, out)
    return m.group(1) if m else '（沒印）'


print('② CLI 讀數')
o = cli('op=work', 'sub=ropes', 'work=' + ASM)
print('   繩：%s 條、ropes_broken %s' % (val(o, 'ropes'), val(o, 'ropes_broken')))
o = cli('op=work', 'sub=sails', 'work=' + ASM)
print('   帆：%s 面、sails_broken %s' % (val(o, 'sails'), val(o, 'sails_broken')))
for k in ('main', 'fore'):
    o = cli('op=work', 'sub=models', 'work=%s-mast-%s' % (HULL, k))
    print('   模型（mast-%s）：%s 個、models_broken %s' % (k, val(o, 'models'), val(o, 'models_broken')))
o = cli('op=work', 'sub=meta', 'part=sail', 'work=' + ASM)
print('   帆的 meta：' + ' '.join(l.strip() for l in o.splitlines() if '沒有 meta' in l or 'no_meta' in l)[:200])
