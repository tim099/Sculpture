# 階段二十 b 船長室 ↔ 船尾陽台的門（TASK-0685；Tim 2026-10-17「接著參考憲法號 完成風暴角號的貨倉梯&其他細節吧」）
#   walkback（第一人稱「掉得進去就要爬得出來」，造船規格 §9.3）量到：船尾陽台（地板站 z 115、x 91–101）552 格走得到、走不回 ——
#     只能從艉樓甲板翻欄杆往下跳 8 格進去（往上只跨得上 6 格）；而陽台跟船長室（地板站 z 113–114）只隔一道艉板牆（x 102–107）。
#   ⇒ 把艉板中線那一扇窗（第 3 扇）改成門：刻掉 x 102–107、y 128–132、z 115–121 的實心（船殼的窗台 109、船尾裝飾的窗框與玻璃 104／158）；
#     z 122 以上的玻璃留著當門上的氣窗；門檻 ＝ z 114 那一層（陽台地板、船殼、後甲板邊）不動。
# 檢查：門裡外各站得住（腳下實心、上 7 格空）；刻掉的格子都在框裡、顏色照子作品匯出（carvevox 帶顏色守門）。
# 用法：python -I -X utf8 -B draft_stern_door.py <design> <exports 資料夾：組裝件 assembly.list.txt、各子作品 <work>.list.txt>
#   ⇒ masks/stern_door/<work>.carve.vox.txt、verify_stern_door.json
import sys, os, json, hashlib

D, EX = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
BOX = ((102, 107), (128, 132), (115, 121))
OWNERS = ['summit-stormkaap-01m', 'summit-stormkaap-01m-stern-deco', 'summit-stormkaap-01m-deck-half', 'summit-stormkaap-01m-quarter-gallery', 'summit-stormkaap-01m-deck-kampanje']
inb = lambda x, y, z: all(BOX[i][0] <= v <= BOX[i][1] for i, v in enumerate((x, y, z)))


def read(p):
    d = {}
    for ln in open(p, encoding='utf-8'):
        if ln[0] == '#' or not ln.strip():
            continue
        x, y, z, c = map(int, ln.split(','))
        d[(x, y, z)] = c
    return d


A = read(os.path.join(EX, 'assembly.list.txt'))
want = {k: c for k, c in A.items() if inb(*k)}
carve, owner = {}, {}
for w in OWNERS:
    for k, c in read(os.path.join(EX, w + '.list.txt')).items():
        if inb(*k):
            assert k not in owner, ('兩件子作品都有這一格', k, owner.get(k), w)
            owner[k] = w
            carve.setdefault(w, {})[k] = c
assert set(owner) == set(want), ('框裡有格子不屬於列出的子作品', sorted(set(want) - set(owner))[:5])
assert all(A[k] == carve[owner[k]][k] for k in owner), '組裝件與子作品顏色不同'
after = {k: c for k, c in A.items() if k not in owner}
S = set(after)
stand = lambda x, y, z: (x, y, z - 1) in S and not any((x, y, z + h) in S for h in range(7))
inside = [(x, 130, 114) for x in range(104, 111)]
outside = [(x, 130, 115) for x in range(96, 106)]
v = {'box': BOX, 'cells': len(owner), 'by_work': {w: len(c) for w, c in carve.items()},
     'by_color': {}, 'stand_inside_z114': [k for k in inside if stand(*k)], 'stand_outside_z115': [k for k in outside if stand(*k)],
     'stand_threshold': [k for k in [(x, y, 115) for x in range(102, 106) for y in range(128, 133)] if stand(*k)]}
for k in owner:
    c = A[k]; v['by_color'][str(c)] = v['by_color'].get(str(c), 0) + 1
assert v['stand_inside_z114'] and v['stand_outside_z115'] and len(v['stand_threshold']) == 20, v
out = os.path.join(D, 'masks', 'stern_door'); os.makedirs(out, exist_ok=True)
NL = chr(10)
v['files'] = {}
for w, cs in sorted(carve.items()):
    txt = '# 船長室 ↔ 船尾陽台的門（draft_stern_door.py）—— 從 %s 刻掉，x,y,z,原色（%d 格）' % (w, len(cs)) + NL + ''.join('%d,%d,%d,%d' % (k + (c,)) + NL for k, c in sorted(cs.items()))
    p = os.path.join(out, w + '.carve.vox.txt')
    open(p, 'w', encoding='utf-8', newline=NL).write(txt)
    v['files'][w] = {'path': 'masks/stern_door/%s.carve.vox.txt' % w, 'cells': len(cs), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()}
v['expect_assembly_after_carve'] = len(A) - len(owner)
with open(os.path.join(D, 'verify_stern_door.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(v, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
print(json.dumps({k: v[k] for k in ('cells', 'by_work', 'by_color', 'expect_assembly_after_carve')}, ensure_ascii=False), len(v['stand_threshold']), 'threshold stand')
