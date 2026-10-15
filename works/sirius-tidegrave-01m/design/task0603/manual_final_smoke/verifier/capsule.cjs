// Independent Euclidean segment/triangle distance. No game collision code used.
const sub=(a,b)=>a.map((v,i)=>v-b[i]),add=(a,b)=>a.map((v,i)=>v+b[i]),mul=(a,s)=>a.map(v=>v*s),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],clamp=x=>Math.max(0,Math.min(1,x));
function triPoint(p,v){let ab=sub(v[1],v[0]),ac=sub(v[2],v[0]),ap=sub(p,v[0]),d1=dot(ab,ap),d2=dot(ac,ap),w;
if(d1<=0&&d2<=0)w=[1,0,0];else{let bp=sub(p,v[1]),d3=dot(ab,bp),d4=dot(ac,bp);if(d3>=0&&d4<=d3)w=[0,1,0];else{let vc=d1*d4-d3*d2;if(vc<=0&&d1>=0&&d3<=0){let q=d1/(d1-d3);w=[1-q,q,0];}else{let cp=sub(p,v[2]),d5=dot(ab,cp),d6=dot(ac,cp);if(d6>=0&&d5<=d6)w=[0,0,1];else{let vb=d5*d2-d1*d6;if(vb<=0&&d2>=0&&d6<=0){let q=d2/(d2-d6);w=[1-q,0,q];}else{let va=d3*d6-d5*d4;if(va<=0&&(d4-d3)>=0&&(d5-d6)>=0){let q=(d4-d3)/((d4-d3)+(d5-d6));w=[0,1-q,q];}else{let inv=1/(va+vb+vc);w=[1-(vb+vc)*inv,vb*inv,vc*inv];}}}}}}
let q=[0,1,2].map(a=>v.reduce((s,p,i)=>s+p[a]*w[i],0));return {p:q,w,d:dot(sub(p,q),sub(p,q))};}
function segmentPair(a,b,c,d){let u=sub(b,a),v=sub(d,c),w=sub(a,c),A=dot(u,u),B=dot(u,v),D=dot(v,v),E=dot(u,w),F=dot(v,w),den=A*D-B*B,s,t;
if(A<1e-14){s=0;t=D>1e-14?clamp(F/D):0;}else if(D<1e-14){t=0;s=clamp(-E/A);}else{s=den>1e-14?clamp((B*F-D*E)/den):0;t=(B*s+F)/D;if(t<0){t=0;s=clamp(-E/A);}else if(t>1){t=1;s=clamp((B-E)/A);}}
let p=add(a,mul(u,s)),q=add(c,mul(v,t));return {s,t,p:q,d:dot(sub(p,q),sub(p,q))};}
function distance(a,b,v){let d=sub(b,a),e1=sub(v[1],v[0]),e2=sub(v[2],v[0]),h=cross(d,e2),det=dot(e1,h);if(Math.abs(det)>1e-12){let q=sub(a,v[0]),u=dot(q,h)/det,r=cross(q,e1),w=dot(d,r)/det,t=dot(e2,r)/det;if(u>=0&&w>=0&&u+w<=1&&t>=0&&t<=1)return {d:0,p:add(a,mul(d,t)),w:[1-u-w,u,w],s:t};}
let best=triPoint(a,v);best.s=0;let end=triPoint(b,v);end.s=1;if(end.d<best.d)best=end;
for(let i=0;i<3;i++){let j=(i+1)%3,r=segmentPair(a,b,v[i],v[j]);if(r.d<best.d){let w=[0,0,0];w[i]=1-r.t;w[j]=r.t;best={...r,w};}}return best;}
module.exports={distance,triPoint,segmentPair};
if(require.main===module){const assert=require('assert');let v=[[0,0,0],[2,0,0],[0,2,0]];assert.equal(distance([.2,.2,-1],[.2,.2,1],v).d,0);assert(Math.abs(distance([.2,.2,2],[.2,.2,3],v).d-4)<1e-10);assert(Math.abs(distance([3,0,0],[3,0,1],v).d-1)<1e-10);assert(Math.abs(segmentPair([0,0,0],[1,0,0],[.5,-1,2],[.5,1,2]).d-4)<1e-10);console.log('capsule controls pass');}
