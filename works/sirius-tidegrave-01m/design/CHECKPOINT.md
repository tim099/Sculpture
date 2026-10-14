# 《潮墓號》續作入口 — 2026-10-14（Tim 要求先告一段落）

主單TASK-0540；工作記憶sirius-tidegrave；設計者Sirius。任務仍in_progress，本次以整改與可讀回的驗收材料收尾，沒有把正式遊戲接入當成已完成。

## 當前資產

- 船殼sirius-tidegrave-01m；組裝sirius-tidegrave-01m-assembly；0.1m/格，+X船頭、-Y左舷、鏡面y120格中心。
- 1,036,066實體格，6鄰接1元件、封閉空腔0、鏡像缺格／異色0、link overlap/clipped0。
- 六層甲板、七實體梯、三桅與艏斜桅；54砲、116模型（19網格）、300繩、10帆旗、17關聯外框。
- preview絕對路徑：D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m-assembly/exports/tidegrave_preview.vxk。
- 最新SHA256：`5e92885eb98c095b41f21d80e0f69e287206e55be7815fe27c6a4e8abc42f8d1`；voxel checksum `bdd5856b`。交付副本與逐格驗證：design/delivery/及design/verify_vxk_delivery.json。
- 總圖Rev04：design/general_arrangement.png，SHA `0bda926677886c2a3e8601fcce9e664768805e2e376eb4ab1335b8c24a7aba9d`。照片final_review_20261014.png及final_stern_review_20261014.png；照片早於最後一條brace綁點升6格，船體／模型／帆／其他繩未變。

## 這輪完成

1. 重建遺失的preview與早期驗收；骨架118405、外板549603格的逐格逐色兩帳、真實3格反向對照及水線洪泛證據收進design/audits/20261014。修正圖紙uint8 RGB溢位。甲板舊清單是零格增量，重新由CLI匯出完整當前甲板，沒有把空圖當通過。
2. 舵輪移至(198.5,143.5,139)，保持scale .2/pivot(50,52,0)。105目標模型對船、彼此正體積碰撞0；舵輪40/40底足支持。54砲20m中心射線阻擋0；砲Y+3的真正反向對照報2相交格。
3. 舵槽按color guard精雕1318格。actual±30度：61角精確檢查及241角＋0.095818格連續保守包絡皆碰撞0。完整組裝件水下洪泛封閉空氣1,370,871格、兩內艙探針不到外水。遊戲尚未消費完整hinge轉軸，不能宣稱已動畫轉舵。
4. 五條穿舷牆繩改綁有根且鏡像的導索柱，新增144格。brace最後綁到柱頂(335,170,136)，完整曲線含半徑內穿0；其他11條已驗繩的曲線、端點、半徑在這次單一anchor修改前後逐項相同。
5. 操舵繩改繞樓梯，增加轉角(225.5,106.5,151.5)及一段繩；甲板精準孔quarter48/upper6/weather6，支柱26格，沒有刻梯。全部七段操舵繩含半徑內穿0。
6. 旗升26格，ornament旗竿以(105,120,208)為根延長23格。旗嚴格內片穿骨飾0；17格接觸均為新旗竿固定邊附着。裝飾31768格、鏡像0、空腔0，219個子件元件均face接船。
7. 新版隔離fixture仍有348船員／2舵手，54砲均滿足crewMin、所有模型有foot、七梯候選版10秒運行與GL error0。報告各自帶source hash，不把不同快照混為同一場測量。

## 尚未結清／下次順序

1. 七梯正式接入仍在ame覆核：原遊戲按高度合層，只留最大walk component，丟了同高艏樓；幾何無須再造梯。design/nav_candidate/42_hands.patch、42_hands_candidate.js與source.json，酒館Florin seq23445已交付。不能用候選版七梯成功替代正式遊戲已套用。
2. 從本檔、notes.md、design/audits/20261014、delivery/README.md及各子單新wrapup接起，逐項簽驗收與結單；本次未把尚未逐格簽完的單宣告done。
3. 主單全結前仍需整理／簽收各階段兩本帳与完整再生入口、正式遊戲匯入後複驗。完整人體動線、所有帆桁動畫掃掠未由本輪靜態驗收涵蓋，見rig_final.json／model_final.md的限制。
4. TASK-0516仍是藝廊素材採用與整合待決，不直接覆寫ame施工中的art或HTML。

## 操作界線

所有作品變更走senate cmd sculpture。初建build_structure.main會把後續殼當多餘骨架刪除；build_rig.main會覆寫baseline；不要在成船盲跑。修正脚本與守門清單保存；共用模型、帆繩、事件帳不手改。

觀測／匯出大型組裝件採串行；本輪並發觀測曾讓一次export等不到鎖，確定零寫入後已串行重匯。回傳成功與輸出路徑不替代hash、讀回與獨立資料。
