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
    mode=sys.argv[2] if len(sys.argv)>2 else ''
    nav_candidate=mode in ('nav','deck')
    deck_meta=mode in ('meta','deck')
    if not 0<=seconds<=60:raise ValueError('Runtime seconds must be 0..60')
    fixture=ROOT/('game_fixture_deck_meta' if deck_meta else 'game_fixture');fixture.mkdir(exist_ok=True)
    template=(GAME/'template.html').read_text(encoding='utf-8')
    template=template.replace('<head>', '''<head><script>window.addEventListener('error',function(e){var p=document.createElement('pre');p.id='fixture-error';p.textContent=e.message+' '+e.filename+':'+e.lineno;document.documentElement.appendChild(p);});</script>''')
    def paths(m):return 'src="'+str((GAME/m.group(1)).resolve()).replace('\\','/')+'"'
    template=re.sub(r'src="([^"]+)"',paths,template)
    template=re.sub(r'(<script type="application/x-vxk" id="ship" src=")[^"]+("\s*>)',lambda m:m[1]+str(VXK).replace('\\','/')+m[2],template)
    hull=(GAME/'js/05_hull.js').read_text(encoding='utf-8')
    marker='var HULL_KNOWN = CFG.ships.map('
    if hull.count(marker)!=1:raise RuntimeError('Game ship configuration source changed')
    override="""CFG = Object.assign({}, CFG, {ships: CFG.ships.map(function(s) {
  return s.id === 'constitution' ? Object.assign({}, s, {name:'潮墓號',names:['潮墓號'],geo:{spar:[114,140],marines:[180,215],center:155,aim:90,aimZ:[30,480],deckAim:[74,106],rigAim:[210,410]},crew:Object.assign({},s.crew,{handsK:1})}) : s;
})});
"""
    hull=hull.replace(marker,override+marker)
    (fixture/'05_hull_fixture.js').write_text(hull,encoding='utf-8')
    template=template.replace(str((GAME/'js/05_hull.js').resolve()).replace('\\','/'),str(fixture/'05_hull_fixture.js').replace('\\','/'))
    main_js=(GAME/'js/90_main.js').read_text(encoding='utf-8')
    old_raf='if (!noRaf) requestAnimationFrame(frame);'
    if main_js.count(old_raf)!=1:raise RuntimeError('Game RAF source changed')
    main_js=main_js.replace(old_raf,'if (!noRaf && !window.__fixtureDone) requestAnimationFrame(frame);')
    (fixture/'90_main_fixture.js').write_text(main_js,encoding='utf-8')
    template=template.replace(str((GAME/'js/90_main.js').resolve()).replace('\\','/'),str(fixture/'90_main_fixture.js').replace('\\','/'))
    if nav_candidate:
        candidate=ROOT/('nav_deck_candidate' if mode=='deck' else 'nav_candidate')/'42_hands_candidate.js'
        template=template.replace(str((GAME/'js/42_hands.js').resolve()).replace('\\','/'),str(candidate).replace('\\','/'))
        if mode=='deck':
            template=template.replace(str((GAME/'js/40_crew.js').resolve()).replace('\\','/'),str(ROOT/'nav_deck_candidate/40_crew_candidate.js').replace('\\','/'))
    probe="""
function fixtureRoutes(s) {
  if (!s.nav) return [];
  var H=s.nav, home=H.home, reg=H.levels[home].N.big;
  return H.ladders.map(function(l) {
    var queue=H.ladders.map(function(q){return q.q;});
    var a=handRoute(s,home,l.lo,s.T.cx,l.x,reg,l.ra);
    H.ladders.forEach(function(q,i){q.q=queue[i];});
    var b=handRoute(s,home,l.hi,s.T.cx,l.x,reg,l.rb);
    H.ladders.forEach(function(q,i){q.q=queue[i];});
    return {name:l.name,fromDeck:H.levels[l.lo].deck?H.levels[l.lo].deck.path:null,toDeck:H.levels[l.hi].deck?H.levels[l.hi].deck.path:null,
      fromRegion:l.ra,toRegion:l.rb,fromReachable:a!==null,toReachable:b!==null,fromLegs:a? a.length:null,toLegs:b?b.length:null};
  });
}
var fixtureProbe = setInterval(function () {
  if (!window.__vxk || !window.__vxk.demo) return;
  clearInterval(fixtureProbe);
  window.__fixtureDone=true;
  var out = {gameVerify: window.__vxk.verify, glError:gl.getError(), simt:SIMT,
    ships:SHIPS.map(function(s){return {name:s.T.name,voxels:s.T.base.count, waterline:s.T.zw,
      mass:s.mass0, designDisplacement:s.T.disp, lift:s.lift, sink:s.sink,
      masts:s.masts.length, sails:s.sails.length, models:s.models.length,
      crew:s.crew.length, helms:s.crew.filter(function(c){return c.role===ROLE.HELM;}).length,
      helmHomes:s.crew.filter(function(c){return c.role===ROLE.HELM;}).map(function(c){return c.home;}),
      mags:s.mags.map(function(m){return {name:m.name,lb:m.lb,kegs:m.kegs.length};}),
      ladders:s.nav?s.nav.ladders.length:0, ladderNames:s.nav?s.nav.ladders.map(function(l){return l.name;}):[],
      guns:s.guns.map(function(g){return {name:g.name,type:g.type,spots:g.spots.length,min:g.crewMin,alive:g.alive};}),
      modelsWithNoFoot:s.models.filter(function(m){return m.foot<0;}).map(function(m){return m.path;}),
      navigation:window.__game.hands(s.i),
      deckMetadata:hullDecks(s.T),
      fixtureGeo:s.T.geo,
      navLevels:s.nav?s.nav.levels.map(function(l){return {key:l.key,name:l.name,zr:l.zr,deck:l.deck?l.deck.path:null,cells:l.N.cells.length,regions:l.N.regs?l.N.regs:[]};}):[],
      ladderRoutes:fixtureRoutes(s),
      ladderCandidates:shipLadders(s.T).map(function(l){
        var H=s.nav,a=l.pts[0],b=l.pts[l.pts.length-1],la=H?(typeof navLevelAt==='function'?navLevelAt(H.levels,a):lvOf(H.levels,a[2])):-1,lb=H?(typeof navLevelAt==='function'?navLevelAt(H.levels,b):lvOf(H.levels,b[2])):-1;
        return {name:l.name,pts:l.pts,from:la,to:lb,
          snapFrom:la>=0?navSnap(H.levels[la].N,a,5):-1,snapTo:lb>=0?navSnap(H.levels[lb].N,b,5):-1};
      })};})};
  if (FIXTURE_SECONDS>0) {
    out.shortRun={requestedSeconds:FIXTURE_SECONDS,stats:window.__game.run(FIXTURE_SECONDS),
      hands:SHIPS.map(function(s){return window.__game.hands(s.i);}), glError:gl.getError()};
  }
  if (FIXTURE_HELM) {
    var s=SHIPS[0], lost=s.crew.filter(function(c){return c.role===ROLE.HELM && able(c);});
    lost.forEach(function(c){c.st=1;});
    callHands(s);
    var assigned=s.crew.filter(function(c){return c.role===ROLE.HAND && c.hand.job && c.hand.job.kind==='helm';});
    out.helmReplacement={scope:'forced casualty after normal short run, then actual stepHand at 60Hz; world combat frozen during replacement-only probe',victims:lost.length,
      jobs:assigned.map(function(c){var j=c.hand.job;return {level:j.lv,deck:s.nav.levels[j.lv].deck.path,spot:j.spot,legs:c.hand.legs.length};})};
    var ticks=0;
    while(ticks<7200 && assigned.some(function(c){return c.role===ROLE.HAND;})) {
      SIMT+=1/60;s.navN=HAND_PATHS;assigned.forEach(function(c){if(c.role===ROLE.HAND)stepHand(s,c,1/60);});ticks++;
    }
    out.helmReplacement.elapsedSeconds=ticks/60;
    out.helmReplacement.arrivals=assigned.map(function(c){return {role:c.role,pos:c.pos,climbing:!!(c.hand && c.hand.climb),remainingLegs:c.hand?c.hand.legs.length:0};});
  }
  var pre=document.createElement('pre');pre.id='tidegrave-fixture-report';pre.textContent=JSON.stringify(out);document.body.appendChild(pre);
}, 50);
"""
    probe=probe.replace('FIXTURE_SECONDS',str(seconds))
    probe=probe.replace('FIXTURE_HELM','true' if mode=='deck' else 'false')
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
    report['mode']=mode
    report['sources']={'vxkSha256':hashlib.sha256(VXK.read_bytes()).hexdigest(),
      'fixtureSha256':hashlib.sha256(out.read_bytes()).hexdigest(),
      'gameJsSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((GAME/'js').glob('*.js'))}}
    if nav_candidate:report['sources']['candidateJsSha256']=hashlib.sha256(candidate.read_bytes()).hexdigest()
    if mode=='deck':report['sources']['crewCandidateJsSha256']=hashlib.sha256((ROOT/'nav_deck_candidate/40_crew_candidate.js').read_bytes()).hexdigest()
    errors=[]
    if not report.get('gameVerify',{}).get('ok'):errors.append('VXK verify failed')
    if report.get('glError')!=0:errors.append('GL error at load')
    if len(report.get('ships',[]))!=2:errors.append('Expected two ships')
    for ship in report['ships']:
        if len(ship['guns'])!=54:errors.append('Expected 54 guns: '+ship['name'])
        if any(g['spots']<g['min'] for g in ship['guns']):errors.append('Gun crew shortfall: '+ship['name'])
        if ship['modelsWithNoFoot']:errors.append('Unsupported models: '+ship['name'])
        if ship['helms']!=2:errors.append('Expected two helms: '+ship['name'])
        if ship['fixtureGeo'].get('spar')!=[114,140]:errors.append('Fixture ship geometry override missing')
        if deck_meta and len(ship['deckMetadata'])!=6:errors.append('Expected six deck metadata records')
        if nav_candidate and ship['ladders']!=7:errors.append('Expected seven usable ladders: '+ship['name'])
        if mode=='deck' and any(not (l['fromReachable'] and l['toReachable']) for l in ship['ladderRoutes']):errors.append('Ladder region unreachable from home: '+ship['name'])
        if mode=='deck' and any(p[2]!=139 for p in ship['helmHomes']):errors.append('Helms did not spawn on wheel quarter deck')
    if seconds and (report['shortRun']['stats']['t']<seconds or report['shortRun']['glError']!=0):errors.append('Short run did not complete cleanly')
    if mode=='deck' and (report['helmReplacement']['victims']!=2 or len(report['helmReplacement']['jobs'])!=2 or any(j['deck']!='甲板-quarter' for j in report['helmReplacement']['jobs'])):errors.append('Helm replacement dispatch did not select quarter deck')
    if mode=='deck' and any(c['role']!=5 or abs(c['pos'][2]-139)>0.01 for c in report['helmReplacement']['arrivals']):errors.append('Helm replacements did not actually arrive at wheel deck')
    report['assertions']={'passed':not errors,'errors':errors,'scope':'VXK decode/GL, gun crew minima, model support, fixture geometry, two helms; candidate additionally seven ladder links and region reachability'}
    name=('verify_game_deck_meta_'+('candidate' if nav_candidate else 'baseline')+('_run' if seconds else '_load')+'.json') if deck_meta else ('verify_game_nav_candidate.json' if nav_candidate and seconds else 'verify_game_nav_load.json' if nav_candidate else 'verify_game_short_run.json' if seconds else 'verify_game_runtime.json')
    (ROOT/name).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for ship in report['ships']:
        bad=[g for g in ship['guns'] if g['spots']<g['min']]
        print(json.dumps({'name':ship['name'],'crew':ship['crew'],'helms':ship['helms'],'ladders':ship['ladders'],'masts':ship['masts'],'mass':ship['mass'],'designDisplacement':ship['designDisplacement'],'gun_shortfalls':bad,'modelsWithNoFoot':ship['modelsWithNoFoot']},ensure_ascii=False))
    if errors:raise RuntimeError('; '.join(errors))
if __name__=='__main__':main()
