# 2026-10-21 階段驗收與續作

新正本：design/acceptance_20261021/README.md。0541總圖Rev10、0545甲板七梯、0548火砲、0550裝飾均逐格簽收，獨立證據與負控保存。21號快照1033347格、502繩10帆239模型；舵支承仍缺，0549與主單0540接續補。0603已由Tim於10-19結單，勿再依舊交接稱它仍in_progress；結單不轉寫為20情境自動PASS。根層舊總圖與舊暗色裝飾圖保留歷史，當期新圖見本資料夾。

---

# 2026-10-19 TASK-0743 砲門蓋板

參考光榮號與 §9.12，新增30片（lower22、upper8），共用19×17×2子作品；18處凸出構件按規格排除、艏三聯砲不做。開著碰船/砲0、關上碰收回砲0、開口全覆蓋，反向對照通過。鉸鏈曲面角端最多外移1格。實物、來源、讀數與限制見 design/portlids_20261019/README.md、design/verify_portlids.json。觀測圖 overlays/portlids_20261019.png。船體、502繩、10帆保留。

---

## 2026-10-18 TASK-0692 甲板陳設完成

新增22模型（19 deco、工作艇1、艉樓燈2），總數191；船體1033347格、502繩、10帆保留且無壞綁定。參考憲法號，來源Credit為basecamp/gura/kotoko/summit。設計、實測、獨立複驗及限制見 works/sirius-tidegrave-01m/design/fittings_20261018/README.md。艇未加船架/繫固；兩燈刻意放大到2.7m。VXK為 works/sirius-tidegrave-01m/exports/fittings_20261018.vxk，尚未匯入遊戲。原全帆Tim人工驗收仍保留。

---

# 2026-10-16 潮墓號：兩項匯入警告已清除

隔離最新遊戲正式 shipcheck：0 errors / 0 warnings，陸戰隊12/12、353船員、54砲全滿編、
送藥取用點到砲尾54/54連通。build與verify通過。正式Blockside仍由ame接入。

對稱艏砲側通道X574..581、Y94..103及137..146、淨空Z117..134；補地板Z115..116。
經sculpture CLI移除1152格、補176格，成船1033347格/checksum55c4e759。
CLI/VXK逐格逐色差0、水線以下不變，原502繩/10帆/168模型/25mesh及固定帆點逐值不變。
交付delivery/tidegrave_import_20261016.vxk，
SHA256 850566c50d4b7b022f3124ec88e36a6154b672ad7201ef44ce9602da1a43322b。

配套game_integration/23_powder.patch修艏艉砲送藥手出生與交藥點至砲尾後方；
suggested_ship.json設marines=12、marineGap=30並保留geo。補丁只套隔離版。
Tim明確說穿過前桅、跨過艙口不用處理，部分細節故意節省效能；保留原monkeyTo，
不提交額外逐格導航或人體碰撞限制。此處連通驗收依現行遊戲標準，未擴大成逐步碰撞驗收。

TASK-0603/0546帆碰撞仍依Tim先前選擇手動驗收；本次不代簽完整動態PASS。
最新交付取代20261015版本；歷史初建腳本不可在成船盲跑。

---

# 2026-10-15 潮墓號：遊戲匯入交付

Tim要求完成造船至可加入遊戲，並通知ame。作者側已補左右共用bower錨、短索與hawse，
錨後移2m避開艏砲班的模型外框。原船體1034323格/d931433f、十帆及固定帆點保留。
最終502繩/10帆/168模型，broken全0；結構1元件/0空腔/鏡像0/關聯重疊裁切0。

交付 D:\Unity\Valhalla\Sculpture\works\sirius-tidegrave-01m\design\delivery\tidegrave_import_20261015.vxk
SHA256 9d296dd5831602b831eaf00fc5fd1926b2d8f57487f3b053d361456a5019b367
0.1m格，水線52，54砲、6甲板、7梯、兩庫各24桶/2400lb。
重匯兩次除exported_at外內容相同；VXK/CLI逐格逐色0差，一格負向可失敗。
這不是所有歷史階段的乾淨初建重跑聲明。

隔離最新遊戲：0 errors / 2 warnings、54砲全滿編、352船員、左右錨/ring/hawse。
配套game_integration/23_powder.patch修艏艉砲送藥手誤生在甲板外的砲口X；舷砲不變。
suggested_ship.json提供geo。未改ame正式遊戲工作樹，需ame覆核採用、匯入及重建。
兩警告保留：陸戰隊11/12，chase-2送藥路徑尋路格不連通（現走直線）。

ame已接手帆物理並提交ebd55ff；TASK-0603/0546按Tim選擇維持手動動態驗收，
不把匯入成功當作穿帆全過。已知自由布接觸與凍結證據保留在design/task0603。
最新圖Rev08、overlays/import_bow_20261015.png；正式匯入說明design/delivery/IMPORT.md。

---

# 潮墓號施工與验收笔记

委託：Tim 2026-10-13，原創電影鬼船風格遊戲資產；主單TASK-0540。Sirius設計，資料根D:/Unity/Valhalla。0.1 m/格，+X船頭、-Y左舷、y=120格中心鏡面、Z0龍骨底。電影觀察、歷史來源與原創決定見design/references/README.md與plan.json；不把電影的旋轉三聯砲、潛航或召喚功能寫成已有遊戲功能。

## 階段零：來源與總圖

側面、俯視與五個剖面在design/general_arrangement.png。Rev04已同步六艏砲木托／間距、移位舵輪與羅經櫃、鏡像導索柱、操舵轉角、加高旗竿及彈藥庫門高。獨立兩次重產逐byte一致；從主桅頂圖紙像素出發，將全部17430格實物Z-3，固定格中心探針由0報3。原像素換算的捨入偏差照實保留，不用改datum冒充資產反向對照。詳design/audits/20261014/general_rev4_final.md。

## 階段一：骨架

凍結設計skeleton.vox.txt 118405格。獨立逐事件重播與設計逐格逐色缺／多／異色0，連通1、空腔0；圖紙占用與實物偏3的反向對照通過。修正了uint8乘255的RGB溢位，修後像素色彩帳0差。初建build_structure.main不是成船重跑器，不能對現有成船盲跑。

## 階段二：殼、塗裝與砲門

凍結外板設計549603格，與骨架合计668008格；階段前骨架零異動。48舷砲門中心射線通。殼圖纸的旧探針會被骨架遮住，改用孤立點(100,150)，完整資產偏3時報3。後續精確開孔、砲托、艉窗與舵槽是各自有清單與事件的改動，不能拿最早殼格數冒充當前。

舵槽原先neutral零碰撞、非零轉角撞船；2026-10-14按color guard清掃1318格。actual後驗0.25度的241角＋0.095818格保守運動包絡覆蓋±30度，全部碰撞0。最新組裝件1036066格／1連通／0空腔／0鏡像差；水下封閉空氣1370871格與兩內艙探針防水均通。水線下有刪格本身不等於破水密；主件與組裝件洪泛讀數分開記，不能混用封閉空氣體積。

## 階段三：甲板與七梯

lower/upper/weather/quarter/poop/forecastle六子件，七座梯共14個foot/head端點支持與14格淨空通。遊戲原版把同高139的艏樓與艉樓合層、只保留最大連通區，因而丟艏樓梯；不是缺一座實體梯。design/nav_candidate是隔離候選，保持兩個空間層；七梯與10秒運行已量，正式接入由ame覆核。deck_*.vox.txt為初建器後來覆寫的零格增量，不能當完整設計；新的甲板圖從CLI匯出當前完整deck重畫，報告明寫來源。

## 階段四：桅帆索具

三桅、艏斜桅，十帆旗；299原繩增加一段繞梯操舵繩。帆自己的16條sheet均有meta，其他繩不假稱全標。五條內段穿舷牆的繩改綁有實際根、左右鏡像的導索柱；brace最終改到共享柱頂136，不讓柱子在綁點上方穿繩。五修繩及七操舵段含半徑內穿0。steer-wheel-P改走(225.5,106.5,151.5)，避免刻梯；甲板通孔有各source的精準color guard。靜態T=3秒驗收與最後單一anchor後驗各存報告；附着邊接觸、嚴格內片穿透與尚未量的動畫掃掠分開列。

## 階段五：54砲

48舷砲與六固定艏砲。砲種24l/18chase、muzzle/breech与模型scale明寫。独立54模型對實體正體積碰撞0，54條20m炮口中心射線暢通；六艏砲木托與平台修後，遊戲54砲全滿足crewMin。三聯只呈現外形，不宣稱旋轉砲機制。

## 階段六：彈藥庫與設備

兩庫各24桶、每庫2400 lb為遊戲庫存，非史料；門净高21格。來源署名保留basecamp舵輪／絞盤及summit羅經櫃。舵輪移至(198.5,143.5,139)，scale .2、pivot(50,52,0)；獨立105目標模型對船、彼此碰撞0，舵輪40/40底足支持。舵的轉軸meta與幾何允許範圍存在，但現行遊戲未消費完整hinge轉軸，不把資產掃掠當成已動畫轉舵。

## 階段七：艉廊與裝飾

哥德艉樓、破星盤、珊瑚冠、牙形艏欄與海蝕附着物。原裝飾31745格及新增23格旗竿合計31768，鏡像與空腔0；219個裝飾元件各有face接船，不把子件內分散誤稱整船浮空。旗整面升26格至top231.5/bottom215.5，旗竿以ornament的(105,120,208)為根延長。後驗嚴格內片穿骨飾0，17格接觸均為旗竿固定邊附着。

## 兩本帳與重產界線

結果帳、圖紙帳、獨立報告各自保存；design/audits/20261014收回先前只在scratchpad的證據。早期凍結階段可以重算，不代表全部初建main可在成船安全重跑。修正腳本走CLI，細胞清單、顏色守門與讀回計數都保留；書卡、events、模型與帆繩帳不手改。缺驗收的格仍保持未勾。


# 2026-10-14 續造：七梯淨空、甲板標籤與操舵接入

Tim在前輪a9b44e8後要求「繼續造船 GO」。本輪最新資產a5994eeeacbb1155776145e3ebc2e69bd743815b7574df45ca6eb58653bdaf73，checksum4cb88a33，1,034,267格。CLI及獨立actual皆1連通、0空腔、鏡像缺格/異色0、關聯重疊/裁切0；交付副本逐格逐色解碼0差，一格改色反向checksum31c2532c不同。

六甲板獨立VXK量得floor66/91/116/139/139/165與thick2；已補kind=deck及level/name/floor/thick。quarter與forecastle真實同高但範圍分開；窄艏尖按floor-1實格補齊標籤範圍。組裝件主名為「潮墓號」，船殼帶sub；七個preset可看內部與各甲板。

通道施工圖在ladder_clearance_20261014/clearance_plan.png。按lift3、直立高18格、橫向y117..123設計，精準color guard刻1799格：船殼1771、quarter14、poop14；梯source與十四處落腳地板完全保留。獨立連續掃掠及足點穿格皆0，恢復一格會再報碰撞。刻格最低z113，不動水線下；水下封閉空氣前後均1,370,871格。這是1.8m×0.7m指定路徑截面，不是遊戲人體碰撞器；2.1m含透明padding的sprite框會撞644格梯件，因此沒刻梯冒充21格通過。navSnap接近/離開段及動畫pose仍另驗。

後桅crossjack原本與gaff動態互穿；已用CLI由z255.5降至224.5。木桁Z223..226、gaff229..317、boom204..207，任意繞Z連續轉角都分離；也避開yardNear將gaff jaws誤認crossjack。新圖Rev05同步實物桁高；修復入口repair_20261014_crossjack.py與build_rig的plan輸入同步，但初建main仍不能盲跑。actual只有crossjack模型、兩條mizzen-topsail.sheet與該帆改；兩sheet含半徑對body內穿0，該帆對十桁嚴格內片0。對桅仍有舊有一格微擦，不報全面0。

正式遊戲檔未改；接入候選已改用nav_deck_candidate/40_crew.patch及42_hands.patch，舊nav_candidate僅歷史。新版保留navRegions，梯端按x/floor/snap選層、cache含deck身份、補砲按meta身份；操舵出生與補位按wheel實際XY/Z；LIFT3只驗本船七梯。fixture注入改成CFG.ships且斷言命中，防舊replace靜默失效。最新VXK兩艘各348人/2舵手、54砲都達最低、七梯十四端region可達，10秒整世界GL0。兩舵手強制傷亡後，使用真stepHand、60Hz及每幀HAND_PATHS額度，35.133秒兩人到quarter z139並轉ROLE.HELM；這段世界戰鬥凍結，僅驗補位分支。

TASK-0546仍有model-aware新發現未結：main/fore course lift直拉桅head穿上層桁、部分shrouds穿course桁、4條ratline端被yardNear誤綁桁、mizzen-topsail對桅一格舊擦碰。既有voxel-only靜態通過不涵蓋這些。完整動態報告與候選scope需分開讀，不把本輪crossjack修正當全索具通過。完整安全再生與正式遊戲匯入複驗仍待。


# 2026-10-15 潮墓號續造：吊索、支索、轉桁索與後桅帆頭

委託：Tim「繼續造船吧 GO」。Sirius接續TASK-0540／0546，所有實物改動走Senate CLI。

## 本輪資產

最新交付 `delivery/tidegrave_candidate_20261015.vxk`，SHA256 `76d945aca4f55556f5b952b7a5a3b4183cbe00a6f1b9d44f7359a56fd3bc5036`，398320 bytes。1,034,267格、checksum `4cb88a33`，302繩（原300全保留，新增2道robband）、10帆旗、116模型、19網格、17關聯。封裝對獨立CLI list逐格逐色0差；改一格反向checksum `31c2532c`。

本輪沒有加刪任何木料格、砲、梯子或模型；與前輪a599快照的voxel/color/order及全部模型網格相同。CLI結構1連通、空腔0、鏡像缺格/異色0、link overlap/clipped0；全部帆繩模型broken0。觀測圖 `../overlays/continued_rig_20261015.png`、總圖Rev06 `general_arrangement.png`，觀測側投影比較 `continued_20261015/rig_comparison.png`。

## 實修與過程

1. 前、主桅course lift改綁既有hounds；topsail lift改綁下一根桁以下的桅側實木格。8條繩原有粗細、色、分組與meta保留。
2. 12條main/fore shroud與4條backstay下端移至桅後舷牆實木；舊chain固定點保留給其他索。第一次路線造成四道最低ratline穿欄，獨立後驗抓到後將第一階比例.04提高至.065；主桅首批足點又穿高艉樓欄板，六個main足點向前1m，落在x245/265/285、z128的既有木料上。126條ratline全保留。
3. 10條上層brace改走鄰桅實體綁點，slack1，不再由上桁直落穿下桁。course brace原路保留。
4. 後桅topsail以兩道0.4m短robband，從原earing拉至source局部x8的帆頭點，讓帆離開桅身。只有這面帆兩個head位置改變；free clews、貼圖、其他角、fullness與meta保留。實作中CLI換corners會重設pin，整檔比對抓到後顯式補free，已記lesson。
5. 4條backstay上端由桅頂中心改到桅頂後側既有實木格，縮短沿桅附著接觸。此修正另有最終增量後驗。

## 獨立後驗的射程

報告與可重跑證據保存於 `continued_20261015/independent/REPORT.md`；最終輸入final_heads，前序快照與負向案例也保留。

- 8lift＋10brace各163個square-yard absolute角，body／十桁精測未見離開具體附著位置的穿越。自身臂端接觸弧長逐項保存，沒有泛豁免首尾三格。
- 16standing對十桁角度取樣無穿越；own square-yard全連續±.70rad的保守下界最小1.692607648格。最終4backstay另做163 square／323 gaff角增量檢查；桅端接觸縮為main≤2.936格、fore≤2.427格。
- 84道main/fore ratline靜態對body／十桁接觸0；實際game meshOcc/yardNear對standing/ratline端點沒有誤認桁，lift/brace只綁自身正確臂端。遊戲程式未改。
- mizzen-topsail完整正背面三角對body／十桁嚴格內部裁切正面積0，原(207,120,336)擦桅消失；兩sheet與兩robband對body0，只保留實際附著端接觸。
- 負向對照真實重現舊course lift穿topsail、topsail lift穿topgallant、shroud穿course及舊布面第96片的0.0123890263格²擦桅。

這些讀數沒有覆蓋全部302繩的model-aware動態、全部自由布連續動態、非同步各桁任意角組合、繩與所有非yard模型／彼此碰撞。TASK-0546最後一格及全船主單仍不冒簽完成。

## 接續入口

先讀本檔、CHECKPOINT及獨立REPORT。正式Blockside匯入與舊nav_deck_candidate覆核仍待遊戲端接入；舊候選不得直接套到搬家後持續變動的源碼。完整階段安全再生及各子單尚未簽清，不要盲跑build_structure.main/build_rig.main。repair_20261015_*是分階段有基線守門的修正工具，不是通用建船器；standing初始修法之後還有main_feet與backstay_heads修正，不能跳過後兩者。


TASK-0747（2026-10-19）：舷砲砲門已由30補齊48片。兩側船錨前移0.3m；lower02 house6，其餘既有30片與ID保留。船殼、海蝕飾條、10帆不變。新接續入口：主船 design/portlids_complete_20261019/README.md與complete.py；不要單跑舊tools/portlids.py draft/apply，會恢復排除18片。遊戲shipcheck錯誤0，砲門警告0，僅既有送藥手24/25警告。


2026-10-21設備支承補件：舵原7428格與239原模型保留；新4800格固定環座及3528格活動短軸/止推肩，來源1cm、顯式scale.1。肩落在環座上承壓，4船格/8舵格為明示嵌接，20格原色109精準孔全在水線以上。±30度原舵保守區間掃掠與新件360度證明保存。實際匯出父代理逐格後驗只差20格，502繩10帆未變；遊戲26_spin窄測同軸同步，完整畫面未測。成品交付候選與證據design/rudder_bearing_20261021/README.md，尚未替換Blockside資產。0549可簽；0546/0540保留，0603已由Tim結單不等於動態全PASS。


2026-10-21最終拍板：Tim明示540完成（含子單）並接入新VXK；0540與全部9子單已done，原始帆動態限制保留作歷史，不改寫自動PASS。工作記憶歸檔3099e78（狀態提交5d0897e）。Blockside權威開發副本D:/Unity/Blocksail/external/Blockside，dev已接入並推6aa0b8c；使用admin reimport來源新船、補部件cellRuns與464條繩的bind，body/模型/網格/帆逐值等於交付候選。verify938網格與20船header/body一致，srccheck a942c64cd51f4d25通過；shipcheck0錯誤/1既有送藥手24/25警告，54砲班完整、送藥54/54可達。完整證據在該repo docs/imports/tidegrave_20261021/README.md。Blocksail核心pointer與battle.html同步；正式main/release未發布。新設備已接入dev，前文「尚未部署」是當時快照。
