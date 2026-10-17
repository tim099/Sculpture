# 餘燼號 往下通貨艙（hold）的梯子（Tim 2026-10-17：「補吧」—— 接 TASK-0519 留言 #4 的量測）
#   量的（組裝件 export list，沿中線 y 160 看 z 15–65 的實心段）：
#   - x < 406 沒拉長、跟憲法號同形 ⇒ after hatch X 274–285、X 307–319 兩處從 orlop（站 42）往下到貨艙底；main hatch X 401–419 從 berth（站 60）往下 —— 照憲法號 draft_hold_ladders.py 的三座。
#   - 🆕 前艙口 X 574–600：從上甲板一路通到貨艙底（中線只有 z 15–16 的船底）。憲法號這底下是前彈藥庫（它的頂擋著）；
#     餘燼號階段二十一換成中央彈藥庫、拿掉了前後兩間（10-13）⇒ 前艙口直接掉到底。前後 orlop 在 X 566–573、604–617（站 42），X 601–603 是艙壁。
#   walkback.py 的讀數（同一份輸入）：前貨艙 X 538–690 照遊戲走法 0 格回不來、只算 0.3 m 台階 10,294 格回不來 —— 照規則能沿船殼內壁爬，
#   但憲法號同一種情形 Tim 在遊戲裡就是上不來（10-16）⇒ 這把尺的「走得回」不當作不用補的理由；判準照憲法號：掉得下去的艙口都放一座梯子。
# 幾何、顏色、扶手、檢查全照憲法號那一支（它又沿用 draft_orlop_ladders.py）；只換船、候選位置、陣列寬度（餘燼號 1100）。
# 用法：python -I draft_hold_ladders.py <組裝件 export list（梯子加進來之前）>
#   ⇒ masks/ladders/hold.vox.txt（梯子子作品，世界座標）、rig_points_hold_ladders.json、hold_ladder_ropes.json、verify_hold_ladders.json
import sys, os, json, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CON = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'basecamp-frigate-constitution-01m', 'design')
sys.path.insert(0, CON)
import draft_orlop_ladders as O
import draft_hold_ladders as H     # 憲法號那一支：Hold.build／write、RUNS、landing 3 都從它來

H.HERE = HERE
H.SUB = 'basecamp-ember-01m-ladders-hold'
H.TITLE = '餘燼號 往下通貨艙的梯子'
NX = 1100

Y = H.Y
H.LADDERS = [
    {'id': 'hold-aft', 'zu': 42, 'zl': 17, 'cands': [(274, 1, y) for y in Y] + [(285, -1, y) for y in Y],
     'note': 'after hatch（orlop X 274–285）—— 同憲法號（X < 406 沒拉長）'},
    {'id': 'hold-mid', 'zu': 42, 'zl': 17, 'cands': [(319, -1, y) for y in Y] + [(309, 1, y) for y in Y],
     'note': 'orlop X 307–319 的艙口 —— 同憲法號'},
    {'id': 'hold-main', 'zu': 60, 'zl': 17, 'cands': [(419, -1, y) for y in Y] + [(401, 1, y) for y in Y] + [(392, 1, y) for y in Y],
     'note': 'main hatch（berth X 401–419）—— 同憲法號'},
    {'id': 'hold-fore', 'zu': 42, 'zl': 17, 'cands': [(574, 1, y) for y in Y] + [(600, -1, y) for y in Y],
     'note': '前艙口 X 574–600（餘燼號才有：前彈藥庫拿掉之後通到底）；梯頂接 orlop 前平台（後緣 X 566–573 或前面 604 起）'},
]


class Hold(H.Hold):
    def __init__(s, asm):
        s.S = {'ladders': []}
        s.asm_sha = hashlib.sha256(open(asm, 'rb').read()).hexdigest()
        s.W = np.zeros((NX, 320, O.ZMAX), np.uint8)
        s.n_asm = 0
        for (x, y, z), c in O.read(asm).items():
            s.n_asm += 1
            if z < O.ZMAX:
                s.W[x, y, z] = c
        s.carve, s.cells, s.kind, s.anchors, s.ropes, s.rows = {}, {}, {}, [], [], []


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    F = Hold(sys.argv[1])
    F.build()
    F.verify()
    F.write()
    F.v['files'] = F.files
    json.dump(F.v, open(os.path.join(HERE, 'verify_hold_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: F.v[k] for k in F.v if k != 'ladders'}, ensure_ascii=False))
    for r in F.rows:
        print(json.dumps({k: r[k] for k in r if k != 'why'}, ensure_ascii=False), ('why: %s' % r['why'][-3:]) if not r['placed'] else '')


if __name__ == '__main__':
    main()
