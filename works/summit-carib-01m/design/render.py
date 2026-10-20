# 預覽圖（TASK-0741；抄來給 TASK-0757）：每件成品用引擎渲一張（白天、內建天空、地板），再拼成一張對照表。
# 用法：python -I -X utf8 -B render.py <design 資料夾> [key …]
import sys, os, json, subprocess
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
want = sys.argv[2:]
man = json.load(open(os.path.join(D, 'manifest.json'), encoding='utf-8'))
ROOT = man['root']
OUT = os.path.join(os.path.dirname(D), 'overlays')
SHOTS = [('house-a', 210), ('house-b', 210), ('house-c', 210), ('house-a2', 150), ('house-b2', 150), ('house-c2', 150),
         ('tavern', 210), ('warehouse', 210), ('church', 215), ('commandant', 210), ('battery', 200)]


def view(work, out, yaw, pitch=28, w=900, h=700, extra=()):
    args = ['senate', 'cmd', 'sculpture', '--arg', 'op=view', '--arg', 'work=' + work, '--arg', 'yaw=%g' % yaw, '--arg', 'pitch=%g' % pitch,
            '--arg', 'floor=on', '--arg', 'skybox=builtin', '--arg', 'sun=1', '--arg', 'width=%d' % w, '--arg', 'height=%d' % h,
            '--arg', 'out=' + out.replace('\\', '/')]
    for e in extra:
        args += ['--arg', e]
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(work, 'rc', r.returncode, [l for l in r.stdout.splitlines() if l.startswith('✓') or l.startswith('✗')][:1])
    return r.returncode == 0


paths = []
for key, yaw in SHOTS:
    if want and key not in want and 'sheet' not in want:
        continue
    p = os.path.join(OUT, 'stage2_%s.png' % key)
    if not want or key in want:
        view('%s-%s' % (ROOT, key), p, yaw)
    paths.append((key, p))
if not want or 'street' in want:
    view(ROOT, os.path.join(OUT, 'stage2_street_yaw200.png'), 200, 35, 1800, 1100)
    view(ROOT, os.path.join(OUT, 'stage2_street_yaw20.png'), 20, 35, 1800, 1100)
# 對照表：4 欄 × 3 列
try:
    font = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 22)
except Exception:
    font = None
cw, ch = 450, 350
sheet = Image.new('RGB', (cw * 4, (ch + 34) * 3), (248, 246, 238))
d = ImageDraw.Draw(sheet)
for i, (key, p) in enumerate(paths):
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert('RGB').resize((cw, ch), Image.LANCZOS)
    x, y = (i % 4) * cw, (i // 4) * (ch + 34)
    sheet.paste(im, (x, y + 34))
    W0 = man['works']['%s-%s' % (ROOT, key)]
    d.text((x + 8, y + 4), '%s　%s' % (key, W0['title'].split('（')[0]), fill=(40, 40, 40), font=font)
sheet.save(os.path.join(OUT, 'stage2_contact_sheet.png'))
print('sheet', os.path.join(OUT, 'stage2_contact_sheet.png'))
