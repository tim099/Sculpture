() => {
  const r = n => Number.isFinite(n) ? +n.toFixed(4) : null;
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const sh = () => SHIPS[PLAYER_I];
  const pos = () => {const p = shipCenter(sh()); return [p[0],p[2]];};
  const dist = (a,b) => Math.hypot(a[0]-b[0],a[1]-b[1]);
  const stages = {}, errors = [];
  const finishedGround = new Set();
  function snapshot() {
    const s = sh(), T = s.T, center = pos(), A = anchorsOf(s);
    const K = groundKeel(T).map(([x,z]) => M4.pt(s.M,x,T.cy,z));
    return {t:r(SIMT), pos:center.map(r), speed:r(Math.hypot(s.vel[0], s.vel[2])), forward:r(s.spd),
      waterDepth:r(-bedHgt(...center)), draught:r(-Math.min(...K.map(p => p[1]))),
      keelClearance:r(Math.min(...K.map(p => p[1]-bedHgt(p[0],p[2])))),
      lift:r(s.lift), sink:r(s.sink), mode:MODE, sail:SAIL, heading:r((90-s.yaw*180/Math.PI+720)%360),
      anchors:['P','S'].map(k => ({side:k,state:A[k].st,depth:r(A[k].dep),hawse:A[k].hw,model:A[k].m?.meta?.id})),
      held:anchorHeld(s), moor:s.moor && {...s.moor}, grnd:s.grnd, hullLost:s.orig-s.grid.count,
      groundLoss:s.grndLost||0, quay:s.quayHit||null, sunk:!!s.sunk
    };
  }
  function run(seconds, enough) {
    const start = SIMT;
    let minimum = Infinity, maximumSpeed = 0, ground = 0, quay = 0, frame = 0, first = null, last = null;
    while (SIMT - start < seconds) {
      simStep();
      const s = sh();
      if (s.grnd) ground++;
      if (s.quayHit) quay++;
      if (frame++ % 15 === 0) {
        const m = snapshot();
        minimum = Math.min(minimum,m.keelClearance);
        maximumSpeed = Math.max(maximumSpeed,m.speed);
        first ??= m;
        last = m;
      }
      if (enough && enough()) break;
    }
    return {duration:r(SIMT-start), minimumClearance:r(minimum), maximumSpeed:r(maximumSpeed), groundFrames:ground, quayFrames:quay, first, last, end:snapshot()};
  }
  function view(distance, az, elevation) {
    const s = sh(), c = shipCenter(s);
    window.__game.cam({mode:0,track:false,tgt:c,dist:distance,pitch:elevation,yaw:az});
    hudFrame(1);
  }
  function finishNearbyGround(dock) {
    const town = TOWNS.list.find(t=>t.id===dock.town);
    const size = TOWN_GT_SZ;
    const x = dock.at[0]+BED.ax, z = dock.at[1]+BED.az;
    const rows = [];
    for (const [key,tile] of Object.entries(town.gt || {})) {
      const [kx,kz] = key.split('_').map(Number);
      const dx = Math.max(kx*size-x,0,x-(kx+1)*size);
      const dz = Math.max(kz*size-z,0,z-(kz+1)*size);
      if (Math.hypot(dx,dz)>DOCK_NEAR) continue;
      if (tile.dirty || tile.job || (!tile.g && !finishedGround.has(key))) {
        // Use the engine's synchronous wrapper for the same ground generator.
        tile.job = null;
        tile.dirty = false;
        townGroundTile(town,tile);
        finishedGround.add(key);
      }
      rows.push({key,mesh:!!tile.g,dirty:!!tile.dirty,triangles:(tile.tri||[]).length,pier:(tile.pier||[]).length});
    }
    return rows;
  }
  return {
    async ready() {
      const begin = performance.now();
      let nearbyGround = [];
      while (performance.now()-begin < 125000) {
        if (RUNNING && MODE==='sail' && sh()?.T?.id==='galea' && BED?.A) {
          if (!PAUSED) flowPause(true);
          if (sh().cfg.base>0) teleSet(sh(),4);
        }
        let trial = dockReady();
        if (trial.wait && trial.why === '停靠處附近的地面還在建') {
          nearbyGround = finishNearbyGround(trial.wait);
          trial = dockReady();
          if (!trial.dock && nearbyGround.some(t=>!t.mesh && !t.dirty)) throw new Error(JSON.stringify({dock:trial,ground:nearbyGround}));
        }
        if (RUNNING && MODE === 'sail' && trial.dock && -bedHgt(...pos()) > 2 && sh()?.T?.id === 'galea') {
          flowPause(true);
          const s = sh(), T = s.T, w = shipT(s), K = groundKeel(T);
          const light = w-T.cargoT, h = (T.zw-Math.min(...K.map(k=>k[1])))*S;
          const mass = {fullT:r(w), standardT:r(light), fixedBallastT:r(s.cfg.ballast-T.cargoT), cargoT:T.cargoT,
            cargoWant:T.cargoWant, cargoShort:T.cargoShort, configBallastT:s.cfg.ballast, hydroDesignT:r(T.disp),
            draughtFull:r(h-liftFor(T,T.disp-w)), draughtStandard:r(h-liftFor(T,T.disp-light)), voxelM:S};
          stages.load = {model:'cargo replaces an equal mass of removable ballast at the game full-load weight',mass,initial:snapshot()};
          stages.harbour = {id:trial.dock.id,town:trial.dock.town,chartedDepth:trial.dock.depth,nearbyGround,
            berthHeading:trial.dock.hdg,path:trial.dock.path,loadedTown:TOWNS.list.filter(t=>t.id===trial.dock.town).map(t=>({id:t.id,groundTiles:Object.keys(t.gt||{}).length,buildingsLoaded:!!t.inst}))};
          return {load:stages.load,harbour:stages.harbour};
        }
        await sleep(700);
      }
      throw new Error(JSON.stringify({running:RUNNING,mode:MODE,ready:dockReady(),towns:TOWNS.list.map(t=>({id:t.id,inst:!!t.inst,gt:!!t.gt})), bed:!!BED, t:SIMT, ship:sh()?.T?.id,host:parent.hostState}));
    },
    anchor() {
      const s = sh();
      setSailMode('manual');
      setSails(s,0);
      if (s.cfg.base>0) teleSet(s,2);
      stages.sail = run(32,() => Math.abs(s.spd)>=1.5);
      const before = snapshot();
      doAct('ancAll');
      const down = run(25,()=>anchorsOf(s).P.st==='down' && anchorsOf(s).S.st==='down');
      const slowing = run(65,()=>Math.hypot(s.vel[0],s.vel[2])<.025 && Math.abs(s.spd)<.025);
      const hold = run(15);
      const drift = dist(hold.first.pos,hold.end.pos);
      stages.anchor = {before,down,slowing,hold,drift:r(drift),stoppingDistance:r(dist(before.pos,hold.end.pos))};
      if (before.speed<0.5) errors.push('anchor drop began below 0.5 m/s');
      if (!hold.end.held || hold.end.anchors.some(a=>a.state!=='down'||!a.hawse)
        || hold.end.speed>.10 || drift>1 || hold.groundFrames || hold.quayFrames) errors.push('anchor hold');
      view(78,3.7,.46);
      return {before,down:down.end,stop:hold.end,drift:r(drift),errors};
    },
    dock() {
      const s = sh();
      teleSet(s,4);
      doAct('ancAll');
      const weigh = run(20,()=>anchorsOf(s).P.st==='up' && anchorsOf(s).S.st==='up');
      stages.weigh = weigh;
      if (weigh.end.held || weigh.end.anchors.some(a=>a.state!=='up')) errors.push('weigh both anchors');
      const eligible = dockReady(), before = snapshot();
      if (!eligible.dock) {
        errors.push('dock readiness: '+eligible.why);
        return {ok:false,errors,stages};
      }
      dockAct();
      stages.dock = {before,pathMeters:DOCK.run?.L,usesGameApproach:!!DOCK.run?.anim};
      const approach = run(100,()=>!!s.moor || !DOCK.run);
      const settling = run(4);
      const after = run(15), final = after.end, m = final.moor;
      const alignment = m ? Math.abs(Math.atan2(Math.sin(s.yaw-m.yaw),Math.cos(s.yaw-m.yaw))*180/Math.PI) : null;
      const berthError = m ? dist(final.pos,[m.x,m.z]) : null;
      const drift = dist(after.first.pos,final.pos);
      Object.assign(stages.dock,{approach,settling,after,result:DOCK.last?.why,alignment:r(alignment),berthError:r(berthError),drift:r(drift)});
      if (!stages.dock.usesGameApproach || final.mode!=='town' || m?.dock!==stages.harbour.id || DOCK.last?.why!=='停好了'
        || final.speed>.10 || berthError>.25 || drift>.25 || approach.groundFrames || after.groundFrames
        || final.groundLoss || final.sunk) errors.push('docking or mooring');
      const initial = stages.load.initial;
      if (initial.keelClearance<=0 || stages.load.mass.cargoT<=0 || final.sink>.10) errors.push('loaded displacement');
      if (TWB.on) twbToggle(false);
      view(94,3.7,.61);
      return {ok:errors.length===0,errors,stages,host:parent.hostState,generator:parent.hostStats()};
    }
  };
}
