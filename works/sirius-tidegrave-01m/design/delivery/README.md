# 潮墓號遊戲接入候選

## 最新：2026-10-15

目前 `tidegrave_candidate_20261015.vxk` 已更新為動態驗收後修正版，SHA256 `f2561bfc294f91b849f59412d80294e9755e90a2ae1af8d81dea3ea7c2b06c9c`；1,034,323格、checksum `d931433f`，302繩／10帆／116模型。CLI list逐格逐色差0，一格改色負向checksum `be3b0c38`。權威讀數是本目錄manifest.json。

驗收結果 **FAIL**：船上的後桅索路、縱帆sheet與jib靜態穿透已修，但完整掛帆物理仍穿桅／桁／索具（TASK-0603），附件局部硬體接觸也未全簽。詳見 `../DYNAMIC_20261015.md`。這是可重現的候選，尚非正式遊戲接入通過。

## 以下為較早2026-10-15歷史

使用 `tidegrave_candidate_20261015.vxk`，SHA256 `76d945aca4f55556f5b952b7a5a3b4183cbe00a6f1b9d44f7359a56fd3bc5036`；1,034,267格、checksum4cb88a33、302繩／10帆／116模型。`manifest.json`與`../verify_vxk_delivery.json`已刷新，CLI list逐格逐色0差，一格改色反向能失敗。驗證器已改讀搬家後的Blockside/VoxelKit。

8lift、16standing、10brace與後桅帆頭整改及有限獨立後驗，見`../CONTINUED_20261015.md`與`../continued_20261015/independent/REPORT.md`。七梯/操舵的既有fixture證據屬舊a599快照，本輪未重跑正式遊戲，不能把它稱作最新資產的正式匯入通過。全302繩與自由布連續動態仍未全驗。舊nav候選需對當前Blockside源碼重審，不能直接套。

## 以下為2026-10-14交付歷史（舊候選保留，非目前匯入檔）

資產：`tidegrave_candidate_20261014.vxk`；精確SHA256、位元組數、checksum与保留段數以同目錄manifest.json為準。這是已驗收幾何的交付副本，正式選單與七梯修法仍由遊戲作者接入。

0.1 m/格，+X船頭、-Y左舷、y120格中心為對稱面。ship meta waterline_z=52；六層甲板、54砲（48舷砲／6固定艏砲）、雙庫各24桶/2400lb、300繩、10帆旗、116模型。不要把旋轉三聯砲、潛航、海怪或舵動畫當作已實作功能。

已保存rig/models/parts/meta/ends。所有十帆旗帶meta；帆自己的16條sheet帶meta，其他繩不宣稱全標；300條繩均保留兩端參照。固定點與外部模型比例以封裝內資料為準，不另從外框猜。

本地fixture的geo設定（需遊戲作者依正式介面覆核）：spar=[114,140]、marines=[180,215]、center=155、aim=90、aimZ=[30,480]、deckAim=[74,106]、rigAim=[210,410]、handsK=1。初始水密與質量只是在目前遊戲下的測量，未作真船穩性認證。

七梯與操舵接入：`../nav_deck_candidate/40_crew.patch`、`42_hands.patch`，對應source.json與crew_source.json。兩個同高139但互不相通的艏／艉樓按deckFloor與端點位置分層；保留新版navRegions。LIFT3對應本船已開好的1.8m高×0.7m寬淨空；其他船需回歸。操舵站位按wheel本身XY/Z，不用整船spar高度。原nav_candidate是舊版，只作歷史，不要套用。

重驗：`python -I -X utf8 ../validate_vxk_delivery.py` 將VXK解碼與CLI當前清單逐格逐色對照，獨立scalar checksum，改一格的反向對照必須失敗；它會刷新本目錄副本与manifest。`python -I -X utf8 ../test_game_fixture.py 10 deck` 為新版隔離候選10秒＋操舵替補測試；`0 meta`量原版。報告記錄VXK與當前JS、兩候選檔來源hash。替補使用真stepHand、60Hz並恢復每幀HAND_PATHS，世界戰鬥於該補位probe凍結。

最新a5994eee快照：348人、2舵手、54砲最低足額、7梯14端region可達、10秒GL0；強制兩舵手傷亡後35.133秒兩人實到quarter z139並轉舵手。仍有舊索具對模型的動態碰撞、ratline誤綁及一格桅邊帆擦，見../CONTINUED_20261014.md；不把候選交付宣告全船已正式驗收。

靜態／舵連續包絡／模型／帆繩／旗的獨立報告在`../audits/20261014/`，總斷點在`../CHECKPOINT.md`。不同scope與快照的限制各自保留。
