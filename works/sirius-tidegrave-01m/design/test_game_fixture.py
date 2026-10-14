"""Build a LOCAL test copy of the current game. Never modify ame's game sources.
The first embedded hull is replaced solely in this fixture for runtime validation.
"""
import re,json,subprocess,sys,uuid,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
GAME=Path('D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside')
VXK=ROOT.parent.parent/(ROOT.parent.name+'-assembly')/'exports'/'tidegrave_preview.vxk'
def main():
    seconds=float(sys.argv[1]) if len(sys.argv)>1 else 0
    nav_candidate=len(sys.argv)>2 and sys.argv[2]=='nav'
    if not 0<=seconds<=60:raise ValueError('Runtime seconds must be 0..60')
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
    main_js=(GAME/'js/90_main.js').read_text(encoding='utf-8')
    old_raf='if (!noRaf) requestAnimationFrame(frame);'
    if main_js.count(old_raf)!=1:raise RuntimeError('Game RAF source changed')
    main_js=main_js.replace(old_raf,'if (!noRaf && !window.__fixtureDone) requestAnimationFrame(frame);')
    (fixture/'90_main_fixture.js').write_text(main_js,encoding='utf-8')
    template=template.replace(str((GAME/'js/90_main.js').resolve()).replace('\\','/'),str(fixture/'90_main_fixture.js').replace('\\','/'))
    if nav_candidate:
        template=template.replace(str((GAME/'js/42_hands.js').resolve()).replace('\\','/'),str(ROOT/'nav_candidate/42_hands_candidate.js').replace('\\','/'))
    probe="""
var fixtureProbe = setInterval(function () {
  if (!window.__vxk || !window.__vxk.demo) return;
  clearInterval(fixtureProbe);
  window.__fixtureDone=true;
  var out = {gameVerify: window.__vxk.verify, glError:gl.getError(), simt:SIMT,
    ships:SHIPS.map(function(s){return {name:s.T.name,voxels:s.T.base.count, waterline:s.T.zw,
      mass:s.mass0, designDisplacement:s.T.disp, lift:s.lift, sink:s.sink,
      masts:s.masts.length, sails:s.sails.length, models:s.models.length,
      crew:s.crew.length, helms:s.crew.filter(function(c){return c.role===ROLE.HELM;}).length,
      mags:s.mags.map(function(m){return {name:m.name,lb:m.lb,kegs:m.kegs.length};}),
      ladders:s.nav?s.nav.ladders.length:0, ladderNames:s.nav?s.nav.ladders.map(function(l){return l.name;}):[],
      guns:s.guns.map(function(g){return {name:g.name,type:g.type,spots:g.spots.length,min:g.crewMin,alive:g.alive};}),
      modelsWithNoFoot:s.models.filter(function(m){return m.foot<0;}).map(function(m){return m.path;}),
      navigation:window.__game.hands(s.i),
      ladderCandidates:shipLadders(s.T).map(function(l){
        var H=s.nav,a=l.pts[0],b=l.pts[l.pts.length-1],la=H?(typeof navLevelAt==='function'?navLevelAt(H.levels,a):lvOf(H.levels,a[2])):-1,lb=H?(typeof navLevelAt==='function'?navLevelAt(H.levels,b):lvOf(H.levels,b[2])):-1;
        return {name:l.name,pts:l.pts,from:la,to:lb,
          snapFrom:la>=0?navSnap(H.levels[la].N,a,5):-1,snapTo:lb>=0?navSnap(H.levels[lb].N,b,5):-1};
      })};})};
  if (FIXTURE_SECONDS>0) {
    out.shortRun={requestedSeconds:FIXTURE_SECONDS,stats:window.__game.run(FIXTURE_SECONDS),
      hands:SHIPS.map(function(s){return window.__game.hands(s.i);}), glError:gl.getError()};
  }
  var pre=document.createElement('pre');pre.id='tidegrave-fixture-report';pre.textContent=JSON.stringify(out);document.body.appendChild(pre);
}, 50);
"""
    probe=probe.replace('FIXTURE_SECONDS',str(seconds))
    (fixture/'probe.js').write_text(probe,encoding='utf-8')
    template=template.replace('</body>',f'<script src="{str(fixture/"probe.js").replace(chr(92),"/")}" data-bundle="game"></script>\n</body>')
    src=fixture/'template.html';src.write_text(template,encoding='utf-8')
    out=fixture/'tidegrave_game_test.html'
    r=subprocess.run([sys.executable,'-X','utf8','D:/Unity/Valhalla/ArtGallery/VoxelKit/vxk_inline.py',str(src),str(out)],capture_output=True,encoding='utf-8')
    (fixture/'inline.log').write_text(r.stdout+r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    chrome='C:/Program Files/Google/Chrome/Application/chrome.exe'
    url=out.as_uri()+'?demo=0&debug=1&dump=1&seed=7&still=1'
    args=[chrome,'--headless=new','--no-sandbox','--disable-extensions','--disable-gpu-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--allow-file-access-from-files','--disable-background-networking','--virtual-time-budget=10000','--dump-dom','--user-data-dir='+str(fixture/('chrome_profile_'+uuid.uuid4().hex[:8])),url]
    r=subprocess.run(args,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
    html=r.stdout.decode('utf-8','replace');(fixture/'runtime_dom.html').write_text(html,encoding='utf-8');(fixture/'chrome.log').write_bytes(r.stderr)
    m=re.search(r'<pre id="tidegrave-fixture-report">(.*?)</pre>',html,re.S)
    if not m:raise RuntimeError('No fixture report. Inspect runtime_dom.html and chrome.log')
    import html as htmllib
    report=json.loads(htmllib.unescape(m[1]))
    report['observedAtUtc']=datetime.now(timezone.utc).isoformat()
    report['navigationCandidate']=nav_candidate
    report['sources']={'vxkSha256':hashlib.sha256(VXK.read_bytes()).hexdigest(),
      'fixtureSha256':hashlib.sha256(out.read_bytes()).hexdigest(),
      'gameJsSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((GAME/'js').glob('*.js'))}}
    errors=[]
    if not report.get('gameVerify',{}).get('ok'):errors.append('VXK verify failed')
    if report.get('glError')!=0:errors.append('GL error at load')
    if len(report.get('ships',[]))!=2:errors.append('Expected two ships')
    for ship in report['ships']:
        if len(ship['guns'])!=54:errors.append('Expected 54 guns: '+ship['name'])
        if any(g['spots']<g['min'] for g in ship['guns']):errors.append('Gun crew shortfall: '+ship['name'])
        if ship['modelsWithNoFoot']:errors.append('Unsupported models: '+ship['name'])
        if nav_candidate and ship['ladders']!=7:errors.append('Expected seven usable ladders: '+ship['name'])
    if seconds and (report['shortRun']['stats']['t']<seconds or report['shortRun']['glError']!=0):errors.append('Short run did not complete cleanly')
    report['assertions']={'passed':not errors,'errors':errors}
    (ROOT/('verify_game_nav_candidate.json' if nav_candidate and seconds else 'verify_game_nav_load.json' if nav_candidate else 'verify_game_short_run.json' if seconds else 'verify_game_runtime.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for ship in report['ships']:
        bad=[g for g in ship['guns'] if g['spots']<g['min']]
        print(json.dumps({'name':ship['name'],'crew':ship['crew'],'helms':ship['helms'],'ladders':ship['ladders'],'masts':ship['masts'],'mass':ship['mass'],'designDisplacement':ship['designDisplacement'],'gun_shortfalls':bad,'modelsWithNoFoot':ship['modelsWithNoFoot']},ensure_ascii=False))
    if errors:raise RuntimeError('; '.join(errors))
if __name__=='__main__':main()
