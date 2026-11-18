"""Create the rig and deck arrangement sheet from plan.json.

Drawing conventions derived from meadow-bizerte-barque-01m/design/draft_hull.py.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DESIGN = Path(__file__).resolve().parent
P = json.loads((DESIGN / "plan.json").read_text(encoding="utf-8"))
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
heading = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 27)
image = Image.new("RGB", (1540, 1390), "#f5efe0")
d = ImageDraw.Draw(image)
d.text((40, 24), "Tungning trader / rig, decks and armament arrangement", font=heading, fill="#243b43")
d.text((40, 70), "DESIGN RECONSTRUCTION | dimensions in 0.1 m cells | three battented junk sails", font=font, fill="#243b43")


def point(x, z):
    return (45 + 4*x, 1330 - 4*z)


# Profile is independently drawn from the design's station coordinates.
for name, spec in P["rig"].items():
    x = spec["x"]
    d.line((point(x, spec["heel"]), point(x, spec["top"])), fill="#664a35", width=6)
    bottom, top = spec["lower_z"], spec["upper_z"]
    aft, fore = x + spec["aft"], x + spec["fore"]
    corners = [point(aft, bottom), point(fore, bottom), point(fore-8, top-10), point(aft+12, top)]
    d.polygon(corners, fill="#d0b286", outline="#75583c")
    for i in range(spec["battens"] + 1):
        t = i/spec["battens"]
        d.line((point(aft+12*t, bottom+(top-bottom)*t),
                point(fore-8*t, bottom+(top-bottom)*t-10*t)), fill="#977247", width=3)
    d.text(point(x+4, spec["top"]+4), name, font=font, fill="#243b43")
d.line([point(x, z) for x,z in P["lines"]["sheer"]], fill="#243b43", width=3)
d.line([point(x, z) for z,x in P["lines"]["stem_rake"]], fill="#243b43", width=3)
d.line([point(x, z) for z,x in P["lines"]["stern_rake"]], fill="#243b43", width=3)
d.line((point(65, 0), point(307, 0)), fill="#243b43", width=3)
for name, deck in P["decks"].items():
    a,b = deck["span"]
    d.line((point(a, deck["floor"]), point(b, deck["floor"])), fill="#8d4e3d", width=2)
    d.text(point(b+2, deck["floor"]), name, font=font, fill="#243b43")
for x in P["guns"]["long6_x"]:
    d.rectangle((*point(x-2, 60), *point(x+2, 55)), fill="#222c32")
for x in P["bulkheads"]:
    d.line((point(x, 16), point(x, 45)), fill="#776c53", width=2)
d.text((50, 120), "Main: 12 x 6-pound long guns, 4 x pierrier swivel guns", font=font, fill="#243b43")
d.text((50, 152), "Sail 1: fore | Sail 2: fore + main | Sail 3: fore + main + mizzen", font=font, fill="#243b43")
d.text((50, 184), "Hold 0.8 m | Main 4.8 m | Poop 7.2 m | Fore platform 5.6 m", font=font, fill="#243b43")
d.text((50, 216), "Loaded design draft 3.8 m | Cargo 260 t | Light draft from actual mass", font=font, fill="#243b43")
image.save(DESIGN / "sheet02_layout.png")
print("sheet02_layout.png")
