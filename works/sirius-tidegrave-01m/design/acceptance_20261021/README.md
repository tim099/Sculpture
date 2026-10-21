# 潮墓號：分階段驗收，2026-10-21

作者與主驗收：Sirius。資料根 D:/Unity/Valhalla，0.1 m/格，+X船首、Y120格中線。
本輪先簽 TASK-0541、0545、0548、0550；設備0549的舵支承另續修，不因有轉軸meta冒簽。

## 現況與證據入口

串行CLI匯出 `shared/current.vxk`：SHA256 ec4b54974425029f6b9bd78ef0fea55f80f5b5207b59c1c17e1353a9f751e2a3；1,033,347格、55c4e759，17關聯、239模型/73網格、502繩、10帆。這是修舵支承前的21號快照；16號的168模型與20號的移錨不可混用。
`shared/parts.json`保存部件和固定點。CLI結構與獨立events/VXK：連通1、封閉空腔0；CLI鏡像缺/異色0、overlap/clipped0。`shared/ropecheck.md`的502繩兩端完整，ends_ok616/onrope388，不等於全繩動態無碰撞。

## TASK-0541：四格簽收

1. 重新親看scratch保留的Disney Archives三張模型照片，與`../references/README.md`逐項核對：三桅高艉廊、尖頂與海蝕枝冠、兩組下1上2的三管艏砲外形。原創破星盤與潮痕不借作電影原物；Vasa/Batavia只借結構概念，52m/13.4m為原創設計。未讀的館藏/研究仍保持未讀。
2. `general/general_arrangement.png`為Rev10附加總圖：側、俯、五剖面與尺寸、0.1m格、拆件說明完整；根層Rev08舊PNG保留歷史。`general/plan_rev10.json`以plan9為底，只同步兩錨x563.5、版本與歷史說明；22件陳設和48蓋板各有原階段細圖，不在示意總圖冒畫細節。
3. `general_audit.py`在兩個隔離資料夾使用**複製的設計產圖器**重產，兩PNG均f130a9aa6770bf7ca385bd251995d9a26406297d40b5d88b66c91cba8ea36e69。未信任作者verify。獨立math量連續型寬13.4m、船長52m；從PNG像素(1031,248)量化到格中心，重播主桅17430格，整資產Z-3，同尺距離0→3。
4. `decks/general_review.md`保存另一視角親看五剖面、尺寸/拆分/來源的複驗；指出繼承的aft20舊註後已在附加plan補正為560.5→563.5的完整沿革。限階段零，不宣稱整船乾淨初建main可安全重跑。

## TASK-0545：最後一格簽收

`decks/README.md`與三支獨立程式由原events重建六甲板初貼、七梯與後續六筆精刻/補柱。結果帳缺多異色0；六份當前PNG從像素端對現況events投影0缺多。四件cache尚未反映後來刻孔/補柱，不改cache代替事件。完整今版1033347格連通1/空腔0，七梯21段指定連續路徑障礙0，14地板保留。
負控：移實物X+3，固定PNG探針距離0→3；梯刪格/改色報1/1；恢復(176,117,157)同尺立即1碰撞。範圍為既定lift3、高18、寬7的靜態路徑，不追加avatar/導航限制，也不推翻Tim允許穿桅/跨艙口的效能取捨。

## TASK-0548：三格簽收

`hardware/REPORT.md`獨立重播來源並按實際矩陣變換；48個24l與6個18chase外模，108個muzzle/breech與CLI固定點距離0。105目標對靜態船體/彼此正體積碰撞0，包含6艏砲支架；54條20m炮口中心線無阻擋。將lower S01實際Y+3，同尺由0報2船格碰撞，非改datum。
`gun_schedule.csv/png`新增逐門安裝表：48舷砲x/z、左右對稱與plan一致，6艏砲與設計基座XYZ一致；來源、pivot、scale、rotate、muzzle、breech逐門列出。與原`../guns_parts.json`、`../chase_crew_design.json`及`../../overlays/guns_bow.png`、`../../journal/20261014_validation.md`形成可讀續作入口。固定三聯外形沿用普通砲，不宣稱旋轉三聯機制。48蓋板開閉另在19/20號既有驗收，本輪靜態安裝不冒充新連續開閉驗證。

## TASK-0550：三格簽收

`ornament/REPORT.md`與新的設計union三視圖/艏齒細圖，從三份原始設計清單31405+340+23生成完整31768格；不是從cache回填假設計。後/側/俯PNG像素端對events缺多異色0；舊暗色5954像素圖只保留初建歷史。
裝飾自身219元件，219/219直接face接到船，其餘16links總1001579格；鏡像0、空腔0、重疊0。239外部模型對裝飾neutral靜態正體積碰撞0。真負控將整個7428格舵模型平移後，同尺檢出38碰撞pair；另有改色、浮格與密閉小殼可失敗對照。
主驗收已親看`shared/stern_detail.png`（yaw180/pitch5/target100,120,180/zoom0.65，帆繩隱藏以顯示細部）：三層艉廊/窗框、中心斷環星盤、上拱與枝冠、旗竿可辨；艏齒側向階梯輪廓見`ornament/ornament_design_union_bow_detail_X560_704.png`，不是只用後視折疊X圖代簽。原多角度過程圖與事後驗證日記保留。這格不代表全帆/繩動態通過。

## 後續仍在正本

0549舵支承是真缺項：現有舵stock-top離船體2.5格、沒有辨識得到的支承件，後續以窄支承設計續修；保留原7428格舵和完整±30轉動。
0603已由Tim在2026-10-19結單；舊工作記憶「仍in_progress」過期。本輪不把結單轉寫為全20情境自動PASS，也不重開已結物理單。0546按其驗收句及當前處置接續整理。主單0540未因這四張完成就宣稱整船完工。

## 重跑與保存

各子資料夾有自己的新程式、原始讀數、輸入SHA及限制；不import作者檢查器。general僅執行複製的**設計產圖器**驗重產，幾何/反向尺獨立。所有雕刻真相仍是events與CLI，不手改work/cache。
SHA manifest列本包每檔，`.gitattributes`保持證據位元組。原始14/16/19/20號報告不靜默改寫。主驗收Sirius負責簽收；三個當期唯讀複驗視角為deck_audit、hardware_audit、ornament_audit，不借用其他persona身分。
