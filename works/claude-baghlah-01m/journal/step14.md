# 2026-11-18 步驟 14：給遊戲的 meta 與匯入

- Tim 說 Blockside 在 Blocksail 的 `external/Blockside`。這台的 Blocksail clone 在別的專案的工作區，所以另外 clone 一份 Blockside `dev` 當暫存副本，不碰人家的。
- 這台是 Linux、沒有 Chrome，Blockside 卻寫死 Windows 的 Chrome 路徑。改用 Debian 的 chromium-headless-shell 裝在使用者空間，WebGL 2 用軟體算圖也跑得動。
- 建置第一次死在「頂層同名檢查讀不到結果」：node 印完 `console.log` 就 `process.exit(0)`，在 Linux 的 pipe 被截在 64 KB。Windows 上不會遇到；我在執行包裝裡改用暫存檔讀 node 的輸出，沒改 Blockside 的程式。
- 選船卡縮圖用軟體算圖要拍將近一小時，而且暫存副本不提交 ⇒ 包裝裡跳過，只跑匯入檢查要的那幾步。
- 艦隊 54 艘的快取從這台 Sculpture 重新匯出，指紋全部對不上（版本不同）。只為了檢查星辰號，暫存副本裡 relock；這件事寫進 notes，正式匯入不能照這樣做。
- 第一次匯入檢查 ✗ 9：8 個迴旋砲座沒有 `mount_of`（要先發 id）、船尾樓那層找不到火藥取用點。`ids` 發號時它說換不了逗號清單的 hoist（步驟 10 就預告過），手寫成 `ladders-2#orlop,ladders-3#quarter-S` 之後，取用點從 1 變 2、火藥 30／30 門都走得到。路徑寫法照理遊戲也認，可是第二座就是沒擺上；換成 id 寫法就好了，原因沒追到底。
- 漏水那三條報「船殼的縫」，我先切剖面看是不是斜角相碰。結果漏點的位置和水位剛好就是水槽的排水孔（z 51），是照 PT 做的設計。錨纜橫樑在頭上，遊戲把水槽算成有蓋的艙。
- `ids` 寫回作品會把 persona 寫死成 ame。我在包裝裡換成自己，meta_log 才不會記成別人寫的。
