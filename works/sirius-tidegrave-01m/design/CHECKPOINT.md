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

# 《潮墓號》動態驗收入口 — 2026-10-15

最新正本：`DYNAMIC_20261015.md`、`dynamic_20261015/independent_final/`、`delivery/manifest.json`。

剩餘案例已量，總判定FAIL而非「尚未量」；TASK-0546最後一格不簽，blocked_by TASK-0603（完整掛帆的遊戲物理穿桅／桁／繩）。船上後桅6支索/42梯繩、2後支索、縱帆sheet及jib兩處原靜態穿透已修。十桁完整非同步角域及後桅48線＋2後支索連續掃掠通過；全302繩/10帆的有限動態、透明洞與附著接觸原值均保存。自有繫砲／操舵硬體接觸未泛豁免，逐件簽收仍待。

當前SHA `f2561bfc294f91b849f59412d80294e9755e90a2ae1af8d81dea3ea7c2b06c9c`，1,034,323格、checksum `d931433f`；302繩10帆116模型，總圖Rev07。原有1,034,267格逐格逐色保留，只新增56格有根支架。最新圖 `../overlays/dynamic_final_20261015.png`。正式遊戲未匯入，完整乾淨再生尚未完成。

下一步：TASK-0603修正後對同輸入回歸，簽自有硬體附件接觸，再處理主單的再生與正式遊戲接入。以下為較早歷史，不是目前輸入與判定。

---

# 歷史：較早2026-10-15索路修正

最新正本：CONTINUED_20261015.md、continued_20261015/independent/REPORT.md及delivery/manifest.json。

本輪修8lift、12shroud/4backstay、10brace、四最低ratline與後桅帆頭；302繩10帆116模型，原300繩全保留。木料1,034,267格、checksum4cb88a33、逐格逐色與前輪相同。交付SHA76d945aca4f55556f5b952b7a5a3b4183cbe00a6f1b9d44f7359a56fd3bc5036；總圖Rev06。舊lift穿桁、standing穿course、四ratline端誤認及後桅帆擦已在有限後驗scope內修正；全302繩及自由布的完整動態仍未全驗。

下一步：補剩餘動態/再生與正式Blockside接入複驗，逐項簽單。以下2026-10-14內容是歷史停點，SHA與300繩讀數不再代表目前交付。

---

# 歷史：2026-10-14（Tim「繼續造船 GO」續作）

主單TASK-0540；工作記憶sirius-tidegrave；設計者Sirius。任務仍in_progress。前輪已提交a9b44e8；本輪補甲板meta、七梯實際淨空、桁碰撞及可驗證的舵手接入候選。正式遊戲未套入候選，索具動態仍有已知未結項。

## 當前資產

- 船殼sirius-tidegrave-01m；組裝sirius-tidegrave-01m-assembly；0.1m/格，+X船頭、-Y左舷、鏡面y120格中心。
- 1,034,267實體格，6鄰接1元件、封閉空腔0、鏡像缺格／異色0、link overlap/clipped0。
- 六層甲板、七實體梯、三桅與艏斜桅；54砲、116模型（19網格）、300繩、10帆旗、17關聯外框。
- preview絕對路徑：D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m-assembly/exports/tidegrave_preview.vxk。
- 最新SHA256：`a5994eeeacbb1155776145e3ebc2e69bd743815b7574df45ca6eb58653bdaf73`；voxel checksum `4cb88a33`。交付副本與逐格驗證：design/delivery/及design/verify_vxk_delivery.json。
- 總圖Rev05：design/general_arrangement.png，SHA `5a4944533d5e6d803ee7da41c43e2c7bbaf6cd8a0260021f693bb5e66438b6bf`，桁高同步實物；最新照片continued_stern_20261014.png。Rev04及原5e928快照報告保留作歷史，不能拿其格數當最新。

## 前輪完成（a9b44e8；下面舊格數是當時觀測）

1. 重建遺失的preview與早期驗收；骨架118405、外板549603格的逐格逐色兩帳、真實3格反向對照及水線洪泛證據收進design/audits/20261014。修正圖紙uint8 RGB溢位。甲板舊清單是零格增量，重新由CLI匯出完整當前甲板，沒有把空圖當通過。
2. 舵輪移至(198.5,143.5,139)，保持scale .2/pivot(50,52,0)。105目標模型對船、彼此正體積碰撞0；舵輪40/40底足支持。54砲20m中心射線阻擋0；砲Y+3的真正反向對照報2相交格。
3. 舵槽按color guard精雕1318格。actual±30度：61角精確檢查及241角＋0.095818格連續保守包絡皆碰撞0。完整組裝件水下洪泛封閉空氣1,370,871格、兩內艙探針不到外水。遊戲尚未消費完整hinge轉軸，不能宣稱已動畫轉舵。
4. 五條穿舷牆繩改綁有根且鏡像的導索柱，新增144格。brace最後綁到柱頂(335,170,136)，完整曲線含半徑內穿0；其他11條已驗繩的曲線、端點、半徑在這次單一anchor修改前後逐項相同。
5. 操舵繩改繞樓梯，增加轉角(225.5,106.5,151.5)及一段繩；甲板精準孔quarter48/upper6/weather6，支柱26格，沒有刻梯。全部七段操舵繩含半徑內穿0。
6. 旗升26格，ornament旗竿以(105,120,208)為根延長23格。旗嚴格內片穿骨飾0；17格接觸均為新旗竿固定邊附着。裝飾31768格、鏡像0、空腔0，219個子件元件均face接船。
7. 新版隔離fixture仍有348船員／2舵手，54砲均滿足crewMin、所有模型有foot、七梯候選版10秒運行與GL error0。報告各自帶source hash，不把不同快照混為同一場測量。

## 續作完成

1. 六甲板依CLI各自VXK量floor/厚2格、補kind=deck、level/name/floor/thick，獨立解碼核對。狹艏尖端延至實際floor-1支撐範圍；沒有捏造同高艏艉樓的高度。組裝件名改「潮墓號」，船殼帶sub；新增內部與六甲板預覽preset。
2. 七梯lift3、淨高18格、橫寬y117..123的連續掃掠，精確color guard刻1799格（船殼1771、quarter14、poop14）。actual與guard逐格逐色完全一致，梯子source與14落腳地板全保留；足點穿格與指定掃掠均0。21格sprite框會撞上層梯，明確不宣稱完整sprite/pose淨空。施工圖與可重跑修復入口：design/ladder_clearance_20261014/、repair_20261014_ladder_clearance.py。
3. 刻格最低z113，高於水線52；獨立前後洪泛同1,370,871格、兩內艙probe仍不通外水。恢復一格的反向對照能重現碰撞。actual報告design/audits/20261014/ladder_clearance/final_actual/。
4. 後桅crossjack由255.5降至224.5，實體Z223..226與gaff229..317、boom204..207全連續角度分離。只有該模型、兩條mizzen-topsail.sheet與該帆改；兩sheet含半徑對body內穿0，該帆對十桁嚴格內片0。該帆對桅尚有既存1格微小擦碰，不能報全帆實內片0。
5. 舊nav_candidate已過時。新版design/nav_deck_candidate保留navRegions，按位置選梯端層、cache含deck身份、補砲按meta身份、舵手出生與補位按舵輪位置；CLIMB_LIFT3僅在本船七梯驗過。最終a599快照：兩艘348人、2舵手、54砲班達最低、7梯14端region可達、10秒GL0；強制兩舵手傷亡後，實際stepHand35.133秒兩人到後甲板z139並轉ROLE.HELM。替補probe期間世界戰鬥凍結、每幀照常恢復HAND_PATHS額度；不是額外35秒整世界對戰測試。
6. TASK-0545已簽第1/2/4格，剩兩本帳/反向尺與完整階段再生總整理那格；TASK-0546只簽帆旗與sheet meta那格，其餘不冒簽。新版候選已在tavern seq23593 @ame交付，工作記憶state_continued-clearance-20261014已保存。

## 尚未結清／下次順序

1. 七梯與舵手正式接入需ame覆核新版nav_deck_candidate的40_crew.patch、42_hands.patch及source hashes；不要套舊seq23445候選。正式源碼沒改。其他船的LIFT3、游泳登船、無梯home、多站操舵等分支未完成通用回歸。
2. 從本檔、notes.md、design/audits/20261014、delivery/README.md及各子單新wrapup接起，逐項簽驗收與結單；本次未把尚未逐格簽完的單宣告done。
3. TASK-0546保留未完成：model-aware動態精測查出main/fore course lift直拉桅head、穿兩層上桁；main/fore shroud與course桁有非中央內穿；四條ratline端被遊戲yardNear幾何誤認綁桁；mizzen-topsail對桅既有1格內擦。先逐類修法與遊戲語意綁定，不能靠刪繩或泛豁免冒充零碰撞。完整人體/pose、navSnap接近離開路段、全階段安全再生入口與正式匯入後複驗也尚未全簽收。
4. TASK-0516仍是藝廊素材採用與整合待決，不直接覆寫ame施工中的art或HTML。

## 操作界線

所有作品變更走senate cmd sculpture。初建build_structure.main會把後續殼當多餘骨架刪除；build_rig.main會覆寫baseline；不要在成船盲跑。修正脚本與守門清單保存；共用模型、帆繩、事件帳不手改。

觀測／匯出大型組裝件採串行；本輪並發觀測曾讓一次export等不到鎖，確定零寫入後已串行重匯。回傳成功與輸出路徑不替代hash、讀回與獨立資料。
