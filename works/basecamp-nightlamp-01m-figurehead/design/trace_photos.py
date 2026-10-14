# 船首像讀圖（TASK-0538）：米羅的維納斯四張全身照 ⇒ 每張的雕像外輪廓（遮罩）＋疊回原圖的對照圖 ＋ 每一列的左右邊界。
# 用法：python -I trace_photos.py <design 資料夾> [視角…]
#   · 照片在 Sculpture/references/venus-de-milo-2023/（README 有出處）；先縮到高 H 再算。
#   · 一張照片一組參數（readings/trace_params.json）：亮度門檻、種子點、只看哪個框、去掉哪些框（台座、背景雜物）。
#   · 雕像 ＝ 從種子點長出去、符合門檻的那一塊 ＋ 補洞；之後開運算去毛邊。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

H = 1600
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'references', 'venus-de-milo-2023')


def load(view):
    im = Image.open(os.path.join(REF, f'Venus_de_Milo_{view}_2023.jpg')).convert('RGB')
    s = H / im.height
    return np.asarray(im.resize((round(im.width * s), H), Image.LANCZOS)).astype(np.float32), s


def mask_of(img, P):
    lum = img.mean(2)
    sat = img.max(2) - img.min(2)
    m = np.ones(lum.shape, bool)
    if 'lum_min' in P:
        m &= lum >= P['lum_min']
    if 'lum_max' in P:
        m &= lum <= P['lum_max']
    if 'sat_max' in P:
        m &= sat <= P['sat_max']
    if 'rgb_ref' in P:
        d = np.sqrt(((img - np.array(P['rgb_ref'], np.float32)) ** 2).sum(2))
        m &= d <= P['rgb_dist']
    box = np.zeros_like(m)
    x0, y0, x1, y1 = P['box']
    box[y0:y1, x0:x1] = True
    m &= box
    if 'clip_poly' in P:                                      # 人工描的外輪廓折線，往外放寬 clip_margin px；門檻漏到背景的地方由它擋
        pm = Image.new('L', (lum.shape[1], lum.shape[0]), 0)
        ImageDraw.Draw(pm).polygon([tuple(p) for p in P['clip_poly']], fill=255)
        pm = np.asarray(pm) > 0
        m &= ndimage.binary_dilation(pm, iterations=P.get('clip_margin', 15))
    for poly in P.get('cut_poly', []):                       # 切掉的多邊形（例：斷臂 —— 手另外做，量剖面時不算身體）
        pm = Image.new('L', (lum.shape[1], lum.shape[0]), 0)
        ImageDraw.Draw(pm).polygon([tuple(p) for p in poly], fill=255)
        m &= ~(np.asarray(pm) > 0)
    for (x0, y0, x1, y1) in P.get('cut', []):
        m[y0:y1, x0:x1] = False
    if P.get('close', 0):
        m = ndimage.binary_closing(m, iterations=P['close'])
    lab, _ = ndimage.label(m)
    sx, sy = P['seed']
    keep = lab == lab[sy, sx]
    assert lab[sy, sx] > 0, ('種子點不在遮罩裡', P['seed'])
    keep = ndimage.binary_fill_holes(keep)
    if P.get('open', 0):
        keep = ndimage.binary_opening(keep, iterations=P['open'])
        lab, _ = ndimage.label(keep)
        assert lab[sy, sx] > 0, ('開運算之後種子點不在遮罩裡', P['seed'])
        keep = lab == lab[sy, sx]
    return keep


def overlay(img, m, path):
    o = img.copy()
    edge = m & ~ndimage.binary_erosion(m, iterations=2)
    o[edge] = (255, 0, 0)
    o[m & ~edge] = o[m & ~edge] * 0.75 + np.array((0, 60, 0)) * 0.25
    Image.fromarray(o.astype(np.uint8)).save(path)


def main():
    design = sys.argv[1]
    P = json.load(open(os.path.join(design, 'readings', 'trace_params.json'), encoding='utf-8'))
    views = sys.argv[2:] or list(P['views'])
    out = {}
    for v in views:
        p = P['views'][v]
        img, s = load(v)
        m = mask_of(img, p)
        Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(design, 'readings', f'mask_{v}.png'))
        overlay(img, m, os.path.join(design, 'readings', f'trace_{v}.jpg'))
        ys = np.where(m.any(1))[0]
        out[v] = {'scale_from_original': s, 'size': [img.shape[1], img.shape[0]], 'pixels': int(m.sum()),
                  'y_top': int(ys.min()), 'y_bottom': int(ys.max())}
        print(v, out[v])
    return out


if __name__ == '__main__':
    main()
