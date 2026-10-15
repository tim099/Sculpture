from audit import *
def pt_tri(p,tr):
 a=tr[:,0];ab=tr[:,1]-a;ac=tr[:,2]-a;normal=np.cross(ab,ac);den=np.einsum('ij,ij->i',normal,normal);s=np.divide(np.einsum('ij,ij->i',p-a,normal),den,out=np.zeros(len(tr)),where=den>0);q=p-s[:,None]*normal;v=q-a;d00=np.einsum('ij,ij->i',ab,ab);d01=np.einsum('ij,ij->i',ab,ac);d11=np.einsum('ij,ij->i',ac,ac);d20=np.einsum('ij,ij->i',v,ab);d21=np.einsum('ij,ij->i',v,ac);dd=d00*d11-d01*d01;u=np.divide(d11*d20-d01*d21,dd,out=np.zeros(len(tr)),where=dd>0);w=np.divide(d00*d21-d01*d20,dd,out=np.zeros(len(tr)),where=dd>0);best=np.where((u>=0)&(w>=0)&(u+w<=1)&(dd>0),s*s*den,np.inf)
 for j in range(3):
  x=tr[:,j];d=tr[:,(j+1)%3]-x;t=np.clip(np.divide(np.einsum('ij,ij->i',p-x,d),np.einsum('ij,ij->i',d,d),out=np.zeros(len(tr)),where=np.einsum('ij,ij->i',d,d)>0),0,1);best=np.minimum(best,np.sum((p-x-t[:,None]*d)**2,axis=1))
 return best
def seg_tri_distance(a,b,tr):
 if len(tr)==0:return np.array([])
 best=np.minimum(pt_tri(a,tr),pt_tri(b,tr));u=b-a;A=u@u
 for j in range(3):
  c=tr[:,j];v=tr[:,(j+1)%3]-c;w=a-c;B=v@u;C=np.sum(v*v,axis=1);D=w@u;E=np.sum(v*w,axis=1);den=A*C-B*B;s=np.divide(B*E-C*D,den,out=np.zeros(len(tr)),where=np.abs(den)>1e-18);s=np.clip(s,0,1);t=np.clip(np.divide(B*s+E,C,out=np.zeros(len(tr)),where=C>0),0,1);s=np.clip((B*t-D)/(A or 1),0,1);t=np.clip(np.divide(B*s+E,C,out=np.zeros(len(tr)),where=C>0),0,1);best=np.minimum(best,np.sum((w+s[:,None]*u-t[:,None]*v)**2,axis=1))
 # Any segment piercing a face gives exact zero, independent of endpoint/edge candidates.
 ts=seg_tri(a,b,tr)
 if len(ts):best[0]=0
 return best
