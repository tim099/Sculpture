async () => {
  await __game.loadHull('galea');
  FLEET_DBG = [{team:'blue',hull:'galea'}];
  flowMode('pve');
  flowPause(true);
  reset();
  const sh = SHIPS[0], deck = sh.decks[0], key = deckId(deck);
  const G = deckGrid(sh.T, deck);
  const poss = [];
  for (let x=0; x<G.nx; x++) for (let y=0; y<G.ny; y++) {
    if (G.x0+x*5 < 397 || G.x0+x*5 > 463) continue;
    const item = {it:'keg',x,y,r:0};
    if (!roomCheck(sh.T,{grid:G},'deck',[item]).items.length) continue;
    poss.push(item);
  }
  function reach(s) {
    return s.guns.map(g => {
      const st=stationPick(s,g.deck,g);
      if (!st) return false;
      const li=lvAt(s,st.at), N=s.nav?.levels[li]?.N;
      if (!N) return false;
      const a=navSnap(N,st.at,4), b=navSnap(N,g.drop,4);
      return a>=0 && b>=0 && Boolean(navPath(N,a,b));
    });
  }
  let best={hits:-1};
  const test = items => {
    SHIP_ROOMS.galea={[key]:{type:'deck',items}};
    reset();
    const boat=SHIPS[0], reachable=reach(boat), hits=reachable.filter(Boolean).length;
    const bestDistance=Math.max(...boat.guns.map(g=>{
      const st=stationPick(boat,g.deck,g);
      return st ? Math.hypot(g.drop[0]-st.at[0],g.drop[1]-st.at[1])*.1 : Infinity;
    }));
    const missing = boat.guns.reduce((n,g)=>n+g.crewFull-g.spots.length,0);
    if (hits>best.hits || (hits===best.hits && (missing<best.missing || (missing===best.missing && bestDistance<best.bestDistance))))
      best={hits,missing,bestDistance,reachable,items,stations:boat.stations.map(st=>st.at)};
    return hits===5 && missing===0;
  };
  const baseline = reach(sh);
  const result = () => ({baseline, best, poss, key, base:[G.x0,G.y0]});
  for (const item of poss) if(test([item])) return result();
  for (let i=0;i<poss.length;i++) for (let j=i+1;j<poss.length;j++) {
    const items=[poss[i],poss[j]], checked=roomCheck(sh.T,{grid:G},'deck',items);
    if (checked.items.length===2 && test(items)) return result();
  }
  return result();
}
