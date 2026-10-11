# 鏡廳的風 —— 產生器（stampvox 清單由它產生，66,770 格）

```python
# 《憲法號的鏡廳》的風：子作品座標 1024×480×800（＝鏡廳上半；船 x 11..958、y 16..304、z 0..649，船頭朝 +x）
# 順風：從船尾（−x）吹向船頭（+x）。流線虛線、斷面 3×3（y,z），淡青 223／淡天藍 187；船頭前方三團小旋渦。
import math, sys
W, H, D = 1024, 480, 800
cells = {}

def put(x, y, z, c):
    x, y, z = int(round(x)), int(round(y)), int(round(z))
    for dy in (-1, 0, 1):
        for dz in (-1, 0, 1):
            X, Y, Z = x, y + dy, z + dz
            if 0 <= X < W and 0 <= Y < H and 0 <= Z < D:
                cells[(X, Y, Z)] = c

def stream(y0, z0, ay, az, lam, phase, color, dash=90, gap=35, x0=0, x1=W - 1, rise=0.0):
    x = x0
    while x <= x1:
        seg_end = min(x1, x + dash)
        # 細分步進：讓斷面在斜段也連續
        t = x
        while t <= seg_end:
            k = (t - x0) / max(1, x1 - x0)
            y = y0 + ay * math.sin(2 * math.pi * t / lam + phase)
            z = z0 + az * math.sin(2 * math.pi * t / (lam * 0.7) + phase * 1.3) + rise * k
            put(t, y, z, color)
            t += 0.5
        x = seg_end + gap

def swirl(cx, cy, cz, r0, turns, color):
    n = int(turns * 360)
    for i in range(n * 2):
        a = math.radians(i / 2)
        r = r0 * (1 - i / (n * 2) * 0.8)
        put(cx + r * math.cos(a) * 0.6 + i / (n * 2) * 40, cy, cz + r * math.sin(a), color)

# 桅頂上方（z 660..790 是空的）
stream(60, 700, 25, 18, 400, 0.0, 223, rise=20)
stream(170, 740, 30, 15, 360, 1.7, 187, rise=15)
stream(270, 690, 20, 20, 430, 3.1, 223, rise=25)
stream(120, 775, 15, 10, 300, 4.4, 187, dash=120, gap=45)
# 舷外側（y 320..470 在上半是空的）
stream(345, 520, 15, 40, 380, 0.6, 223, rise=40)
stream(390, 380, 20, 35, 420, 2.2, 187, rise=30)
stream(440, 250, 18, 30, 350, 3.8, 223, rise=50)
stream(465, 600, 10, 25, 450, 5.0, 187, dash=70, gap=40)
# 另一舷外（y 0..15 很窄，只放一條貼邊的）
stream(6, 450, 4, 45, 380, 1.1, 187, dash=80, gap=50)
# 船頭前方的小旋渦（x 960..1020，船已經結束）
swirl(965, 160, 420, 28, 1.5, 223)
swirl(975, 360, 300, 22, 1.5, 187)
swirl(960, 420, 560, 18, 1.3, 223)

out = sys.argv[1]
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 鏡廳的風（apex-one）—— x,y,z,color；子作品 1024×480×800\n')
    for (x, y, z), c in sorted(cells.items()):
        f.write(f'{x},{y},{z},{c}\n')
print(len(cells))
```
