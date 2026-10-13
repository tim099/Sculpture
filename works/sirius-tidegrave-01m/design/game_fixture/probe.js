
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
