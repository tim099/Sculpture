"""Build a LOCAL test copy of the current game. Never modify ame's game sources.
The first embedded hull is replaced solely in this fixture for runtime validation.
"""
import re,json,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent
GAME=Path('D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside')
VXK=ROOT.parent.parent/(ROOT.parent.name+'-assembly')/'exports'/'tidegrave_preview.vxk'
def main():
    fixture=ROOT/'game_fixture';fixture.mkdir(exist_ok=True)
    template=(GAME/'template.html').read_text(encoding='utf-8')
    template=template.replace('<head>', '''<head><script>window.addEventListener('error',function(e){var p=document.createElement('pre');p.id='fixture-error';p.textContent=e.message+' '+e.filename+':'+e.lineno;document.documentElement.appendChild(p);});</script>''')
    def paths(m):return 'src="'+str((GAME/m.group(1)).resolve()).replace('\\','/')+'"'
    template=re.sub(r'src="([^"]+)"',paths,template)
    template=re.sub(r'(<script type="application/x-vxk" id="ship" src=")[^"]+("\s*>)',lambda m:m[1]+str(VXK).replace('\\','/')+m[2],template)
    hull=(GAME/'js/05_hull.js').read_text(encoding='utf-8')
    hull=hull.replace("{ id: 'constitution', el: 'ship', name: '憲法號' }","{ id: 'constitution', el: 'ship', name: '潮墓號', geo: { spar:[114,140], marines:[180,215], center:155, aim:90, aimZ:[30,480], deckAim:[74,106], rigAim:[210,410], handsK:1 } }")
    (fixture/'05_hull_fixture.js').write_text(hull,encoding='utf-8')
    template=template.replace(str((GAME/'js/05_hull.js').resolve()).replace('\\','/'),str(fixture/'05_hull_fixture.js').replace('\\','/'))
    probe="""
var fixtureProbe = setInterval(function () {
  if (!window.__vxk || !window.__vxk.demo) return;
  clearInterval(fixtureProbe);
  var out = {gameVerify: window.__vxk.verify, glError:gl.getError(), simt:SIMT,
    ships:SHIPS.map(function(s){return {name:s.T.name,voxels:s.T.base.count, waterline:s.T.zw,
      mass:s.mass0, designDisplacement:s.T.disp, lift:s.lift, sink:s.sink,
      masts:s.masts.length, sails:s.sails.length, models:s.models.length,
      crew:s.crew.length, helms:s.crew.filter(function(c){return c.role===ROLE.HELM;}).length,
      mags:s.mags.map(function(m){return {name:m.name,lb:m.lb,kegs:m.kegs.length};}),
      ladders:s.nav?s.nav.ladders.length:0, ladderNames:s.nav?s.nav.ladders.map(function(l){return l.name;}):[],
      guns:s.guns.map(function(g){return {name:g.name,type:g.type,spots:g.spots.length,min:g.crewMin,alive:g.alive};}),
      modelsWithNoFoot:s.models.filter(function(m){return m.foot<0;}).map(function(m){return m.path;})};})};
  var pre=document.createElement('pre');pre.id='tidegrave-fixture-report';pre.textContent=JSON.stringify(out);document.body.appendChild(pre);
}, 50);
"""
    (fixture/'probe.js').write_text(probe,encoding='utf-8')
    template=template.replace('</body>',f'<script src="{str(fixture/"probe.js").replace(chr(92),"/")}" data-bundle="game"></script>\n</body>')
    src=fixture/'template.html';src.write_text(template,encoding='utf-8')
    out=fixture/'tidegrave_game_test.html'
    r=subprocess.run([sys.executable,'-X','utf8','D:/Unity/Valhalla/ArtGallery/VoxelKit/vxk_inline.py',str(src),str(out)],capture_output=True,encoding='utf-8')
    (fixture/'inline.log').write_text(r.stdout+r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    chrome='C:/Program Files/Google/Chrome/Application/chrome.exe'
    url=out.as_uri()+'?demo=0&debug=1&dump=1&seed=7&still=1'
    args=[chrome,'--headless=new','--no-sandbox','--disable-extensions','--disable-gpu-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--allow-file-access-from-files','--disable-background-networking','--virtual-time-budget=60000','--dump-dom','--user-data-dir='+str(fixture/('chrome_profile_'+uuid.uuid4().hex[:8])),url]
    r=subprocess.run(args,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
    html=r.stdout.decode('utf-8','replace');(fixture/'runtime_dom.html').write_text(html,encoding='utf-8');(fixture/'chrome.log').write_bytes(r.stderr)
    m=re.search(r'<pre id="tidegrave-fixture-report">(.*?)</pre>',html,re.S)
    if not m:raise RuntimeError('No fixture report. Inspect runtime_dom.html and chrome.log')
    import html as htmllib
    report=json.loads(htmllib.unescape(m[1]));(ROOT/'verify_game_runtime.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for ship in report['ships']:
        bad=[g for g in ship['guns'] if g['spots']<g['min']]
        print(json.dumps({'name':ship['name'],'crew':ship['crew'],'helms':ship['helms'],'ladders':ship['ladders'],'masts':ship['masts'],'mass':ship['mass'],'designDisplacement':ship['designDisplacement'],'gun_shortfalls':bad,'modelsWithNoFoot':ship['modelsWithNoFoot']},ensure_ascii=False))
if __name__=='__main__':main()
