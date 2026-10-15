# 2026-10-16 潮墓號：正式工作版本接入驗證通過

Tim要求與ame配合完成正式遊戲接入；已透過酒館通知施工範圍及結果。
正式Blockside/src/config/game.json已加入tidegrave，陸戰隊12人、marineGap30，
套入艏艉砲送藥出生/交藥點修正，並以admin writer使用精確20261016凍結VXK。
既有其他船與全域設定在本次匯入前後逐值不變；原monkeyTo保留，前桅/艙口的效能取捨不改。

正式成品：D:/Unity/Valhalla/Blockside/index.html
SHA256 d9b260564f9be820aacfdf20723ea18f8f5e4bd6fb1212c5dcd11f401745c6cb
檢查前後成品hash一致。verify：447份模型網格三角形、格子與header均與cache一致。
正式shipcheck：0 errors / 0 warnings、54砲全滿編、353船員、送藥54/54連通。
報告：D:/Unity/Valhalla/Blockside/reports/shipcheck_tidegrave.md
凍結證據：design/delivery/formal_game_20261016/。

建置期間曾偵測到共用來源同步修改，因此另外對穩定成品重跑verify及shipcheck才簽此結果。
這是正式本機工作產物；Blockside包含ame與其他人的未提交施工，未代提交或push、未宣稱遠端上線。
正式提交與發布由ame協調；TASK-0603/0546帆碰撞仍由Tim手動驗收。
