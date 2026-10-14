# 潮墓號遊戲接入候選

資產：`tidegrave_candidate_20261014.vxk`；精確SHA256、位元組數、checksum与保留段數以同目錄manifest.json為準。這是已驗收幾何的交付副本，正式選單與七梯修法仍由遊戲作者接入。

0.1 m/格，+X船頭、-Y左舷、y120格中心為對稱面。ship meta waterline_z=52；六層甲板、54砲（48舷砲／6固定艏砲）、雙庫各24桶/2400lb、300繩、10帆旗、116模型。不要把旋轉三聯砲、潛航、海怪或舵動畫當作已實作功能。

已保存rig/models/parts/meta/ends。所有十帆旗帶meta；帆自己的16條sheet帶meta，其他繩不宣稱全標；300條繩均保留兩端參照。固定點與外部模型比例以封裝內資料為準，不另從外框猜。

本地fixture的geo設定（需遊戲作者依正式介面覆核）：spar=[114,140]、marines=[180,215]、center=155、aim=90、aimZ=[30,480]、deckAim=[74,106]、rigAim=[210,410]、handsK=1。初始水密與質量只是在目前遊戲下的測量，未作真船穩性認證。

七梯接入：`../nav_candidate/42_hands.patch`。兩個同高139但互不相通的艏／艉樓必須分成不同空間component；原版只留最大層，故只得到六梯。候選修法維持砲甲板政策，在有梯端點的h*次區另建空間層。採用前先對source.json的基底hash；遊戲源碼由ame與gura施工，不盲蓋。

重驗：`python -I -X utf8 ../validate_vxk_delivery.py` 將VXK解碼與CLI當前清單逐格逐色對照，獨立scalar checksum，改一格的反向對照必須失敗；它會刷新本目錄副本与manifest。`../test_game_fixture.py 10 nav` 為隔離七梯候選10秒測試；不帶nav量原版。報告記錄VXK與當前JS來源hash。

靜態／舵連續包絡／模型／帆繩／旗的獨立報告在`../audits/20261014/`，總斷點在`../CHECKPOINT.md`。不同scope與快照的限制各自保留。
