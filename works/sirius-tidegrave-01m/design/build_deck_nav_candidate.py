"""Position-aware deck selection against the current game; isolated candidate only."""
from pathlib import Path
import difflib, hashlib, json
ROOT = Path(__file__).resolve().parent
SOURCE = Path('D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/42_hands.js')

def main():
    before = SOURCE.read_text(encoding='utf-8')
    after = before
    def replace(old, new):
        nonlocal after
        if after.count(old) != 1:
            raise RuntimeError('Game source changed: ' + old[:80])
        after = after.replace(old, new)
    replace('CLIMB_LIFT = 2;', 'CLIMB_LIFT = 3;')
    replace('lo、hi 抬 0.2 m', 'lo、hi 抬 0.3 m')
    replace('function navCell(N, p) {', '''/** Select the actual deck under a point; disjoint decks can share a height.
 * Old exports without deck metadata retain the original height selection. */
function navLevelAt(Ls, p) {
  var hasMeta = Ls.some(function(L) { return !!L.deck; });
  if (!hasMeta) return lvOf(Ls, p[2]);
  var best = -1, bd = Infinity;
  Ls.forEach(function(L, i) {
    if (!L.deck) return;
    var f = deckFloor(L.deck, p[0]); if (f === null || Math.abs(f - p[2]) > 3) return;
    var a = navSnap(L.N, p, 5); if (a < 0) return;
    var q = navPos(L.N, a), dz = Math.abs(q[2] - p[2]); if (dz > 3) return;
    var d = (q[0]-p[0])*(q[0]-p[0]) + (q[1]-p[1])*(q[1]-p[1]) + dz*8;
    if (d < bd) { bd = d; best = i; }
  });
  return best;
}
function navCell(N, p) {''')
    replace("key = L.zr.join(',') + ':' + sh.models.length, d = L.deck;",
            "key = L.zr.join(',') + ':' + sh.models.length + ':' + (L.deck ? L.deck.path : ''), d = L.deck;")
    replace('la = lvOf(Ls, a[2]), lb = lvOf(Ls, b[2]);',
            'la = navLevelAt(Ls, a), lb = navLevelAt(Ls, b);')
    replace('var lv = lvOf(NV.levels, D.zr[0]);',
            'var lv = D.meta ? NV.levels.findIndex(function(L) { return L.deck === D.meta; }) : lvOf(NV.levels, D.zr[0]);')
    replace('var lvh = lvOf(NV.levels, hd[0].home[2]);',
            'var lvh = navLevelAt(NV.levels, hd[0].home);')
    out = ROOT/'nav_deck_candidate'
    out.mkdir(exist_ok=True)
    (out/'42_hands_candidate.js').write_text(after, encoding='utf-8')
    (out/'42_hands.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/js/42_hands.js',tofile='b/js/42_hands.js')),encoding='utf-8')
    crew_source=SOURCE.parent/'40_crew.js'
    crew_before=crew_source.read_text(encoding='utf-8')
    old="if (wheel) { var wx = Math.floor(wheel.bb[0]) - 3; [[wx, CY + 3], [wx, CY - 3], [wx - 5, CY + 7], [wx - 5, CY - 7]].slice(0, CW.helm).forEach(function (p) { add(ROLE.HELM, standNear(g, p[0], p[1], sz0, sz1, 14, taken), null, -1); }); }"
    new="if (wheel) { var wx = Math.floor(wheel.bb[0]) - 3, wy = Math.floor(wheel.c[1]), wz = Math.floor(wheel.bb[2]); [[wx, wy + 3], [wx, wy - 3], [wx - 5, wy + 7], [wx - 5, wy - 7]].slice(0, CW.helm).forEach(function (p) { add(ROLE.HELM, standNear(g, p[0], p[1], wz - 1, wz + 3, 14, taken), null, -1); }); }"
    if crew_before.count(old)!=1:raise RuntimeError('Game helm spawn source changed')
    crew_after=crew_before.replace(old,new)
    (out/'40_crew_candidate.js').write_text(crew_after,encoding='utf-8')
    (out/'40_crew.patch').write_text(''.join(difflib.unified_diff(crew_before.splitlines(True),crew_after.splitlines(True),fromfile='a/js/40_crew.js',tofile='b/js/40_crew.js')),encoding='utf-8')
    (out/'source.json').write_text(json.dumps({'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'candidateSha256':hashlib.sha256((out/'42_hands_candidate.js').read_bytes()).hexdigest(),'scope':'isolated Tidegrave fixture only; preserves navRegions, uses deck position for ladder/helm and deck identity for gun crew; CLIMB_LIFT3 validated on these seven stairs, other ships require regression before adoption'},indent=2)+'\n',encoding='utf-8')
    (out/'crew_source.json').write_text(json.dumps({'source':str(crew_source),'sha256':hashlib.sha256(crew_source.read_bytes()).hexdigest(),'candidateSha256':hashlib.sha256((out/'40_crew_candidate.js').read_bytes()).hexdigest(),'scope':'helm spawn follows wheel XY and base Z; other role spawns unchanged'},indent=2)+'\n',encoding='utf-8')

if __name__ == '__main__': main()
