歐式學校（kaguya 2026-11-04，TASK-1186；Tim「/scp-task 1186 GO」）—— Blocksail BUILDING_SPEC §6.38。
- 成品：kaguya-school-01m-common-school（Blocksail common-school：共用那一套 ⇒ 君士坦丁堡、加拉塔、阿姆斯特丹）、-pt-school（pt-school：葡萄牙那一套 ⇒ 里斯本、豐沙爾、安格拉，以前借 es-school）。
- 產生程式 design/school.py；build.py、apply.py 抄自 calli-civic-01m（教室與工作點借它的 gaps.py：school_room、school_work ⇒ 五款學校同一套站位）；工具一路借 es.py、english.py、townpub.py、summit-carib 的 kit／carib。
- common：毛石牆、木瓦兩坡頂（屋面蓋過毛石山牆 ⇒ rubble_gable 碰到屋頂的格就不砌；en、es 那兩款是山牆高出屋面）、右牆壁爐＋山牆上的毛石煙囪（固定點 smoke）、字母板、沙漏、後院吊鐘木架與柴堆；不掛宗教的東西（三座城三種教會）。
- pt：刷白＋黃赭牆腳（barra 213）＋lioz 牆角柱與簷線（250／246／218）、陶瓦四坡頂、lioz 門框與門上的花磚十字（registo：藍 42、釉白 219）、lioz 窗框與窗台、教室一圈藍黃花磚牆裙（azulejos de padrão：6 格一個單元）、木十字、後院石井欄。
- 百葉兩款都是沒上漆的木色（put_part 對借來的部件本來就換成 SHUT）—— 綠漆像是更晚的事，沒查到就不上。
- 史料與設計的分界寫在 school.py 檔頭：〔摘：通說〕蒙學老師與租來的教室、葡萄牙的花磚牆裙與 lioz 石框；〔沒查到〕三地學校房子的樣子 ⇒ 平面、壁爐、字母板、registo、井全部〔設計〕；沒有黑板。
- 讀數：框外 0、撞格 0、浮空 0、空腔 0、door_ok；重跑兩次遮罩逐位元組相同；apply.py check 6 件缺 0 多 0 色差 0、link_overlap 0、link_clipped 0。
- 遊戲裡（暫時改 worktree 的烘好規劃）：豐沙爾 byModel pt-school 1、阿姆斯特丹 common-school 1（Blocksail docs/evidence/school-1186/ingame.jpg）。
