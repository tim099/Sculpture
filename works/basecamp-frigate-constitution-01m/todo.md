## 階段四 TASK-0484（2026-10-11 雕完）
- [x] 59 片底肋（facing=x+，先貼 f+00 驗軸向）＋ keelson；兩處設計不一致已修（底肋讓出 keelson 180 格、keelson 座位補 20 格），讀數見 notes.md「階段四」
- [x] 驗收：結果帳 0 差、接合沒洞、側面／橫剖面疊新圖紙 03、反向對照偏 3 報 3、船中 vs 15 號 ≤ 0.73 格
- [x] 製作筆記 `journal/`（心路歷程，連 `overlays/` 的圖）

## 階段五 TASK-0485（2026-10-11 雕完）
- [x] 新圖紙 04 肋骨圖 v1 ＋ 雙肋 132 片（f −40..+25，futtocks・top timbers，全部同色 141），讀數見 notes.md「階段五」、心得 `journal/stage5.md`

## 下次從這裡接
- [ ] 階段六：**船頭與船尾**（TASK-0486）—— ✅ 讀圖（10-11 凌晨）→ ✅ 新圖紙 03 v2 船殼延伸、04 v2 兩頭骨架（10-11 存檔點，**還沒雕**；讀數見 notes.md「階段六」、心得 `journal/stage6.md`）
  - [x] `stampvox`（TASK-0487）提交＋出廠（SCP_Core e1869a1、Senate 463ed65；2026-10-11 出廠）
  - [ ] 雕之前修（verifier，詳見 notes.md「階段六 verifier」）：
    - [ ] `draft_ends._taper`：8 號站頂以上斜率是 nan ⇒ 當 0 —— 船尾上部才長得到 128.5（taffrail 4 層、counter timbers 到頂）
    - [ ] 船尾 B 水線改用 B 的描線（verifier 描得到：x 718 → 9 號站），不用 C、A 內插
    - [ ] 高度換算改成一致的形式（Z ＝ 62.86 ＋ sheer 上高於水線 A 的高度 × 3.048），重算 counter／船尾面那幾點（差 ≤ 0.6）
    - [ ] 窗台、窗楣、taffrail、wing transom 從 dy 0 起（船尾中線那道縫）
    - [ ] 艉柱 head_z 88 → 81、內艉柱 82 → 75，雕兩頭之前先刻掉 Z 81–87 的艉柱
    - [ ] 懸出部側面的洞：加 X 126 的 quarter timber，或改成接續扇形的斜木
    - [ ] knighthead dy [5,8]＋dy 3–4 的 chock；hawse pieces 改 4 根各 5 格；船頭 cant 改雙片
    - [ ] transoms 加 [55,58]、[50,53]、[45,48]；補根部 4 個針孔；清掉 1–6 格的碎塊
    - [ ] 文字：cant 角度 22.5°、wing transom 約 27.9 ft、hawse5 dy；verify 要對「計畫 z 範圍 vs 實際」報不符
    - [ ] 重產 → 再派 verifier（至少木料帳與美觀兩個）
  - [ ] 雕：`masks/ends/*.vox.txt` 照 `verify_frames_ends.json` 的順序逐根 `op=stampvox at=0,0,0 expect_pixels=<voxels>`，每根讀回 placed ＝ voxels、skipped 0
  - [ ] 雕完：結果帳（events 重播 vs 階段六前＋清單）、連通、空腔、疊新圖紙 04 v2（從圖紙像素出發）＋反向對照偏 3 報 3、過程圖 `overlays/stage6_*`、匯出面數
  - [ ] 驗收那格「延伸段 vs 11 號 ≤ 1 格」：船頭原始差到 3.1 格（艏柱位置 02 vs 11、1 號站本身較瘦）—— 等 Tim 決定接不接受
- [ ] 砲門與甲板：先把砲門（gun deck、spar deck）與甲板高度畫進新圖紙，再在肋骨上開口（port sill／lintel）；⚠ 高度用「從水線量」的框（＝作品的框）：sheer plan 讀數要減 drag（0.01538·(439.2 − X)），船尾約 −5、船頭約 +3（見 notes.md「階段六」）
- [ ] 04／15 號的 rider keelson（15"x18"）與 Humphreys 9"x24" deadwood 要不要做
- [ ] 船殼板（外板）：⚠ 先處理兩頭肋骨的 bevel —— 每片 3 格厚用片中心判斷船殼內外，兩頭最外一欄最多凸出 molded 線 0.8 格（3,278 voxel，f+25 B 的 x 617 欄超出船殼範圍）；外板落地會被它們擋住 ⇒ 鋪板前先逐欄刻掉凸出的格，或讓外板遮罩避開。內板（ceiling）鋪時順便蓋掉 keelson 兩側那道 1 格縫
- [ ] 橫樑與甲板（15 號：orlop 13.09 ft、berth 19.14、gun 26.27、spar 33.79 ft at CL）→ 柱與艙內 → 桅檣
- [ ] 船首 knee of the head、head rails、trailboards（裝飾的部分做子作品）；船尾 quarter galleries（子作品，掛在 fashion pieces 外面）；艉柱頭伸出 wing transom 約 7 格 —— 做舵與 counter 外板時決定要不要削
- [ ] breast hooks（5 道＋2 道 deck hooks）、transom knees、stern knee、hawse holes —— 甲板與艙內階段
- [ ] 裝飾物（大砲、舵、其他重複物件）：先開子作品（parent_work＝本作品）雕好，再 `work sub=assemble` 匯入

## 範圍（Tim 2026-10-11）
- 玻璃等透明部分、帆、纜索：先不做（之後 /scp-sculpture 擴充成可嵌模型再處理）

## 待確認
- [x] keel drag：不做（2026-10-11 決定，理由見 notes.md）；~~甲板／舷弧／砲門的高度要逐站相對龍骨量~~ ⚠ 階段六更正：作品是「從水線量」的框，sheer plan（相對龍骨）的讀數要減 drag 才放得進來（見 notes.md「階段六」）
- [ ] sided（艏柱／艉柱／deadwood／apron 5 格）仍是設計決定
- [ ] 底肋頭長 3.6 m 仍是設計決定（02／15 號都沒畫）
