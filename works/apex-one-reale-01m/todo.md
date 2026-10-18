# 皇家號 TODO

## 下一步：階段四 砲
- Tim「可以加炮種」⇒ Blockside 砲種表（`src/config/game.json` guns）加 36 磅（coursier）、8 磅（bâtarde）、迴旋砲（pierrier）—— 在自己的 worktree 改、合進 dev。
- 中央 36 磅在砲台中線通道（|dy| ≤ 7）朝前；兩旁 8 磅（甲板上）、外側 6 磅（角落平台 conilles 上）；14 門迴旋砲（舷外走道、砲台胸牆）。砲是外部模型、沿用現有元件縮放、退到零碰撞、砲口在船殼外。
- ⚠ 前桅在甲板處 x 553、偏左舷 5 格：砲尾後面要留給前桅。

## 之後
- 艙底：彈藥庫在船尾艙底（艙口已開在 espale 中線，梯子在階段五）；舷側登船梯、船尾篷兩側長椅。
- 階段五：舵模型（舵柄、spin）、彈藥庫與火藥桶、旗、燈、遊戲 meta；匯出 vxk、Blockside 暫存副本跑 shipcheck。
- 槳：等 TASK-0691。
