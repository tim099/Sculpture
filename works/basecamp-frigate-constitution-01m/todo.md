## 下次從這裡接（階段四 TASK-0484 剩下的）
- [ ] 先看一眼新圖紙 03 的底肋設計（底肋頭 3.6 m 是設計決定）；要改就改 plan.json 的 lines.floor 重跑 `python -I draft_lines.py <design>`
- [ ] 雕 59 片底肋：照 `verify_lines.json` floors[].stamp 逐片 `sculpture op=stampimg facing=x+ thickness=3 expect_pixels=…`（建議寫成一支小迴圈，每片讀回 placed 是否 ＝ expect × 3）
- [ ] 雕 keelson：`verify_lines.json` keelson.stamp（facing=y+、thickness 5）
- [ ] 驗收：剖面（axis=x+ 疊新圖紙 03 的橫剖面）探針 ≤ 1 格；反向對照偏 3 報 3；y／x 切片格數對設計
- [ ] ⚠ x± 貼片的軸向（u→Z、v→Y 翻轉）第一次用 —— 先貼一片、用 section axis=x+ 看形狀對不對再全貼

## 之後
- [ ] 其餘肋骨（雙肋的另一片＝first futtock、second futtocks、top timbers）—— 新圖紙 03 的船殼已經有了，肋骨外緣直接用它
- [ ] 04／15 號的 rider keelson（15"x18"）與 Humphreys 9"x24" deadwood 要不要做
- [ ] 船殼板 → 橫樑與甲板（15 號：orlop 13.09 ft、berth 19.14、gun 26.27、spar 33.79 ft at CL）→ 柱與艙內 → 桅檣與索具
- [ ] 船尾 transom、counter；船首 knee of the head

## 待確認
- [x] keel drag：不做（2026-10-11 決定，理由見 notes.md）；⚠ 甲板／舷弧／砲門的高度要逐站相對龍骨量，不要用一條水平線
- [ ] sided（艏柱／艉柱／deadwood／apron 5 格）仍是設計決定
