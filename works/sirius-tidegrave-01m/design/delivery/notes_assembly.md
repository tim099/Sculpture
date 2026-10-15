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

# 2026-10-14 續造：七梯淨空、甲板標籤與操舵接入

Tim在前輪a9b44e8後要求「繼續造船 GO」。本輪最新資產a5994eeeacbb1155776145e3ebc2e69bd743815b7574df45ca6eb58653bdaf73，checksum4cb88a33，1,034,267格。CLI及獨立actual皆1連通、0空腔、鏡像缺格/異色0、關聯重疊/裁切0；交付副本逐格逐色解碼0差，一格改色反向checksum31c2532c不同。

六甲板獨立VXK量得floor66/91/116/139/139/165與thick2；已補kind=deck及level/name/floor/thick。quarter與forecastle真實同高但範圍分開；窄艏尖按floor-1實格補齊標籤範圍。組裝件主名為「潮墓號」，船殼帶sub；七個preset可看內部與各甲板。

通道施工圖在ladder_clearance_20261014/clearance_plan.png。按lift3、直立高18格、橫向y117..123設計，精準color guard刻1799格：船殼1771、quarter14、poop14；梯source與十四處落腳地板完全保留。獨立連續掃掠及足點穿格皆0，恢復一格會再報碰撞。刻格最低z113，不動水線下；水下封閉空氣前後均1,370,871格。這是1.8m×0.7m指定路徑截面，不是遊戲人體碰撞器；2.1m含透明padding的sprite框會撞644格梯件，因此沒刻梯冒充21格通過。navSnap接近/離開段及動畫pose仍另驗。

後桅crossjack原本與gaff動態互穿；已用CLI由z255.5降至224.5。木桁Z223..226、gaff229..317、boom204..207，任意繞Z連續轉角都分離；也避開yardNear將gaff jaws誤認crossjack。新圖Rev05同步實物桁高；修復入口repair_20261014_crossjack.py與build_rig的plan輸入同步，但初建main仍不能盲跑。actual只有crossjack模型、兩條mizzen-topsail.sheet與該帆改；兩sheet含半徑對body內穿0，該帆對十桁嚴格內片0。對桅仍有舊有一格微擦，不報全面0。

正式遊戲檔未改；接入候選已改用nav_deck_candidate/40_crew.patch及42_hands.patch，舊nav_candidate僅歷史。新版保留navRegions，梯端按x/floor/snap選層、cache含deck身份、補砲按meta身份；操舵出生與補位按wheel實際XY/Z；LIFT3只驗本船七梯。fixture注入改成CFG.ships且斷言命中，防舊replace靜默失效。最新VXK兩艘各348人/2舵手、54砲都達最低、七梯十四端region可達，10秒整世界GL0。兩舵手強制傷亡後，使用真stepHand、60Hz及每幀HAND_PATHS額度，35.133秒兩人到quarter z139並轉ROLE.HELM；這段世界戰鬥凍結，僅驗補位分支。

TASK-0546仍有model-aware新發現未結：main/fore course lift直拉桅head穿上層桁、部分shrouds穿course桁、4條ratline端被yardNear誤綁桁、mizzen-topsail對桅一格舊擦碰。既有voxel-only靜態通過不涵蓋這些。完整動態報告與候選scope需分開讀，不把本輪crossjack修正當全索具通過。完整安全再生與正式遊戲匯入複驗仍待。


判定：本輪剩餘動態案例已執行，總驗收FAIL，最後一格不簽；本單保持in_progress，新增被TASK-0603阻擋。

憑據：最終f2561bfc294f91b849f59412d80294e9755e90a2ae1af8d81dea3ea7c2b06c9c，1034323格/d931433f、302繩10帆116模型；原有1034267格逐格逐色保留，只新增56格有根支架。修掉後桅6支索/42梯繩誤綁與穿桁、2後支索穿桁、縱帆sheet中段穿船體、jib兩處原靜態穿透；否決會新增跨桅交繩的外舷候選。

十桁與非同步雙角域連續掃掠通過；最終48支索梯繩及2後支索含半徑的完整角域通過。全302繩、10帆23場景、fine布對body/model/其他帆/索具的讀數與限制見design/DYNAMIC_20261015.md與dynamic_20261015/independent_final。完整掛帆在遊戲物理中仍有全自由、不透明三角穿桅/桁/繩的確證，已另開TASK-0603；自有繫砲/舵輪硬體接觸原值亦保留，未泛豁免。

球在Sirius（船的附件接觸逐件簽收、完整再生與主單後續），TASK-0603目前尚無參與者，需遊戲物理修正後再對同一輸入回歸。不能因船檔已修或測試已跑完就結本單。
