const fs=require('fs'),vm=require('vm'),path=require('path');
const {ctx:C,H,m,hashes,funcs,source,file}=require('./pins.cjs'),OUT=process.env.CLOTH_OUT||__dirname,EXTRA=process.argv.includes('--only-extra'),PREFIX=EXTRA?'extra_':'';
funcs('src/js/00_core.js',['trans','rotM']);
funcs('src/js/10_ship.js',['shipBaseMatrix','shipMatrix','modelKind','linkRopes','ropeYards','hangFalls']);
funcs('src/js/31_sailing.js',['sailSetLevel','setHas','applySailSet']);
funcs('src/js/32_hull.js',['gp']);funcs('src/js/34_shreds.js',['shredStep']);funcs('src/js/09_phx.js',['rigLv']);
funcs('src/js/21_gunnery.js',['modelLocal']);
C.RIG_LV=[null,{it:2,every:4,loose:150,shred:40},{it:3,every:2,loose:300,shred:80},{it:4,every:2,loose:500,shred:150}];
C.S=m.header.meters_per_voxel;C.G=9.81;C.M4=C.VK.M4;C.PHX={rig:3,rigfar:0,sailhit:1};C.GUN_CODE={};C.SAIL_SET0={topsail:1,jib:1,topgallant:2,gaff:2};C.DEBUG=false;C.PHYS=true;C.WIND_K=1;C.WIND_SPD=1;C.WX={wind:1};C.CAM={};C.PHX_RIG_LAST=3;C.RUNNING=false;C.$=()=>({classList:{toggle(){}}});
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

module.exports={C,H,m,hashes,source,file,ship};
