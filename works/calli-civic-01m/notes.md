補缺的城鎮建築（calli 2026-10-31；Tim「布里奇敦（英屬）的小教堂、監獄，巴拉科阿（西屬）的砲台，也缺模型 那補上模型吧 GO」）。
- 成品：calli-civic-01m-en-chapel（Blocksail en-chapel）、-en-jail（en-jail）、-es-battery（es-battery）；產生程式 design/gaps.py（工具借 basecamp-es-01m 的 es.py、ame-carib-civic-01m 的 english.py、trailhead-harbour-01m 的 forts.py 那一串）。
- 史料與設計的分界寫在 gaps.py 檔頭：英國國教堂的講台、聖餐桌欄杆、十誡板與監獄前的枷是英國本土的通法〔摘〕；三棟的平面、尺寸、木鐘樓、哨亭全部〔設計〕。
- 工作點：en-jail 5 點（a 看守那一間、b 牢門那一間）、es-battery 3 點（每門砲後面）—— 寫在 gaps.py 的 M.anchor ⇒ 重跑 apply.py anchors 不會被拿掉。
- 讀數：框外 0、撞格 0、浮空 0、door_ok；引擎 check 缺 0 多 0 色差 0、link_overlap 0、link_clipped 0；en-jail 的封閉空腔是關著窗的樓上（BUILDING_SPEC §8：不管）。
- 學校（TASK-1068；Tim「那開工建設學校吧 GO」）：calli-civic-01m-carib-school（Blocksail carib-school，BUILDING_SPEC §6.33）—— 釘板教室、前廊、開著百葉的窗、講台與老師的桌椅、木十字、書架、四排長桌長凳、後院吊鐘架；工作點 5（講台 2、走道 2、書架前 1）；讀數 框外 0、撞格 0、浮空 0、引擎 check 缺 0 多 0 色差 0、空腔 0。
- 英國、西班牙的學校（TASK-1135；Tim「推吧 然後繼續手上的task吧」，接 1068 的缺口：en、es 的城挑不到 carib-school）：calli-civic-01m-en-school（Blocksail en-school：磚造教室、紅瓦四坡頂、十誡與主禱文的板、後院磚牆與吊鐘木架）、-es-school（es-school：刷白砌石、紅陶瓦兩坡頂、正面小鐘牆、切石門框、木十字、後院砌石牆與蓄水池井口）；平面與 5 個工作點同 carib-school（gaps.py 的 school_room、school_work 共用）；讀數 框外 0、撞格 0、浮空 0、door_ok、引擎 check 缺 0 多 0 色差 0、link_overlap 0、空腔 0。
