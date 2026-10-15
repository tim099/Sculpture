import sys,json,zlib,struct,numpy as np
sys.path.insert(0,r'D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/attachment_audit')
from clearance import *
q=P/'route_explore';r=zlib.decompress((q/'manual_candidate.vxk').read_bytes(),-15);nn=struct.unpack_from('<I',r,4)[0];rig=json.loads(r[8:8+nn])['rig']
for x in [550,560,570,580,590,600,610,620,630]:
 print('X',x,[(z, (BODY[(BODY[:,0]==x)&(BODY[:,2]==z),1].min().item(),BODY[(BODY[:,0]==x)&(BODY[:,2]==z),1].max().item()) if np.any((BODY[:,0]==x)&(BODY[:,2]==z)) else None) for z in [90,100,110,120,130,140,150,158]])
print('models',[(m['name'],m['bbox']) for m in rig['models'] if m['bbox'][3]>550 and m['bbox'][0]<650 and m['bbox'][2]<160])
