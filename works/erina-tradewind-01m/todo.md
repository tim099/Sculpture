# 信風號 TODO

（2026-10-29：步驟 1–11、14、15 做完；Blockside 1e96edc、Blocksail 0ec6ecc、Sculpture 都已在遠端。）

- [ ] Tim 看過一次（Blockside `?ship=tradewind`、Blocksail 航海模式的雙桅帆船船隊）—— TASK-1097 最後一格。
- [x] 推（Tim 2026-10-29「全推」）：Blockside dev 1e96edc、Blocksail main 0ec6ecc 在 10:02 被別人推 dev／main 時一起帶上去了；Sculpture 本小姐推到 023fcf45。
- [ ] 年代：有原圖的 150 噸級 brig 最早 1759 ⇒ 1666 開局就有是刻意的時代錯置；brig 是 seedType ⇒ 加 `from` 就發不出來 —— 等 Tim 定。
- 可以之後做（沒做、照實留著）：空艙房（Ship_Decks §9.2）、起錨機 windlass（沒有現成元件 ⇒ 要的話做成通用部件）、砲索、迴旋砲 arc −80..80 逐角量穿模。
- ⚠ 動到線形或舷頂（lines.top）⇒ 船殼、塗裝、channels 都要照 `tools/hull_state.py` ⇒ `tools/delta_apply.py` 重落（舷牆加高那次的做法，notes 步驟 9）；重匯 Blockside 前 `game.json` 只插這一艘的差（notes 步驟 14）。
