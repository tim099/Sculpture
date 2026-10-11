## 階段四 TASK-0484（2026-10-11 雕完）
- [x] 59 片底肋（facing=x+，先貼 f+00 驗軸向）＋ keelson；兩處設計不一致已修（底肋讓出 keelson 180 格、keelson 座位補 20 格），讀數見 notes.md「階段四」
- [x] 驗收：結果帳 0 差、接合沒洞、側面／橫剖面疊新圖紙 03、反向對照偏 3 報 3、船中 vs 15 號 ≤ 0.73 格
- [x] 製作筆記 `journal/`（心路歷程，連 `overlays/` 的圖）

## 階段五 TASK-0485（2026-10-11 雕完）
- [x] 新圖紙 04 肋骨圖 v1 ＋ 雙肋 132 片（f −40..+25，futtocks・top timbers，全部同色 141），讀數見 notes.md「階段五」、心得 `journal/stage5.md`

## 下次從這裡接
- [ ] 階段六：**船頭與船尾**（TASK-0486）—— ✅ 讀圖（10-11 凌晨）→ ✅ 新圖紙 03 v2 船殼延伸、04 v2 兩頭骨架（10-11 存檔點，**還沒雕**；讀數見 notes.md「階段六」、心得 `journal/stage6.md`）
  - [x] `stampvox`（TASK-0487）提交＋出廠（SCP_Core e1869a1、Senate 463ed65；2026-10-11 出廠）
  - [x] 雕之前修（2026-10-11 wake #130；做法與讀數見 notes.md「階段六 雕之前修」）：
    - [x] 船尾 Z 126 以上 nan：根因是 9 號站本身在 126.1 以上就算不出值（1–9 號站的樣條跨站），`_taper` 只是其中一處 ⇒ ztop9 夾到有效高度
    - [x] 船尾 B 水線改用 B 自己的描線（本 session 沿線追蹤）；同時船尾 g_end 1.6 → 2.5、接縫補正只攤 16 格 ⇒ 六條水線 vs 原圖最大 ≤ 0.58
    - [x] 高度換算改成一致的形式，重算 counter／船尾面（同一個 z 的 X 差 −0.71..+0.75）
    - [x] 窗台、窗楣、taffrail、wing transom 從 dy 0 起
    - [x] 艉柱 head_z 88 → 81、內艉柱 82 → 75（雕刻時先刻 370 格）
    - [x] 懸出部側面：雙片的方 quarter timbers（X 122–127、115–120、108–113、101–106）
    - [x] knighthead dy [5,8]＋dy 3–4 的 chock；hawse 4 根各 4 格；船頭 cant 雙片 6 對（弧長等分）
    - [x] transoms 改成連續的水平帶子（Z 70–74…49–54）；針孔、夾縫、碎塊照 fill 規則
    - [x] 文字（cant 22.5°、wing transom 27.9 ft、hawse、transoms、counter 寬度）；verify 報「計畫 vs 清單」的 x／z／dy 不符
    - [x] 重產 → 再派 verifier（第二輪，3 個：木料帳 fail、船殼 fail、美觀 pass_with_minor）→ 照它們的讀數修完，本小姐自己量（同一對 cant 的缺口 0、舷頂接縫無台階、接縫的縫 1 格、從船尾看的洞只剩窗位）。第三輪沒派 —— Tim：「細節放上去之後再細修，不用一次到位」
  - [x] 雕（2026-10-11）：先刻柱頭 4 盒 370 格 → 51 根逐根 stampvox，每根 placed ＝ 清單格數、總數差 ＝ 清單格數；363,037 → 435,561
  - [x] 雕完：結果帳 0 差（`design/tools/ledger_stage6.py`）、1 元件、空腔 0、匯出 87,698 面、過程圖 `overlays/stage6_*`
    - ⚠ 沒做「疊新圖紙 04 v2」與它的反向對照：04 v2 是從同一批清單畫出來的，拿作品去比它只會證明作品＝清單（結果帳已經證明了），是同源的證人。設計＝原圖那本帳在船殼（03 v2 vs 11 號，兩位 verifier 量過）
  - [x] 驗收那格「延伸段 vs 11 號 ≤ 1 格」：Tim 2026-10-11 接受船頭的誤差（已簽）；船尾 B 改用自己的描線之後 ≤ 0.54
  - [ ] **放上去之後再細修**（Tim 2026-10-11：「細節可以實際放置上去後再細修，不用一次到位」；讀數見 notes.md「階段六 雕之前修＋雕刻」）：
    - [ ] 艏柱頭後面中線的槽（dy 0–2、X 665–671、夾在兩根 chock 之間，約 11 格深）—— 做 bowsprit 時決定要填還是當 bowsprit 座
    - [ ] S-counter-timber-35 在 Z 81 多 3 格 dy 34（舷邊那根的碎塊歸過來的）
    - [ ] 上層船尾窗（Z 113.6–123.8、hb 18.25–28.22）被 dy 25–26 的 counter timber 穿過 —— 鋪船尾板時開窗再處理
    - [ ] 船頭 cant 根部擠在一起、後片沒碰到 deadwood／apron（只靠鄰片撐）
    - [ ] 高度換算的 LWL 用直線擬合，船尾那段可能偏高 0.6–0.9 格（verifier minor，證據兩邊都有）—— 做砲門高度前先決定
    - [ ] 階段二 gripe 在 Z 66–67 伸出艏柱前面一塊平台 —— knee of the head 子作品時處理
    - [ ] 階段五的方肋頂沒照 sheer_points 起翹（船頭幾乎沒有 sheer 上揚）—— 要不要改等 Tim
- [ ] 砲門與甲板：先把砲門（gun deck、spar deck）與甲板高度畫進新圖紙，再在肋骨上開口（port sill／lintel）；⚠ 高度用作品的框（11 號 body plan 沒畫 drag）：sheer plan 讀數用 plan.json `ends.provenance.frame_of_heights` 的一致換算（Z ＝ 62.86 ＋（Z_sheer − Z_LWL(X)）／0.15859 × 局部比例），⛔ 不要用舊式「− 0.01538·(439.2 − X)」（比例修正算兩次）；船尾約 −5、船頭約 +3（見 notes.md「階段六」）
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
