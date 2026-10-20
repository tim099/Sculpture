# 法式殖民城鎮建築套件（風格 fr）—— 筆記（TASK-0741）

委託：Tim 2026-10-19（TOWN_BUILD.md §6）：建築跟造船同一套 voxel（0.1 m、子模組、部件跟船通用）；住宅照參考圖（灰泥牆土黃／藍／米白、紅陶瓦四坡頂、深出簷、二樓木陽台、煙囪、圍出院子）；城牆照世紀帝國（關鍵部件雕刻、牆身一節斷面沿曲線拉）；找時代的建築圖紙。外觀由 summit 決定、Tim 預覽一次（不派 agent 審草稿）。

規格正本：Blocksail `docs/BUILDING_SPEC.md`（`senate cmd doc --arg op=show --arg name=BUILDING_SPEC`）。參考資料：本作品 `references/README.md`。

## 第一階段：參考資料（2026-10-19）
- 查了四個方向：Saint-Domingue 1791 年版畫冊（Ponce／Phélipeau，JCB、NYPL、BnF）、Le Cap 平面圖（Manioc，公有領域）、Moreau de Saint-Méry（只讀到 Les Cayes 那段的二手引用）、HABS（Bolduc House MO-1105、Madame John's Legacy、Old Ursuline Convent）、聖多明哥殖民區、Natchitoches 的木柵堡。
- 沒查到的照實寫：ANOM 的 DFC 平面圖、Moreau 描寫 Le Cap 房子的原文、Cahokia／Parlange 的 HABS 編號（LOC 被機器人驗證擋，⛔ 沒去闖）。
- 只存連結與讀數，圖檔一張都沒下載。

## 第二階段：新圖紙＋產生程式（design/）
| 檔 | 做什麼 |
|---|---|
| `kit.py` | 調色盤（角色色）、Model（分層 body／gallery／roof）、四坡／兩坡／單坡屋頂（高度場取最高 ⇒ 自然長天溝）、部件擺放＋挖洞（turn 公式抄引擎）、毛石、隅石、線腳、三視圖圖紙 |
| `parts.py` | 10 個通用部件（窗、落地窗、門、貨門、氣窗、老虎窗、煙囪、弧拱窗、教堂圓拱窗、圓窗） |
| `houses.py` | 住宅 A／B／C |
| `public.py` | 酒館、倉庫、市場、市政廳、總督府、教堂 |
| `walls.py` | 城牆 1～3 級 × 斷面／塔／城門／接頭／收尾 |
| `build.py` | 全部產生：masks、sheets（新圖紙）、manifest、verify；配色變化、樣板段、樣板街 |
| `apply.py` | 下 CLI：create／stamp（只補差）／anchors／links／models／check |
| `render.py` | 引擎預覽圖＋對照表 |

## 第三階段：落格與組裝
- 子作品 120 件（部件 10、各棟的牆身／屋頂／廊 27、成品 12＋配色變化 3、城牆模組 15＋樣板段 3…），parent 都是本作品；本作品 ＝ 樣板街（只有關聯）。
- 讀數見規格 §8.1；全部 缺 0 多 0 色差 0、link_overlap 0、link_clipped 0。

## 🩸 踩過的（細節在規格 §10）
1. 屋頂在牆頂那一圈斷開（元件數 2）⇒ 屋面蓋過牆頂那一層。
2. 陽台托架撞一樓窗的百葉 2 格 ⇒ 托架挪位置。
3. 鐵門扇、門碉樓兩側的短柵、一級塔的二樓：差一格沒接上（浮空 13,028 格那次是塔的二樓）⇒ 鉸鏈壓到門柱、短柵伸進碉樓、樓板伸到挑出的牆。
4. 總督府門廳 5.6 m 塞不下門＋兩扇窗（百葉壓到壁柱 17 格）⇒ 加寬到 6 m。
5. 老虎窗靠斜脊太近，後半截凸出屋面 ⇒ 往中間挪。
6. 樣板段的框照「有格的地方」算 ⇒ 引擎擋（城門框 96 高、塔框 84 高，被關聯的作品整個框都要放得進來）⇒ 照框算。
7. RGB332 沒有真的灰：145 畫出來像綠磚 ⇒ 毛石改 177。

## 沒做的
碉堡、砲台、長官的屋子；城牆四級稜堡、三級方塔；室內；遠近四級（TASK-0740）；第二套海盜據點。
