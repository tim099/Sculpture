## 階段四 TASK-0484（2026-10-11 雕完）
- [x] 59 片底肋（facing=x+，先貼 f+00 驗軸向）＋ keelson；兩處設計不一致已修（底肋讓出 keelson 180 格、keelson 座位補 20 格），讀數見 notes.md「階段四」
- [x] 驗收：結果帳 0 差、接合沒洞、側面／橫剖面疊新圖紙 03、反向對照偏 3 報 3、船中 vs 15 號 ≤ 0.73 格
- [x] 製作筆記 `journal/`（心路歷程，連 `overlays/` 的圖）

## 階段五 TASK-0485（2026-10-11 雕完）
- [x] 新圖紙 04 肋骨圖 v1 ＋ 雙肋 132 片（f −40..+25，futtocks・top timbers，全部同色 141），讀數見 notes.md「階段五」、心得 `journal/stage5.md`

## 下次從這裡接
- [ ] 階段六：**船頭與船尾** —— 新圖紙 03 的船殼只到 11 號 1 號站（X 617.1）與 9 號站（X 181.5）⇒ 先把船殼延伸到 stem 的 rabbet 與 sternpost（船頭的水線怎麼收到 rabbet、船尾的 run 與 counter／transom），再補船頭 cant frames、船尾骨架（fashion pieces、transoms）
  - 資料：02 號側面（rabbet、船尾形狀）、11 號（水線半寬若能讀到兩頭）；缺的參考其他巡防艦，美觀優先
- [ ] 砲門與甲板：先把砲門（gun deck、spar deck）與甲板高度畫進新圖紙，再在肋骨上開口（port sill／lintel）；高度逐站相對龍骨量
- [ ] 04／15 號的 rider keelson（15"x18"）與 Humphreys 9"x24" deadwood 要不要做
- [ ] 船殼板（外板）：⚠ 先處理兩頭肋骨的 bevel —— 每片 3 格厚用片中心判斷船殼內外，兩頭最外一欄最多凸出 molded 線 0.8 格（3,278 voxel，f+25 B 的 x 617 欄超出船殼範圍）；外板落地會被它們擋住 ⇒ 鋪板前先逐欄刻掉凸出的格，或讓外板遮罩避開。內板（ceiling）鋪時順便蓋掉 keelson 兩側那道 1 格縫
- [ ] 橫樑與甲板（15 號：orlop 13.09 ft、berth 19.14、gun 26.27、spar 33.79 ft at CL）→ 柱與艙內 → 桅檣
- [ ] 船尾 transom、counter；船首 knee of the head
- [ ] 裝飾物（大砲、舵、其他重複物件）：先開子作品（parent_work＝本作品）雕好，再 `work sub=assemble` 匯入

## 範圍（Tim 2026-10-11）
- 玻璃等透明部分、帆、纜索：先不做（之後 /scp-sculpture 擴充成可嵌模型再處理）

## 待確認
- [x] keel drag：不做（2026-10-11 決定，理由見 notes.md）；⚠ 甲板／舷弧／砲門的高度要逐站相對龍骨量，不要用一條水平線
- [ ] sided（艏柱／艉柱／deadwood／apron 5 格）仍是設計決定
- [ ] 底肋頭長 3.6 m 仍是設計決定（02／15 號都沒畫）
