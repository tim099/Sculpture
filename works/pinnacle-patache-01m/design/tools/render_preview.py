# 直接出處：apex-two-galeon-01m/design/tools/render_preview.py（康塞普西翁號，TASK-0969）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是康塞普西翁號那時寫的出處
# 聖羅曼號 步驟 17（TASK-0970）：還沒落格的設計清單直接出預覽圖（不用先貼進作品）—— 體素清單的正交渲染、z-buffer、每格照露出的面估法向量打光
#   用法：python -I tools/render_preview.py <out.png> <az> <el> <scale> "<清單;清單…>" [x0,x1,z0,z1 裁切]（Git Bash 下先 export MSYS_NO_PATHCONV=1，不然 ; 分隔的路徑會被改掉）
#   · az：相機在哪個方向（度；0 ＝ +y、90 ＝ −x 船尾、180 ＝ −y、40 ≈ 右舷船尾四分之一）、el 仰角；後面的清單蓋前面的
#   · ⚠ 畫面跟作品的左右是鏡像的（作品座標是左手系：從船尾看左手 ＝ −y）⇒ 字會反著讀；只看形狀用。斜面一格一格的台階打光會像一根根欄杆，那是台階不是縫
import sys, numpy as np
from PIL import Image
out, az, el, sc = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
paths = sys.argv[5].split(';')
crop = list(map(int, sys.argv[6].split(','))) if len(sys.argv) > 6 else None
rows = []
for p in paths:
    a = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    if a.size:
        rows.append(a[:, :4])
A = np.concatenate(rows)
A = A[::-1]; _, idx = np.unique(A[:, :3], axis=0, return_index=True); A = A[idx]    # 後面的清單蓋前面的：反過來取第一個
if crop:
    m = (A[:, 0] >= crop[0]) & (A[:, 0] <= crop[1]) & (A[:, 2] >= crop[2]) & (A[:, 2] <= crop[3])
    A = A[m]
P = A[:, :3].astype(np.int64)
key = lambda q: (q[:, 0] * 1024 + q[:, 1]) * 1024 + q[:, 2]
S = np.sort(key(P))
def has(q):
    k = key(q); i = np.searchsorted(S, k); i = np.clip(i, 0, len(S) - 1); return S[i] == k
n = np.zeros((len(P), 3))
for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
    e = ~has(P + np.array(d)); n += np.outer(e, d)
nn = np.linalg.norm(n, axis=1); vis = nn > 0
P, A, n = P[vis], A[vis], n[vis] / nn[vis][:, None]
c = A[:, 3]
rgb = np.stack([(c >> 5 & 7) * 255 // 7, (c >> 2 & 7) * 255 // 7, (c & 3) * 255 // 3], 1).astype(float)
a, e = np.radians(az), np.radians(el)
# 視線（從相機往場景）：az 0 ⇒ 相機在 +y 看 −y
cam = np.array([-np.sin(a) * np.cos(e), np.cos(a) * np.cos(e), np.sin(e)])   # 相機方向（場景往相機）
right = np.cross(-cam, [0.0, 0.0, 1.0]); right /= np.linalg.norm(right)
up = np.cross(cam, right); up /= np.linalg.norm(up)
Q = P + 0.5
u = Q @ right; v = Q @ up; depth = Q @ cam
L = np.array([0.4, 0.6, 0.7]); L /= np.linalg.norm(L)
sh = 0.45 + 0.55 * np.clip(n @ L, 0, 1)
col = np.clip(rgb * sh[:, None], 0, 255)
U = ((u - u.min()) * sc).astype(int) + 10; V = ((v.max() - v) * sc).astype(int) + 10
W, H = U.max() + 12 + int(sc), V.max() + 12 + int(sc)
img = np.full((H, W, 3), 245, np.uint8)
s = max(1, int(np.ceil(sc))) + 1                                      # 每格畫 s × s 個像素（比 scale 大一格 ⇒ 沒有縫），z-buffer 取離相機最近的
pix_u, pix_v, pix_d, pix_i = [], [], [], []
for dx in range(s):
    for dy in range(s):
        pix_u.append(U + dx); pix_v.append(V + dy); pix_d.append(depth); pix_i.append(np.arange(len(U)))
pu, pv, pd, pi = map(np.concatenate, (pix_u, pix_v, pix_d, pix_i))
flat = pv * W + pu
best = np.full(H * W, -1e18); np.maximum.at(best, flat, pd)
win = pd >= best[flat] - 1e-9
img.reshape(-1, 3)[flat[win]] = col[pi[win]].astype(np.uint8)
Image.fromarray(img).save(out)
print(out, img.shape)
