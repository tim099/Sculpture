import numpy as np
from build_structure import get_actual,ROOT,BASE
from build_decks import stamp
from build_rig import linevox
name=BASE+'-bowsprit';old=get_actual(name);a=np.zeros((800,241,640),np.uint8)
for q,c in old.items():a[q]=c
linevox(a,(580,120,139),(580,120,145),3,109)
stamp(name,a,'bowsprit_root_support')
print('bowsprit stump connected to forecastle')
