# 三叉戟號 TODO

## 下一步：遊戲那側換成新的船（TASK-0588 → ame）
- 階段十五（三叉戟砲重配：船頭砲台 2 門、船尾 4 門、封船頭斜砲門）已落格、驗收讀數在 notes.md；總數 142。
- vxk：`gura-tridente-01m-assembly/exports/tridente.vxk`（2,052,378 格、header checksum 2746992056）；遊戲那側 `admin.py reimport --id tridente`（會改戰局，ame 的流程）。
- 旗跟 gaff 轉的修正在 Blockside `src/js/30_rig_physics.js`，還沒提交（ame 的 repo）。

## 再之後
- 砲具與砲索（階段十）、rammer／sponge（階段十一）、shot garland（階段十二）已做；三叉戟砲不掛砲索。
- jib-boom 尖 x 953、z 344（組裝件 x 1100 夠用）；之後若加 flying jib-boom 再量一次。
- orlop 艙房 22 間（階段十四，TASK-0581）已做；其他層（軍官室、船長室）可以之後加 —— 上砲甲板船尾現在有兩門三叉戟砲，船長室要隔的話讓開它們的站位（砲尾往前 10 格）。
- 父層 Valhalla 的 Sculpture 指標還沒 bump。
