# TASK-0744 潮墓號船尾三角帆被拉歪

Tim 的兩張截圖是砲門更新前的版本。砲門修改沒有改帆；本問題在原設計的 mizzen-lateen 綁邊已存在。

## 根因與修正

三個角的固定點本身是對的：tack → gaff/jaws、head → gaff/top、clew → boom/end，全為 pin=true。
錯在 bind=[0,2]：邊0沿著同一根gaff，能跟著它轉；邊2的兩端分屬gaff與boom，遊戲 clothBindMeta 的 cell 分支把中間15點固定在格子或原始位置，sim.yk=-1，帆桁追風時不轉。
本次只把 bind 改成 [0]，不移固定點、不改帆桁。下緣仍由原本兩端固定，中間交給布料。
CLI work sub=sail overwrite=1 落地；sails.json 與上一版逐欄比較只改 bind 與解釋 note，其他9面帆、三角的名稱/座標/pin、meta、布料解析度/鬆度/顏色全部保留。

## 隔離重現與反向對照

check.cjs 直接載入遊戲 29_sailrecipe.js、30_rig_physics.js 的配方、clothBindMeta、clothTemplate、clothBrace、yardPins。
fixture.json 是修改前VXK抽出的這面帆、兩根桁與自己的sheet；把吹鼓秒數設0以隔離綁定。anchorNear 使用無格路徑：回格與無格兩條都不跟桁轉，這裡不宣稱量過船殼碰撞。
轉角0.7rad：原版下緣15中間點鎖在原位，最大差51.43468格（0.1m/格，5.143m）；改bind=[0]後鎖住0點，轉後初始化差0.0000063格（float32捨入）。三個角仍為模型綁定。
將bind改回[0,2]便重現15點與51.43格，探針能抓回此缺陷。

執行：node check.cjs <Blockside根> fixture.json。

## 遊戲內檢查

browser_probe.py 在成品附加只用於測量的腳本，透過現有 __game.ships/phx/run 讀真實模板與物理，cache=0、seed3；不提交測量用HTML。
修改前從0.1秒到20.1秒每5秒：鎖在原位15點，三角固定點誤差小於0.000008格。原版即能重現，不依賴砲門。
修改後結果、匯入與建置驗證見同目錄報告。

## 射程

這次修掉下緣錯誤固定；不把20秒取樣擴成所有風向、破帆、非同步桁角、全部接觸與收放帆的完整驗收。

## 最終實測與交付

同一個Chrome遊戲客戶端、相同seed3、cache=0，0.1/5.1/10.1/15.1/20.1秒取樣：修前始終15個原地固定點，修後始終0個。修後三角固定點偏差最大0.000009格，所有布點數值有限，gaff與boom的轉角從-0.014變到-0.557再回到約-0.383rad，沒有把帆桁凍住來過關。資料見 before_browser.json、after_browser.json。
VXK前後逐欄比較：格子、221模型（含砲門）、網格與502繩完全相同，10面帆只有mizzen-lateen改變（asset_diff.json）。
遊戲建置完成，17艘網格還原與程式AST驗算一致，來源指紋a0a671bf388e314c／125檔，srccheck通過。匯入錯誤0、既有送藥手24/25警告1。
