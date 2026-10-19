const fs=require('fs'),vm=require('vm'),assert=require('assert');
const root=process.argv[2], rig=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const C={console, Math, Float32Array,Float64Array,Uint8Array,Int8Array,Uint16Array,Int16Array,Int32Array,Map,Set,Array,JSON,Number, G:9.81,S:0.1,Q:{get:()=>null}};
vm.createContext(C);
vm.runInContext(`function sub(a,b){return a.map((v,i)=>v-b[i]);} function len(a){return Math.hypot(...a);} function norm(a){let n=len(a)||1;return a.map(v=>v/n);} function dot(a,b){return a.reduce((s,v,i)=>s+v*b[i],0);} function isFlag(){return false;} function sailRope(r,s){return r.meta&&r.meta.sail===s;} function anchorNear(){return -1;} function segDist2(p,ax,ay,az,bx,by,bz){let a=[ax,ay,az],b=[bx,by,bz],v=sub(b,a),w=sub(p,a),t=Math.max(0,Math.min(1,dot(w,v)/(dot(v,v)||1)));return dot(sub(w,v.map(x=>x*t)),sub(w,v.map(x=>x*t)));} function rotZ(P,piv,a){let c=Math.cos(a),s=Math.sin(a),x=P[0]-piv[0],y=P[1]-piv[1];return [piv[0]+x*c-y*s,piv[1]+x*s+y*c,P[2]];}`,C);
for(const f of ['30_rig_physics.js','29_sailrecipe.js']) vm.runInContext(fs.readFileSync(root+'/src/js/'+f,'utf8'),C);
C.SAILR_SEC=0;
function run(bind,angle){
 const H={rig:structuredClone(rig)};const s=H.rig.sails.find(s=>s.name==='mizzen-lateen');s.recipe.bind=bind;
 const g=C.sailFromRecipe(s.recipe,[]);Object.assign(s,g);
 const T=C.clothTemplate(H,s);const c={T};C.clothInit(c);
 const sh={models:H.rig.models.map(m=>({piv:m.points.pivot||m.points.jaws||[205.5,120.5,0],rot:angle,meta:m.meta})),yards:[]};sh.yards=sh.models.filter(m=>m.meta&&m.meta.kind==='yard');C.clothBrace(sh,c);C.yardPins(sh,c);
 const res=s.recipe.res,edge=[];let idx=0;
 for(let row=0;row<=res;row++)for(let col=0;col<=res-row;col++,idx++)if(col===0&&row>0&&row<res)edge.push(idx);
 let immobile=edge.filter(i=>T.sim.hk[i]&&T.sim.yk[i]<0).length;
 let maxGap=0;
 for(const i of edge){const o=i*3,ref=C.rotZ(Array.from(T.sim.p0.slice(o,o+3)),[205.5,120.5,0],angle);maxGap=Math.max(maxGap,Math.hypot(c.p[o]-ref[0],c.p[o+1]-ref[1]));}
 const corners=s.cornerIdx.map(i=>({i,hk:T.sim.hk[i],yard:T.sim.yk[i]}));
 return {bind,angle,immobileInteriorPins:immobile,maxGapToRotatedFootCells:maxGap,corners};
}
const out={before:run([0,2],0.7),after:run([0],0.7)};
assert.equal(out.before.immobileInteriorPins,15);assert.equal(out.after.immobileInteriorPins,0);assert(out.before.maxGapToRotatedFootCells>40);assert(out.after.maxGapToRotatedFootCells<0.0001);assert(out.after.corners.every(c=>c.hk===4&&c.yard>=0));
console.log(JSON.stringify(out,null,2));
