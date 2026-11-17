"""Lay the working decks, cargo hatch, and passenger shelter."""
from draft_hull import CENTER, DESIGN, PLAN, X_RANGE, shell

WOOD, RAIL, PLANK, IRON, CLOTH = 104, 141, 177, 109, 214
solid, hull_colors = shell()
used = {(x + X_RANGE.start, y, z) for x, y, z in zip(*hull_colors.nonzero())}


def row(z, start, end):
    return {(x, y, z): PLANK for x in range(start, end + 1) for y in range(PLAN["size"][1])
            if solid[x - X_RANGE.start, y, z] and (x, y, z) not in used}


def write(name, cells, linked=True):
    if linked:
        assert not (cells.keys() & used), name
        used.update(cells)
    out = DESIGN / "masks"
    out.mkdir(exist_ok=True)
    (out / f"{name}.txt").write_bytes("".join(f"{x},{y},{z},{c}\n" for (x, y, z), c in sorted(cells.items())).encode("ascii"))
    print(name, len(cells))


def usable(name, cells):
    write(name, {p: c for p, c in cells.items() if p not in used})


def stepped(start, end, low, high, ys):
    cells = {}
    for i, x in enumerate(range(start, end + (1 if end > start else -1), 1 if end > start else -1)):
        z = low + round((high - low) * i / abs(end - start))
        for y in ys:
            cells[x, y, z] = WOOD if y in (ys.start, ys.stop - 1) else PLANK
        for y in (ys.start, ys.stop - 1):
            cells[x, y, z - 1] = WOOD
    return cells


def main():
    hold = row(2, 72, 155)
    write("hold", hold)
    deck = row(16, 61, 181)
    deck = {p: c for p, c in deck.items() if not (105 <= p[0] <= 121 and 29 <= p[1] <= 43)}
    write("deck", deck)
    write("aft-deck", row(22, 56, 84))
    usable("hold-ladder", stepped(104, 121, 3, 15, range(33, 40)))
    usable("aft-ladder", stepped(94, 85, 17, 22, range(33, 40)))

    fitting = {(x,y,17): RAIL for x in range(103,124) for y in (28,44)}
    fitting.update({(x,y,17): RAIL for x in (104,122) for y in range(29,44) if not 33 <= y <= 39})
    # Coaming leaves both ends of the ladder passable.
    usable("coaming", fitting)

    hatch = {(x,y,0): (RAIL if x in (0,16) or y in (0,14) else PLANK)
             for x in range(17) for y in range(15)}
    for x in (6,10):
        for y in range(11,14):
            hatch[x,y,1] = IRON
    write("hatch", hatch, linked=False)

    ends = {}
    # The stem's open rising beak follows the two curves on plate 18.
    for x in range(186, 212):
        fraction = (x - 186) / 25
        z = 25 + round(6*fraction*fraction)
        width = max(0, 5 - round(5*fraction))
        for y in range(CENTER - width, CENTER + width + 1):
            ends[x, y, z] = PLANK if abs(y - CENTER) < width else RAIL
            if abs(y - CENTER) == width and width:
                ends[x, y, z+1] = WOOD
                ends[x, y, z+2] = RAIL
        ends[x, CENTER, z - 1] = WOOD
    # Short stern rail and upright timbers.
    for x in range(56,77):
        yt = 6 + (x-56)//4
        for side in (-1,1):
            for y in (CENTER+side*yt,):
                ends[x,y,31] = RAIL
                if x % 5 == 1 or x == 75:
                    for z in range(23,31):
                        ends[x,y,z] = WOOD
    usable("ends", ends)

    shelter = {}
    # A removable awning over two side benches, with a clear central aisle.
    for x in range(65,81):
        for y in range(26,47):
            top = 41 - round(abs(y-CENTER)/5)
            shelter[x,y,top] = CLOTH if x not in (65,80) else RAIL
            if x in (65,80) and y in (27,45):
                for z in range(23,top):
                    shelter[x,y,z] = WOOD
        for y in (28,29,43,44):
            shelter[x,y,27] = PLANK
    for x in (68,77):
        for y in (28,44):
            for z in range(23,27):
                shelter[x,y,z] = WOOD
    write("shelter", shelter, linked=False)

    cargo = {}
    for start, y0 in ((82,30),(90,39),(126,42),(144,29)):
        for x in range(start, start+5):
            for y in range(y0, y0+4):
                for z in range(3, 7):
                    cargo[x,y,z] = PLANK if z in (3,6) else WOOD
                    if y in (y0,y0+3) and x in (start,start+4):
                        cargo[x,y,z] = RAIL
    write("cargo", cargo, linked=False)


if __name__ == "__main__":
    main()
