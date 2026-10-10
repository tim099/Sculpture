# 階段六的檢查工具（2026-10-11 從 scratchpad 搬來；路徑以本作品為準）
# 設計水線疊回 11 號水線半寬圖（船頭、船尾各一張），給製作筆記用
import sys, os, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
D = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m/design'
sys.path.insert(0, D)
import draft_ends as DE
plan, src, tr, H = DE.load(D)
img = Image.open('D:/Unity/Valhalla/Sculpture/references/uss-constitution-1927/RG19_ALPHA_Constitution_1797_11.JPG').convert('RGB')
CL = sorted([(500, 3603), (700, 3599.4), (1000, 3594), (1300, 3590.5), (1360, 3590.4), (2000, 3583), (3000, 3566), (3710, 3552.6), (4000, 3548), (4040, 3546.2), (4500, 3536)])
cx = np.array([p[0] for p in CL], float); cy = np.array([p[1] for p in CL], float)
ycl = lambda x: np.interp(x, cx, cy)
def to_px(X, hb):
    u = (X - 17.266) / 0.161954
    y = ycl(u) - hb / 0.15618
    x = u + 0.005 * (y - ycl(u))
    return x, y
font = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 26)
for name, (x0, y0, x1, y1), xr in (('stern', (640, 3120, 1120, 3620), (95, 185)), ('bow', (3560, 3180, 4100, 3570), (612, 675))):
    k = 3
    crop = img.crop((x0, y0, x1, y1)).resize(((x1 - x0) * k, (y1 - y0) * k), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    for w, z in DE.WLZ.items():
        pts = []
        for X in np.arange(xr[0], xr[1], 0.25):
            h = H.hb(X, [z])[0]
            if not np.isnan(h):
                px, py = to_px(X, h)
                pts.append(((px - x0) * k, (py - y0) * k))
        if len(pts) > 1:
            d.line(pts, fill=(230, 40, 40), width=3)
    d.text((20, 16), '11 號水線半寬圖（%s）＋ 新圖紙 03 v2 的水線 A–F（紅）' % ('船尾' if name == 'stern' else '船頭'), fill=(230, 40, 40), font=font)
    out = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m/overlays/stage6_lines_%s_vs_d11.png' % name
    crop.save(out)
    print(out, crop.size)
