import pathlib,shutil,json,hashlib
from PIL import Image,ImageDraw,ImageFont
O=pathlib.Path(__file__).parent
D=pathlib.Path('D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m/design/rudder_bearing_20261021');D.mkdir(exist_ok=True)
for f in ['after_readback.py','after_readback.json','spin_readback.cjs','spin_readback.json','package_bearing.py']:
 shutil.copy2(O/f,D/f)
for f in ['proposal.json','DESIGN.md','fixed.vox.txt','moving.vox.txt','carve_exact.vox.txt','fixed_meta.json','moving_meta.json']:
 shutil.copy2(O/'hardware/bearing_proposal'/f,D/f)
for f in ['check.py','report.json','proposal_snapshot.json']:
 shutil.copy2(O/'rudder_independent'/f,D/('independent_'+f))
for f in ['magazine_verify.py','magazine_report.json','magazine_review.md']:
 shutil.copy2(O/'decks'/f,D/f)
for f in ['after_parts.json','after_bearing.vxk']:
 shutil.copy2(O/'shared'/f,D/f)
shutil.copy2(pathlib.Path('D:/Unity/Valhalla/ChatTavern/baton/letters/Sirius/cmd/sculpture_stats.md'),D/'after_structure.md')
im=Image.new('RGB',(1100,1050),'white');draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21);title=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',30)
def xy(u,s):return (370+u*100,900-(s-76)*90)
def rect(x0,s0,x1,s1,col):draw.rectangle([xy(x0,s1),xy(x1,s0)],fill=col,outline='black',width=2)
draw.text((45,25),'Tidegrave rudder bearing: axial section',font=title,fill='black')
draw.text((45,70),'Rigid geometry and contact; no material strength claim',font=font,fill='black')
for s in range(76,85):
 draw.line([xy(-1.8,s),xy(2,s)],fill='#ddd');draw.text(xy(-2.4,s),str(s),font=font,fill='black')
for x in [-1,.5]:rect(x,80.4,x+.5,82,'#64748b')
rect(-.3,76.4,.3,83,'#fb923c');rect(-.9,82,.9,82.4,'#fb923c')
for x0,x1 in [(-.9,-.5),(.5,.9)]:draw.line([xy(x0,82),xy(x1,82)],fill='#16a34a',width=6)
draw.line([xy(-1.5,80.2956665725),xy(2,80.2956665725)],fill='#9333ea',width=2)
for y,text in [(155,'Orange: rotating shaft + shoulder'),(200,'Slate: fixed ring (square bore)'),(245,'Green: shoulder rests on ring'),(310,'Shoulder underside s=82'),(355,'Fixed ring top s=82'),(400,'Shaft 0.6 / bore 1.0'),(465,'Purple: old rudder max s=80.29567'),(530,'All lengths: parent voxels (0.1 m)'),(575,'Source grid: 0.01 m; scale: 0.1'),(620,'Fixed 4800 / moving 3528 cells'),(665,'20 guarded cuts above waterline'),(710,'Joints: 4 hull / 8 rudder cells')]:draw.text((610,y),text,font=font,fill='black')
draw.text((45,970),'Axial s increases upward along the inclined rudder axis. Cross section is local u/s.',font=font,fill='black');im.save(D/'bearing_section.png')
(D/'.gitattributes').write_text('* -text\n',encoding='utf-8')
(D/'README.md').write_text('''# 2026-10-21 舵實體支承與設備簽收補件

原舵上端離船體2.5格，既有meta不能代替實體支承。本次增加固定環座與同軸活動短軸／止推肩，原7428格舵不改。肩下表面落在環座上表面，形成向上承壓面；固定座嵌接4個船格，短軸嵌接8個原舵格，這是明示接頭，不冒稱所有模型兩兩重疊為零。

## 驗證與讀回

- `DESIGN.md`、`proposal.json`是事前設計；4800/3528來源格、20格原色109守門清單與meta一同保存。來源1cm，父船10cm；顯式scale0.1。
- `independent_check.py`與`independent_report.json`是另一個subagent獨立公式／事件回播，非另一persona。新活動件完整360度包絡與接觸面證明；原舵±30度保守區間SAT，244區間呼叫、無實碰或未解區間。負控：去肩即承壓面積0，恢復孔格會命中7個軸圓柱候選。
- 獨立報告保留原文：它完成時父代理已刻孔，故`carve_guard_bad`列20個已空位置，且status仍寫proposal only。這項不是失敗後改成通過。落地前後的完整VXK逐格對照由父代理另外執行，見`after_readback.json`：指定20格原色守門完全吻合、沒有其他增格或改色、水線以下完全一致。獨立代理沒有執行落地後驗，不混稱為其結果。
- `after_readback.py`比較前一批`../acceptance_20261021/shared/current.vxk`與本件`after_bearing.vxk`：1033347→1033327格；239原模型（含網格）逐值未變，新增2；502繩與10帆逐值未變。實際來源事件回播4800/3528、模型變換、轉軸與控制meta吻合。
- `after_structure.md`是CLI落地讀數：單一連通、封閉空腔0、左右缺格／異色0、關聯重疊／裁切0。
- `spin_readback.cjs/json`在Node VM執行當前未修改的Blockside `26_spin.js`，餵實際匯出meta；舵與活動肩兩件成功綁定，固定座不轉，六組舵輸入均同軸同心同角。去掉活動軸meta的負控產生1個匯入警告。此為遊戲轉動函式的窄測，沒有執行完整載入器／畫面。
- `magazine_*`補齊雙庫各24桶、每庫2400磅、完整室內包絡、7×21×2門洞、門框與爆心meta；舊設備逐件避碰／支承、60個穿甲板孔、繩組與Credit在`../acceptance_20261021/hardware/`及既有`equipment_parts`，正式本機遊戲接入歷史證據在`../delivery/formal_game_20261016/RESULT.md`。

## 接續與限制

`after_bearing.vxk` SHA256：9a5780caee1df71a635e0b34b376933ec30e94996467a35e042c3b408959286b。它是本次作者交付候選，未替換Blockside已匯入資產，也未發布。原模型與繩帆完整保留；遊戲端下次匯入應使用本件並再跑verify/shipcheck。bearing_section.png是局部施工剖面，不是渲染或材料強度測試。

TASK-0549設備階段依本次證據可簽；TASK-0546最後一格與0540整船主單仍開著。0603雖由Tim於10-19後台結單，不能據此宣稱全部布料動態案例通過；維持Tim手動動態驗收邊界，不復開0603，也不代簽最後一格。

重跑腳本沿用原scratch絕對路徑與前批輸入；離線重跑須先將快照配置到所記路徑，不宣稱這是通用成船再生器。新件為Sirius自製；既有wheel/capstan/powder Credit basecamp、binnacle Credit summit不變。
''',encoding='utf-8')
manifest={p.relative_to(D).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(D.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(D, len(manifest))
