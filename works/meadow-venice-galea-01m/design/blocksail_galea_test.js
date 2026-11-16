/* Run with the actual Blocksail battle page and debug=1, after loadHull. */
async ({layout, timber, oarCells}) => {
  await __game.loadHull('galea');
  FLEET_DBG = [{team: 'blue', hull: 'galea'}];
  flowMode('pve');
  WIND_FIX = {rot:90, s0:1};
  reset();
  uiAway();
  flowRun(true);
  flowPause(true);
  SAIL = 'manual';
  const sh = SHIPS[0];
  const round = (x, n = 3) => +x.toFixed(n);
  const onBoard = sh.crew.filter(c => c.role === ROLE.OAR);
  const oars = sh.drive.P.filter(p => p.kind === 'oar');
  const cells = new Set(timber);
  const keyed = (x, y, z) => Math.floor(x) + 560 * (Math.floor(y) + 321 * Math.floor(z));
  const links = new Map(layout.map(r => [r.name, r]));
  const byOar = new Map(oars.map(p => [p.m, []]));
  onBoard.forEach(c => byOar.get(c.oar).push(c));
  const starts = onBoard.map(c => c.pos.slice());
  const oarData = oars.map(({m, sg}) => {
    const key = m.name.split('/').pop();
    const row = links.get(key);
    if (!row) throw Error('Missing design row for ' + m.name);
    if (m.pts.pivot.some((v, i) => Math.abs(v - row.pivot[i]) > .01))
      throw Error('Pivot mismatch ' + key + ': ' + m.pts.pivot);
    const people = byOar.get(m);
    if (people.length !== 4) throw Error('Wrong crew count ' + key + ': ' + people.length);
    const local = oarCells.map(([x,y,z]) => [
      x + .5 - 6.5 + row.pivot[0] - m.origin[0],
      sg * (y + .5 - 30.5) + row.pivot[1] - m.origin[1],
      z + .5 - 23.5 + row.pivot[2] - m.origin[2]
    ]);
    const blade = m.pts.blade.map((v,i) => v - m.origin[i]);
    return {m, people, local, blade, sg};
  });
  const offsets = [[0,0,0]];
  // The centers and eight points just inside each cube, transformed by the render matrix.
  for (const x of [-.49,.49]) for (const y of [-.49,.49]) for (const z of [-.49,.49])
    offsets.push([x,y,z]);
  function state() {
    return {t:round(SIMT), pos:[round(sh.px),round(sh.pz)], yaw:sh.yaw,
      knots:round(sh.spd * 1.9438), sinkM:round(sh.sink || 0), oarPower:sh.drive.kind,
      oarCap:round(sh.drive.cap), rudder:round(sh.rudder), afloat:!sh.sunk && !(sh.grnd && sh.grnd.on),
      sails:sh.sails.filter(s=>!s.flag && !s.dead && !s.furled).length,
      flags:sh.sails.filter(s=>s.flag && s.meta && s.meta.nation === 'venice' && !s.dead).length,
      sideFraction:sh.drive.sideF?.map(v => round(v))};
  }
  function leg(label, sec, tele, sails, turn) {
    teleSet(sh,tele);
    setSails(sh,sails);
    KEYS.l = turn > 0;
    KEYS.r = turn < 0;
    const initial = state(), phases = [new Set(), new Set()];
    const info = { label, initial, solidHits:0, hitExample:null, crewBadTicks:0,
      fixedSeatShift:0, crewPairsBelow42cm:0, minCrewGapM:Infinity, visibleFrames:[], torsoProbeTicks:0, torsoExample:null, minOwnShaftToFixedRootM:Infinity,
      bothWays:false, minTipSeaM:Infinity, maxTipSeaM:-Infinity, checkedPoints:0 };
    const seen = new Set();
    let wind = __game.wind();
    let prev = sh.drive.ophS.slice(), wraps = [0,0], travel = 0, maxKnots = -Infinity;
    let last = initial.pos;
    for (let i=0; i<Math.round(sec / DT); i++) {
      simStep();
      const st = state();
      travel += Math.hypot(st.pos[0] - last[0], st.pos[1] - last[1]);
      last = st.pos;
      maxKnots = Math.max(maxKnots,st.knots);
      sh.drive.ophS.forEach((ph,j) => {
        phases[j].add(Math.floor(ph*72));
        let delta = ph - prev[j];
        if (delta > .5) delta -= 1;
        if (delta < -.5) delta += 1;
        wraps[j] += delta;
      });
      prev = sh.drive.ophS.slice();
      const side = sh.drive.sideF;
      info.bothWays ||= !!side && side[0]*side[1] < 0;
      if (oarData.some(r => r.people.some(c => c.st !== 0 || c.walk || c.oar !== r.m)))
        info.crewBadTicks++;
      if (i % 3 !== 0) continue;
      for (const row of oarData) {
        const {m, local, blade} = row;
        if (!m.swM) throw Error('Oar transform not running ' + m.name);
        const mat = modelLocal(m);
        const tip = M4.pt(mat,...blade);
        const h = M4.pt(sh.M,...tip)[1];
        info.minTipSeaM = Math.min(info.minTipSeaM,h);
        info.maxTipSeaM = Math.max(info.maxTipSeaM,h);
        for (const v of local) for (const off of offsets) {
          const t = M4.pt(mat,v[0]+off[0],v[1]+off[1],v[2]+off[2]);
          if (cells.has(keyed(...t))) {
            info.solidHits++;
            info.hitExample ||= {name:m.name, phase:m.oph, point:t};
          }
          info.checkedPoints++;
        }
        row.people.forEach(c => seen.add(crewFrame(sh,c)));
        for (const c of row.people) {
          const p = c.pos;
          let min = Infinity;
          for (const v of local.slice(0,30)) {
            const t = M4.pt(mat,...v);
            if (t[2]-p[2] >= 5.5 && t[2]-p[2] <= 13.5)
              min = Math.min(min, Math.hypot(t[0]-p[0], t[1]-p[1])*.1);
          }
          info.minOwnShaftToFixedRootM = Math.min(info.minOwnShaftToFixedRootM,min);
          if (min < .21) {
            info.torsoProbeTicks++;
            info.torsoExample ||= {oar:m.name, phase:m.oph, root:p.slice(), distanceM:round(min)};
          }
        }
      }
      for (let a=0; a<onBoard.length; a++) {
        const p = onBoard[a].pos, old = starts[a];
        info.fixedSeatShift = Math.max(info.fixedSeatShift,Math.hypot(p[0]-old[0],p[1]-old[1],p[2]-old[2]));
        for (let b=0; b<a; b++) {
          const q = onBoard[b].pos;
          const dist = Math.hypot(p[0]-q[0],p[1]-q[1])*.1;
          info.minCrewGapM = Math.min(info.minCrewGapM,dist);
          if (dist < .42) info.crewPairsBelow42cm++;
        }
      }
    }
    info.wind = wind;
    info.phaseBins72 = phases.map(p=>p.size);
    info.cycles = wraps.map(v=>round(v));
    info.visibleFrames = Array.from(seen).sort();
    info.final = state();
    info.turnDeg = round((info.final.yaw - initial.yaw)*180/Math.PI,2);
    info.travelM = round(travel,2);
    info.maxKnots = maxKnots;
    info.minCrewGapM = round(info.minCrewGapM);
    info.minOwnShaftToFixedRootM = round(info.minOwnShaftToFixedRootM);
    info.minTipSeaM = round(info.minTipSeaM);
    info.maxTipSeaM = round(info.maxTipSeaM);
    return info;
  }
  __game.wind(90, 1);
  const report = {page:document.title, ship:sh.T.name, checksum:sh.T.h.checksum ?? null,
    waterline:sh.T.zw, dt:DT, crew:onBoard.length, oars:oars.length, sailArtCols:CREW_COLS,
    roles:{draw:'crewFrame and drawCrew; oar crew are fixed-root sprites with two work frames',
           probe:'oar cube center and 8 near-corners every third engine tick, against exported timber'},
    legs:[]};
  report.legs.push(leg('straight_furled',12,0,0,0));
  window.galeaCam = (dist=65, pitch=.45, x=258) => {
    let s = SHIPS[0];
    __game.cam({mode:0, track:false, yaw:s.yaw+2.55, pitch, dist, tgt:M4.pt(s.M,x,160,34)});
    hudFrame(1);
  };
  galeaCam();
  window.galeaAdvance = count => { for (let j = 0; j < count; j++) simStep(); galeaCam(16,.63,250); };
  window.galeaMore = () => {
    report.legs.push(leg('port_turn_full_sail',12,0,2,1));
    report.legs.push(leg('starboard_turn_half_power',8,1,1,-1));
    report.legs.push(leg('reverse_furled',24,8,0,0));
    KEYS.l = KEYS.r = false;
    if (onBoard.length !== 196 || oars.length !== 49 || report.legs.some(r =>
        r.crewBadTicks || r.solidHits || r.visibleFrames.length !== 2 || !r.final.afloat))
      throw Error("Trial regression: " + JSON.stringify(report));
    if (!(report.legs[1].bothWays && report.legs[2].bothWays && report.legs.at(-1).final.knots < 0))
      throw Error("Missing differential turn or reverse motion");
    return report;
  };
  return report;
}
