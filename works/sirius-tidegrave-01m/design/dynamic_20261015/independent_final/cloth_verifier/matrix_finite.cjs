const fs=require('fs'),vm=require('vm'),path=require('path');
const {ctx:C,H,m,hashes,funcs,source,file}=require('./pins.cjs'),OUT=process.env.CLOTH_OUT||__dirname,EXTRA=process.argv.includes('--only-extra'),PREFIX=EXTRA?'extra_':'';
funcs('src/js/00_core.js',['trans','rotM']);
funcs('src/js/10_ship.js',['shipBaseMatrix','shipMatrix','modelKind','linkRopes','ropeYards','hangFalls']);
funcs('src/js/31_sailing.js',['sailSetLevel','setHas','applySailSet']);
funcs('src/js/32_hull.js',['gp']);funcs('src/js/34_shreds.js',['shredStep']);funcs('src/js/09_phx.js',['rigLv']);
funcs('src/js/21_gunnery.js',['modelLocal']);
C.RIG_LV=[null,{it:2,every:4,loose:150,shred:40},{it:3,every:2,loose:300,shred:80},{it:4,every:2,loose:500,shred:150}];
C.S=m.header.meters_per_voxel;C.G=9.81;C.M4=C.VK.M4;C.PHX={rig:3,rigfar:0};C.GUN_CODE={};C.SAIL_SET0={topsail:1,jib:1,topgallant:2,gaff:2};C.DEBUG=false;C.PHYS=true;C.WIND_K=1;C.WIND_SPD=1;C.WX={wind:1};C.CAM={};C.PHX_RIG_LAST=3;C.RUNNING=false;C.$=()=>({classList:{toggle(){}}});
H.cx=(m.header.bbox[0]+m.header.bbox[3])/2;H.cy=m.header.size[1]/2;H.zw=63;H.cloth=H.rig.sails.map(s=>C.clothTemplate(H,s));
C.CACC=new Float32Array(10000);C.CCNT=new Uint16Array(10000);
// Original makeShip rig state, restricted to intact undamaged ship. No survey/gunnery/navigation step.
function ship(){let sh={T:H,grid:H.base,i:0,crew:[],phase:0,yaw:0,px:0,pz:0,sink:0,lift:0,bob:0,pitchA:0,rollA:0,vel:[0,0,0],loose:[],shreds:[],sailSet:3};
sh.models=H.rig.models.map((x,k)=>({T:H,k,path:x.name,name:x.name.split('/').pop(),kind:C.modelKind(x),mesh:x.mesh,origin:x.origin,bb:x.bbox,pts:x.points||{},meta:x.meta||{},alive:true,rot:0,r0:(+(x.meta||{}).rotate_z_deg||0)*Math.PI/180,piv:(x.points||{}).pivot,yk:(x.meta||{}).yard,sail:(x.meta||{}).sail,c:[(x.bbox[0]+x.bbox[3])/2,(x.bbox[1]+x.bbox[4])/2,(x.bbox[2]+x.bbox[5])/2]}));
sh.yards=sh.models.filter(x=>x.kind==='yard'&&x.piv);
sh.models.forEach(md=>{let b=md.bb,cx=Math.floor((b[0]+b[3])/2),cy=Math.floor((b[1]+b[4])/2),fz=Math.floor(b[2])-1,foot=-1;if(md.kind==='yard'&&md.piv)foot=C.anchorNear(H,...md.piv,8);let st=md.pts['stock-top'];if(md.kind==='rudder'&&st)foot=C.anchorNear(H,...st,8);let bl=md.pts.bail;if(foot<0&&bl)foot=C.anchorNear(H,...bl,8);if(foot<0){let z0=fz;while(fz>0&&!H.base.get(cx,cy,fz))fz--;if(z0-fz<=12||md.kind!=='model')foot=C.VK.pack(cx,cy,fz);else md.hang=true}md.foot=foot<0?C.VK.pack(cx,cy,fz):foot;});
sh.ropes=H.rig.ropes.map(r=>({pts:r.pts,col:r.color,bb:C.ropeBox(r.pts),a:C.anchorNear(H,...r.pts.slice(0,3),5),b:C.anchorNear(H,...r.pts.slice(-3),5),name:r.name,meta:r.meta||null}));C.linkRopes(H,sh.ropes,sh.models);C.ropeYards(sh);
C.hangFalls(sh);
sh.sails=H.rig.sails.map((s,k)=>({name:s.name,meta:s.meta,k,flag:C.isFlag(s),dead:false,furled:false}));sh.cl=H.cloth.map(T=>({T,p:null,hidden:true}));C.applySailSet(sh);sh.M=C.shipMatrix(sh);sh.inv=C.M4.inv(sh.M);return sh;}
function P(v,i){return [v[i*3],v[i*3+1],v[i*3+2]]}
function box(v){let b=[Infinity,Infinity,Infinity,-Infinity,-Infinity,-Infinity];for(let i=0;i<v.length;i++)b[i%3]=Math.min(b[i%3],v[i]),b[i%3+3]=Math.max(b[i%3+3],v[i]);return b}
function overlap(a,b){return a[0]<=b[3]&&a[3]>=b[0]&&a[1]<=b[4]&&a[4]>=b[1]&&a[2]<=b[5]&&a[5]>=b[2]}
function alpha(k,t,bary=[1/3,1/3,1/3]){let s=H.rig.sails[k],tx=s.texture;if(!tx)return 255;let vs=H.cloth[k].tris.slice(t*3,t*3+3),uv=[0,0];vs.forEach((v,i)=>{uv[0]+=tx.uv[v*2]*bary[i];uv[1]+=tx.uv[v*2+1]*bary[i]});let x=Math.max(0,Math.min(tx.w-1,Math.floor(uv[0]*tx.w))),y=Math.max(0,Math.min(tx.h-1,Math.floor(uv[1]*tx.h)));return Buffer.from(tx.rgba,'base64')[(y*tx.w+x)*4+3]}
// Exact segment-triangle interior crossing; reports barycentric coordinates for texture alpha.
function crossTri(a,b,v0,v1,v2){let d=C.sub(b,a),e1=C.sub(v1,v0),e2=C.sub(v2,v0),p=C.cross(d,e2),det=C.dot(e1,p);if(Math.abs(det)<1e-8)return null;let u=C.dot(C.sub(a,v0),p)/det;if(u<1e-6||u>1-1e-6)return null;let q=C.cross(C.sub(a,v0),e1),v=C.dot(d,q)/det;if(v<1e-6||u+v>1-1e-6)return null;let t=C.dot(e2,q)/det;if(t<1e-6||t>1-1e-6)return null;return {p:C.add(a,C.mul(d,t)),bary:[1-u-v,u,v],t};}
function insideMesh(p,mesh){let ts=mesh.tris,v=mesh.verts,xs=[];let b=[p[0]+10000,p[1]+.000013,p[2]+.000027];for(let j=0;j<ts.length;j+=3){let hit=crossTri(p,b,P(v,ts[j]),P(v,ts[j+1]),P(v,ts[j+2]));if(hit)xs.push(hit.p[0])}xs.sort((a,b)=>a-b);return xs.filter((x,i)=>!i||Math.abs(x-xs[i-1])>1e-5).length%2===1}
let scenarios=[];for(let lv=1;lv<=3;lv++)for(let psi of [0,1.4,-1.4,2.85,-2.85])scenarios.push({name:`lv${lv}-psi${psi}`,lv,psi,duration:12});
scenarios.push({name:'storm-pressure-max',lv:3,psi:1.4,wind:3,weather:2.2,duration:20},{name:'pressure-min',lv:3,psi:1.4,wind:.25,duration:12},{name:'far-low',lv:1,psi:1.4,far:true,duration:12},{name:'far-high',lv:3,psi:1.4,far:true,duration:12},{name:'sets-reset-roll-turn',lv:3,psi:1.4,sequence:true,duration:32});
if(EXTRA)scenarios=[{name:'static-off-all',lv:3,psi:0,duration:0,off:true},{name:'fine-init-all',lv:3,psi:0,duration:0,init:true},{name:'pressure-min-config',lv:3,psi:1.4,wind:.25,duration:12}];
let reports=[];const trajectoryPath=OUT+'/'+PREFIX+'phys_trajectory.jsonl',traj=fs.openSync(trajectoryPath,'w');
for(const sc of scenarios){C.PHX.rig=sc.lv;C.PHX.rigfar=sc.far?2:0;C.PHYS=true;C.WIND_K=sc.wind||1;C.WX.wind=sc.weather||1;C.CAM=sc.far?{eye:[10000,10000,10000],vp:new Float32Array(16)}:{};let sh=ship();C.SHIPS=[sh];if(sc.off)C.setPhys(false);if(sc.init)sh.cl.forEach(c=>{C.clothInit(c);c.hidden=false});let hits=[],seen=new Set(),counts={body:0,models:0,sailSail:0,transparent:0,attachment:0},checks={body:0,models:0,sailSail:0},active=new Set(),frames=0;
function record(x){let key=x.type+':'+x.sail+':'+x.tri+':'+(x.other||'');if(!seen.has(key)){seen.add(key);hits.push(x)}}
for(let step=0;step<=sc.duration*60;step++){
C.SIMT=step/60;let t=C.SIMT,psi=sc.psi;
if(sc.sequence){psi=t<16?1.4:-1.4;sh.yaw=t<16?0:(t-16)*.04;sh.rollA=.12*Math.sin(t*.7);sh.pitchA=.06*Math.sin(t*.4);sh.vel=[1.3,0,.4];sh.sailSet=Math.floor(t/4)%4;C.applySailSet(sh);if(step===600)C.setPhys(false);if(step===660)C.setPhys(true);}
C.WIND=[Math.cos(psi),0,Math.sin(psi)];sh.M=C.shipMatrix(sh);sh.inv=C.M4.inv(sh.M);if(C.PHYS&&!sc.init)C.physStep(sh);
let fines=sh.cl.map((c,k)=>{let s=sh.sails[k];if(C.PHYS?(c.hidden||!c.p||c.gone):(s.dead||s.furled))return null;active.add(s.name);return C.PHYS?Array.from(C.clothFine(c,new Float32Array(c.T.n*3))):Array.from(c.T.p0)});
// Parent adds a finite-value assertion; original collision algorithms unchanged.
if(fines.some(f=>f&&f.some(x=>!Number.isFinite(x))))throw Error('Nonfinite cloth at '+sc.name+':'+t);
if(step%6===0&&sc.name==='sets-reset-roll-turn')fs.writeSync(traj,JSON.stringify({scenario:sc.name,time:t,phys:C.PHYS,sailSet:sh.sailSet,angles:sh.yards.map(y=>({k:y.k,rot:y.rot})),ropes:sh.ropes.map(r=>Array.from(r.pts)),fine:fines})+'\n');
if(step%60)continue;frames++;
sh.models.forEach(md=>md.inverseLocal=C.M4.inv(C.modelLocal(md)));
let boxes=fines.map(f=>f?box(f):null),triData=fines.map((f,k)=>{if(!f)return null;let T=H.cloth[k],a=[];for(let ti=0;ti<T.tris.length;ti+=3){let ids=Array.from(T.tris.slice(ti,ti+3)),vv=ids.map(i=>P(f,i)),cent=[0,0,0];vv.forEach(p=>p.forEach((x,a)=>cent[a]+=x/3));a.push({ids,vv,cent,bb:box(vv.flat()),ti:ti/3})}return a});
for(let k=0;k<fines.length;k++)if(fines[k])for(let td of triData[k]){
let q=td.cent.map(Math.floor),T=H.cloth[k],a=alpha(k,td.ti),attachment=td.ids.some(i=>T.hk[i]);checks.body++;
if(sh.grid.get(...q)){let type=a<128?'transparent':attachment?'attachment':'body';counts[type==='body'?'body':type]++;record({type,sail:sh.sails[k].name,tri:td.ti,time:t,p:td.cent,cell:q,alpha:a,physics:C.PHYS,pins:td.ids.map(i=>T.hk[i])})}
for(let md of sh.models){checks.models++;let orig=H.rig.models[md.k],local=C.M4.pt(md.inverseLocal,...td.cent),b=orig.bbox;if(local.some((x,a)=>x<=b[a]-orig.origin[a]+.02||x>=b[a+3]-orig.origin[a]-.02))continue;let mesh=H.rig.meshes[orig.mesh];if(!insideMesh(local,mesh))continue;counts.models++;record({type:a<128?'transparent':attachment?'attachment':'model',sail:sh.sails[k].name,tri:td.ti,time:t,p:td.cent,other:md.path,modelIndex:md.k,alpha:a,physics:C.PHYS});}
}
for(let k=0;k<fines.length;k++)for(let l=k+1;l<fines.length;l++){checks.sailSail++;if(!fines[k]||!fines[l]||!overlap(boxes[k],boxes[l]))continue;let found=false;for(let a of triData[k]){if(found)break;for(let b of triData[l]){if(!overlap(a.bb,b.bb))continue;for(let e=0;e<3;e++){let hit=crossTri(a.vv[e],a.vv[(e+1)%3],...b.vv);if(!hit)continue;let ba=[0,0,0];ba[e]=1-hit.t;ba[(e+1)%3]=hit.t;let aa=alpha(k,a.ti,ba),ab=alpha(l,b.ti,hit.bary);if(aa<128||ab<128){counts.transparent++;continue}counts.sailSail++;record({type:'sail-sail',sail:sh.sails[k].name,tri:a.ti,other:sh.sails[l].name,otherTri:b.ti,time:t,p:hit.p,alpha:[aa,ab]});found=true;break}if(found)break}}
}
}
let r={scenario:sc,frames,active:[...active],checks,counts,hits,rigM:sh.rigM,deadRopes:sh.ropes.filter(r=>r.dead).map(r=>r.name)};reports.push(r);fs.writeFileSync(OUT+'/'+PREFIX+'matrix_partial.json',JSON.stringify({hashes,file,reports},null,2));console.log(sc.name,JSON.stringify(counts),'hits',hits.length);
}
fs.closeSync(traj);fs.writeFileSync(OUT+'/'+PREFIX+'matrix.json',JSON.stringify({hashes,file,reports,negativeControl:{clearSeparatedTriangles:crossTri([0,0,2],[0,0,3],[-1,-1,0],[1,-1,0],[0,1,0])===null,interiorCrossingDetected:!!crossTri([0,0,-1],[0,0,1],[-1,-1,0],[1,-1,0],[0,1,0])}},null,2));
