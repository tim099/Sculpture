# 潮墓號 final actual 獨立驗收 — 2026-10-14

唯讀作品，所有驗收程式由 verifier 另寫，未 import 作者的檢查程式。before 在上一層；舵輪移位後／舵掃掠預驗在 `../after/`；本資料夾全由整改後 actual events/models 重讀。預覽 SHA256 自行讀檔核對：`9f079ab5c5789d4f4253726e97d348e7e28a08dd461dc8b2c82a6269bece018d`。

## 通過讀數

- **結構**：1,036,066格，6鄰接元件1（唯一元件同1,036,066格）、3D封閉空腔0、y120鏡像缺格0／異色0。支持探針保留。`preflight_grouped_carve.json` 是final actual，mask_count=0，沒有做假設刪格。
- **105目標模型**：54砲、48桶、舵輪、羅經櫃、絞盤；每來源voxel經actual變換後對assembly unit cubes，正體積碰撞0；105模型彼此正體積碰撞0。`report.json`。
- **碰撞尺反向對照**：直接抽取同一支`verify.py`的`touched()`函式（AST只編譯函式，不重跑全套）。真實砲-S01原位0；記憶中Z+3仍0，接著實際Y+3測得2個正體積相交對／2個船體格，故能辨識確定穿牆。位移僅在記憶中，未改作品。`gun_negative_control.json`與可重跑`gun_negative_control.py`。
- **七實體梯端點**：14個foot/head全部腳下有格，向上14格淨空。只驗端點，不宣稱完整梯身或遊戲路徑的可通行性。遊戲同高艏艉樓分區問題在主agentfixture另驗。
- **54砲20m炮口射線**：從muzzle格中心，向muzzle-breech方向，以DDA逐格追200格，對整改後船體阻擋0。`sweep_rays_hull.json`。
- **舵掃掠**：actual source events 7428格，neutral對船0；依hinge(135,120.5,0)及正規化axis(-.2983,0,.9545)，-30..30每1°共61角OBB/AABB SAT正體積相交全部0。`sweep_rays_hull.json`。
- **完整±30°連續保守包絡**：241角、0.25°步距，unit OBB每方向半邊額外0.095818331589格。margin由最大離軸半徑（加cube circumradius）與半個採樣區間角位移推得，包住樣本間所有頂點運動。這個加厚包絡對actual船體相交0，剩餘需carve格0。`sweep_dense_proposal.json`。
- **水密**：完整800×241×52的水線下空氣洪泛，外側X/Y界與底界注入外水，頂部z51不作內艙外水種子；封閉水下空氣1,370,871格。艙內(350,120,40)及(170,120,40)均不與外水連通，與整改前assembly讀數相同。此讀數包含彈藥庫等靜態子件，不與主船殼單件的1,397,278格混比。

## 界線

中心射線不驗炮彈口徑、火砲後座或人員避讓；帆／繩／其他動態模型的碰撞由另一verifier處理。本驗收的舵連續包絡只對靜態船體。人員全站位、遊戲短時運行及vxk完整解碼不由本verifier宣稱通過。

目前所讀遊戲JS未消費hinge_x/axis_x/max_deg，舵只依kind提供操舵效能及依stock-top找支持；資產幾何的±30°淨空已量成，但不能因此聲稱遊戲已動畫旋轉此舵。

來源events/models等雜湊在`report.json`的inputs；預覽及本次證據檔雜湊在`manifest.json`。作品無任何由本verifier發起的修改。
