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
    - [ ] 高度換算的 LWL 用直線擬合，船尾那段可能偏高 0.6–0.9 格（verifier minor，證據兩邊都有）—— 砲門那段（X 185–625）量過不影響（≤ 0.26 格，階段七）；只剩船尾 X < 185 的 counter／船尾面
    - [ ] 階段二 gripe 在 Z 66–67 伸出艏柱前面一塊平台 —— knee of the head 子作品時處理
    - [ ] 階段五的方肋頂沒照 sheer_points 起翹（船頭幾乎沒有 sheer 上揚）—— ⚠ 鋪了外板之後這條線變得很顯眼（`overlays/stage7_view_side.png`：白帶照 sheer 往船頭翹，舷頂幾乎是直的，兩條線不平行 ⇒ 船頭看起來往下垂）
      - **拍板（Tim 2026-10-11 交給本小姐、美觀為主）：照 sheer_points 起翹**；在肋骨頂與外板上面往上補（不用拆），跟舷牆（spar deck 那一層）一起做
## 階段七 TASK-0489（2026-10-11 雕完）
- [x] 讀圖：11 號 gun deck 砲門 14 個（`design/source_ports.json`）＋ Humphreys 1794 規格（wales、black strakes、船底板、砲門）
- [x] 新圖紙 05 外板與塗裝 v1（`design/draft_planking.py`、`sheet05_planking_v1.png`）：dubbing（overwrite 蓋掉凸出 molded 線的 3,698 格）、外板 1 格、wales 2 格、銅／黑／白帶、結構露在外面的那層上色
- [x] 雕：8 刀 stampvox，435,561 → 593,700；結果帳 0 差、不漏水、反向對照會叫、1 元件；過程圖 `overlays/stage7_*`、心得 `journal/stage7.md`
- [x] LWL 那題對砲門不影響（直線擬合 vs 圖上畫的 LWL ≤ 0.26 格）

## 階段八 TASK-0490（2026-10-11 雕完）
- [x] 船頭那個砲門（平行四邊形）讀圖；新圖紙 06（`design/draft_ports.py`、`sheet06_ports_v1.png`）；44 刀 carve ＋ 砲門框 416 格；593,700 → 586,192；結果帳 0 差、透光、框沒有縫、1 元件、反向對照會叫（`design/tools/check_ports.py`）；標記 `砲門:begin／end`
- [x] 雕完派的 3 個 verifier（原圖幾何／帳與結構／外觀）：無 blocker；第 4 個砲門白帶、船頭砲門後壁的縫、兩個單格空腔 ⇒ 細修 v1.1 已修（586,200）；讀數見 notes.md「階段八」
- [x] 階段七外板封住的封閉空腔 ⇒ 2026-10-11 補實（Tim：「用鄰近 voxel 顏色填滿」）：2,200 個／5,602 格、`design/tools/fill_cavities.py after_stage8`、標記 `補空腔:begin／end`；591,668、空腔 0、匯出 120,832 → 107,225 面（notes.md「補空腔」）
  - [ ] ⚠ 之後每鋪一層封得住空氣的東西（內板、甲板…）都會封出新空腔 ⇒ 那一階段收尾時再跑一次 `fill_cavities.py <名稱>`
- [x] 白帶補漆的兩角（第 4 個左上角 (283, 99) 等）⇒ v1.2 一起補（第 4／13／14 個共 10 格）
- [x] `check_ports.py` 砲門框量不到 cant 那一帶 ⇒ v1.2 加「牆不能有洞」那一格（從產物量；反向對照會叫）
- [x] 船頭那個砲門斜看有鋸齒（格子表現斜邊）—— Tim 目視檢查過砲門：「沒問題的」（2026-10-11）
- [x] **v1.2 船頭砲門改垂直**（Tim 2026-10-11 稍晚：「船頭的炮窗 試著雕刻成垂直的吧」＋示意圖 ＝ 平行四邊形的外框 X 643..651）：草稿（刻 138／補 4／補漆 16）→ Tim「套用吧 GO」→ apply；586,066；`砲門:end` 已移（notes.md「階段八 v1.2」）

## 階段九 TASK-0496（2026-10-11 雕完）
- [x] 讀圖＋資料（04／15 號、Humphreys、Martin《Close Up》、1816 Waldo、1931 inboard profile）；新圖紙 07（`design/draft_interior.py`、`sheet07_interior_v1.png`）；甲板高度定案（分段平整、高低差在艙壁；Tim「甲板大致平整」）
- [x] 內板、limber、clamps／stringer／spirketting、斜肋 6 對、hooks、舷頂封口、中線換色、補空腔 ⇒ 817,010；v1.1 橫向 rider 14 根 ⇒ **821,444**；標記 `船殼內部:begin／end`；`check_interior.py` 全過、反向對照會叫（notes.md「階段九」）
- [x] keelson 兩側那道 1 格縫：內板蓋掉
- [x] 甲板高度那題 ⇒ 定案在 plan.json `interior.decks`（砲門那邊＋15 號 ＋2）；~~甲板跟著 sheer 走（每個 X 一個值）~~ ⇒ Tim 要大致平整，改成分段平、折在艙壁

## 下一階段（現實順序：內板之後是橫樑與甲板）
- **範圍（Tim 2026-10-11）：砲門與其他可動件之後另外做；甲板階段只做甲板主體＋房間，門也不放；甲板骨架跟房間開子作品**
- [ ] ⚠ 先做 TASK-0497（關聯／組裝支援鏡像）—— 兩舷對稱的肘、艙房只做一份
- [ ] 甲板子作品（每層一件，子作品尺寸 ＝ 船殼、at=0,0,0、turn=0）：橫樑（gun deck「每個砲門底下一根、之間一根」）、carlings／ledges、hanging／lodging／dagger knees、standards、waterways、deck hooks、柱子、甲板板；高度照 plan.json `interior.decks`（橫樑底 ＝ clamp 頂）
  - [ ] orlop 平台照 z 38–41 的艙內空氣裁；斜肋穿過的 x 範圍（notes.md 階段九）橫樑開槽或避開
  - [ ] seam 504（前艙口後緣）不是艙壁 ⇒ 放一道橫向的東西（艙口圍板＋隔板或梯子）蓋住 1 格的高低差
  - [ ] deck hooks（船頭 orlop／berth／gun）、berth deck 的 transom knee（船尾 Z ≈ 61）
  - [ ] 甲板做完再跑一次 `fill_cavities.py <名稱>`
- [ ] 房間子作品（關聯進甲板子作品；不放門）：1816 Waldo orlop（filling rooms、bread room／magazine、cockpit、cable tiers…）、berth deck（wardroom、steerage、sick bay）、gun deck（captain's cabin、galley）
- [ ] 舷牆、舷弧（照 sheer 起翹，見階段五那條拍板）：舷牆高度（sheer plan 船尾 rail Z 130–134、waist 約 119.6、見 source_ends_raw.json readings[1] rail_structure）；舷頂蓋板疊在階段九的封口上；spar deck 兩組砲門（船尾 X ≈ 100–371、船頭 X ≈ 515 起）⛔ 現在不開，跟可動件之後一起做
- [ ] ⚠ 重跑 `draft_interior.py` 讀標記 `船殼內部:begin` 並對 world_voxels（已設好）
- [ ] ⚠ 高度一律用 plan.json `ends.provenance.frame_of_heights` 的一致換算；⛔ 不要用舊式「− 0.01538·(439.2 − X)」
- [ ] ⚠ 重跑 `draft_ports.py` 讀 `gunports.world_upto`（階段八第一刀之前），已設好
- [ ] ⚠ 重跑 `draft_planking.py` 要讀 `planking.world_upto`（階段七第一刀之前）—— 讀現況會長出第二層外板
- [ ] `draft_frames_ends.py`（階段六）的 Ctx 也讀現況（events 重播減柱頭）⇒ 雕完重跑會讀到自己雕上去的木料、清單會變；補同一道閘（`framing_ends.world_upto` ＝ 階段六第一刀之前），重產比對事件記的 51 個 sha256
- [ ] 砲門蓋（port lids）與其他活動部件：⛔ 不用 voxel 做 —— 等 `/scp-sculpture` 擴充成可以匯入模型之後用模型做（Tim 2026-10-11）；舷牆上的 hammock netting 同上再看
- [ ] 04／15 號的 rider keelson（15"x18"）與 Humphreys 9"x24" deadwood 要不要做
- [ ] 桅檣（桅位 X：後桅 206、主桅 351、前桅 587 是站位換算，做的時候再對 02 號）
- [ ] 船首 knee of the head、head rails、trailboards（裝飾的部分做子作品）；船尾 quarter galleries（子作品，掛在 fashion pieces 外面）；艉柱頭伸出 wing transom 約 7 格 —— 做舵與 counter 外板時決定要不要削
- [x] breast hooks（hold 裡船頭 2 道、船尾 crutches 2 道 —— 階段九）；deck hooks、transom knees ⇒ 甲板子作品
- [ ] stern knee、hawse holes
- [ ] 裝飾物（大砲、舵、其他重複物件）：先開子作品（parent_work＝本作品）雕好，再 `work sub=assemble` 匯入

## 範圍（Tim 2026-10-11）
- 玻璃等透明部分、帆、纜索：先不做（之後 /scp-sculpture 擴充成可嵌模型再處理）
- 砲門蓋與其他活動部件：不用 voxel 做，等可以匯入模型再做

## 待確認
- [x] keel drag：不做（2026-10-11 決定，理由見 notes.md）；~~甲板／舷弧／砲門的高度要逐站相對龍骨量~~ ⚠ 階段六更正：作品是「從水線量」的框，sheer plan（相對龍骨）的讀數要減 drag 才放得進來（見 notes.md「階段六」）
- [ ] sided（艏柱／艉柱／deadwood／apron 5 格）仍是設計決定
- [ ] 底肋頭長 3.6 m 仍是設計決定（02／15 號都沒畫）
