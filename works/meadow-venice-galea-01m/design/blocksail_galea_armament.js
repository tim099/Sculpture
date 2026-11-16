/* Browser probe executed inside Blocksail's compiled game scope. */
async () => {
  await __game.loadHull('galea');
  FLEET_DBG = [{team:'blue', hull:'galea'}];
  flowMode('pve');
  WIND_FIX = {rot:90, s0:.3};
  reset();
  uiAway();
  flowRun(true);
  flowPause(true);
  SAIL = 'manual';
  const sh = SHIPS[0];
  teleSet(sh,4);
  setSails(sh,0);
  const n = v => +v.toFixed(3);
  const rows = sh.guns.map(g => ({
    name:g.model.name || g.model.path, path:g.model.path, type:g.type, axis:g.ax, muzzle:g.muz,
    crew:g.spots.length, want:g.crewFull, drop:g.drop, ammoInitial:g.box,
    shots:0, replenished:0, clearedHull:0
  }));
  const report = {
    page:document.title, checksum:sh.T.h.checksum, dt:DT,
    magazine:sh.mags.map(m => ({name:m.name,kegs:m.kegs.length})),
    stations:sh.stations.map(st => ({name:st.name,deck:st.deck,pos:st.pos})),
    rowers:sh.crew.filter(c=>c.role===ROLE.OAR).length,
    powderCrew:sh.crew.filter(c=>c.role===ROLE.POWDER).length,
    simulatedSeconds:0, firstVolley:[], guns:rows
  };
  window.galeaGunsReport = report;
  const balls = [];
  const shoot = () => {
    const before = sh.guns.map(g => g.firedAt);
    if (!fireOne(sh,0)) return false;
    const i = sh.guns.findIndex((g,j)=>g.firedAt!==before[j]);
    if (i < 0) throw Error('Shot without matching gun event');
    const projectile = BALLS[BALLS.length-1];
    if (!projectile) throw Error('No projectile for ' + rows[i].name);
    rows[i].shots++;
    balls.push({i, projectile, origin:projectile.p.slice(), started:SIMT});
    return rows[i].name;
  };
  for (let i=0; i<Math.round(3/DT); i++) simStep();
  let fired;
  while ((fired = shoot())) report.firstVolley.push(fired);
  window.galeaGunsCamera = () => {
    __game.cam({mode:0,track:false,yaw:sh.yaw + 1.8,pitch:.45,dist:23,
      tgt:M4.pt(sh.M,432,160,40)});
    hudFrame(1);
  };
  galeaGunsCamera();
  window.galeaContinueFire = () => {
    let ticks = 0;
    while (ticks++ < Math.round(180/DT)) {
      const before = sh.guns.map(g=>g.box);
      simStep();
      sh.guns.forEach((g,i) => { if (g.box > before[i]) rows[i].replenished += g.box-before[i]; });
      for (let j=balls.length-1;j>=0;j--) {
        const b = balls[j], isAlive = BALLS.includes(b.projectile);
        const distance = isAlive ? Math.hypot(...b.projectile.p.map((v,k)=>v-b.origin[k])) : 0;
        if (distance >= 10) {
          rows[b.i].clearedHull++;
          balls.splice(j,1);
        } else if (!isAlive || SIMT-b.started>1) balls.splice(j,1);
      }
      if (ticks%Math.round(.20/DT)===0) {
        while (shoot()) {}
        if (rows.length===5 && balls.length===0 &&
            rows.every(r=>r.shots>r.ammoInitial && r.replenished>0)) break;
      }
    }
    rows.forEach((r,i)=>{ r.ammoFinal = sh.guns[i].box; r.alive = sh.guns[i].alive; });
    report.simulatedSeconds = n(SIMT);
    report.totalFired = sh.fired;
    report.selfHits = sh.hits;
    report.afloat = !sh.sunk;
    report.ok = report.firstVolley.length===5 && rows.every(r=>r.shots>r.ammoInitial &&
        r.replenished>0 && r.clearedHull===r.shots && r.alive) && report.selfHits===0 && report.rowers===196;
    return report;
  };
  return report;
}
