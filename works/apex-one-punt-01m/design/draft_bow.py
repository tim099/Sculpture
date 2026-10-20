# 弓（角形複合弓，弓手站位；通用部件，0.05 m、模型 scale 0.5）—— 「換皮大砲」（造船規格 §2.2，照持火號弩砲的做法）
#   Tim 2026-10-20：「做「弓」換皮砲（照弩砲的做法）加箭箱當彈藥庫」。
#   ⇒ masks/bow/bow.vox.txt、bow_part.json（框、固定點）
#   用法：python -I -X utf8 draft_bow.py
#   · 座標照 §4.1：x 中線、箭朝 +y、z 0 ＝ 站的那一面（弓架底）。
#   · 形狀：新王國的角形複合弓（上弦後兩臂近直、在握把處折成鈍角；Tutankhamun 墓的弓長約 1.1–1.4 m）—— 弓長 1.2 m、
#     握把在弓架頂（z 1.3 m）、上了弦的弓臂往後收 0.2 m；一支箭搭在弦上（拉滿 0.6 m、箭長 0.85 m）。
#   · 固定點：breech（拉滿時的扣弦點）、muzzle（箭頭前一格）、pivot（弓架底中心 ＝ 迴旋軸）、nock（＝ breech，弦的 rest）、
#     nock-fire（放箭後扣弦點回到兩臂尖的連線上）、string-a／string-b（上下兩臂尖）。
import sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 11, 24, 40
CX = 5
GRIP_Y, GRIP_Z = 20, 26          # 握把（弓架頂）
HALF_LEN = 12                    # 握把到臂尖（z 方向，0.6 m）
BACK = 4                         # 上了弦臂尖往後收（0.2 m）
DRAW = 12                        # 拉滿：扣弦點在弦線後 0.6 m
COL = {'bow': 100, 'grip': 244, 'post': 104, 'base': 104, 'shaft': 177, 'head': 146, 'fletch': 160, 'tip': 244}


def main():
    cells = {}
    put = lambda x, y, z, c: cells.__setitem__((x, y, z), c)
    # 弓架：底板 5×5×1、柱 1×1 從底到握把下一格
    for x in range(CX - 2, CX + 3):
        for y in range(GRIP_Y - 2, GRIP_Y + 3):
            put(x, y, 0, COL['base'])
    for z in range(1, GRIP_Z):
        put(CX, GRIP_Y, z, COL['post'])
    # 弓臂：握把（z ±1 金）→ 兩臂尖（z ±HALF_LEN、往後 BACK）直線；臂寬 1 格（x 中線）
    tips = {}
    for sgn, nm in ((1, 'string-a'), (-1, 'string-b')):
        py = GRIP_Y
        for k in range(0, HALF_LEN + 1):
            z = GRIP_Z + sgn * k
            y = GRIP_Y - round(BACK * k / HALF_LEN)
            if y != py:                                     # y、z 同時變 ⇒ 只靠斜角相接、6 連通斷開 ⇒ 前一個 y 補一格
                put(CX, py, z, COL['bow'])
            py = y
            put(CX, y, z, COL['grip'] if k <= 1 else COL['bow'])
            if k >= HALF_LEN - 1:
                put(CX, y, z, COL['tip'])
        tips[nm] = [CX, GRIP_Y - BACK, GRIP_Z + sgn * HALF_LEN]
    # 箭：從扣弦點（拉滿）往前 17 格；箭頭 2 格灰、尾羽 2 格紅
    sy = GRIP_Y - BACK            # 弦線
    ny = sy - DRAW                # 拉滿的扣弦點
    L = 17
    for k in range(L):
        y = ny + k
        c = COL['fletch'] if k < 2 else (COL['head'] if k >= L - 2 else COL['shaft'])
        if (CX, y, GRIP_Z) not in cells:
            put(CX, y, GRIP_Z, c)
    anchors = {'breech': [CX, ny, GRIP_Z], 'nock': [CX, ny, GRIP_Z], 'muzzle': [CX, ny + L, GRIP_Z], 'pivot': [CX, GRIP_Y, 0],
               'nock-fire': [CX, sy, GRIP_Z], **tips}
    assert all(0 <= v[0] < SX and 0 <= v[1] < SY and 0 <= v[2] < SZ for v in anchors.values())
    assert all(0 <= x < SX and 0 <= y < SY and 0 <= z < SZ for (x, y, z) in cells)
    os.makedirs(os.path.join(HERE, 'masks', 'bow'), exist_ok=True)
    with open(os.path.join(HERE, 'masks', 'bow', 'bow.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 弓（角形複合弓＋弓架＋搭在弦上的箭；draft_bow.py）x,y,z,color —— 元件自己的座標（0.05 m）\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(cells.items(), key=lambda kv: (kv[0][2], kv[0][1], kv[0][0]))) + '\n')
    out = {'size': [SX, SY, SZ], 'anchors': anchors, 'cells': len(cells), 'pivot_model': [CX + 0.5, GRIP_Y + 0.5, 0],
           'meta': {'kind': 'gun', 'gun': 'bow', 'weapon': 'bow', 'ammo': 'bolt', 'mount': 'pivot', 'ports': '0,45,-45'},
           'm': {'bow_len': round(2 * (HALF_LEN ** 2 + BACK ** 2) ** 0.5 * 0.05, 2), 'grip_h': GRIP_Z * 0.05, 'draw': DRAW * 0.05, 'arrow': L * 0.05}}
    with open(os.path.join(HERE, 'bow_part.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
