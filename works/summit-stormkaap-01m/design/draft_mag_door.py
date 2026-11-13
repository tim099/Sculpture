# 彈藥庫門對齊貨艙梯（2026-11-13，Tim：「協助修復 風暴角號 彈藥庫樓梯連接處跟門錯開問題」「門可以開歪一邊(因為桅杆擋住了)」）
#   現況（exports/stage24_pre 量的）：門洞在前艙壁 x 172 的中線（y 128–132、z 29–43）；門正前方是後桅（x 175–181、中線）⇒ 階段二十把 hold-mag 梯子擺在
#     後桅右舷（側板 y 134、138，踏階 y 135–137，最上一階 z 25 在 x 174–175），門口鋪 x 173–174、y 128–134 的踏板接過去 ⇒ 爬上來要跨過 y 134 的側板、
#     往左舷橫走 4～8 格才到門；梯子的 head 點寫在舊門中線 (172,130,29)，離梯子中線 6 格。
#   ⇒ ① 門洞挪到 y 134–138（對著梯子，寬、高照舊：half 2、15 格）—— 從彈藥庫子作品刻掉那 75 格（銅皮）；
#     ② 舊門洞 y 128–132 補回艙壁（75 格，顏色照門邊：銅皮 168 —— draft_magazine.py 的艙壁規則：外圈一格才是橡木框，門洞在裡面）；
#     ③ 梯頂補一階：x 173、y 135–137、z 27–28（6 格，踏板色 104，同舊踏板的高度）—— 最上一階 z 25 ＋3 ＝ z 28，跟門檻同高；x 174 不補（會壓在最上一階的人頭上）；
#     ④ 固定點：彈藥庫 door → (172,136,29)；梯子 hold-mag.head → (172,136,29)（foot／lo／hi 不動）。
#   舊門前那段踏板（x 173–174、y 128–133）留著（拿掉 ⇒ 後桅旁多一個掉得下去的洞）。桶不動：門內 x 157–171、y 123–137 沒有桶（最近的在 y 140.5，佔到 y 138.3 以後）。
#   ⛔ 沒改 draft_magazine.py／draft_hold_ladders.py（它們讀的 stage12／stage20_pre 匯出已經是舊的）：重跑那兩支會把門放回中線 —— 之後要重跑先把這支的四件併進去。
# 檢查（照引擎匯出，不照設計）：新門檻 10 格（x 172–173、y 134–138；x 173 的 y 134、138 踩在側板頂上）腳下實心、頭上 7 格空；梯頂那一階站得住；舊門洞補完是實心；改的格子都在框裡、顏色照匯出。
# 用法：python -I -X utf8 -B draft_mag_door.py <design> <exports 資料夾：assembly.list.txt、summit-stormkaap-01m-magazine.list.txt、summit-stormkaap-01m-ladders-hold.list.txt>
#   ⇒ masks/mag_door/*.vox.txt、verify_mag_door.json
import sys, os, json, hashlib

D, EX = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
PRE = 'summit-stormkaap-01m'
MAG, LAD = PRE + '-magazine', PRE + '-ladders-hold'
FA = (140, 100, 0)                                                      # 彈藥庫子作品的框（plan.json magazine.frame_at）
X1, ZF, H = 172, 28, 15                                                 # 前艙壁、地板、門高（plan.json magazine：x[1]、floor_z、door.height）
OLD_Y, NEW_Y = range(128, 133), range(134, 139)
STEP = [(173, y, z) for y in range(135, 138) for z in (27, 28)]
STEP_COL, WALL_COL = 104, 168
HEAD = (172, 136, 29)


def read(p, off=(0, 0, 0)):
    d = {}
    for ln in open(p, encoding='utf-8'):
        if ln[0] == '#' or not ln.strip():
            continue
        x, y, z, c = map(int, ln.split(','))
        d[(x + off[0], y + off[1], z + off[2])] = c
    return d


A = read(os.path.join(EX, 'assembly.list.txt'))
M = read(os.path.join(EX, MAG + '.list.txt'), FA)
L = read(os.path.join(EX, LAD + '.list.txt'))
assert all(A.get(k) == c for k, c in M.items()), '彈藥庫子作品跟組裝件對不上'
assert all(A.get(k) == c for k, c in L.items()), '梯子子作品跟組裝件對不上'
old = [(X1, y, z) for y in OLD_Y for z in range(ZF + 1, ZF + H + 1)]
new = [(X1, y, z) for y in NEW_Y for z in range(ZF + 1, ZF + H + 1)]
assert not any(k in A for k in old), '舊門洞裡有格子'
assert all(k in M for k in new), ('新門洞那幾格不全是彈藥庫的', [k for k in new if k not in M][:5])
assert {M[k] for k in new} == {WALL_COL}, ('新門洞的顏色', sorted({M[k] for k in new}))
side = {M[(X1, y, z)] for y in (OLD_Y[0] - 1, OLD_Y[-1] + 1) for z in range(ZF + 1, ZF + H + 1)}
assert side == {WALL_COL}, ('舊門兩邊的顏色', side)
assert not any(k in A for k in STEP), '梯頂那一階的位置有格子'
after = set(A) - set(new) | set(old) | set(STEP)
air7 = lambda x, y, z: not any((x, y, z + h) in after for h in range(7))
stand = lambda x, y, z: (x, y, z - 1) in after and air7(x, y, z)
thr = [(x, y, ZF + 1) for x in (X1, X1 + 1) for y in NEW_Y if (x, y, ZF + 1) not in after]
v = {'old_door': [list(old[0]), list(old[-1])], 'new_door': [list(new[0]), list(new[-1])], 'step': [list(STEP[0]), list(STEP[-1])], 'head': list(HEAD),
     'threshold': [list(k) for k in thr], 'threshold_stand': sum(1 for k in thr if stand(*k)),
     'inside_stand': [y for y in NEW_Y if stand(X1 - 1, y, ZF + 1)], 'step_stand': [k[1] for k in STEP if k[2] == 28 and stand(k[0], k[1], 29)],
     'head_stand': stand(*HEAD), 'old_air_after': sum(1 for k in old if k not in after), 'expect_assembly_after': len(after), 'assembly_before': len(A)}
assert v['head_stand'] and v['threshold_stand'] == len(thr) and len(v['inside_stand']) == 5 and len(v['step_stand']) == 3 and v['old_air_after'] == 0, v
assert v['expect_assembly_after'] == len(A) + len(STEP), v           # 刻 75、補 75 ⇒ 只多梯頂 6 格
out = os.path.join(D, 'masks', 'mag_door'); os.makedirs(out, exist_ok=True)
NL = chr(10)
files = {}


def write(name, work, op, cells, off, note):
    txt = '# %s（draft_mag_door.py）—— %s，x,y,z,色（%d 格；子作品座標 ＝ 世界 − %s）' % (note, op, len(cells), list(off)) + NL + ''.join(
        '%d,%d,%d,%d' % (k[0] - off[0], k[1] - off[1], k[2] - off[2], c) + NL for k, c in sorted(cells.items()))
    p = os.path.join(out, name)
    open(p, 'w', encoding='utf-8', newline=NL).write(txt)
    files[name] = {'work': work, 'op': op, 'path': 'masks/mag_door/' + name, 'cells': len(cells), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()}


write('magazine.carve.vox.txt', MAG, 'carvevox', {k: M[k] for k in new}, FA, '新門洞 y 134–138')
write('magazine.add.vox.txt', MAG, 'stampvox', {k: WALL_COL for k in old}, FA, '舊門洞 y 128–132 補回艙壁')
write('ladders-hold.add.vox.txt', LAD, 'stampvox', {k: STEP_COL for k in STEP}, (0, 0, 0), '梯頂補一階')
v['files'] = files
v['anchors'] = [{'work': MAG, 'name': 'door', 'at': [HEAD[0] - FA[0], HEAD[1] - FA[1], HEAD[2] - FA[2]], 'world': list(HEAD)},
                {'work': LAD, 'name': 'hold-mag.head', 'at': list(HEAD), 'world': list(HEAD)}]
with open(os.path.join(D, 'verify_mag_door.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(v, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
print(json.dumps({k: v[k] for k in ('threshold_stand', 'inside_stand', 'step_stand', 'head_stand', 'assembly_before', 'expect_assembly_after')}, ensure_ascii=False))
print({k: (f['op'], f['cells']) for k, f in files.items()})
