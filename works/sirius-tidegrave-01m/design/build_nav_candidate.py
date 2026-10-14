"""Isolated game integration candidate; never writes ame's game sources."""
from pathlib import Path
import difflib,hashlib,json
ROOT=Path(__file__).resolve().parent
SOURCE=Path('D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/42_hands.js')
def main():
    before=SOURCE.read_text(encoding='utf-8');after=before
    def replace(old,new):
        nonlocal after
        if after.count(old)!=1:raise RuntimeError('Game source changed: '+old[:70])
        after=after.replace(old,new)
    replace('N.ok = ok; N.cells = cells; N.parts = nc;',
            'N.ok = ok; N.cells = cells; N.parts = nc; N.component = comp; N.bestComponent = best;')
    replace('Ls.forEach(function (L) { L.N = navBuild(sh, L); });',r'''var expanded = [];
  Ls.forEach(function (L) {
    var N = L.N = navBuild(sh, L); expanded.push(L);
    if (L.key.charAt(0) !== 'h') return; // Gun deck policy stays unchanged.
    var wanted = {};
    lads.forEach(function (l) {
      [l.pts[0], l.pts[l.pts.length - 1]].forEach(function (p) {
        if (p[2] < L.zr[0] || p[2] > L.zr[1]) return;
        var cx = Math.round((p[0] - 0.5 - N.x0) / NAV_C), cy = Math.round((p[1] - 0.5) / NAV_C), best = -1, bd = Infinity;
        for (var dy = -5; dy <= 5; dy++) for (var dx = -5; dx <= 5; dx++) {
          var x = cx + dx, y = cy + dy; if (x < 0 || y < 0 || x >= N.nx || y >= N.ny) continue;
          var i = x + y * N.nx, dz = Math.abs(N.Z[i] - p[2]);
          if (N.component[i] < 0 || dz > 3) continue;
          var d = dx * dx + dy * dy + dz * 8;
          if (d < bd) { bd = d; best = N.component[i]; }
        }
        if (best >= 0 && best !== N.bestComponent) wanted[best] = true;
      });
    });
    Object.keys(wanted).forEach(function (id) {
      var ok = new Uint8Array(N.ok.length), cells = [];
      for (var i = 0; i < ok.length; i++) if (N.component[i] === +id) { ok[i] = 1; cells.push(i); }
      expanded.push({key:L.key + '-c' + id, name:L.name + ' / island ' + id, zr:L.zr,
        N:{x0:N.x0,nx:N.nx,ny:N.ny,Z:N.Z,ok:ok,cells:new Int32Array(cells),parts:1}});
    });
  });
  Ls = expanded;''')
    replace('la = lvOf(Ls, a[2]), lb = lvOf(Ls, b[2]);',
            'la = navLevelAt(Ls, a), lb = navLevelAt(Ls, b);')
    replace('function navCell(N, p) {',r'''/** Same height can contain disconnected decks. Choose by position without joining islands. */
function navLevelAt(Ls, p) {
  var best = -1, bd = Infinity;
  Ls.forEach(function (L, k) {
    if (p[2] < L.zr[0] || p[2] > L.zr[1]) return;
    var i = navSnap(L.N, p, 5); if (i < 0) return;
    var q = navPos(L.N, i), dz = Math.abs(q[2] - p[2]);
    if (dz > 3) return;
    var d = Math.pow(q[0]-p[0],2)+Math.pow(q[1]-p[1],2)+dz*8;
    if (d < bd) { bd = d; best = k; }
  });
  return best;
}
function navCell(N, p) {''')
    out=ROOT/'nav_candidate';out.mkdir(exist_ok=True)
    (out/'42_hands_candidate.js').write_text(after,encoding='utf-8')
    (out/'42_hands.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/js/42_hands.js',tofile='b/js/42_hands.js')),encoding='utf-8')
    (out/'source.json').write_text(json.dumps({'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'scope':'isolated fixture only; same-height external decks split only when a ladder endpoint needs a separate component'},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
