
/* VoxelKit —— 雕刻作品的瀏覽器端：.vxk 解碼、稀疏網格、網格化、WebGL2 算繪、射線、連通。
 * 區塊職責：把 voxel_export.py 產的 .vxk（deflate-raw）變成可以畫、可以改的格子。零外部依賴。
 * 物理意義：座標一律是作品的格座標（x 船長、y 船寬、z 高），1 格 ＝ header.meters_per_voxel 公尺；
 *           世界座標怎麼擺由呼叫端給模型矩陣（格 → 世界）。
 * 設計取捨：
 *   · 網格是「16³ 區塊表」：只存非空區塊；兩份 Grid 可以共用同一份資料，誰先改哪一塊誰才複製（copy-on-write）。
 *   · 網格化以區塊為單位做同色面合併（greedy），GPU 緩衝以 64³ 為一區（少 draw call、改一格只重組一區）。
 *   · 頂點 8 bytes：uvec4(x, y, z, 法線 | 色值<<3)；色值在著色器裡照 RGB332 解。
 * 失敗處置：解碼對不上（magic、長度）⇒ 丟例外，⛔ 不畫半艘船；checksum 由呼叫端比（VoxelKit.verify）。
 */
(function (root) {
  'use strict';
  var CH = 16, CH3 = 4096, PAD = 18, PAD2 = 324;

  // ───────────────────────── 調色盤與 checksum ─────────────────────────
  function rgb332(i) { return [((i >> 5) & 7) * 255 / 7 | 0, ((i >> 2) & 7) * 255 / 7 | 0, (i & 3) * 255 / 3 | 0]; }
  function hashVoxel(x, y, z, c) {   // voxel_export.py 的 checksum 是同一式（mod 2^32）
    return (Math.imul(x, 73856093) ^ Math.imul(y, 19349663) ^ Math.imul(z, 83492791) ^ Math.imul(c, 2654435761 | 0)) >>> 0;
  }

  // ───────────────────────── 解碼 ─────────────────────────
  function b64ToBytes(s) {
    var bin = atob(s.replace(/\s+/g, '')), n = bin.length, u = new Uint8Array(n);
    for (var i = 0; i < n; i++) u[i] = bin.charCodeAt(i);
    return u;
  }
  function inflateRaw(u8) {
    if (typeof DecompressionStream === 'undefined') return Promise.reject(new Error('這個瀏覽器沒有 DecompressionStream（deflate-raw）'));
    var s = new Blob([u8]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    return new Response(s).arrayBuffer().then(function (b) { return new Uint8Array(b); });
  }
  function parse(raw) {
    if (raw[0] !== 86 || raw[1] !== 88 || raw[2] !== 75 || raw[3] !== 49) throw new Error('不是 VXK1 封裝');
    var dv = new DataView(raw.buffer, raw.byteOffset, raw.byteLength);
    var hn = dv.getUint32(4, true);
    var header = JSON.parse(new TextDecoder().decode(raw.subarray(8, 8 + hn)));
    var n = header.nchunks, p = 8 + hn;
    if (raw.length !== p + n * 6 + n * CH3) throw new Error('VXK1 長度不對：' + raw.length + ' ≠ ' + (p + n * 6 + n * CH3));
    var keys = new Uint16Array(n * 3);
    for (var i = 0; i < n * 3; i++) keys[i] = dv.getUint16(p + i * 2, true);
    p += n * 6;
    var chunks = [];
    for (i = 0; i < n; i++) chunks.push({ cx: keys[i * 3], cy: keys[i * 3 + 1], cz: keys[i * 3 + 2], data: raw.subarray(p + i * CH3, p + (i + 1) * CH3) });
    return { header: header, chunks: chunks };
  }
  function decode(u8) { return inflateRaw(u8).then(parse); }
  /** <script type="application/x-asset" id="…" data-mime="…">base64<\/script>（vxk_inline.py 填的）；空的（optional 素材沒交）⇒ null。 */
  function embedded(id) {
    var el = document.getElementById(id); if (!el) return null;
    var t = el.textContent.replace(/\s+/g, '');
    return t ? { mime: el.getAttribute('data-mime') || 'application/octet-stream', b64: t } : null;
  }
  /** 內嵌的圖 ⇒ Promise<Image|null>（沒有或解不開 ⇒ null，呼叫端用替代品）。 */
  function embeddedImage(id) {
    var e = embedded(id); if (!e) return Promise.resolve(null);
    return new Promise(function (res) { var im = new Image(); im.onload = function () { res(im); }; im.onerror = function () { res(null); }; im.src = 'data:' + e.mime + ';base64,' + e.b64; });
  }
  /** 內嵌的 JSON ⇒ 物件（沒有或解不開 ⇒ null）。 */
  function embeddedJSON(id) {
    var e = embedded(id); if (!e) return null;
    try { return JSON.parse(new TextDecoder().decode(b64ToBytes(e.b64))); } catch (x) { return null; }
  }
  /** <script type="application/x-vxk" id="…">base64<\/script>（vxk_inline.py 填進去的）⇒ 模型。 */
  function loadEmbedded(id) {
    var el = document.getElementById(id);
    if (!el) return Promise.reject(new Error('找不到內嵌的 .vxk：#' + id));
    return decode(b64ToBytes(el.textContent));
  }

  // ───────────────────────── 稀疏網格 ─────────────────────────
  function Grid(size) {
    this.sx = size[0]; this.sy = size[1]; this.sz = size[2];
    this.nx = Math.ceil(this.sx / CH); this.ny = Math.ceil(this.sy / CH); this.nz = Math.ceil(this.sz / CH);
    this.tab = new Array(this.nx * this.ny * this.nz).fill(null);
    this.own = new Uint8Array(this.tab.length);    // 1 ＝ 這份 Grid 自己的（可以直接寫）
    this.count = 0;
  }
  Grid.fromModel = function (model) {
    var g = new Grid(model.header.size);
    model.chunks.forEach(function (c) { g.tab[g.ci(c.cx, c.cy, c.cz)] = c.data; });
    g.count = model.header.voxels;
    return g;
  };
  /** 共用同一份資料的另一份網格（之後各改各的）。 */
  Grid.prototype.share = function () {
    var g = new Grid([this.sx, this.sy, this.sz]);
    g.tab = this.tab.slice(); g.count = this.count;
    return g;
  };
  Grid.prototype.ci = function (cx, cy, cz) { return cx + this.nx * (cy + this.ny * cz); };
  Grid.prototype.get = function (x, y, z) {
    if (x < 0 || y < 0 || z < 0 || x >= this.sx || y >= this.sy || z >= this.sz) return 0;
    var c = this.tab[(x >> 4) + this.nx * ((y >> 4) + this.ny * (z >> 4))];
    return c === null ? 0 : c[(x & 15) | ((y & 15) << 4) | ((z & 15) << 8)];
  };
  /** 寫一格，回舊值。界外 ⇒ 不寫、回 -1。 */
  Grid.prototype.set = function (x, y, z, v) {
    if (x < 0 || y < 0 || z < 0 || x >= this.sx || y >= this.sy || z >= this.sz) return -1;
    var i = (x >> 4) + this.nx * ((y >> 4) + this.ny * (z >> 4)), c = this.tab[i];
    var li = (x & 15) | ((y & 15) << 4) | ((z & 15) << 8);
    if (c === null) { if (!v) return 0; c = this.tab[i] = new Uint8Array(CH3); this.own[i] = 1; }
    else if (!this.own[i]) { if (c[li] === v) return v; c = this.tab[i] = new Uint8Array(c); this.own[i] = 1; }
    var old = c[li];
    if (old !== v) { c[li] = v; this.count += (v ? 1 : 0) - (old ? 1 : 0); }
    return old;
  };
  /** 每格走一次（cb(x, y, z, c)）。 */
  Grid.prototype.each = function (cb) {
    for (var cz = 0; cz < this.nz; cz++) for (var cy = 0; cy < this.ny; cy++) for (var cx = 0; cx < this.nx; cx++) {
      var c = this.tab[this.ci(cx, cy, cz)];
      if (c === null) continue;
      for (var li = 0; li < CH3; li++) if (c[li]) cb(cx * CH + (li & 15), cy * CH + ((li >> 4) & 15), cz * CH + (li >> 8), c[li]);
    }
  };
  /** 逐格 checksum 與格數 ⇒ 跟 header 比（還沒動過的網格才該相等）。 */
  function verify(grid, header) {
    var sum = 0, n = 0;
    grid.each(function (x, y, z, c) { sum = (sum + hashVoxel(x, y, z, c)) >>> 0; n++; });
    return { voxels: n, checksum: sum, ok: n === header.voxels && sum === header.checksum };
  }

  // ───────────────────────── 網格化（區塊內同色面合併） ─────────────────────────
  var pad = new Uint8Array(PAD * PAD * PAD), mask = new Int16Array(CH * CH);
  // 軸 a 的面：u、v 取讓 (u, v, a) 成右手系的兩軸
  var UAX = [1, 2, 0], VAX = [2, 0, 1], P = [0, 0, 0];
  /** 一個區塊的四邊形 ⇒ Uint16Array（每頂點 x,y,z,packed；每四邊形 4 頂點）。空 ⇒ null。 */
  function meshChunk(grid, cx, cy, cz) {
    var c = grid.tab[grid.ci(cx, cy, cz)];
    if (c === null) return null;
    var x0 = cx * CH, y0 = cy * CH, z0 = cz * CH, x, y, z;
    // 填 18³（含鄰居一層）：內部直接抄，外框一格一格問網格
    pad.fill(0);
    for (z = 0; z < CH; z++) for (y = 0; y < CH; y++) {
      var src = (y << 4) | (z << 8), dst = 1 + (y + 1) * PAD + (z + 1) * PAD2;
      for (x = 0; x < CH; x++) pad[dst + x] = c[src + x];
    }
    for (var a = 0; a < 3; a++) for (var s = -1; s <= CH; s += CH + 1) for (var p = -1; p <= CH; p++) for (var q = -1; q <= CH; q++) {
      var lx, ly, lz;
      if (a === 0) { lx = s; ly = p; lz = q; } else if (a === 1) { lx = p; ly = s; lz = q; } else { lx = p; ly = q; lz = s; }
      pad[(lx + 1) + (ly + 1) * PAD + (lz + 1) * PAD2] = grid.get(x0 + lx, y0 + ly, z0 + lz);
    }
    var out = [], st = [1, PAD, PAD2];
    for (a = 0; a < 3; a++) {
      var ua = UAX[a], va = VAX[a], sa = st[a], su = st[ua], sv = st[va], B = 1 + PAD + PAD2;
      for (var sgn = 1; sgn >= -1; sgn -= 2) {
        var nrm = a * 2 + (sgn > 0 ? 0 : 1), off = sgn * st[a];
        for (var d = 0; d < CH; d++) {
          var any = false, row0 = B + d * sa;
          for (var v = 0; v < CH; v++) for (var u = 0, pi = row0 + v * sv; u < CH; u++, pi += su) {
            var col = pad[pi], m = (col && !pad[pi + off]) ? col : 0;
            mask[u + v * CH] = m; if (m) any = true;
          }
          if (!any) continue;
          var plane = (a === 0 ? x0 : a === 1 ? y0 : z0) + d + (sgn > 0 ? 1 : 0);
          var bu = (ua === 0 ? x0 : ua === 1 ? y0 : z0), bv = (va === 0 ? x0 : va === 1 ? y0 : z0);
          for (v = 0; v < CH; v++) for (u = 0; u < CH;) {
            var k = mask[u + v * CH];
            if (!k) { u++; continue; }
            var w = 1; while (u + w < CH && mask[u + w + v * CH] === k) w++;
            var h = 1, ok = true;
            while (v + h < CH && ok) { for (var t = 0; t < w; t++) if (mask[u + t + (v + h) * CH] !== k) { ok = false; break; } if (ok) h++; }
            for (var hh = 0; hh < h; hh++) for (t = 0; t < w; t++) mask[u + t + (v + hh) * CH] = 0;
            var U0 = bu + u, V0 = bv + v, U1 = U0 + w, V1 = V0 + h, pk = nrm | (k << 3);
            var cs = sgn > 0 ? [U0, V0, U1, V0, U1, V1, U0, V1] : [U0, V0, U0, V1, U1, V1, U1, V0];
            for (var e = 0; e < 4; e++) {
              P[a] = plane; P[ua] = cs[e * 2]; P[va] = cs[e * 2 + 1];
              out.push(P[0], P[1], P[2], pk);
            }
            u += w;
          }
        }
      }
    }
    return out.length ? new Uint16Array(out) : null;
  }

  // ───────────────────────── 矩陣（column-major，WebGL 慣例） ─────────────────────────
  var M4 = {
    ident: function () { return new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]); },
    mul: function (a, b) {
      var o = new Float32Array(16);
      for (var c = 0; c < 4; c++) for (var r = 0; r < 4; r++)
        o[c * 4 + r] = a[r] * b[c * 4] + a[4 + r] * b[c * 4 + 1] + a[8 + r] * b[c * 4 + 2] + a[12 + r] * b[c * 4 + 3];
      return o;
    },
    persp: function (fovy, asp, n, f) {
      var t = 1 / Math.tan(fovy / 2), o = new Float32Array(16);
      o[0] = t / asp; o[5] = t; o[10] = (f + n) / (n - f); o[11] = -1; o[14] = 2 * f * n / (n - f); return o;
    },
    lookAt: function (e, c, up) {
      var zx = e[0] - c[0], zy = e[1] - c[1], zz = e[2] - c[2], l = Math.hypot(zx, zy, zz); zx /= l; zy /= l; zz /= l;
      var xx = up[1] * zz - up[2] * zy, xy = up[2] * zx - up[0] * zz, xz = up[0] * zy - up[1] * zx; l = Math.hypot(xx, xy, xz); xx /= l; xy /= l; xz /= l;
      var yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
      return new Float32Array([xx, yx, zx, 0, xy, yy, zy, 0, xz, yz, zz, 0,
        -(xx * e[0] + xy * e[1] + xz * e[2]), -(yx * e[0] + yy * e[1] + yz * e[2]), -(zx * e[0] + zy * e[1] + zz * e[2]), 1]);
    },
    inv: function (m) {
      var o = new Float32Array(16), a = m;
      var b00 = a[0] * a[5] - a[1] * a[4], b01 = a[0] * a[6] - a[2] * a[4], b02 = a[0] * a[7] - a[3] * a[4], b03 = a[1] * a[6] - a[2] * a[5];
      var b04 = a[1] * a[7] - a[3] * a[5], b05 = a[2] * a[7] - a[3] * a[6], b06 = a[8] * a[13] - a[9] * a[12], b07 = a[8] * a[14] - a[10] * a[12];
      var b08 = a[8] * a[15] - a[11] * a[12], b09 = a[9] * a[14] - a[10] * a[13], b10 = a[9] * a[15] - a[11] * a[13], b11 = a[10] * a[15] - a[11] * a[14];
      var det = b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06; det = 1 / det;
      o[0] = (a[5] * b11 - a[6] * b10 + a[7] * b09) * det; o[1] = (a[2] * b10 - a[1] * b11 - a[3] * b09) * det;
      o[2] = (a[13] * b05 - a[14] * b04 + a[15] * b03) * det; o[3] = (a[10] * b04 - a[9] * b05 - a[11] * b03) * det;
      o[4] = (a[6] * b08 - a[4] * b11 - a[7] * b07) * det; o[5] = (a[0] * b11 - a[2] * b08 + a[3] * b07) * det;
      o[6] = (a[14] * b02 - a[12] * b05 - a[15] * b01) * det; o[7] = (a[8] * b05 - a[10] * b02 + a[11] * b01) * det;
      o[8] = (a[4] * b10 - a[5] * b08 + a[7] * b06) * det; o[9] = (a[1] * b08 - a[0] * b10 - a[3] * b06) * det;
      o[10] = (a[12] * b04 - a[13] * b02 + a[15] * b00) * det; o[11] = (a[9] * b02 - a[8] * b04 - a[11] * b00) * det;
      o[12] = (a[5] * b07 - a[4] * b09 - a[6] * b06) * det; o[13] = (a[0] * b09 - a[1] * b07 + a[2] * b06) * det;
      o[14] = (a[13] * b01 - a[12] * b03 - a[14] * b00) * det; o[15] = (a[8] * b03 - a[9] * b01 + a[10] * b00) * det;
      return o;
    },
    pt: function (m, x, y, z) { return [m[0] * x + m[4] * y + m[8] * z + m[12], m[1] * x + m[5] * y + m[9] * z + m[13], m[2] * x + m[6] * y + m[10] * z + m[14]]; },
    dir: function (m, x, y, z) { return [m[0] * x + m[4] * y + m[8] * z, m[1] * x + m[5] * y + m[9] * z, m[2] * x + m[6] * y + m[10] * z]; }
  };

  // ───────────────────────── 射線（格座標；Amanatides–Woo） ─────────────────────────
  /** 從 o 沿 d（不必單位化）走到 tMax（以 d 的長度為單位），第一個非空格 ⇒ {x,y,z,t,c,face}；沒碰到 ⇒ null。 */
  function raycast(grid, o, d, tMax) {
    var t0 = 0, t1 = tMax, lo = [0, 0, 0], hi = [grid.sx, grid.sy, grid.sz];
    for (var a = 0; a < 3; a++) {
      if (Math.abs(d[a]) < 1e-12) { if (o[a] < lo[a] || o[a] >= hi[a]) return null; continue; }
      var ta = (lo[a] - o[a]) / d[a], tb = (hi[a] - o[a]) / d[a];
      if (ta > tb) { var s = ta; ta = tb; tb = s; }
      if (ta > t0) t0 = ta; if (tb < t1) t1 = tb; if (t0 > t1) return null;
    }
    var t = t0 + 1e-6, p = [o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t];
    var c = [Math.floor(p[0]), Math.floor(p[1]), Math.floor(p[2])], step = [0, 0, 0], tN = [0, 0, 0], tD = [0, 0, 0], face = -1;
    for (a = 0; a < 3; a++) {
      c[a] = Math.min(hi[a] - 1, Math.max(0, c[a]));
      step[a] = d[a] > 0 ? 1 : -1;
      tD[a] = Math.abs(d[a]) < 1e-12 ? Infinity : Math.abs(1 / d[a]);
      tN[a] = Math.abs(d[a]) < 1e-12 ? Infinity : ((d[a] > 0 ? c[a] + 1 : c[a]) - o[a]) / d[a];
    }
    for (var it = 0; it < 8192; it++) {
      var v = grid.get(c[0], c[1], c[2]);
      if (v) return { x: c[0], y: c[1], z: c[2], t: t, c: v, face: face };
      var m = tN[0] < tN[1] ? (tN[0] < tN[2] ? 0 : 2) : (tN[1] < tN[2] ? 1 : 2);
      t = tN[m]; if (t > t1) return null;
      c[m] += step[m]; tN[m] += tD[m]; face = m * 2 + (step[m] > 0 ? 1 : 0);
      if (c[m] < 0 || c[m] >= hi[m]) return null;
    }
    return null;
  }

  // ───────────────────────── 連通：哪些格跟錨點斷開了 ─────────────────────────
  /**
   * seeds：被打掉那些格的鄰格（打包 x | y<<10 | z<<20）。從每顆種子往外找，先往下（z 小）走：
   * 碰到錨點、或碰到已知連著的格 ⇒ 連著；找完都沒碰到 ⇒ 這一團斷開了。
   * budget：一團超過這麼多格就當連著（⛔ 不讓一次判定卡住畫面 —— 代價是極大的一塊不會掉）。
   * 回：斷開的每一團（Int32Array，打包座標）。
   */
  function detached(grid, seeds, isAnchor, budget) {
    var vis = new Map(), pieces = [];
    function mk(x, y, z) {
      var i = (x >> 4) + grid.nx * ((y >> 4) + grid.ny * (z >> 4)), m = vis.get(i);
      if (!m) { m = new Uint8Array(CH3); vis.set(i, m); }
      return m;
    }
    function getv(x, y, z) { var m = vis.get((x >> 4) + grid.nx * ((y >> 4) + grid.ny * (z >> 4))); return m ? m[(x & 15) | ((y & 15) << 4) | ((z & 15) << 8)] : 0; }
    function setv(x, y, z, v) { mk(x, y, z)[(x & 15) | ((y & 15) << 4) | ((z & 15) << 8)] = v; }
    var NB = [[0, 0, 1], [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, -1]];   // 往下最後推 ⇒ 最先彈出
    var stack = new Int32Array(1 << 16), list = [];
    for (var si = 0; si < seeds.length; si++) {
      var s = seeds[si], sx = s & 1023, sy = (s >> 10) & 1023, sz = s >> 20;
      if (!grid.get(sx, sy, sz) || getv(sx, sy, sz)) continue;
      var sp = 0, conn = false; list.length = 0;
      stack[sp++] = s; setv(sx, sy, sz, 2); list.push(s);
      outer: while (sp) {
        var p = stack[--sp], x = p & 1023, y = (p >> 10) & 1023, z = p >> 20;
        if (isAnchor(x, y, z)) { conn = true; break; }
        for (var k = 0; k < 6; k++) {
          var nx = x + NB[k][0], ny = y + NB[k][1], nz = z + NB[k][2];
          if (!grid.get(nx, ny, nz)) continue;
          var mv = getv(nx, ny, nz);
          if (mv === 1) { conn = true; break outer; }
          if (mv) continue;
          setv(nx, ny, nz, 2);
          var q = nx | (ny << 10) | (nz << 20);
          if (sp >= stack.length) { var ns = new Int32Array(stack.length * 2); ns.set(stack); stack = ns; }
          stack[sp++] = q; list.push(q);
        }
        if (list.length > budget) { conn = true; break; }
      }
      for (var j = 0; j < list.length; j++) { var r = list[j]; setv(r & 1023, (r >> 10) & 1023, r >> 20, conn ? 1 : 3); }
      if (!conn) pieces.push(Int32Array.from(list));
    }
    return pieces;
  }

  // ───────────────────────── WebGL2 ─────────────────────────
  function compile(gl, vs, fs) {
    function sh(t, src) {
      var s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error('著色器編譯失敗：' + gl.getShaderInfoLog(s) + '\n' + src.split('\n').slice(0, 3).join('\n'));
      return s;
    }
    var p = gl.createProgram();
    gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error('著色器連結失敗：' + gl.getProgramInfoLog(p));
    var u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (var i = 0; i < n; i++) { var info = gl.getActiveUniform(p, i), nm = info.name.replace(/\[0\]$/, ''); u[nm] = gl.getUniformLocation(p, info.name); }
    return { prog: p, u: u };
  }

  // 體素著色器：格座標進、世界座標出；邊線與每格明暗是在片段裡從格座標算的（合併過的大面也看得到一格一格）
  var VOXEL_VS = '#version 300 es\n' +
    'layout(location=0) in uvec4 aV;\n' +
    'uniform mat4 uModel, uVP;\n' +
    'out vec3 vL; out vec3 vW; flat out uint vN; flat out uint vC;\n' +
    'void main(){ vec3 p=vec3(aV.xyz); vL=p; vec4 w=uModel*vec4(p,1.0); vW=w.xyz; vN=aV.w&7u; vC=(aV.w>>3u)&255u; gl_Position=uVP*w; }\n';
  var VOXEL_FS = '#version 300 es\nprecision highp float;\n' +
    'in vec3 vL; in vec3 vW; flat in uint vN; flat in uint vC;\n' +
    'uniform mat4 uModel; uniform vec3 uSun, uEye, uFog, uSky, uGround; uniform float uFogD, uWater, uTint;\n' +
    'out vec4 o;\n' +
    'const vec3 NT[6]=vec3[6](vec3(1,0,0),vec3(-1,0,0),vec3(0,1,0),vec3(0,-1,0),vec3(0,0,1),vec3(0,0,-1));\n' +
    'float h3(vec3 p){ return fract(sin(dot(p,vec3(12.9898,78.233,37.719)))*43758.5453); }\n' +
    'void main(){\n' +
    '  vec3 nl=NT[int(vN)]; vec3 n=normalize(mat3(uModel)*nl);\n' +
    '  vec3 base=vec3(float((vC>>5u)&7u)/7.0, float((vC>>2u)&7u)/7.0, float(vC&3u)/3.0);\n' +
    '  vec3 cell=floor(vL-nl*0.5); base*=0.92+0.16*h3(cell);\n' +
    '  vec3 f=fract(vL); vec3 e=min(f,1.0-f); float ed=min(e.x,e.y);\n' +
    '  if(vN<2u){ ed=min(e.y,e.z); } else if(vN<4u){ ed=min(e.x,e.z); }\n' +
    '  base*=mix(0.82,1.0,smoothstep(0.0,0.09,ed));\n' +
    '  float di=max(dot(n,uSun),0.0); vec3 amb=mix(uGround,uSky,n.y*0.5+0.5);\n' +
    '  vec3 c=base*(amb*0.62+vec3(1.0,0.96,0.88)*di*0.78);\n' +
    '  if(vW.y<uWater){ float dd=clamp((uWater-vW.y)*0.12,0.0,1.0); c=mix(c,vec3(0.04,0.18,0.22),0.35+0.55*dd); }\n' +
    '  c=mix(c,vec3(1.0,0.45,0.2),uTint);\n' +
    '  float fd=length(vW-uEye); c=mix(c,uFog,1.0-exp(-fd*uFogD));\n' +
    '  o=vec4(c,1.0);\n' +
    '}\n';

  /**
   * RegionSet：一份 Grid 的 GPU 端。區塊網格快取在 meshes（區塊索引 → Uint16Array|null），
   * 64³ 一區上傳成一個 VAO。share(other) 讓第二份網格先借用第一份的區（被改到的區才自己建）。
   */
  function RegionSet(gl, grid, quadIbo) {
    this.gl = gl; this.grid = grid; this.ibo = quadIbo;
    this.meshes = new Map(); this.regions = new Map(); this.dirty = new Set(); this.dirtyRegions = new Set();
    this.rx = Math.ceil(grid.nx / 4); this.ry = Math.ceil(grid.ny / 4);
  }
  RegionSet.prototype.rkey = function (cx, cy, cz) { return (cx >> 2) + this.rx * ((cy >> 2) + this.ry * (cz >> 2)); };
  RegionSet.prototype.buildAll = function () {
    var g = this.grid;
    for (var cz = 0; cz < g.nz; cz++) for (var cy = 0; cy < g.ny; cy++) for (var cx = 0; cx < g.nx; cx++) {
      var i = g.ci(cx, cy, cz); if (g.tab[i] === null) continue;
      this.meshes.set(i, meshChunk(g, cx, cy, cz)); this.dirtyRegions.add(this.rkey(cx, cy, cz));
    }
    this.flush();
  };
  /** 跟另一份（同一份資料長出來的）共用網格與區；之後被改到的才各自重建。 */
  RegionSet.prototype.shareFrom = function (o) {
    var self = this;
    o.meshes.forEach(function (m, k) { self.meshes.set(k, m); });
    o.regions.forEach(function (r, k) { self.regions.set(k, { vao: r.vao, vbo: r.vbo, n: r.n, own: false }); });
  };
  /** 一格改了 ⇒ 它的區塊（貼邊的話連鄰區塊）要重網格化。 */
  RegionSet.prototype.touch = function (x, y, z) {
    var g = this.grid, cx = x >> 4, cy = y >> 4, cz = z >> 4, lx = x & 15, ly = y & 15, lz = z & 15;
    this.dirty.add(g.ci(cx, cy, cz));
    if (lx === 0 && cx > 0) this.dirty.add(g.ci(cx - 1, cy, cz)); if (lx === 15 && cx < g.nx - 1) this.dirty.add(g.ci(cx + 1, cy, cz));
    if (ly === 0 && cy > 0) this.dirty.add(g.ci(cx, cy - 1, cz)); if (ly === 15 && cy < g.ny - 1) this.dirty.add(g.ci(cx, cy + 1, cz));
    if (lz === 0 && cz > 0) this.dirty.add(g.ci(cx, cy, cz - 1)); if (lz === 15 && cz < g.nz - 1) this.dirty.add(g.ci(cx, cy, cz + 1));
  };
  RegionSet.prototype.flush = function () {
    var g = this.grid, self = this;
    this.dirty.forEach(function (i) {
      var cx = i % g.nx, cy = Math.floor(i / g.nx) % g.ny, cz = Math.floor(i / (g.nx * g.ny));
      self.meshes.set(i, meshChunk(g, cx, cy, cz)); self.dirtyRegions.add(self.rkey(cx, cy, cz));
    });
    this.dirty.clear();
    var gl = this.gl;
    this.dirtyRegions.forEach(function (rk) {
      var rx = rk % self.rx, ry = Math.floor(rk / self.rx) % self.ry, rz = Math.floor(rk / (self.rx * self.ry));
      var parts = [], len = 0;
      for (var cz = rz * 4; cz < Math.min(g.nz, rz * 4 + 4); cz++) for (var cy = ry * 4; cy < Math.min(g.ny, ry * 4 + 4); cy++)
        for (var cx = rx * 4; cx < Math.min(g.nx, rx * 4 + 4); cx++) { var m = self.meshes.get(g.ci(cx, cy, cz)); if (m) { parts.push(m); len += m.length; } }
      var r = self.regions.get(rk);
      if (!len) { if (r && r.own) { gl.deleteBuffer(r.vbo); gl.deleteVertexArray(r.vao); } self.regions.delete(rk); return; }
      var all = new Uint16Array(len), o = 0;
      parts.forEach(function (m) { all.set(m, o); o += m.length; });
      if (!r || !r.own) {
        r = { vao: gl.createVertexArray(), vbo: gl.createBuffer(), n: 0, own: true };
        gl.bindVertexArray(r.vao); gl.bindBuffer(gl.ARRAY_BUFFER, r.vbo);
        gl.enableVertexAttribArray(0); gl.vertexAttribIPointer(0, 4, gl.UNSIGNED_SHORT, 8, 0);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.ibo.buf); gl.bindVertexArray(null);
        self.regions.set(rk, r);
      }
      gl.bindBuffer(gl.ARRAY_BUFFER, r.vbo); gl.bufferData(gl.ARRAY_BUFFER, all, gl.DYNAMIC_DRAW);
      r.n = len / 16; self.ibo.ensure(r.n);
    });
    this.dirtyRegions.clear();
  };
  RegionSet.prototype.quads = function () { var n = 0; this.regions.forEach(function (r) { n += r.n; }); return n; };
  RegionSet.prototype.draw = function () {
    var gl = this.gl;
    this.regions.forEach(function (r) { gl.bindVertexArray(r.vao); gl.drawElements(gl.TRIANGLES, r.n * 6, gl.UNSIGNED_INT, 0); });
    gl.bindVertexArray(null);
  };
  RegionSet.prototype.dispose = function () {
    var gl = this.gl;
    this.regions.forEach(function (r) { if (r.own) { gl.deleteBuffer(r.vbo); gl.deleteVertexArray(r.vao); } });
    this.regions.clear();
  };

  /** 共用的四邊形索引（0,1,2,0,2,3, 4,5,6,…）；不夠長就就地加長（同一個 buffer 物件 ⇒ 各 VAO 的綁定不用重設）。 */
  function QuadIndex(gl) { this.gl = gl; this.buf = gl.createBuffer(); this.cap = 0; this.ensure(1 << 16); }
  QuadIndex.prototype.ensure = function (n) {
    if (n <= this.cap) return;
    var cap = Math.max(n, this.cap * 2), a = new Uint32Array(cap * 6);
    for (var i = 0; i < cap; i++) { var b = i * 4, o = i * 6; a[o] = b; a[o + 1] = b + 1; a[o + 2] = b + 2; a[o + 3] = b; a[o + 4] = b + 2; a[o + 5] = b + 3; }
    var gl = this.gl; gl.bindVertexArray(null); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.buf); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, a, gl.STATIC_DRAW);
    this.cap = cap;
  };

  root.VoxelKit = {
    CHUNK: CH, rgb332: rgb332, hashVoxel: hashVoxel,
    b64ToBytes: b64ToBytes, inflateRaw: inflateRaw, parse: parse, decode: decode, loadEmbedded: loadEmbedded,
    embeddedImage: embeddedImage, embeddedJSON: embeddedJSON,
    Grid: Grid, verify: verify, meshChunk: meshChunk, M4: M4, raycast: raycast, detached: detached,
    compile: compile, VOXEL_VS: VOXEL_VS, VOXEL_FS: VOXEL_FS, RegionSet: RegionSet, QuadIndex: QuadIndex,
    pack: function (x, y, z) { return x | (y << 10) | (z << 20); }
  };
})(typeof window !== 'undefined' ? window : this);



(function () {
'use strict';
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/00_core.js ──
/* 憲法號對轟 —— 遊戲本體（體素的解碼、網格、算繪、射線、連通在 VoxelKit）。
 * 世界：公尺、Y 朝上、海面 y = 0。船的格座標 (x 船長、y 船寬、z 高) ⇒ 船體座標 (x, z, −y)（行列式 +1，繞序不翻）。
 * 同一型的兩艘共用一份 1:1 資料（船型 sh.T，05_hull.js），被打到的區塊才各自複製（VoxelKit.Grid.share）。
 * 模擬固定步長 1/60 秒、亂數有種子 ⇒ ?demo=<秒>&seed=<n> 每次快轉出同一格（縮圖與驗收用）。
 *
 * 拆檔：js/ 底下照功能分檔，檔名前面的數字就是順序。template.html 照這個順序列出（每檔一個帶 data-bundle="game" 的 script 標籤），
 *   vxk_inline.py 把同一個 bundle 接成一段、包進同一個閉包（(function () { 'use strict'; … })()）⇒ 各檔共用變數與函式，
 *   跟沒拆之前是同一個作用域；不會掛到 window、不會跟瀏覽器的全域名字撞。
 *   ⛔ 各檔沒有自己的作用域：新的頂層名字先搜一遍有沒有撞名（以前 IIFE 裡也撞過：船員的 kill 蓋掉碎屑的 kill）。
 *   ⛔ 頂層的敘述照檔案順序執行：要在載入時就跑的（讀網址、建 GL）放在用到它的檔之前。
 */
var VK = window.VoxelKit, M4 = VK.M4;
var Q = new URLSearchParams(location.search);
var DEMO = Q.has('demo') ? Math.max(0, parseFloat(Q.get('demo')) || 0) : -1;
var STILL = Q.get('still') === '1', DEBUG = Q.get('debug') === '1';
var SEED = (parseInt(Q.get('seed'), 10) >>> 0) || 1797;
var CAMQ = Q.get('cam') || '';
// 逐幀分段計時（?debug=1 才有；TASK-0531 找卡頓）：每一格畫面各段花幾 ms（模擬每一步的各段累加），留最近 PF.max 格；__game.frames() 讀最慢的幾格。
//   pfLap(k)：從上一個 lap（或這一段的起點 PF.t）到現在的時間記到 k。沒開 debug ⇒ PF ＝ null，呼叫端一個判斷就跳過。
var PF = DEBUG ? { t: 0, cur: {}, ring: [], max: 1200 } : null;
function pfLap(k) { var t = performance.now(); PF.cur[k] = (PF.cur[k] || 0) + t - PF.t; PF.t = t; }
function pfEnd(f0, steps) { var c = PF.cur; c.total = performance.now() - f0; c.steps = steps; c.simt = SIMT; PF.ring.push(c); if (PF.ring.length > PF.max) PF.ring.shift(); PF.cur = {}; }
if (STILL) document.getElementById('stage').classList.add('still');
function $(id) { return document.getElementById(id); }

// ───────────────────────── 亂數（有種子） ─────────────────────────
var rs = SEED;
function rnd() { rs |= 0; rs = rs + 0x6D2B79F5 | 0; var t = Math.imul(rs ^ rs >>> 15, 1 | rs); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
function rr(a, b) { return a + (b - a) * rnd(); }
function gauss() { var u = rnd() || 1e-9, v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(6.2831853 * v); }
function hash3(x, y, z) { var h = (Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(z, 1274126177)) | 0; h = Math.imul(h ^ (h >>> 13), 1103515245); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

// ───────────────────────── 常數 ─────────────────────────
// 一場最多幾艘船（TASK-0537；Tim 2026-10-13：上限 4 ⇒ 8，改檔案可調；之後放進設定後台 TASK-0542）。
// 每一格只給「視野裡離鏡頭最近的幾艘」GPU 的格（Tim 2026-10-13「優先選最近的 N 條船，超過的就沒陰影＆遮罩」「超過的靠全局覆蓋」「只選視野範圍內最近的」；60_render.js gpuSlots）：
//   · 自己的陰影圖：最近的 GFX.shships 艘（畫質設定「陰影船數」0～MAX_SHIPS，最高畫質 ＝ MAX_SHIPS）；其他的船畫進一張罩住它們的全局陰影圖（解析度低）。
//   · 船艙遮罩（與透視）：最近的 MASK_NEAR 艘；其他的沒有（遠處看不到艙裡）。
//   陰影圖、船艙遮罩都是貼圖陣列（各佔一個單元：陰影第 4 號、遮罩第 1 號）⇒ 船數不受貼圖單元限制。
var MAX_SHIPS = 8, MASK_NEAR = 4;
var DT = 1 / 60, G = 9.81, V0 = 175, ZW0 = 63;    // ZW0：沒有 meta 時的設計水線（憲法號吃水 63 格，basecamp 的下水段同一個數）；每種船的在 T.zw
var RELOAD = 7, RELOAD_SANDBOX = 1.6;
var AMMO = ['實心彈', '爆裂彈', '鏈彈'];
var S;                                            // 公尺／格（封裝檔的 header；每種船都要一樣）。中線、外框、水線…每種船各一份：sh.T（05_hull.js）
var SUN = norm([-0.45, 0.62, -0.38]), SKY = [0.42, 0.58, 0.80], HORIZON = [0.80, 0.80, 0.77], GROUND = [0.30, 0.27, 0.22];
var WIND = [0.6, 0, 1.65];   // 風往哪吹（m/s，煙飄的速度）；方向也是航行的風向：開局兩艘的航向跟它大致垂直（橫風起跑）

function norm(v) { var l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / l, v[1] / l, v[2] / l]; }
function add(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
function mul(a, k) { return [a[0] * k, a[1] * k, a[2] * k]; }
function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function len(a) { return Math.hypot(a[0], a[1], a[2]); }
function rotM(axis, ang) {          // 繞任意軸的 mat4
  var a = norm(axis), c = Math.cos(ang), s = Math.sin(ang), t = 1 - c, x = a[0], y = a[1], z = a[2];
  return new Float32Array([t * x * x + c, t * x * y + s * z, t * x * z - s * y, 0, t * x * y - s * z, t * y * y + c, t * y * z + s * x, 0,
    t * x * z + s * y, t * y * z - s * x, t * z * z + c, 0, 0, 0, 0, 1]);
}
function trans(x, y, z) { var m = M4.ident(); m[12] = x; m[13] = y; m[14] = z; return m; }
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/01_gl.js ──
// ───────────────────────── WebGL ─────────────────────────
var cv = $('cv'), gl = cv.getContext('webgl2', { antialias: false, preserveDrawingBuffer: true });   // 反鋸齒自己做（MSAA framebuffer，畫質設定；60_render.js targets）
function fail(msg) { var e = $('err'); e.style.display = 'block'; e.textContent = msg; $('load').textContent = msg; }
if (!gl) { fail('這個瀏覽器沒有 WebGL2，畫不出來。'); throw new Error('no WebGL2'); }   // 拆檔後這裡是閉包的頂層：throw ＝ 原本的 return（停下來）

var P = {};
// 陰影（畫質；60_render.js shadowPass）：每艘船一張陰影圖（太陽方向的正交投影，uShM[k]），收的那一點落在哪張就用哪張（都在 ⇒ 取暗的）；
//   全部放在同一個深度貼圖陣列 uShA（固定第 4 號）⇒ 船再多也只佔一個貼圖單元（TASK-0537：上限 8 艘時，每艘一張 ⇒ 片段著色器 16 個單元不夠）。
//   第 k 層 ＝ 陰影的第 k 格（60_render.js gpuSlots：視野裡最近的 GFX.shships 艘），只查前 uNS 層（0 ＝ 一層都不查）；
//   全局（沒排進去的船，uShG 開著才查）：矩陣 uShM[MAX_SHIPS]、層 uShGL（＝ uNS，緊接在後面 ⇒ 陣列只配用到的層數）、格子大 ⇒ 沿法線推得遠 uShOffG。
//   一對一 ⇒ 跟以前同一個值：min(2, s0, s1) ＝ min(s0, s1)（shOne 最大就是 2）。
//   uShOn ＝ 0 關、1 低（硬體 2×2）、2 高（再 4 點柔邊）；沿法線推出去 uShOff 公尺再比（⛔ 不推 ⇒ 平面上自己遮自己的條紋）；
//   陽光越斜推越遠（呼叫端把法線乘 1～3 倍：斜面在陰影圖上一格跨的深度大）。
// uClip：反射那一趟丟掉水面以下的（平常是 −10⁹）。
// uSunK：直射光的強度（天氣；晴天 1）—— 收陰影的地方都乘 shadowK，順便乘在這裡。
var NS_SH = String(MAX_SHIPS), NS_MK = String(MASK_NEAR);                // 著色器的陣列長度：陰影照 MAX_SHIPS（＋1 格全局）、船艙遮罩照 MASK_NEAR（00_core.js）
var SHADOW_GLSL = 'uniform highp sampler2DArrayShadow uShA; uniform mat4 uShM[' + (MAX_SHIPS + 1) + ']; uniform int uNS; uniform float uShOn, uShPx, uShOff, uShG, uShGL, uShOffG, uClip, uSunK;\n' +
  'float shOne(int k, float L, vec3 w){ vec4 p=uShM[k]*vec4(w,1.0); vec3 q=p.xyz*0.5+0.5;\n' +
  '  if(q.x<0.002||q.y<0.002||q.x>0.998||q.y>0.998||q.z>0.999) return 2.0; q.z-=0.0006;\n' +
  '  if(uShOn<1.5) return texture(uShA,vec4(q.xy,L,q.z));\n' +
  '  float e=uShPx*0.9; return 0.25*(texture(uShA,vec4(q.xy+vec2(-e,-e),L,q.z))+texture(uShA,vec4(q.xy+vec2(e,-e),L,q.z))+texture(uShA,vec4(q.xy+vec2(-e,e),L,q.z))+texture(uShA,vec4(q.xy+vec2(e,e),L,q.z))); }\n' +
  'float shadowK(vec3 w, vec3 n){ if(uShOn<0.5) return uSunK; vec3 p=w+n*uShOff; float m=2.0;' +
  ' for(int k=0;k<' + NS_SH + ';k++){ if(k>=uNS) break; m=min(m,shOne(k,float(k),p)); }' +
  ' if(uShG>0.5) m=min(m,shOne(' + NS_SH + ',uShGL,w+n*uShOffG)); return min(m,1.0)*uSunK; }\n';
// 船艙遮罩（海、船邊水花的白沫共用；要有 in vec3 vW）：那一點換到船的格座標，落在原本船殼的外形裡 ⇒ 呼叫端丟掉（HULL_HIT）。
//   遮罩照船型一層（uHullA：R8 貼圖陣列，每層 ＝ 那一型每個 (x, z) 船殼的半寬；固定第 1 號；60_render.js hullArr）；
//   格（60_render.js gpuSlots：視野裡最近的 GFX.masks 艘，最多 MASK_NEAR）：uInv[k]（世界 → 格）、uHullK[k] ＝ (那一型的寬, 高, 中線 y, 第幾層)、
//   uHide[k] ＝ 那艘還沒開始沉（60_render.js hullUniforms）。沒用到的那幾格 uHide 0 ⇒ 一比就跳過、不取樣。uNM ＝ 用到幾格（透視 nearAny 也照它）。
var HULL_GLSL = 'uniform mat4 uInv[' + NS_MK + ']; uniform float uHide[' + NS_MK + ']; uniform highp sampler2DArray uHullA; uniform vec4 uHullK[' + NS_MK + ']; uniform int uNM;\n' +
  'bool inHull(int k){ vec4 K=uHullK[k]; vec4 l=uInv[k]*vec4(vW,1.0); if(l.x<0.0||l.z<0.0||l.x>=K.x||l.z>=K.y) return false; float hb=texelFetch(uHullA,ivec3(int(l.x),int(l.z),int(K.w)),0).r*255.0; return hb>0.0 && abs(l.y-K.z)<hb; }\n' +
  'bool hullHit(){ for(int k=0;k<' + NS_MK + ';k++) if(uHide[k]>0.5&&inHull(k)) return true; return false; }\n';
var HULL_HIT = 'hullHit()';                                              // 落在哪一艘的船艙裡
// 剖面與隱藏甲板（停格；74_cutaway.js）：照船的格座標丟掉 —— uCut ＝ (中線 y, 剖哪一邊 ±1（0 ＝ 不剖）, 拿掉到第幾層（−1 ＝ 不拿）, 開關)；
//   uCutT：那艘船型每一層的切高（R32F，寬 ＝ 格的 x、高 ＝ 層；照舷弧逐欄），uCutW.x ＝ 寬。模型、繩、帆另給 uCutInv（世界 → 格）。
//   uCutT 一律指第 8 號（setCommon；沒開時綁 1×1 的空貼圖）：⛔ 預設的第 0 號 ⇒ 那一號綁著正在畫的畫布的貼圖時，整次繪製被丟掉（Feedback loop，量到 203 筆警告）——
//   就算分支沒走到，驅動照樣檢查程式裡每一個取樣器。
//   開著時水線下不染海水色（剖開、拿掉甲板看到的是艙內：⛔ 照染 ⇒ 沒進水的船底看起來像積了一層水）。
var CUT_GLSL = 'uniform highp sampler2D uCutT; uniform vec4 uCut; uniform vec2 uCutW;\n' +
  'bool cutOut(vec3 l){ if(uCut.w<0.5) return false; if(uCut.y*(l.y-uCut.x)>0.0) return true;\n' +
  '  return uCut.z>=0.0 && l.z>=texelFetch(uCutT,ivec2(clamp(int(floor(l.x)),0,int(uCutW.x)-1),int(uCut.z)),0).r; }\n';
function programs() {
  var cd = gl.createTexture(); gl.activeTexture(gl.TEXTURE8); gl.bindTexture(gl.TEXTURE_2D, cd);   // 第 8 號：剖面切高的空貼圖（見 CUT_GLSL）
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.R32F, 1, 1, 0, gl.RED, gl.FLOAT, new Float32Array([1e9]));
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST); gl.activeTexture(gl.TEXTURE0);
  P.vox = VK.compile(gl, VK.VOXEL_VS, voxFS());
  P.deb = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec3 aP; layout(location=1) in vec3 aN; layout(location=2) in vec4 iP; layout(location=3) in vec4 iQ; layout(location=4) in float iC;\n' +
    'uniform mat4 uVP; out vec3 vN; out vec3 vW; flat out float vC;\n' +
    'vec3 rq(vec4 q, vec3 v){ return v+2.0*cross(q.xyz, cross(q.xyz,v)+q.w*v); }\n' +
    'void main(){ vec3 w=iP.xyz+rq(iQ,aP*iP.w); vW=w; vN=rq(iQ,aN); vC=iC; gl_Position=uVP*vec4(w,1.0); }\n',
    '#version 300 es\nprecision highp float;\n' + SEA_GLSL + 'in vec3 vN; in vec3 vW; flat in float vC; uniform vec3 uSun,uEye,uFog,uSky,uGround; uniform float uFogD,uLum; out vec4 o;\n' +
    'void main(){ uint c=uint(vC+0.5); vec3 b=vec3(float((c>>5u)&7u)/7.0,float((c>>2u)&7u)/7.0,float(c&3u)/3.0); vec3 n=normalize(vN);\n' +
    ' vec3 col=b*(mix(uGround,uSky,n.y*0.5+0.5)*0.62+vec3(1.0,0.96,0.88)*max(dot(n,uSun),0.0)*0.78);\n' +
    ' col*=uLum; if(vW.y<seaH(vW.xz)) col=mix(col,vec3(0.04,0.18,0.22),0.6); float fd=length(vW-uEye); o=vec4(mix(col,uFog,1.0-exp(-fd*uFogD)),1.0); }\n');
  P.tri = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec3 aP; layout(location=1) in vec3 aN; layout(location=2) in vec3 aC; uniform mat4 uModel,uVP; out vec3 vN; out vec3 vW; out vec3 vC;\n' +
    'void main(){ vec4 w=uModel*vec4(aP,1.0); vW=w.xyz; vN=mat3(uModel)*aN; vC=aC; gl_Position=uVP*w; }\n',
    '#version 300 es\nprecision highp float;\n' + SEA_GLSL + SHADOW_GLSL + CUT_GLSL + 'in vec3 vN; in vec3 vW; in vec3 vC; uniform vec3 uSun,uEye,uFog,uSky,uGround; uniform float uFogD,uLit,uGlow; uniform mat4 uCutInv; out vec4 o;\n' +
    'void main(){ if(vW.y<uClip) discard; if(uCut.w>0.5 && cutOut((uCutInv*vec4(vW,1.0)).xyz)) discard; vec3 n=normalize(vN); float sd=dot(n,uSun), d=abs(sd); vec3 col=vC;\n' +
    ' if(uLit>0.5){ d*=shadowK(vW,(sd<0.0?-n:n)*(3.0-2.0*d)); col=vC*(mix(uGround,uSky,0.6)*0.65+vec3(1.0,0.96,0.88)*d*0.7); }\n' +
    // 燈籠（meta kind=lantern；drawModels 設 uGlow）：只有琥珀色的燈罩發光（色 245 ＝ 1, .71, .33）—— 金框（248，藍 0）、暗紅（128）照常受光
    ' if(uGlow>0.0) col=mix(col,vC*1.2+vec3(0.3,0.14,0.0),uGlow*step(0.9,vC.r)*step(0.2,vC.b)*step(vC.b,0.5));\n' +
    ' if(uCut.w<0.5 && vW.y<seaH(vW.xz)) col=mix(col,vec3(0.04,0.18,0.22),0.6); float fd=length(vW-uEye); o=vec4(mix(col,uFog,1.0-exp(-fd*uFogD)),1.0); }\n');
  // 帆：頂點法線（平滑，不是一個三角形一個平面）；法線翻向看的那一面；包覆光（背光面不死黑、明暗過渡慢）＋太陽在帆後面時布透出暖光
  P.sail = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec3 aP; layout(location=1) in vec3 aN; layout(location=2) in vec3 aC; uniform mat4 uModel,uVP; out vec3 vN; out vec3 vW; out vec3 vC;\n' +
    'void main(){ vec4 w=uModel*vec4(aP,1.0); vW=w.xyz; vN=mat3(uModel)*aN; vC=aC; gl_Position=uVP*w; }\n',
    '#version 300 es\nprecision highp float;\n' + SEA_GLSL + SHADOW_GLSL + CUT_GLSL + 'in vec3 vN; in vec3 vW; in vec3 vC; uniform vec3 uSun,uEye,uFog,uSky,uGround; uniform float uFogD; uniform mat4 uCutInv; out vec4 o;\n' +
    'void main(){ if(vW.y<uClip) discard; if(uCut.w>0.5 && cutOut((uCutInv*vec4(vW,1.0)).xyz)) discard; vec3 n=normalize(vN); if(!gl_FrontFacing) n=-n; float s=dot(n,uSun), sk=shadowK(vW,(s<0.0?-n:n)*(3.0-2.0*abs(s)));\n' +
    ' float lit=max(s,0.0)*0.45*sk+(s*0.5+0.5)*0.32*(0.55+0.45*sk); float thru=max(-s,0.0)*0.30*sk;\n' +
    ' vec3 col=vC*(mix(uGround,uSky,n.y*0.5+0.5)*0.62+vec3(1.0,0.96,0.88)*lit)+vC*vec3(1.0,0.88,0.66)*thru;\n' +
    ' if(uCut.w<0.5 && vW.y<seaH(vW.xz)) col=mix(col,vec3(0.04,0.18,0.22),0.6); float fd=length(vW-uEye); o=vec4(mix(col,uFog,1.0-exp(-fd*uFogD)),1.0); }\n');
  P.pt = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec3 aP; layout(location=1) in float aS; layout(location=2) in vec4 aC; layout(location=3) in float aT; uniform mat4 uVP; uniform float uPx; out vec4 vC; out float vT; out float vR;\n' +
    'void main(){ vec4 c=uVP*vec4(aP,1.0); gl_Position=c; gl_PointSize=clamp(aS*uPx/max(c.w,0.1),1.0,256.0); vC=aC; vT=aT; vR=aP.y*0.9+aT*1.7; }\n',
    // 類型 4（vT ≥ 16）＝ 帆的布片：程式畫的菱形，角度跟著高度轉、側過來時變窄（像在翻）；fx.png 沒有這一列 ⇒ 一律程式畫
    '#version 300 es\nprecision highp float; in vec4 vC; in float vT; in float vR; uniform sampler2D uFx; uniform float uUseFx; out vec4 o;\n' +
    'void main(){ if(vT>=16.0){ vec2 d=gl_PointCoord*2.0-1.0; float cr=cos(vR), sr=sin(vR); vec2 q=vec2(cr*d.x-sr*d.y, sr*d.x+cr*d.y);\n' +
    '   float fl=0.3+0.7*abs(sin(vR*0.7)); if(abs(q.x)/(0.95*fl)+abs(q.y)/(0.5+0.12*(vT-16.0))>1.0) discard; o=vec4(vC.rgb*(0.75+0.25*fl),vC.a); return; }\n' +
    ' if(uUseFx>0.5 && vT>=0.0){ float ty=floor(vT/4.0), va=vT-ty*4.0; vec4 t=texture(uFx,(vec2(va,ty)+gl_PointCoord)/4.0); if(t.a<0.02) discard; o=vec4(t.rgb,t.a*vC.a); return; }\n' +
    ' vec2 d=gl_PointCoord*2.0-1.0; float r=dot(d,d); if(r>1.0) discard; float a=vC.a*(1.0-r*r); o=vec4(vC.rgb*(1.0-0.25*r),a); }\n');
  // 海：跟著鏡頭的同心圓網格（60_render.js seaGrid；aP ＝ 離中心的 x、z 與那一圈的網格間距），頂點照浪位移（08_sea.js；比網格粗的浪拿掉、1 km 外放平）；
  //   法線在片段裡照解析的坡度算（seaG，遠處淡掉）＋細的漣漪 uDet 道（畫質）—— 漣漪只在畫面上，不進物理。
  P.water = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec3 aP; uniform mat4 uVP; uniform vec2 uC;\n' + SEA_GLSL +
    'out vec3 vW; void main(){ vec2 p=uC+aP.xy; float h=seaHs(p,aP.z)*(1.0-smoothstep(900.0,1600.0,length(aP.xy))); vW=vec3(p.x,h,p.y); gl_Position=uVP*vec4(vW,1.0); }\n',
    '#version 300 es\nprecision highp float; in vec3 vW; uniform vec3 uEye,uSun,uFog,uSky; uniform float uFogD,uDet,uReflOn,uRefr,uFoam; uniform vec2 uView; uniform sampler2D uRefl,uScene,uSceneD; out vec4 o;\n' + SEA_GLSL + SHADOW_GLSL +
    // 反射（uReflOn）：RT.R 是鏡像過來的船，照螢幕座標＋法線擾動讀，沒畫到的地方（a ＝ 0）照舊是天空。
    // 折射（uRefr）：0 不透明、1 半透明（底下的照舊混進來）、2 讀 RT.B（畫海之前的場景）：照法線擾動、照水的厚度（兩個深度相減）吸收成海的顏色。
    'float linZ(float d){ float z=d*2.0-1.0; return 5000.0/(5000.5-z*4999.5); }\n' +
    // 船艙裡不畫海（HULL_GLSL）：海面那一點落在原本船殼的外形裡 ⇒ 丟掉
    HULL_GLSL +
    // 細浪（只在畫面）：uDet 道，波長從 7 m 往下每道 ×0.8 再亂一點、方向在風向 ±70° 亂撒、相位亂撒（雜湊，不抽亂數）⇒ 不成整數比、不會一格一格重複；
    // 每道照像素寬 fp 淡掉（遠處自動變平滑，不疊紋）；再乘一層慢慢飄的雜訊 ⇒ 海面一塊皺、一塊平（陣風吹過的樣子）。
    'float hs1(float n){ return fract(sin(n*12.9898)*43758.5453); }\n' +
    'float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f); float a=hs1(dot(i,vec2(1.0,57.0))), b=hs1(dot(i+vec2(1.0,0.0),vec2(1.0,57.0))), c=hs1(dot(i+vec2(0.0,1.0),vec2(1.0,57.0))), d=hs1(dot(i+vec2(1.0,1.0),vec2(1.0,57.0))); return mix(mix(a,b,f.x),mix(c,d,f.x),f.y); }\n' +
    'vec2 detail(vec2 p,float fp){ vec2 g=vec2(0.0); float L=7.0, st=0.07;\n' +
    '  for(int i=0;i<16;i++){ if(float(i)>=uDet) break; float fi=float(i)+1.0; float l=L*(0.85+0.3*hs1(fi*3.1)); float k=6.2832/l, a=SEA_WA+(hs1(fi*7.7)-0.5)*2.4; vec2 d=vec2(cos(a),sin(a));\n' +
    '    g+=d*st*(1.0-smoothstep(0.25*l,0.6*l,fp))*cos(dot(p,d)*k-sqrt(9.81*k)*uSeaT+hs1(fi*5.3)*6.2832); L*=0.8; st*=0.88; }\n' +
    '  return g*(0.45+1.1*vn(p*0.025+vec2(uSeaT*0.013,uSeaT*0.007))); }\n' +
    // 停格的「🔍 透視」（72_floodui.js）：船附近的海面不畫 ⇒ 看得到水線下的船殼與破口。uXb ＝ 那艘船型在格座標的中心與半長、半寬（xrBox），再往外 6 m（60 格）；uXr ＝ 0 ⇒ 照原本畫
    'uniform float uXr; uniform vec4 uXb[' + NS_MK + ']; bool nearShip(int k){ vec4 b=uXb[k]; vec4 l=uInv[k]*vec4(vW,1.0); vec2 q=abs(l.xy-b.xy)-b.zw; return length(max(q,vec2(0.0)))<60.0; }\n' +
    'bool nearAny(){ for(int k=0;k<' + NS_MK + ';k++){ if(k>=uNM) break; if(nearShip(k)) return true; } return false; }\n' +
    'void main(){ if(' + HULL_HIT + ') discard; if(uXr>0.5&&nearAny()) discard; vec2 p=vW.xz; float fd0=length(vW-uEye); float k0=1.0-smoothstep(300.0,1400.0,fd0), k1=1.0-smoothstep(60.0,260.0,fd0), k2=1.0-smoothstep(25.0,110.0,fd0);\n' +
    ' vec2 dd=fwidth(vW.xz); float fp=max(dd.x,dd.y);\n' +
    ' vec2 g=seaGf(p,fp)+detail(p,fp);\n' +
    ' vec3 n=normalize(vec3(-g.x,1.0,-g.y)); vec3 v=normalize(uEye-vW); float fr=0.04+0.96*pow(1.0-max(dot(n,v),0.0),5.0);\n' +
    ' vec3 r=reflect(-v,n); vec3 sky=mix(uFog,uSky,clamp(r.y*1.6,0.0,1.0)); vec2 sc=gl_FragCoord.xy/uView; float sk=shadowK(vW,vec3(0.0,1.0,0.0));\n' +
    ' if(uReflOn>0.5){ vec4 rc=textureLod(uRefl,sc+n.xz*0.035,0.0); sky=mix(sky,rc.rgb,rc.a); }\n' +
    ' float sp=pow(max(dot(r,uSun),0.0),180.0)*1.6*sk; float fd=length(vW-uEye), a=mix(0.86,1.0,clamp(fd/600.0,0.0,1.0));\n' +
    ' vec3 deep=vec3(0.03,0.16,0.21)*mix(0.72,1.0,sk);\n' +
    ' if(uRefr<0.5) a=1.0; else if(uRefr>1.5){ float zw=linZ(gl_FragCoord.z); vec2 off=n.xz*0.045; float zs=linZ(textureLod(uSceneD,sc+off,0.0).r);\n' +
    '   if(zs<zw){ off=vec2(0.0); zs=linZ(textureLod(uSceneD,sc,0.0).r); } float th=max(zs-zw,0.0);\n' +
    '   vec3 under=textureLod(uScene,sc+off,0.0).rgb*vec3(0.55,0.86,0.92); deep=mix(deep,under,exp(-th*0.3)*clamp(1.0-fd/500.0,0.0,1.0)); a=1.0; }\n' +
    ' vec3 c=mix(deep,sky,fr)+vec3(1.0,0.92,0.75)*sp;\n' +
    // 白沫（天氣：暴風雨）：浪頭（高度在全部振幅的 40% 以上）照一層慢慢飄的雜訊碎成一塊一塊；晴天 uFoam ＝ 0 ⇒ 整段跳過（畫面逐位元組不變）
    ' if(uFoam>0.0){ float hn=seaH(p)/max(uSeaK*1.14,1e-3); float fm=smoothstep(0.4,0.8,hn)*smoothstep(0.3,0.7,vn(p*0.16+vec2(uSeaT*0.05,0.0)))+0.25*smoothstep(0.6,0.9,vn(p*0.9-vec2(0.0,uSeaT*0.2)))*smoothstep(0.2,0.6,hn);\n' +
    '   c=mix(c,vec3(0.82,0.86,0.88)*(0.55+0.45*uSunK),clamp(fm,0.0,1.0)*0.8*uFoam*(1.0-smoothstep(200.0,900.0,fd))); }\n' +
    ' c=mix(c,uFog,1.0-exp(-fd*uFogD)); o=vec4(c,a); }\n');
  // 雨（天氣 × 畫質的「雨」）：整個畫面一層斜的雨絲，三層遠近（越近越粗越快）；欄位照雜湊挑哪幾欄有雨、每欄的相位亂撒。鏡頭轉的時候雨絲跟著水平滑（uYaw）。
  P.rain = VK.compile(gl, '#version 300 es\nlayout(location=0) in vec2 aP; void main(){ gl_Position=vec4(aP,0.0,1.0); }\n',
    '#version 300 es\nprecision highp float; uniform float uT,uRain,uYaw; uniform vec2 uView; out vec4 o;\n' +
    'float h1(float n){ return fract(sin(n*12.9898)*43758.5453); }\n' +
    'float lay(vec2 uv,float sc,float sp,float th){ vec2 q=uv*sc; q.x+=q.y*0.16; float col=floor(q.x), h=h1(col+sc*17.0); if(h<th) return 0.0;\n' +
    '  float y=fract(q.y*0.05+uT*sp*(0.75+0.5*h)+h*7.0); float w=1.0-smoothstep(0.0,0.12,abs(fract(q.x)-0.5)); return w*smoothstep(0.0,0.1,y)*smoothstep(0.4,0.12,y); }\n' +
    'void main(){ vec2 uv=gl_FragCoord.xy/uView.y; uv.x+=uYaw*0.5; float th=1.0-0.55*uRain;\n' +
    ' float a=lay(uv,90.0,1.6,th)*0.35+lay(uv,55.0,1.25,th)*0.5+lay(uv,32.0,0.95,th)*0.65; o=vec4(vec3(0.78,0.82,0.86),clamp(a,0.0,1.0)*0.45*uRain); }\n');
  // 只寫深度（陰影圖）：體素照 VoxelKit 的頂點著色器、模型與帆共用一支
  var NOFS = '#version 300 es\nprecision highp float; void main(){}\n';
  P.dvox = VK.compile(gl, VK.VOXEL_VS, NOFS);
  P.dtri = VK.compile(gl, '#version 300 es\nlayout(location=0) in vec3 aP; uniform mat4 uModel,uVP; void main(){ gl_Position=uVP*(uModel*vec4(aP,1.0)); }\n', NOFS);
  P.sky = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec2 aP; uniform mat4 uInv; out vec3 vD; void main(){ vec4 a=uInv*vec4(aP,1.0,1.0); vD=a.xyz/a.w; gl_Position=vec4(aP,0.9999,1.0); }\n',
    '#version 300 es\nprecision highp float; in vec3 vD; uniform vec3 uEye,uSun,uFog,uSky; out vec4 o;\n' +
    'void main(){ vec3 d=normalize(vD-uEye); float h=clamp(d.y,0.0,1.0); vec3 c=mix(uFog,uSky,pow(h,0.55)); float s=max(dot(d,uSun),0.0);\n' +
    ' c+=vec3(1.0,0.85,0.6)*(pow(s,600.0)*3.0+pow(s,12.0)*0.18); if(d.y<0.0) c=uFog; o=vec4(c,1.0); }\n');
}
function setCommon(p) {
  var u = p.u;
  if (u.uVP) gl.uniformMatrix4fv(u.uVP, false, PASS.vp || CAM.vp);          // PASS：反射、陰影那一趟換掉（60_render.js）
  if (u.uSun) gl.uniform3fv(u.uSun, SUN);
  if (u.uEye) gl.uniform3fv(u.uEye, PASS.eye || CAM.eye);
  if (u.uFog) gl.uniform3fv(u.uFog, HORIZON);
  if (u.uSky) gl.uniform3fv(u.uSky, SKY);
  if (u.uGround) gl.uniform3fv(u.uGround, GROUND);
  if (u.uFogD) gl.uniform1f(u.uFogD, WX.fog);                   // 霧（天氣：晴 0.0016、暴風雨 0.0042）
  if (u.uWater) gl.uniform1f(u.uWater, 0.0);
  if (u.uTint) gl.uniform1f(u.uTint, 0.0);
  if (u.uSeaK) gl.uniform1f(u.uSeaK, SEA_K * WX.sea);                  // 浪（08_sea.js）：大小、時間（模擬時間 ⇒ 暫停時浪也停）
  if (u.uSeaT) gl.uniform1f(u.uSeaT, SIMT);
  if (u.uClip) gl.uniform1f(u.uClip, PASS.clip);
  if (u.uCutT) gl.uniform1i(u.uCutT, 8);                       // 剖面的切高貼圖（74_cutaway.js）：固定第 8 號
  if (u.uSunK) gl.uniform1f(u.uSunK, WX.sun);                   // 天氣（08_weather.js）：陽光、水手與碎木的亮度、白沫
  if (u.uLum) gl.uniform1f(u.uLum, WX.lum);
  if (u.uFoam) gl.uniform1f(u.uFoam, WX.foam);
  if (u.uNS) gl.uniform1i(u.uNS, nsGPU());                      // 場上幾艘（陰影、透視只跑這幾格；60_render.js）
  if (u.uShOn) {                                              // 陰影圖陣列綁在第 4 號（60_render.js render 開頭綁）；每一層的矩陣一次給（沒用到的 ＝ FAR_M）
    gl.uniform1f(u.uShOn, PASS.sh ? GFX.shadow : 0);
    gl.uniform1i(u.uShA, 4); gl.uniformMatrix4fv(u.uShM, false, SHM.mats);
    gl.uniform1f(u.uShPx, 1 / SHM.n); gl.uniform1f(u.uShOff, SHM.off);
    gl.uniform1f(u.uShG, SHM.glob ? 1 : 0); gl.uniform1f(u.uShOffG, SHM.offG);
  }
}
/** 船殼的著色器：VoxelKit 那一份＋這個遊戲要的（水下的顏色照浪的水面）。⛔ 不改 VoxelKit（別的作品也用）；找不到要換的那一段 ⇒ 照原本的畫。 */
function voxFS() {
  var s = VK.VOXEL_FS, a = 'out vec4 o;', b = 'if(vW.y<uWater){ float dd=clamp((uWater-vW.y)*0.12', c = 'float di=max(dot(n,uSun),0.0);', d = 'void main(){';
  if ([a, b, c, d].some(function (x) { return s.indexOf(x) < 0; })) { console.warn('VoxelKit 的體素著色器改過了：船殼不跟著浪著色、不收陰影'); return s; }
  return s.replace(a, SEA_GLSL + SHADOW_GLSL + CUT_GLSL + a).replace(b, 'float wy=uWater+seaH(vW.xz); if(uCut.w<0.5 && vW.y<wy){ float dd=clamp((wy-vW.y)*0.12')
    .replace(c, 'float di=max(dot(n,uSun),0.0); if(di>0.0) di*=shadowK(vW,n*(3.0-2.0*di));').replace(d, d + ' if(vW.y<uClip) discard; if(cutOut(vL)) discard;');   // cutOut：剖面與隱藏甲板（vL ＝ 格座標）
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/02_audio.js ──
// ───────────────────────── 音效（按下開始後才建；沒有聲音也完整） ─────────────────────────
var AC = null, master = null, noiseBuf = null, muted = false;
function initAudio() {
  if (AC || DEMO >= 0) return;
  try {
    AC = new (window.AudioContext || window.webkitAudioContext)();
    master = AC.createGain(); master.gain.value = 0.8; master.connect(AC.destination);
    var n = AC.sampleRate * 2; noiseBuf = AC.createBuffer(1, n, AC.sampleRate);
    var d = noiseBuf.getChannelData(0), s = 22222;
    for (var i = 0; i < n; i++) { s = (Math.imul(s, 1103515245) + 12345) & 0x7fffffff; d[i] = s / 0x3fffffff - 1; }
  } catch (e) { AC = null; }
}
function sfx(kind, at, vol) {
  if (!AC || muted) return;
  var dist = at ? len(sub(at, CAM.eye)) : 0, v = (vol || 1) / (1 + dist / 70);
  if (v < 0.01) return;
  var t = AC.currentTime + Math.min(0.25, dist / 340) * 0.5, g = AC.createGain(); g.connect(master);
  var src = AC.createBufferSource(); src.buffer = noiseBuf; src.playbackRate.value = 0.6 + Math.random() * 0.5;
  var f = AC.createBiquadFilter(); src.connect(f); f.connect(g);
  function env(a, d) { g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(a * v, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t + d); src.start(t, Math.random()); src.stop(t + d + 0.05); }
  if (kind === 'boom') {
    f.type = 'lowpass'; f.frequency.setValueAtTime(1400, t); f.frequency.exponentialRampToValueAtTime(90, t + 0.9); env(1.1, 1.3);
    var o = AC.createOscillator(), og = AC.createGain(); o.frequency.setValueAtTime(70, t); o.frequency.exponentialRampToValueAtTime(32, t + 0.6);
    og.gain.setValueAtTime(0.9 * v, t); og.gain.exponentialRampToValueAtTime(0.0001, t + 0.7); o.connect(og); og.connect(master); o.start(t); o.stop(t + 0.75);
  } else if (kind === 'crack') { f.type = 'bandpass'; f.frequency.value = 900 + Math.random() * 900; f.Q.value = 0.8; env(1.4, 0.35); }
  else if (kind === 'splash') { f.type = 'highpass'; f.frequency.setValueAtTime(400, t); f.frequency.exponentialRampToValueAtTime(2500, t + 0.5); env(0.6, 0.8); }
  else if (kind === 'blast') { f.type = 'lowpass'; f.frequency.setValueAtTime(2400, t); f.frequency.exponentialRampToValueAtTime(60, t + 1.8); env(1.6, 2.2); }
  else if (kind === 'thunder') { f.type = 'lowpass'; f.frequency.setValueAtTime(260, t); f.frequency.exponentialRampToValueAtTime(40, t + 3.2); env(1.5, 3.6); }   // 暴風雨的雷（08_weather.js）
  else if (kind === 'creak') { f.type = 'lowpass'; f.frequency.setValueAtTime(300, t); f.frequency.exponentialRampToValueAtTime(80, t + 2.5); env(1.2, 2.8); }
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/03_camera.js ──
// ───────────────────────── 鏡頭 ─────────────────────────
var CAM = { yaw: 2.2, pitch: 0.24, dist: 175, tgt: [0, 6, 0], eye: [0, 0, 0], vp: null, inv: null, mode: 4, follow: null, hold: 0, w: 1, h: 1, track: true, aoff: 0 };
var CAM_NAMES = ['自由鏡頭', '追砲彈', '看敵艦', '看我艦', '我艦→敵艦'];
var CAM_ORDER = [4, 0, 1, 2, 3];                 // C 鍵循環的順序：我艦→敵艦（預設）→ 自由 → 追砲彈 → 看敵艦 → 看我艦
function camUpdate(dt) {
  // 我艦→敵艦（預設，mode 4）：注視點 ＝ 我艦中心（略高），鏡頭在我艦背對敵艦的那一側 ⇒ 畫面中間是我艦、敵艦在它後方；
  // 兩艘繞著彼此轉時鏡頭跟著轉。拖曳改的是相對這條視線的角度（aoff）與俯仰，滾輪改遠近。沒有敵艦 ⇒ 看船頭方向。
  if (CAM.mode === 4 && SHIPS.length) {
    var m4 = SHIPS[PLAYER_I], f4 = foeOf(m4), c4 = m4.center || shipCenter(m4), fc = f4 && (f4.center || shipCenter(f4));
    var a4 = fc && Math.hypot(fc[0] - c4[0], fc[2] - c4[2]) > 1 ? Math.atan2(fc[2] - c4[2], fc[0] - c4[0]) : Math.atan2(-Math.sin(m4.yaw), Math.cos(m4.yaw));
    var y4 = a4 + Math.PI + CAM.aoff, t4 = [c4[0], c4[1] + 4, c4[2]];
    var e4 = [t4[0] + Math.cos(y4) * Math.cos(CAM.pitch) * CAM.dist, t4[1] + Math.sin(CAM.pitch) * CAM.dist, t4[2] + Math.sin(y4) * Math.cos(CAM.pitch) * CAM.dist];
    var e4s = seaH(e4[0], e4[2], SIMT) + 1.5; if (e4[1] < e4s) e4[1] = e4s;          // 鏡頭不鑽到浪底下
    var k4 = CAM.snap ? 1 : 1 - Math.exp(-dt * 4); CAM.snap = false;
    CAM.eye = lerp3(CAM.eye, e4, k4); CAM.look = lerp3(CAM.look || t4, t4, k4); CAM.trMe = CAM.trYaw = null;
    var pr4 = M4.persp(0.9, CAM.w / CAM.h, 0.5, 5000); CAM.vp = M4.mul(pr4, M4.lookAt(CAM.eye, CAM.look, [0, 1, 0])); CAM.inv = M4.inv(CAM.vp);
    return;
  }
  // 鏡頭跟船（預設；V 關掉 ⇒ 固定在世界上）：跟著那艘移動、旋轉 —— 拖曳改的是相對船頭的角度、偏移與遠近。
  // 自由鏡頭的注視點照我艦平移＋繞我艦中心轉；鏡頭角度跟著被看的那艘轉（看敵艦 ⇒ 敵艦，其他 ⇒ 我艦）。
  // ⛔ 跟兩艘的中點：兩艘繞著中點轉圈 ⇒ 中點幾乎不動，看起來像沒在跟。
  // 角度慣例：鏡頭 yaw 是 (x, z) 平面上 atan2(z, x)；船頭方向的這個角 ＝ −sh.yaw ⇒ 船 yaw 增 Δ，鏡頭 yaw 減 Δ。
  if (SHIPS.length >= 2 && CAM.track) {
    var me = SHIPS[PLAYER_I], mc = me.center || shipCenter(me);
    if (CAM.trMe) {
      var d0 = -(me.yaw - CAM.trMe.yaw), c0 = Math.cos(d0), s0 = Math.sin(d0), ox = CAM.tgt[0] - CAM.trMe.c[0], oz = CAM.tgt[2] - CAM.trMe.c[2];
      CAM.tgt[0] = mc[0] + ox * c0 - oz * s0; CAM.tgt[2] = mc[2] + ox * s0 + oz * c0;
    }
    CAM.trMe = { yaw: me.yaw, c: mc.slice() };
    var ts = CAM.mode === 2 ? foeOf(me) || me : me;
    if (CAM.trYaw && CAM.trYaw.i === ts.i) CAM.yaw -= ts.yaw - CAM.trYaw.yaw;
    CAM.trYaw = { i: ts.i, yaw: ts.yaw };
  } else CAM.trMe = CAM.trYaw = null;
  var tgt = CAM.tgt, dist = CAM.dist, yaw = CAM.yaw, pitch = CAM.pitch, eye;
  if (CAM.mode === 1 && CAM.follow) {
    var b = CAM.follow, vd = norm(b.v);
    eye = add(sub(b.p, mul(vd, 9)), [0, 2.2, 0]); tgt = add(b.p, mul(vd, 25));
    CAM.eye = lerp3(CAM.eye, eye, 1 - Math.exp(-dt * 10)); CAM.look = lerp3(CAM.look || tgt, tgt, 1 - Math.exp(-dt * 10));
  } else {
    if (CAM.mode >= 1 && CAM.mode <= 3) { var sh = CAM.mode === 2 ? foeOf(SHIPS[PLAYER_I]) || SHIPS[PLAYER_I] : SHIPS[PLAYER_I]; if (sh) tgt = shipCenter(sh); }   // 追砲彈沒有在追的 ⇒ 跟看我艦一樣
    eye = [tgt[0] + Math.cos(yaw) * Math.cos(pitch) * dist, tgt[1] + Math.sin(pitch) * dist, tgt[2] + Math.sin(yaw) * Math.cos(pitch) * dist];
    var eys = seaH(eye[0], eye[2], SIMT) + 1.5; if (eye[1] < eys) eye[1] = eys;
    var k = CAM.snap ? 1 : 1 - Math.exp(-dt * 6); CAM.snap = false;
    CAM.eye = lerp3(CAM.eye, eye, k); CAM.look = lerp3(CAM.look || tgt, tgt, k);
  }
  var proj = M4.persp(0.9, CAM.w / CAM.h, 0.5, 5000), view = M4.lookAt(CAM.eye, CAM.look, [0, 1, 0]);
  CAM.vp = M4.mul(proj, view); CAM.inv = M4.inv(CAM.vp);
}
function lerp3(a, b, k) { return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k]; }
// 追砲彈（mode 1；Tim 2026-10-13）：只追我艦打的（觀戰也是）；追著的那顆打中或落水才換（落點停 1.2 秒，CAM.hold）。
//   挑下一顆的時機：這輪齊射打完（最新那顆飛了 BALL_SETTLE 秒）或最舊那顆飛了 BALL_WAIT 秒（連續開火時不等到天荒地老）；
//   挑哪顆：照現在的位置與速度往前推算（重力、打水漂同 stepBall；敵艦照現在的船速平移），會打中敵艦的優先、其中離命中最久的那顆；
//   都不中 ⇒ 只追剛開出去的（飛不到 BALL_FRESH 秒）；連這也沒有 ⇒ 落點停完就回去看我艦（CAM.follow ＝ null，鏡頭照看我艦平滑移過去），等下一輪
//   （⛔ 追一顆快落水的不中彈 ⇒ 看不到東西；⛔ 停在落點等 ⇒ 不開砲就一直看著水面，Tim 2026-10-13）。
//   每顆只推算一次（BALL_PRED；一次最多約 20 ms，⛔ 每一格重算會卡）。
//   ⛔ 以前每開一砲就切到新那顆 ⇒ 齊射時鏡頭一直跳、追的那顆還沒打中就換掉；觀戰還會追到敵艦的砲彈。
//   只在畫面這一層跑（frame），不抽 rnd()、不改狀態 ⇒ 戰局不受影響。
var BALL_SETTLE = 0.25, BALL_WAIT = 1.2, BALL_FRESH = 0.6, BALL_PRED = new WeakMap();
/** 砲彈 b 照現在的速度飛下去，幾秒後打中別艘（格或模型；開砲那艘以外最早打中的那艘）；不會中 ⇒ null。 */
function ballPredict(b) {
  var best = null;
  SHIPS.forEach(function (o) { if (o.i === b.owner) return; var t = ballPredictOn(b, o); if (t !== null && (best === null || t < best)) best = t; });
  return best;
}
function ballPredictOn(b, foe) {
  if (!foe || !foe.center || !foe.inv || foe.sunk) return null;
  var p = b.p.slice(), v = b.v.slice(), bounced = b.bounced, h = 1 / 1500, M = foe.inv, c = foe.center, fv = foe.vel || [0, 0, 0], g = foe.grid;
  for (var t = 0; t < 12 - b.age; t += h) {                            // 每步約 0.1 m（初速 175 m/s）
    v[1] -= G * h; p[0] += v[0] * h; p[1] += v[1] * h; p[2] += v[2] * h;
    var sea = seaH(p[0], p[2], SIMT + t);
    if (p[1] < sea) {
      var sp = len(v);
      if (b.ammo === 0 && !bounced && Math.asin(-v[1] / sp) < 0.11 && sp > 90) { v[1] = -v[1] * 0.45; v[0] *= 0.7; v[2] *= 0.7; p[1] = sea + 0.01; bounced = true; continue; }
      return null;
    }
    var x = p[0] - fv[0] * t, y = p[1], z = p[2] - fv[2] * t, dx = x - c[0], dy = y - c[1], dz = z - c[2];   // 換到敵艦「現在」的座標（它照船速平移）
    if (dx * dx + dy * dy + dz * dz > foe.rad2) continue;
    var L = [M[0] * x + M[4] * y + M[8] * z + M[12], M[1] * x + M[5] * y + M[9] * z + M[13], M[2] * x + M[6] * y + M[10] * z + M[14]];
    if (g.get(L[0] | 0, L[1] | 0, L[2] | 0) || hitModel(foe, L, b.ammo === 2 ? 10 : 1.5, null)) return t;
  }
  return null;
}
/** 每一格（frame）：追著的那顆沒了 ⇒ 落點停 CAM.hold 秒；之後挑下一顆，沒有就看我艦。debug：__game.camFollow(dt) 手動推進（預覽窗格在背景時 rAF 會停）。 */
function camFollow(dt) {
  if (CAM.mode !== 1) return;
  var f = CAM.follow;
  if (f && f.alive) return;                                            // 追著的那顆還在飛 ⇒ 不換
  if (f && CAM.hold > 0) { CAM.hold -= dt; return; }                   // 落點停一下（50_sim.js 在那顆沒了的時候設）
  CAM.follow = pickBall();                                             // 沒有值得追的 ⇒ null（回去看我艦）
}
/** 下一顆要追的砲彈（還不到挑的時候 ⇒ null）。 */
function pickBall() {
  var mine = BALLS.filter(function (b) { return b.alive && b.owner === PLAYER_I; });
  if (!mine.length) return null;
  var young = 1e9, old = 0; mine.forEach(function (b) { young = Math.min(young, b.age); old = Math.max(old, b.age); });
  if (young < BALL_SETTLE && old < BALL_WAIT) return null;             // 這輪齊射還在開
  var best = null, bt = -1, fresh = null;
  mine.forEach(function (b) {
    if (!BALL_PRED.has(b)) BALL_PRED.set(b, { at: b.age, t: ballPredict(b) });
    var pr = BALL_PRED.get(b), left = pr.t === null ? null : pr.t - (b.age - pr.at);   // 離命中還有幾秒
    if (left !== null && left > 0.05 && left > bt) { bt = left; best = b; }
    if (b.age < BALL_FRESH) fresh = b;
  });
  CAM.pick = { n: mine.length, hit: !!best, t: best ? +bt.toFixed(2) : null };   // 讀數（__game.camera）
  return best || fresh;
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/04_state.js ──
// ───────────────────────── 全域狀態與選單設定（網址參數、滑桿上下限、降旗規則、模式） ─────────────────────────
var QIDX = null;                                   // 四邊形索引（每種船共用）；船型的資料在 05_hull.js
var SHIPS = [], PIECES = [], BALLS = [], EVENTS = [], FLY = [], PLAYER_I = 0;
// 選單的滑桿：[下限, 上限, 預設]。網址參數與滑桿共用這一組（⛔ 各一組 ⇒ ?demo 跑的不是網址寫的那組）；讀不懂的值 ⇒ 預設
var LIM = { hard: [0.5, 20, 3], flood: [0, 2, 0.35], ballast: [0, 2000, 1075], gunw: [0, 5, 1], cas: [0.1, 1, 1], speed: [0.25, 3, 1], agile: [0.25, 3, 1], upwind: [0.5, 2, 1],
  // 細節設定頁：血量（砲／帆／船員／火藥桶）、每發傷害（砲種）、殉爆威力。火藥桶預設 675（很難殉爆但有機率；Tim 2026-10-12：450 還是很容易炸 ⇒ 1.5 倍），拉滿 1000 ＝ 不會爆
  gunhp: [20, 500, 200], sailhp: [20, 500, 100], crewhp: [20, 300, 100], powderhp: [20, 1000, 675], blast: [0.25, 4, 1], blastv: [0, 0.9, 0.4],   // blastv：每次爆炸的威力浮動 ±（Tim 2026-10-13：自爆太固定）
  dmg24: [10, 300, 100], dmg32l: [10, 300, 130], dmg32: [10, 300, 120], dmg18: [10, 300, 70], dmg4: [10, 300, 35],   // dmg32l：32 磅長砲（餘燼號）、dmg4：4 磅砲（夜隼號）
  box: [1, 8, 2], carry: [1, 6, 1], wind: [0.25, 3, 1],                                     // 補給：砲旁藥箱放幾份、送藥手一次搬幾份（Tim：可以一次存 n 發）
  hands: [0, 120, 40],                                                                        // 預備水手（每艘幾個人物；0 ＝ 沒有，42_hands.js）
  drown: [0, 120, 45],                                                                        // 溺水時間（秒；落水、被水淹過頭的人撐多久，43_swim.js；0 ＝ 照以前：落水當場算陣亡）
  sea: [0, 3, 1],                                                                             // 浪的大小（08_sea.js）：0 ＝ 平靜、1 ＝ 中浪（浪高約 1–2 m）、3 ＝ 大浪
  stall: [0, 1, 1],                                                                           // 頂風失速（31_sailing.js）：0 ＝ 頂風只是慢、1 ＝ 寫實
  funspeed: [1, 3, 1.4], funagile: [1, 3, 1.5], funstall: [0, 1, 0.4],                       // 娛樂加成：玩法選「娛樂」時再乘的倍率（寫實 ＝ 都是 1）
  funpowder: [0.1, 1, 2 / 3] };                                                               // 火藥血量：675 × 2/3 ＝ 450（Tim 2026-10-13 晚：「娛樂模式的彈藥庫血量要增加一些，憲法號很容易爆」；原本 4/9 ＝ 300）
function qnum(k, lim) { var v = parseFloat(Q.get(k)); return isFinite(v) ? clamp(v, lim[0], lim[1]) : lim[2]; }
// 玩法（Tim 2026-10-13：配置分成寫實與娛樂兩組，主選單切換，預設娛樂）：細節設定的滑桿 ＝ 寫實的基準，
//   娛樂 ＝ 在那之上再乘娛樂加成（航速、靈活性、頂風失速）。⇒ 兩組共用同一份滑桿，切換不會把調好的數字蓋掉。網址 ?play=real／fun
var PLAY = Q.get('play') === 'real' ? 'real' : 'fun';
var STALL_K = qnum('stall', LIM.stall);
var FUN = { speed: qnum('funspeed', LIM.funspeed), agile: qnum('funagile', LIM.funagile), stall: qnum('funstall', LIM.funstall), powder: qnum('funpowder', LIM.funpowder) };
function playK(k) { return PLAY === 'fun' ? FUN[k] : 1; }
// 船隻設定（照船型套；Tim 2026-10-12：不同船套用不同設定）：每一型一組，開戰時複製到每艘船（sh.cfg）。
//   hard  船殼硬度倍率（越硬越難打穿、洞越小；被打的那艘照自己的）：預設 3（Tim：原本 2 ⇒ 1.5 倍）
//   flood 進水速度倍率（0 ＝ 不會沉）
//   ballast 壓艙物（噸）：不會被打掉的重量；預設 ＝ 那一型「剛好在設計水線」（T.ballast0：憲法號 1,075），越輕浮得越高（減重上浮，32_hull.js）
//   gunw  砲的重量倍率（照實 ＝ 1：長砲 2.5 噸、carronade 0.9、追擊砲 2.1）：越重 ⇒ 吃水越深、砲被打飛浮得越多
//   speed 航速倍率（乘在 VMAX 上）；agile 靈活性倍率（乘在最大轉向率上；跟航速倍率分開 —— 轉向率用的是除掉倍率的航速）。玩法選娛樂 ⇒ 兩個再乘娛樂加成（playK）
//   upwind 逆風性能（31_sailing.js）：風從船頭那一半（迎風、頂風）的角度照它壓縮 ⇒ 同一個角度跑得快、吃風更近（失速晚開始）、越接近頂風轉得越快（最多 ×它）；1 ＝ 照舊
// 起始值 ＝ 網址參數（?hard= …，套到每一型）或 LIM 的預設；壓艙物網址沒給 ⇒ 存檔裡那一型的（同一份船才算，69_prefs.js）⇒ 那一型的 ballast0（船型載好才知道）。
var SHIP_KEYS = ['hard', 'flood', 'ballast', 'gunw', 'speed', 'agile', 'upwind'], SHIP_CFG = {};
// 船型自己的預設（沒列的 ＝ LIM 的預設）。Tim 2026-10-13：憲法號要比餘燼號快、靈活 ⇒ 憲法號照舊 1（巡防艦），
//   餘燼號是兩層砲甲板、90 門砲的重船 ⇒ 航速 0.85、靈活 0.7。網址參數（?speed= …）照舊套到每一型。
//   夜隼號（Tim 2026-10-13：「速度更快、更靈活，彌補火力劣勢」「加強逆風航速與轉彎，彌補火力跟防禦不足」「材質硬度兩倍試試」）：
//   12 門 4 磅砲的雙桅小船（brigantine：主桅縱帆，吃風比全橫帆的船近）⇒ 航速 1.2、靈活 1.6、逆風 1.25、硬度 6（預設 3 的兩倍）。
var HULL_CFG0 = { ember: { speed: 0.85, agile: 0.7 }, falcon: { speed: 1.2, agile: 1.6, upwind: 1.25, hard: 6 } };
function cfgBase(k, id) { var d = HULL_CFG0[id]; return d && d[k] !== undefined ? d[k] : LIM[k][2]; }
var PREF_BALLAST = {};                                   // 存檔裡的壓艙物：id → { v: 噸, chk: 存的時候那艘船的 checksum }（船重匯過 ⇒ 不套）
function cfgDefault(k, T, id) {
  if (k !== 'ballast') return Q.has(k) ? qnum(k, LIM[k]) : cfgBase(k, id);
  if (Q.has('ballast')) return Math.round(qnum('ballast', LIM.ballast));
  var pb = T && PREF_BALLAST[T.id];
  if (pb && pb.chk === T.h.checksum) return pb.v;
  return T && isFinite(T.ballast0) ? T.ballast0 : LIM.ballast[2];
}
/** 那一型的設定（第一次用到才建；壓艙物等船型載好才填）。 */
function shipCfg(id) {
  var c = SHIP_CFG[id];
  if (!c) { c = SHIP_CFG[id] = {}; SHIP_KEYS.forEach(function (k) { if (k !== 'ballast') c[k] = cfgDefault(k, null, id); }); }
  if (c.ballast === undefined && HULLT[id]) c.ballast = cfgDefault('ballast', HULLT[id]);
  return c;
}
function cfgCopy(id) { var c = shipCfg(id), o = {}; SHIP_KEYS.forEach(function (k) { o[k] = c[k]; }); return o; }
var GUN_HP = Math.round(qnum('gunhp', LIM.gunhp));          // 砲的血量（舵輪 6 成）：預設 200 ⇒ 24 磅實心兩發（Tim 2026-10-12：100 太脆，翻倍）
var SAIL_HP = Math.round(qnum('sailhp', LIM.sailhp));       // 帆的血量
var CREW_HP = Math.round(qnum('crewhp', LIM.crewhp));       // 船員的血量：歸零陣亡、掉到一半以下受傷倒下、一半以上照常作戰（只閃紅）
var POWDER_HP = Math.round(qnum('powderhp', LIM.powderhp)); // 火藥桶的血量：歸零殉爆；拉滿（LIM 上限）＝ 不會爆；預設 675 ＝ 很難但有機率
var BLAST_K = qnum('blast', LIM.blast);                             // 殉爆威力倍率（能量；爆炸半徑 ∝ 立方根）
var BLAST_V = qnum('blastv', LIM.blastv);                           // 每一次爆炸（火藥桶、彈藥庫、藥包）的威力再乘 1 ± 這個數之間的亂數（23_powder.js blastRoll）
var BOX_N = Math.round(qnum('box', LIM.box)), CARRY_N = Math.round(qnum('carry', LIM.carry));   // 砲旁藥箱容量、送藥手一次搬幾份（火藥與彈藥一份 ＝ 裝填一次）
var HANDS = Math.round(qnum('hands', LIM.hands));                  // 預備水手：缺人手時補位（42_hands.js）
var DROWN_T = Math.round(qnum('drown', LIM.drown));                // 落水求生：浮上水面、往自己的船游，撐這麼久（× 0.6～1.2）就溺水（43_swim.js）
var SEA_K = qnum('sea', LIM.sea);                                   // 浪的大小（08_sea.js；物理與畫面共用）
var WIND_K = qnum('wind', LIM.wind);                                // 帆的風壓倍率（只管物理開著時帆被吹成什麼樣子；不改航速）
function powderNever() { return POWDER_HP >= LIM.powderhp[1]; }      // 拉滿 ＝ 不會爆：兩種玩法都是（娛樂的倍率不管它）
function powderHP() { return Math.round(POWDER_HP * playK('powder')); }   // 實際的火藥血量：娛樂再乘 FUN.powder（預設 675 ⇒ 300）
// 每發傷害（砲種）：砲彈開火時帶著 b.dmg
var DMG = { long: Math.round(qnum('dmg24', LIM.dmg24)), long32: Math.round(qnum('dmg32l', LIM.dmg32l)), carr: Math.round(qnum('dmg32', LIM.dmg32)), chase: Math.round(qnum('dmg18', LIM.dmg18)), long4: Math.round(qnum('dmg4', LIM.dmg4)) };
// 彈種倍率（%）：列 ＝ 實心／爆裂／鏈彈，欄 ＝ 對砲（模型：砲、舵輪、火藥桶）／對帆／對人。網址 ?ammo= 九個數字（照列）
var AMMO_LIM = [0, 400], AMMO_K0 = [[100, 10, 100], [160, 10, 100], [50, 100, 100]];   // 爆裂對人原訂 115：量過死亡平均 42（舊版 27）⇒ 100（35，傷亡合計 62 對舊版 65）
var AMMO_K = AMMO_K0.map(function (r) { return r.slice(); });
if (Q.has('ammo')) Q.get('ammo').split(',').forEach(function (w, i) { var v = parseFloat(w); if (i < 9 && isFinite(v)) AMMO_K[(i / 3) | 0][i % 3] = clamp(Math.round(v), AMMO_LIM[0], AMMO_LIM[1]); });
var VS_GUN = 0, VS_SAIL = 1, VS_CREW = 2;
function ammoK(ammo, vs) { return AMMO_K[ammo][vs] / 100; }
// 降旗規則（選單設定）：死傷比例到 cas 就降旗（1 ＝ 全員倒下才停）；三個勾選各自是另一條。預設 ＝ 不降旗，打到沉或全員倒下。
// 網址：?strike=60,guns,masts,officers（數字是死傷百分比，後面列出要勾的規則）
var STRIKE = { cas: LIM.cas[2], guns: false, masts: false, officers: false };
if (Q.has('strike')) Q.get('strike').split(',').forEach(function (w) {
  var v = parseFloat(w);
  if (isFinite(v)) STRIKE.cas = clamp(v / 100, LIM.cas[0], LIM.cas[1]);
  else if (w === 'guns' || w === 'masts' || w === 'officers') STRIKE[w] = true;
});
// 砲長（51_captain.js）：[我艦, 敵艦]，random ＝ 開局抽；網址 ?cap=sink,mast
var CAP_SET = ['random', 'random'];
if (Q.has('cap')) Q.get('cap').split(',').forEach(function (w, i) { if (i < 2) CAP_SET[i] = w; });
var LAST_MODE = null;                                // 上一場的模式（自動開砲換了模式才套預設，見 reset）
var MODE = 'pve', DIST = 140, SIMT = 0, RUNNING = false, PAUSED = false, OVER = false, AMMO_I = 0;
var SAIL = Q.get('sail') === 'off' ? 'off' : Q.get('sail') === 'manual' ? 'manual' : 'auto';   // 航行：auto ＝ 兩艘自動（預設）、manual ＝ 我艦手動、off ＝ 停船
var KEYS = { l: false, r: false };                    // 手動操舵：按住的舵鍵
// 殉爆的慢動作與特寫（73_slowmo.js）：on／cam 是設定；ts 現在的時間倍率。SLOW_VIS：這一格畫面裡只給人看的效果改由 frame 走（step() 讀它決定要不要跳過）
var SLOW = { on: Q.get('slowmo') !== '0', cam: Q.get('slowcam') !== '0', ts: 1, t: 0, min: 1, hold: 0, active: false, camSave: null, camT: 0, camMode: 0, kicks: 0 }, SLOW_VIS = false;
var AUTOFIRE = false;                                  // 自動開砲：電腦替我艦瞄準、開火（觀戰 ＝ 一般戰鬥＋自動開砲預設開；G 切換）
var PHYS = Q.get('phys') !== '0';                      // 帆與繩的物理（選單勾選、B 鍵、下方按鈕；?phys=0 關）：關 ＝ 靜態，跟以前一樣
// ── D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m/design/game_fixture/05_hull_fixture.js ──
// ───────────────────────── 船型（一種船一份；兩艘同型就共用） ─────────────────────────
// 船型 T：內嵌的 .vxk（<script type="application/x-vxk" id="…">）解碼之後的一切 —— 格子（T.base）、合併過的網格（T.pristine）、
//   繩與帆與模型（T.rig）、模型的網格（T.meshes）、桅（T.masts）、帆的布模板（T.cloth）、水線（T.wl0／wl1／bowHalf）、
//   海面遮罩（T.hullHB）、浮力表（T.hyd／disp），以及從 header 來的中線、外框、設計水線（T.cx／cy／hx0／hx1／zw／sz）。
// 每艘船 sh.T 指向它的船型；⛔ 船型是共用的、不能改（被打掉的格子在 sh.grid：Grid.share 寫的時候才複製那一塊）。
// 只在被選到時才解碼（Tim 2026-10-12：預設只載憲法號，其他船選了才載）—— 資料本身還是內嵌在同一個 HTML 裡
//   （畫廊的 iframe 只開 allow-scripts、讀不了旁邊的檔，展品也要零外部依賴），省的是解碼與網格化的時間和記憶體。
// 公尺／格（S）每種船都要一樣（模擬裡的距離、速度、碰撞都用同一個 S）；不一樣就不載、說為什麼。
// 認得的船（el ＝ 內嵌 .vxk 的 id）；選單只列 HTML 裡真的有內嵌資料的那幾艘 ⇒ 加一艘 ＝ template 加一個 x-vxk 標籤＋這裡一行。
// zw0：作品沒有 `kind=ship, waterline_z` 的 meta 時用的設計水線（格的 z）。餘燼號 71 ＝ basecamp 的作品筆記（basecamp-ember-01m/todo.md「水線抬高 z 63 → 71」，
//   Tim：船變高了水線也往上）。⛔ 沒有這一格 ⇒ 用憲法號的 63，多出來那層砲甲板的排水沒算進去（排水量 2,522 噸，跟憲法號 2,154 差不多 —— Tim 2026-10-13 發現）。meta 補上之後以 meta 為準。
// geo：船型的高度（格的 z）與範圍 —— 這些本來寫死成憲法號的數字；沒給的照 GEO0（＝ 原本的數字 ⇒ 憲法號、餘燼號照舊）。
//   夜隼號（summit，2026-10-13 接）只有憲法號一半高：水線 15、主甲板 z 30、後甲板 45、桅頂平台 126（前）／136（主）、桅頂 272 ⇒ 照她的作品量的。
//   桅不在這裡：照帆桁的 meta 判斷（10_ship.js findMasts）。
var GEO0 = {
  spar: null,              // 露天甲板站人的高度 [z0, z1]（陸戰隊、軍官、舵手）；null ⇒ 照 carronade 推、沒有 carronade ⇒ 100–109
  marines: [160, 220],     // 陸戰隊沿舷牆站的範圍：船尾外框 + [0] 到船頭外框 − [1]（每 37 格一個，最多 12）
  center: 140,             // 船的中心高度（鏡頭看哪裡）
  aim: 90,                 // 沒有目標時瞄哪個高度（21_gunnery.js）
  aimZ: [40, 320],         // 瞄準點的高度夾在這段裡
  deckAim: [84, 104],      // 砲長「砲甲板」模式瞄的高度（51_captain.js）
  rigAim: [150, 300],      // 砲長「桅」模式瞄的高度
  handsK: 1                // 預備水手的人數倍率（細節設定的人數 × 這個）
};
var GEO_FALCON = { spar: [28, 47], marines: [100, 60], center: 50, aim: 30, aimZ: [5, 270], deckAim: [25, 40], rigAim: [60, 240], handsK: 0.25 };
var HULL_KNOWN = [{ id: 'constitution', el: 'ship', name: '潮墓號', geo: { spar:[114,140], marines:[180,215], center:155, aim:90, aimZ:[30,480], deckAim:[74,106], rigAim:[210,410], handsK:1 } }, { id: 'ember', el: 'ship-ember', name: '餘燼號', zw0: 71 },
  { id: 'falcon', el: 'ship-falcon', name: '夜隼號', geo: GEO_FALCON }];
var HULL_LIST = HULL_KNOWN.filter(function (h) { return !!document.getElementById(h.el); });
var HULLS = {}, HULLT = {};                                             // id → 載入中的 Promise ／ 載好的船型
// 艦隊編成（TASK-0537）：FLEET_SET[0] ＝ 我方（第一艘是我艦）、[1] ＝ 敵方，各是一串船型；每一邊至少 1 艘、合計最多 MAX_SHIPS。
//   主選單編；網址 ?blue=我艦,友艦…&red=敵艦,…；舊的 ?ship=我艦,敵艦 照舊（＝ 一邊一艘；?blue／?red 給了那一邊照它）。
var FLEET_SET = [['constitution'], ['constitution']];
if (Q.has('ship')) Q.get('ship').split(',').forEach(function (w, i) { if (i < 2 && hullInfo(w)) FLEET_SET[i] = [w]; });
['blue', 'red'].forEach(function (k, i) { if (!Q.has(k)) return; var L = Q.get(k).split(',').filter(hullInfo); if (L.length) FLEET_SET[i] = L; });
fleetTrim(FLEET_SET);
/** 合計超過 MAX_SHIPS ⇒ 從艘數多的那一邊的尾巴拿掉（一樣多 ⇒ 敵方先拿）；每一邊至少留 1 艘。 */
function fleetTrim(F) { while (F[0].length + F[1].length > MAX_SHIPS) { var s = F[0].length > F[1].length ? 0 : 1; if (F[s].length <= 1) break; F[s].pop(); } return F; }
/** 編成裡用到的船型（不重複；我艦那一型第一個）。 */
function fleetHulls() { return FLEET_SET[0].concat(FLEET_SET[1]).filter(function (id, i, a) { return a.indexOf(id) === i; }); }
function myHull() { return FLEET_SET[0][0]; }
function hullInfo(id) { return HULL_LIST.filter(function (h) { return h.id === id; })[0] || null; }
/** 船型（解碼、網格化一次，之後都拿同一份）。分成幾步、每步之間讓出一次（Tim 2026-10-12：進到主選單之後才解析，解析完之前不能開戰、但可以調設定）；
 *  每一步開始時呼叫 hullSay（主選單的開戰鈕寫進度）。 */
function loadHull(id) {
  if (HULLS[id]) return HULLS[id];
  var info = hullInfo(id);
  if (!info) return Promise.reject(new Error('沒有這艘船：' + id));
  var t0 = performance.now();
  hullSay(info.name + '：解碼…');
  return (HULLS[id] = yieldUI().then(function () { return Promise.all([VK.loadEmbedded(info.el), cacheGet(info)]); })   // 解碼與讀快取一起跑（06_cache.js）
    .then(function (r) { return buildHull(info, r[0], t0, r[1]); })
    .then(function (T) { HULLT[id] = T; cachePut(T, info); return T; }));
}
/** 讓出一次（MessageChannel：一個新的工作 ⇒ 瀏覽器可以先畫一格、處理點擊）。⛔ 不用 setTimeout：分頁在背景時會被壓到一秒一次。 */
function yieldUI() { return new Promise(function (r) { var ch = new MessageChannel(); ch.port1.onmessage = function () { r(); }; ch.port2.postMessage(0); }); }
var hullSay = function () {};                                            // 90_main.js 換成寫進度的那支
/** C：快取的記錄（06_cache.js；null ⇒ 全部現場算）。現場算的時候，要存的那幾份另外留在 T.keep，給 cachePut 存。 */
function buildHull(info, model, t0, C) {
  var h = model.header, t1 = performance.now();                            // 到這裡是解碼（loadEmbedded，跟讀快取一起），之後是網格化
  if (C && (C.voxels !== h.voxels || C.checksum !== h.checksum)) C = null;  // 雙保險：鍵是 .vxk 原文的雜湊，格數與 checksum 也要一樣
  if (S && Math.abs(h.meters_per_voxel - S) > 1e-9) throw new Error(info.name + ' 是 ' + h.meters_per_voxel + ' 公尺一格，跟已經載入的船（' + S + '）不一樣 —— 模擬只吃同一個比例');
  S = h.meters_per_voxel;
  var T = { id: info.id, name: info.name, model: model, h: h, rig: h.rig || { ropes: [], sails: [] },
    sz: h.size[2], cx: (h.bbox[0] + h.bbox[3]) / 2, cy: h.size[1] / 2, hx0: h.bbox[0], hx1: h.bbox[3], zw: hullZW(h, info), geo: Object.assign({}, GEO0, info.geo) };   // 外框：含艏斜桅與後桅帆桁
  T.cached = !!C; T.keep = C ? null : {};
  T.ms = {};                                                               // 每一段花多久（毫秒；讀數 window.__vxk.ms）
  function tm(k, f) { var a = performance.now(); f(); T.ms[k] = +(performance.now() - a).toFixed(1); }
  var steps = [
    ['格子', function () { tm('grid', function () { T.base = VK.Grid.fromModel(model); }); tm('verify', function () { T.chk = VK.verify(T.base, h); }); }],   // 格子不存快取：照解出來的比 checksum
    ['模型網格', function () { tm('meshes', function () { buildMeshes(T, C && C.models); }); }],
    ['水線與浮力', function () {
      tm('waterline', function () { waterline(T); }); tm('hullTex', function () { hullTex(T, C && C.hb); }); tm('navImg', function () { navImg(T); });
      tm('hydro', function () { if (C) { T.hyd = C.hyd; T.disp = C.disp; } else hydrostatics(T); });
    }],
    ['船體網格', function () { tm('pristine', function () { T.pristine = new VK.RegionSet(gl, T.base, QIDX); if (C) meshesFromCache(T.pristine, C.mesh); else T.pristine.buildAll(); }); }],
    ['桅與帆', function () {
      tm('masts', function () { findMasts(T); }); tm('cloth', function () { clothSetup(T, C); });
      var mt = 12 * KEG_T; (T.rig.models || []).forEach(function (m) { mt += modelT({ kind: modelKind(m) }, 1); });   // 模型的重量（砲照實、取用點 12 桶）
      T.ballast0 = Math.max(0, Math.round((T.disp - T.base.count * VOX_T - mt) / 25) * 25);   // 剛好浮在設計水線的壓艙物（滑桿一格 25 噸）
    }]
  ];
  var p = Promise.resolve();
  steps.forEach(function (s, i) { p = p.then(function () { hullSay(info.name + '：' + s[0] + '（' + (i + 1) + '／' + steps.length + '）…'); return yieldUI(); }).then(s[1]); });
  return p.then(function () { T.decodeMs = t1 - t0; T.meshMs = performance.now() - t1; return T; });
}
/** 羅盤中間的船（Tim 2026-10-13：藍色箭頭換成從上面俯瞰的船，載入時算一次、解析度可以低）：
 *  每 NAV_CELL × NAV_CELL 格取最高那一格的顏色（照高度提亮一點 ⇒ 桅頂、甲板、舷牆分得開），裁到有東西的範圍。
 *  畫布：船頭朝上、右舷（格 +y）在右 ⇒ 羅盤只要轉、不用翻。原始格子（沒有砲、帆桁這些模型；開戰後被打掉的也不跟）。 */
var NAV_CELL = 4;
function navImg(T) {
  var G = T.base, C = NAV_CELL, W = Math.ceil(G.sy / C), H = Math.ceil(G.sx / C), top = new Int16Array(W * H).fill(-1), col = new Uint8Array(W * H);
  G.each(function (x, y, z, c) { var i = ((H - 1 - ((x / C) | 0)) * W) + ((y / C) | 0); if (z > top[i]) { top[i] = z; col[i] = c; } });
  var x0 = W, x1 = -1, y0 = H, y1 = -1, i, u, v;
  for (v = 0; v < H; v++) for (u = 0; u < W; u++) if (top[v * W + u] >= 0) { if (u < x0) x0 = u; if (u > x1) x1 = u; if (v < y0) y0 = v; if (v > y1) y1 = v; }
  if (x1 < 0) return;
  var cv = document.createElement('canvas'); cv.width = x1 - x0 + 1; cv.height = y1 - y0 + 1;
  var g = cv.getContext('2d'), im = g.createImageData(cv.width, cv.height), d = im.data;
  for (v = y0; v <= y1; v++) for (u = x0; u <= x1; u++) {
    i = v * W + u; var o = ((v - y0) * cv.width + (u - x0)) * 4; if (top[i] < 0) continue;
    var c = col[i], k = 0.62 + 0.38 * clamp((top[i] - T.zw) / 80, 0, 1);
    d[o] = ((c >> 5) & 7) * 255 / 7 * k; d[o + 1] = ((c >> 2) & 7) * 255 / 7 * k; d[o + 2] = (c & 3) * 255 / 3 * k; d[o + 3] = 255;
  }
  g.putImageData(im, 0, 0);
  T.navImg = cv; T.navU = ((T.cy / C) | 0) - x0 + 0.5; T.navV = (H - 1 - ((T.cx / C) | 0)) - y0 + 0.5;   // 船的中心（格的 cx, cy）在圖上的位置 ⇒ 羅盤照它對準圓心
}
/** 設計水線（格的 z）：組裝件或關聯的 meta `kind=ship, waterline_z`（跟 basecamp 提議中）；沒有 ⇒ ZW0（憲法號 63）。 */
function hullZW(h, info) {
  var p = (h.parts || []).filter(function (q) { return q.meta && q.meta.kind === 'ship'; })[0], m = (p && p.meta) || h.meta || {};
  return isFinite(+m.waterline_z) && +m.waterline_z > 0 ? +m.waterline_z : info && info.zw0 ? info.zw0 : ZW0;   // meta ＞ 船型清單的 zw0 ＞ 63
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/06_cache.js ──
// ───────────────────────── 船型快取（IndexedDB；Tim 2026-10-13：緩存船隻解析結果，加速下次啟動） ─────────────────────────
// 存的是載入時算一次、之後不改的東西：船體網格（每個區塊的四邊形）、模型網格（三角形＋佔用格）、海面遮罩、浮力表、帆的布模板。
//   格子本身不存：解碼很快（憲法號約 70 ms），而且 checksum 要照解出來的格子比（VK.verify）。
//   GPU 那一半（上傳、VAO）每次照樣做，只省 CPU 算的那一半。量過（2026-10-13，PC）：船體網格 CPU 240 ms，讀回同一份 6.8 MB 約 19 ms。
// 一型一筆（鍵 ＝ 船的 id）；兩艘同型共用那一筆。
// 失效：那筆記錄的 vxk（內嵌 .vxk 原文的雜湊：basecamp 每次重匯都會變，繩／帆／模型改了也會變）、code（頁面裡 JS 原文的雜湊：
//   產生網格的程式改了也要清）、fmt（快取格式）任何一個對不上 ⇒ 不用、現場解析完蓋掉它。
// 存不了（畫廊彈窗的 iframe 只開 allow-scripts：不透明來源，一碰 indexedDB 就丟錯；無痕模式；配額滿）⇒ 照常現場解析，不壞。
// ?cache=0 ⇒ 不讀也不寫（量現場解析的時間用）。
var CACHE_DB = 'ame_constitution_broadside', CACHE_FMT = 1, CACHE_ON = Q.get('cache') !== '0';
/** FNV-1a 32 位元（字串照 UTF-16 碼位）。 */
function fnv(s) { var h = 0x811c9dc5; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
// 程式版本 ＝ 頁面上所有內嵌 JS 的原文（VoxelKit ＋ 遊戲本體）：改了任何一行都會換 ⇒ 寧可多清，不拿舊程式算的網格
var CODE_VER = fnv([].map.call(document.scripts, function (el) { return !el.type || /javascript/i.test(el.type) ? el.textContent : ''; }).join('\n'));
var cacheDB = null;
/** 開資料庫 ⇒ Promise<IDBDatabase|null>（開不了 ⇒ null；1.5 秒沒回也當開不了）。 */
function cacheOpen() {
  if (cacheDB) return cacheDB;
  return (cacheDB = new Promise(function (res) {
    var done = false; function ok(v) { if (!done) { done = true; res(v); } }
    setTimeout(function () { ok(null); }, 1500);
    try {
      var q = indexedDB.open(CACHE_DB, 1);
      q.onupgradeneeded = function () { q.result.createObjectStore('hull'); };
      q.onsuccess = function () { ok(q.result); };
      q.onerror = q.onblocked = function () { ok(null); };
    } catch (e) { ok(null); }
  }));
}
/** 那艘船的快取 ⇒ Promise<記錄|null>（從不 reject）。info.cache 留讀數：key、讀了多久、為什麼沒用。 */
function cacheGet(info) {
  var el = document.getElementById(info.el), st = info.cache = { vxk: fnv(el ? el.textContent : ''), code: CODE_VER, hit: false, why: '' };
  if (!CACHE_ON) { st.why = '?cache=0'; return Promise.resolve(null); }
  var t0 = performance.now();
  return cacheOpen().then(function (db) {
    if (!db) { st.why = '存不了（這個頁面不能用 IndexedDB）'; return null; }
    return new Promise(function (res) {
      try {
        var q = db.transaction('hull').objectStore('hull').get(info.id);
        q.onsuccess = function () {
          var r = q.result; st.readMs = performance.now() - t0;
          if (!r) st.why = '還沒有快取';
          else if (r.fmt !== CACHE_FMT || r.vxk !== st.vxk || r.code !== st.code) st.why = '快取過期（' + [r.fmt !== CACHE_FMT && '格式', r.vxk !== st.vxk && '船', r.code !== st.code && '程式'].filter(Boolean).join('、') + '換了）';
          else { st.hit = true; res(r); return; }
          res(null);
        };
        q.onerror = function () { st.why = '讀不了'; res(null); };
      } catch (e) { st.why = '讀不了'; res(null); }
    });
  });
}
/** 現場解析完的船型 ⇒ 存一筆（蓋掉舊的）。在背景做，失敗只記讀數。 */
function cachePut(T, info) {
  var st = info.cache;
  if (!CACHE_ON || st.hit || !T.keep) return;
  var g = T.base, ms = T.pristine.meshes, idx = [], n = 0;
  ms.forEach(function (m, i) { if (m) { idx.push(i, m.length); n += m.length; } });
  var all = new Uint16Array(n), o = 0;
  for (var k = 0; k < idx.length; k += 2) { all.set(ms.get(idx[k]), o); o += idx[k + 1]; }
  var rec = { fmt: CACHE_FMT, vxk: st.vxk, code: st.code, voxels: T.h.voxels, checksum: T.h.checksum, at: Date.now(), nx: g.nx, ny: g.ny,
    mesh: { all: all, idx: new Int32Array(idx) }, models: T.keep.models, hb: T.hullHB, hyd: T.hyd, disp: T.disp, rbox: T.rbox, cloth: T.cloth };
  T.keep = null;
  cacheOpen().then(function (db) {
    if (!db) return;
    try {
      var t0 = performance.now(), tx = db.transaction('hull', 'readwrite');
      tx.objectStore('hull').put(rec, info.id);
      tx.oncomplete = function () { st.saved = true; st.saveMs = performance.now() - t0; };
      tx.onerror = tx.onabort = function () { st.saved = false; st.why = '存不了：' + (tx.error && tx.error.name || '?'); };
    } catch (e) { st.saved = false; st.why = '存不了：' + (e && e.name || e); }
  });
}
/** 快取的船體網格 ⇒ RegionSet（跟 buildAll 同一份結果：每個區塊的四邊形，之後照樣 flush 上傳）。 */
function meshesFromCache(rs, M) {
  var g = rs.grid, o = 0;
  for (var k = 0; k < M.idx.length; k += 2) {
    var i = M.idx[k], n = M.idx[k + 1];
    rs.meshes.set(i, M.all.subarray(o, o + n)); o += n;
    rs.dirtyRegions.add(rs.rkey(i % g.nx, Math.floor(i / g.nx) % g.ny, Math.floor(i / (g.nx * g.ny))));
  }
  rs.flush();
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/07_gfx.js ──
// ───────────────────────── 畫質（TASK-0522） ─────────────────────────
// 主選單：低／中／高（GFX_PRESET）；畫質設定頁可以一項一項調，跟三檔都對不上 ⇒ 主選單顯示「自訂」。
// ⛔ 只改畫面：這裡的值一個都不能被 step() 讀到（反向對照：同一個種子，低與高跑同樣秒數，戰局讀數逐項相同）。
//   浪的大小（SEA_K）是物理，在細節設定；這裡的「海面細緻度」只是網格多密、漣漪幾道。
// 每一項怎麼畫在 60_render.js（管線：陰影圖 → 反射 → 場景 → 折射 → 海 → 粒子 → 縮放貼到畫布）。
// 網址：?gfx=low|mid|high（縮圖、對拍用），單項 ?g_shadow= ?g_refl= ?g_refr= ?g_sea= ?g_res= ?g_aa= ?g_rain= ?g_drops= ?g_dropspl=（數字 ＝ 第幾檔，從 0 起）。
// 雨有兩種、各自一項：「雨」＝ 整個畫面一層的雨絲（01_gl.js P.rain）；「雨滴（3D）」＝ 3D 空間裡的雨絲粒子（14_rain.js）。高 ＝ 只開 3D（Tim 2026-10-13）；自訂可以兩種一起開。3D 雨滴打在海面與船上的水花另外一項（雨滴水花，Tim：要能開關）。
var GFX_ITEMS = [
  { k: 'shadow', name: '陰影', opt: ['關', '低（1024）', '高（2048、柔邊）'] },
  { k: 'refl', name: '海面反射', opt: ['關（只反射天空）', '低（船身，1/4 解析度）', '高（船身＋砲與帆，1/2 解析度）'] },
  { k: 'refr', name: '海水折射', opt: ['關（不透明）', '低（半透明）', '高（折射＋水深）'] },
  { k: 'sea', name: '海面細緻度', opt: ['低', '中', '高'] },
  { k: 'res', name: '解析度', opt: ['50%', '75%', '100%'] },
  { k: 'aa', name: '反鋸齒', opt: ['關', '開（MSAA 4×）'] },
  { k: 'rain', name: '雨', opt: ['關', '低（稀）', '高（密）'] },     // 只在暴風雨下（08_weather.js）：整個畫面一層
  { k: 'drops', name: '雨滴（3D）', opt: ['關', '少（1500）', '中（3000）', '多（6000）'] },   // 只在暴風雨下：3D 空間裡的雨絲粒子（14_rain.js）
  { k: 'dropspl', name: '雨滴水花', opt: ['關', '開'] }];                                   // 3D 雨滴打在海面與船上濺起的小水花
var GFX_PRESET = {
  low: { shadow: 0, refl: 0, refr: 0, sea: 0, res: 1, aa: 0, rain: 0, drops: 0, dropspl: 0 },
  mid: { shadow: 1, refl: 1, refr: 1, sea: 1, res: 2, aa: 1, rain: 1, drops: 0, dropspl: 0 },
  high: { shadow: 2, refl: 2, refr: 2, sea: 2, res: 2, aa: 1, rain: 0, drops: 3, dropspl: 1 } };
var GFX_NAME = { low: '低', mid: '中', high: '高', custom: '自訂' }, GFX_DEFAULT = 'mid';
var GFX = {}, GFX_FPS = false;                     // GFX_FPS：畫面右上角顯示 FPS（畫質設定頁的勾選）
var GFX_RES = [0.5, 0.75, 1];                      // 解析度：乘在畫布的像素上（畫布 ＝ 螢幕像素，裝置像素比最多 1.5）
function gfxSet(level) { var p = GFX_PRESET[level]; for (var k in p) GFX[k] = p[k]; }
/** 現在的畫質是哪一檔（三檔都對不上 ⇒ custom）。 */
function gfxLevel() {
  for (var l in GFX_PRESET) { var p = GFX_PRESET[l], ok = true; for (var k in p) if (GFX[k] !== p[k]) ok = false; if (ok) return l; }
  return 'custom';
}
function gfxText() { return GFX_ITEMS.map(function (it) { return it.name + ' ' + it.opt[GFX[it.k]].replace(/（.*$/, ''); }).join('・'); }
gfxSet(GFX_PRESET[Q.get('gfx')] ? Q.get('gfx') : GFX_DEFAULT);
GFX_ITEMS.forEach(function (it) { var v = parseInt(Q.get('g_' + it.k), 10); if (isFinite(v)) GFX[it.k] = clamp(v, 0, it.opt.length - 1); });
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/08_sea.js ──
// ───────────────────────── 海浪（TASK-0522） ─────────────────────────
// 物理與畫面共用同一組浪（WAVES）：水面高度 h(x, z, t) ＝ SEA_K × Σ a·sin(kx·x ＋ kz·z − ω·t ＋ φ)，深水色散 ω ＝ √(g·k)。
//   浪向跟著風（WIND，開局固定）：主浪順風，其他幾道偏一點 ⇒ 海面不會整片一條一條。SEA_K ＝ 細節設定的「浪」（0 ＝ 平靜的海）。
// 用到水面高度的（seaH）：砲彈落水與打水漂（21_gunnery.js；03_camera.js 的推算）、碎片與斷開的一團浮沉（12／21／22）、
//   落水的人（40）、垂到水裡的繩（30）、航跡（31）、船的起伏與搖晃（stepWaves，32_hull.js 每步呼叫）。
// 船的起伏：船底 5（船長）× 2（兩舷）個點的水面擬合一個平面 ⇒ 平均高度、縱向坡度、橫向坡度，彈簧阻尼跟過去（船有慣性）。
//   短浪在 54 m 的船長上被平均掉，長浪才搖得動船。sh.wl ＝ 船底的平均水面（絕對高度）、sh.bob ＝ 船身相對它的起伏（彈簧的落後量）
//   ⇒ 進水、電腦瞄水線那些「水線在船上的哪一層」照舊用 sink − lift − bob（相對的），船的矩陣多加 sh.wl（10_ship.js shipMatrix）。
// 畫面（60_render.js 的海面網格）頂點照同一個 h 位移，法線在片段裡照解析的坡度算；細的漣漪只在法線裡、跟畫質走 ——
//   ⛔ 漣漪不進物理 ⇒ 畫質不改戰局。⛔ 相位寫死、不抽 rnd() ⇒ 浪不打亂亂數的順序。
// 七道：波長之間不是整數比、方向左右交錯（⛔ 四道整齊的浪 ⇒ 海面一格一格的重複紋路，Tim 2026-10-13）
var WAVES = [                                   // a 振幅（m，再乘 SEA_K）、L 波長（m）、d 偏離風向幾度、ph 相位
  { a: 0.40, L: 78, d: 0, ph: 0.0 },              // 主浪（週期 7.1 秒）：搖得動整艘船
  { a: 0.24, L: 51, d: 31, ph: 1.7 },
  { a: 0.19, L: 37, d: -23, ph: 4.1 },
  { a: 0.12, L: 26.5, d: 52, ph: 2.3 },
  { a: 0.09, L: 19, d: -61, ph: 5.2 },
  { a: 0.06, L: 13.3, d: 14, ph: 0.9 },
  { a: 0.04, L: 9.1, d: -38, ph: 3.6 }];          // 最短的：船上感覺不到，只看得到
(function () {
  var wa = Math.atan2(WIND[2], WIND[0]);
  WAVES.forEach(function (w) { var k = 2 * Math.PI / w.L, a = wa + w.d * Math.PI / 180; w.kx = Math.cos(a) * k; w.kz = Math.sin(a) * k; w.w = Math.sqrt(G * k); });
})();
/** 水面高度（世界座標 x, z、時間 t）。 */
function seaH(x, z, t) {
  if (!(SEA_K > 0)) return 0;
  var h = 0;
  for (var i = 0; i < WAVES.length; i++) { var w = WAVES[i]; h += w.a * Math.sin(w.kx * x + w.kz * z - w.w * t + w.ph); }
  return h * SEA_K * WX.sea;                    // 天氣（08_weather.js）：暴風雨 ×2.5；晴天 ×1（逐位元組不變）
}
// 著色器用的同一組浪（常數照 WAVES 生成；uSeaK、uSeaT 在 setCommon 給）。seaH ＝ 高度，seaG ＝ 坡度（∂h/∂x, ∂h/∂z）；
// seaHs ＝ 照網格間距 s 拿掉太短的浪（⛔ 頂點間距比波長的 1/4 還粗 ⇒ 鋸齒、浪在網格上游動）；
// seaGf ＝ 照一個像素在海面上多寬（fp，公尺）淡掉太短的浪的坡度（⛔ 不淡 ⇒ 遠處的浪比像素還細，疊出規則的疊紋）。
var SEA_GLSL = (function () {
  var f = function (v) { var s = (+v).toPrecision(9); return s.indexOf('.') < 0 && s.indexOf('e') < 0 ? s + '.0' : s; };
  var h = [], g = [], hs = [], gf = [];
  WAVES.forEach(function (w) {
    var arg = 'dot(p,vec2(' + f(w.kx) + ',' + f(w.kz) + '))-' + f(w.w) + '*uSeaT+' + f(w.ph);
    h.push(f(w.a) + '*sin(' + arg + ')');
    g.push(f(w.a) + '*cos(' + arg + ')*vec2(' + f(w.kx) + ',' + f(w.kz) + ')');
    hs.push(f(w.a) + '*(1.0-smoothstep(' + f(w.L * 0.18) + ',' + f(w.L * 0.3) + ',s))*sin(' + arg + ')');
    gf.push(f(w.a) + '*(1.0-smoothstep(' + f(w.L * 0.25) + ',' + f(w.L * 0.6) + ',fp))*cos(' + arg + ')*vec2(' + f(w.kx) + ',' + f(w.kz) + ')');
  });
  return 'uniform float uSeaK, uSeaT;\n' +
    'float seaH(vec2 p){ return uSeaK*(' + h.join('+') + '); }\n' +
    'vec2 seaG(vec2 p){ return uSeaK*(' + g.join('+') + '); }\n' +
    'float seaHs(vec2 p,float s){ return uSeaK*(' + hs.join('+') + '); }\n' +
    'vec2 seaGf(vec2 p,float fp){ return uSeaK*(' + gf.join('+') + '); }\n' +
    'const float SEA_WA=' + f(Math.atan2(WIND[2], WIND[0])) + ';\n';
})();
// 彈簧 [k, c]（k ＝ ωn²、c ＝ 2ζωn）：起伏、縱搖週期 2.5 秒、阻尼比 0.6 ⇒ 長浪（6.9 秒）幾乎同相跟著走；橫搖週期 5 秒、阻尼比 0.35 ⇒ 會晃、會落後一點。
//   ⛔ 起伏設成 5 秒（照巡防艦的固有週期）⇒ 跟主浪差不多快、落後 60°，船身對水面的上下跟浪本身一樣大（量過：相對 0.33 m 對浪 0.32 m），看起來像沒在跟
var WV_K = { h: [6.25, 3.0], p: [6.25, 3.0], r: [1.44, 0.84] };
/** 每步：船底的水面擬合平面 ⇒ 船的起伏、縱搖、橫搖（彈簧阻尼跟過去）。開戰第一步直接放在目標上（不從平的海晃過去）。 */
function stepWaves(sh, dt) {
  var T = sh.T, Lh = (T.hx1 - T.hx0) * S, c = sh.center || [sh.px, 0, sh.pz], F = fwd(sh.yaw), Z = [Math.sin(sh.yaw), 0, Math.cos(sh.yaw)];   // Z：船體 +Z（格 +y、右舷）在世界的方向
  var n = 0, hm = 0, su = 0, uu = 0, sw = 0, ww = 0;
  for (var a = -2; a <= 2; a++) for (var b = -1; b <= 1; b += 2) {
    var u = a * 0.2 * Lh, w = b * 0.1 * Lh, h = seaH(c[0] + F[0] * u + Z[0] * w, c[2] + F[2] * u + Z[2] * w, SIMT);
    hm += h; su += u * h; uu += u * u; sw += w * h; ww += w * w; n++;
  }
  hm /= n;
  var tp = Math.atan(su / uu), tr = -Math.atan(sw / ww);              // 縱搖正 ＝ 船頭（格 +x）抬起；橫搖正 ＝ 船體 +Z 那舷往下 ⇒ 水在 +Z 那邊高就取負
  var V = sh.wv;
  if (!V) V = sh.wv = { h: hm, hv: 0, p: tp, pv: 0, r: tr, rv: 0 };
  V.hv += (WV_K.h[0] * (hm - V.h) - WV_K.h[1] * V.hv) * dt; V.h += V.hv * dt;
  V.pv += (WV_K.p[0] * (tp - V.p) - WV_K.p[1] * V.pv) * dt; V.p += V.pv * dt;
  V.rv += (WV_K.r[0] * (tr - V.r) - WV_K.r[1] * V.rv) * dt; V.r += V.rv * dt;
  sh.wl = hm; sh.bob = V.h - hm; sh.pitchW = V.p; sh.rollW = V.r;
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/08_weather.js ──
// ───────────────────────── 天氣（TASK-0523） ─────────────────────────
// 主選單「天氣」：晴（預設）／暴風雨；網址 ?weather=storm。開戰前選、整場不變。
// 進戰局的（物理）：浪（seaH 再乘 sea）、風（煙飄的速度與帆上的風再乘 wind）、航速（乘 speed）、操舵（最大轉向率乘 agile）、
//   開砲的散布（aim：照船搖晃的角速度放大，wxSpread）。
// 只在畫面的：天色（SKY／HORIZON／GROUND）、霧（fog）、陽光（sun：直射光的強度）、水手與碎木的亮度（lum）、浪頭的白沫（foam）、
//   雨（rain，大小再看畫質設定的「雨」）、閃電（bolt：照模擬時間的雜湊挑時刻，不抽亂數；打雷的聲音照距離延後）。
// ⛔ 晴天的每一個係數都是 1（或 0 且有分支擋著）⇒ 跟加天氣之前逐位元組相同：同一個種子的戰局、縮圖都一樣（反向對照）。
//   新的效果一律寫成「晴天剛好是 1 的乘數」，⛔ 不要另外抽 rnd()（會讓晴天的亂數錯位）。
var WEATHERS = {
  clear: { name: '晴', sea: 1, wind: 1, speed: 1, agile: 1, aim: 0, sky: SKY, horizon: HORIZON, ground: GROUND, fog: 0.0016, sun: 1, lum: 1, foam: 0, rain: 0, bolt: 0 },
  storm: { name: '暴風雨', sea: 2.5, wind: 2.2, speed: 1.15, agile: 0.8, aim: 1,
    sky: [0.25, 0.28, 0.32], horizon: [0.34, 0.36, 0.38], ground: [0.13, 0.13, 0.12], fog: 0.0042, sun: 0.3, lum: 0.62, foam: 1, rain: 1, bolt: 1 } };
// 風會變（Tim 2026-10-13：風速、風向在遊戲中變動，照天氣；暴風雨變得快、風速高）：
//   風向 ＝ 開局的風向 ＋ dir ×（三道正弦，權重 0.6／0.3／0.1、週期 per）；風速倍率 WIND_SPD ＝ 1 ＋ spd ×（另外三道，週期再 ×0.73）。
//   每道都寫成 sin(ωt＋φ) − sin φ ⇒ 開局那一刻 ＝ 原本的風；相位照種子的雜湊（不抽亂數）⇒ 同一個種子同一陣風。
//   晴：週期 233／97／41 秒，風向最多偏約 23°、風速 ±30%；暴風雨：71／29／11 秒，風向最多約 70°、風速 0.4–1.6 倍（再乘 wind 2.2）。
//   WIND（00_core.js）每一步就地改：方向給航行（風向係數、頂風失速）、帆、羅盤；長度 ＝ 開局的長度 × WIND_SPD（煙飄的速度）。
//   航速 ∝ √WIND_SPD（31_sailing.js）、帆上的風 × WIND_SPD（30_rig_physics.js）。浪的方向不跟：湧浪是開局那陣風吹出來的（08_sea.js 建一次）。
WEATHERS.clear.gusts = { dir: 0.2, spd: 0.15, per: [233, 97, 41] };
WEATHERS.storm.gusts = { dir: 0.6, spd: 0.3, per: [71, 29, 11] };
var WIND0 = WIND.slice(), WIND_A0 = Math.atan2(WIND0[2], WIND0[0]), WIND_L0 = Math.hypot(WIND0[0], WIND0[2]), WIND_SPD = 1, WIND_LOG = { a: WIND_A0, s: 1, t: 0 };
var WX_ID = WEATHERS[Q.get('weather')] ? Q.get('weather') : 'clear', WX = WEATHERS[WX_ID];
function seedHash(k) { var x = Math.sin((SEED % 99991) * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); }
/** 每一步（50_sim.js step 開頭、70_flow.js 開局）：照模擬時間算現在的風，改 WIND 與 WIND_SPD；風向轉了 20° 以上、風速變了三成以上 ⇒ 上方廣播（15 秒內不重複）。 */
function stepWind(t) {
  var g = WX.gusts, wt = [0.6, 0.3, 0.1], da = 0, ds = 0;
  for (var i = 0; i < 3; i++) {
    var om = 2 * Math.PI / g.per[i], p1 = seedHash(i) * 6.2832, p2 = seedHash(i + 7) * 6.2832;
    da += wt[i] * (Math.sin(om * t + p1) - Math.sin(p1)); ds += wt[i] * (Math.sin(om * 1.37 * t + p2) - Math.sin(p2));
  }
  var a = WIND_A0 + g.dir * da; WIND_SPD = Math.max(0.4, 1 + g.spd * ds);
  WIND[0] = Math.cos(a) * WIND_L0 * WIND_SPD; WIND[1] = 0; WIND[2] = Math.sin(a) * WIND_L0 * WIND_SPD;
  if (t <= 0) { WIND_LOG = { a: a, s: WIND_SPD, t: 0 }; return; }
  if (t - WIND_LOG.t < 15 || !SHIPS[PLAYER_I]) return;
  var turn = Math.atan2(Math.sin(a - WIND_LOG.a), Math.cos(a - WIND_LOG.a)) * 57.3, ds2 = WIND_SPD / WIND_LOG.s;
  if (Math.abs(turn) >= 20 || ds2 > 1.3 || ds2 < 0.77) {
    var msg = Math.abs(turn) >= 20 ? '風向轉了 ' + Math.round(Math.abs(turn)) + '°（現在從 ' + compassName(bearing(-WIND[0], -WIND[2])) + ' 吹來）' : '';
    if (ds2 > 1.3 || ds2 < 0.77) msg += (msg ? '，' : '') + (ds2 > 1 ? '風勢增強' : '風勢減弱') + '（約 ' + windKnots().toFixed(0) + ' 節）';
    note(SHIPS[PLAYER_I], msg); WIND_LOG = { a: a, s: WIND_SPD, t: t };
  }
}
/** 帆上的風速（節）：給 HUD 與廣播看。 */
function windKnots() { return WIND_SAIL * WIND_K * WX.wind * WIND_SPD * 1.944; }
/** 換天氣：天色跟著換（00_core.js 的 SKY／HORIZON／GROUND；晴天 ＝ 原本那三個陣列本身）。 */
function setWeather(id) {
  WX_ID = WEATHERS[id] ? id : 'clear'; WX = WEATHERS[WX_ID];
  SKY = WX.sky; HORIZON = WX.horizon; GROUND = WX.ground;
  [].forEach.call(document.querySelectorAll('#wxs button'), function (b) { b.className = b.dataset.w === WX_ID ? 'on' : ''; });
}
/** 開砲散布的倍率：晴天 1；暴風雨 ＝ 1.25 ＋ 9 ×（橫搖角速度 ＋ 一半的縱搖角速度，rad/s）—— 船晃得越快，點火那一下差得越多。 */
function wxSpread(sh) {
  if (!WX.aim || !sh.wv) return 1;
  return 1.25 + 9 * (Math.abs(sh.wv.rv) + 0.5 * Math.abs(sh.wv.pv));
}
/** 閃電（只在畫面）：每 0.1 秒一格，照模擬時間的雜湊決定那一格有沒有打（平均約 7 秒一次）；回傳最近一道的亮度（0.3 秒內衰減）與它在哪（方位、多遠）。 */
function wxBolt(t) {
  if (!WX.bolt) return null;
  for (var k = 0; k < 4; k++) {
    var n = Math.floor(t * 10) - k, h = fract(Math.sin(n * 91.7 + 13.1) * 43758.5453);
    if (h < 0.014) { var age = t - n / 10; return { f: Math.max(0, 1 - age / 0.3) * (0.6 + 0.4 * fract(h * 977)), n: n, az: fract(h * 7919) * 6.2832, d: 600 + 1800 * fract(h * 31337) }; }
  }
  return null;
}
function fract(x) { return x - Math.floor(x); }
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/09_phx.js ──
// ───────────────────────── 物理效果分級（TASK-0526） ─────────────────────────
// 主選單：全開／高／中／低（PHX_PRESET）；「物理設定…」頁一項一項調，跟四檔都對不上 ⇒ 主選單顯示「自訂」。
// 管的是「給人看的物理」：帆與繩（30_rig_physics.js）、碎木（12_effects.js 的碎片）、煙與水花（粒子）、船邊水花（13_water.js：船頭浪、船尾白沫、拍浪、擦撞與落水的水滴與白沫）；
//   以及進水（33_flood.js：公式或粒子 —— ⛔ 粒子會改戰局，Tim 要的：開了就完全由粒子判斷）。
//   ⛔ 浪不在這裡：浪的大小改戰局（砲彈打到浪頭、船的姿態），在細節設定。
// 戰局：
//   · 船邊水花：自己的亂數（rndW）、不回寫模擬；開著時原本的航跡與水花照樣抽亂數、只是不放（PT_MUTE）⇒ 開關不改戰局。
//   · 進水：粒子模式改戰局（進水量、下沉、傾斜照艙內的水），粗／中／細各自一局；開戰時決定（FLOOD_LV），戰鬥中改了下一場生效。
//   · 碎木、煙與水花少生幾顆不改戰局：照固定的節拍跳過（不抽亂數）。煙與水花的參數照樣由呼叫端抽完亂數（只是不放進去）；
//     碎木自己的亂數（轉軸、落水、落地）走另一條（rndD，12_effects.js）。⛔ 碎木以前跟戰局共用 rnd() ⇒ 少一顆碎木，後面的亂數全部錯位、整局都變。
//   · 帆與繩：低／中／高只差布與繩的細緻度（迭代次數、帆幾步走一次、垂繩上限），不碰 rnd()、不改命中；
//     關 ⇒ 帆停在雕刻作品那一刻、帆桁不追風 —— 帆桁的角度會改到打中帆桁的那幾下（30_rig_physics.js），跟以前「關掉物理」一樣。
// 網址：?phx=full|high|mid|low，單項 ?p_rig= ?p_debris= ?p_fx= ?p_water= ?p_flood=（第幾檔，從 0 起）；舊的 ?phys=0 ＝ 帆與繩關。
var PHX_ITEMS = [
  { k: 'rig', name: '帆與繩', opt: ['關（靜態）', '低', '中', '高'] },
  { k: 'debris', name: '碎木', opt: ['20%', '45%', '70%', '100%'] },
  { k: 'fx', name: '煙與水花', opt: ['40%', '65%', '85%', '100%'] },
  { k: 'water', name: '船邊水花', opt: ['關（原本的）', '低', '中', '高'] },
  { k: 'flood', name: '進水', opt: ['公式', '粒子 粗', '粒子 中', '粒子 細'] }];
var PHX_PRESET = { full: { rig: 3, debris: 3, fx: 3, water: 3, flood: 3 }, high: { rig: 2, debris: 2, fx: 2, water: 2, flood: 2 }, mid: { rig: 1, debris: 1, fx: 1, water: 1, flood: 1 }, low: { rig: 0, debris: 0, fx: 0, water: 0, flood: 0 } };
var PHX_NAME = { full: '全開', high: '高', mid: '中', low: '低', custom: '自訂' }, PHX_DEFAULT = 'full';
// 帆與繩每一檔：it 布與繩的迭代次數、every 帆幾步走一次（2 ＝ 30 Hz，4 ＝ 15 Hz；一半的帆錯開一步）、loose 垂下來的繩最多幾條、shred 帆的布片每艘最多幾片（34_shreds.js）。高 ＝ 原本的。
var RIG_LV = [null, { it: 2, every: 4, loose: 150, shred: 40 }, { it: 3, every: 2, loose: 300, shred: 80 }, { it: 4, every: 2, loose: 500, shred: 150 }];
var DEB_KS = [0.2, 0.45, 0.7, 1], FX_KS = [0.4, 0.65, 0.85, 1];
var PHX = {}, PHX_RIG_LAST = 3;                 // PHX_RIG_LAST：B 鍵關掉再開，回到關之前那一檔
function phxSet(level) { var p = PHX_PRESET[level]; for (var k in p) PHX[k] = p[k]; }
/** 現在是哪一檔（四檔都對不上 ⇒ custom）。 */
function phxLevel() {
  for (var l in PHX_PRESET) { var p = PHX_PRESET[l], ok = true; for (var k in p) if (PHX[k] !== p[k]) ok = false; if (ok) return l; }
  return 'custom';
}
function phxText() { return PHX_ITEMS.map(function (it) { return it.name + ' ' + it.opt[PHX[it.k]].replace(/（.*$/, ''); }).join('・'); }
function rigLv() { return RIG_LV[PHX.rig] || RIG_LV[3]; }
phxSet(PHX_PRESET[Q.get('phx')] ? Q.get('phx') : PHX_DEFAULT);
PHX_ITEMS.forEach(function (it) { var v = parseInt(Q.get('p_' + it.k), 10); if (isFinite(v)) PHX[it.k] = clamp(v, 0, it.opt.length - 1); });
if (Q.get('phys') === '0' && !Q.has('p_rig')) PHX.rig = 0;
PHYS = PHX.rig > 0;                             // 帆與繩開不開（04_state.js 的 PHYS）跟著這一項走
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/10_ship.js ──
// ───────────────────────── 船 ─────────────────────────
// 格 → 船體（公尺）：(x, y, z) ⇒ (S(x−cx), S(z−zw), S(y−cy))。船體 ＝ 世界的軸（+X 船頭、+Y 上、+Z ＝ 右舷）。
// 雕刻引擎的格是另一個手性（面向船頭 +x、上 +z，+y 在右手邊 ＝ 右舷 S：basecamp 的命名、船尾名牌 EMBER 在雕刻引擎的 view 裡讀起來是正的）
// ⇒ 這是一個鏡射（行列式 −1）：船殼的繞序反過來（畫船時 frontFace CW，見 60_render.js shipFace）。
// ⛔ 2026-10-13 以前是 −S(y−cy)（旋轉、不是鏡射）⇒ 整艘船畫成作品的鏡像：EMBER 反著寫、右舷 S 出現在畫面左邊。
function shipBaseMatrix(T) {
  return new Float32Array([S, 0, 0, 0, 0, 0, S, 0, 0, S, 0, 0, -S * T.cx, -S * T.zw, -S * T.cy, 1]);
}
function shipMatrix(sh) {
  var m = trans(sh.px, -sh.sink + sh.lift + (sh.wl || 0) + sh.bob, sh.pz);   // wl：船底的平均水面、bob：船身相對它的起伏（08_sea.js）
  m = M4.mul(m, rotM([0, 1, 0], sh.yaw));
  m = M4.mul(m, rotM([0, 0, 1], sh.pitchA + (sh.pitchW || 0)));
  m = M4.mul(m, rotM([1, 0, 0], sh.rollA + (sh.rollW || 0)));
  return M4.mul(m, shipBaseMatrix(sh.T));
}
function shipCenter(sh) { return M4.pt(sh.M, sh.T.cx, sh.T.cy, sh.T.geo.center); }
function toLocal(sh, p) { return M4.pt(sh.inv, p[0], p[1], p[2]); }

function makeShip(i, team, yaw, pz, T, px) {                          // T：船型（05_hull.js）；px：編隊裡的前後位置（52_fleet.js spawnFleet；沒給 ＝ 0）
  var grid = T.base.share(), rsSet = new VK.RegionSet(gl, grid, QIDX);
  rsSet.shareFrom(T.pristine);
  var sh = {                                                            // cfg：船隻設定（開戰時那一型的值，04_state.js）
    T: T, cfg: cfgCopy(T.id), i: i, team: team, grid: grid, rs: rsSet, yaw: yaw, px: px || 0, pz: pz, sink: 0, sinkV: 0, lift: 0, liftT: 0, rollA: 0, pitchA: 0, rollV: 0, bob: 0,
    phase: rnd() * 6.28, orig: grid.count, flood: new Float32Array(T.sz * 3), lost: 0, seeds: [], impulse: [0, 0, 0],
    guns: [], ropes: [], sails: [], rigDirty: true, lines: null, tris: null, masts: [], aim: null, reloadT: MODE === 'sandbox' && i === PLAYER_I ? RELOAD_SANDBOX : RELOAD,
    fired: 0, hits: 0, salvo: 0, aiWait: rr(1, 3), sunk: false, struck: false, fate: '', silentT: -1, gunsAlive: 0, mastsUp: T.masts.length, sinkingFinal: false,
    spd: 0, spd0: true, yawRate: 0, vel: [0, 0, 0], wakeT: 0, sailFrac: 1, pos: '',
    side: 'S', manual: false, rudder: 0, sailSet: 3, bumpT: 0
  };
  // 模型（砲、火藥桶、舵輪）：整個是一塊剛體 —— 被打到扣血，歸零整個飛出去（火藥桶 ⇒ 殉爆，見 23_powder.js），⛔ 不拆格。
  // 種類照 basecamp 給的 meta（TASK-0517）：{kind:'gun', gun:'24l'|'32c'|'18chase'}、{kind:'powder', powder_lb}；舵輪沒有 meta ⇒ 照名字。
  sh.models = (T.rig.models || []).map(function (m, k) {
    var b = m.bbox, kind = modelKind(m), pv = (m.points || {}).pivot;
    var cx = Math.floor((b[0] + b[3]) / 2), cy = Math.floor((b[1] + b[4]) / 2), fz = Math.floor(b[2]) - 1;
    var foot = -1;
    if (kind === 'yard' && pv) foot = anchorNear(T, pv[0], pv[1], pv[2], 8);   // 帆桁：「腳」是轉軸旁最近的那一格桅（桅斷了跟著走、被打掉就掉）；⛔ 往下找：艏斜桅下面是空的，spritsail 一開局就掉
    var st = (m.points || {})['stock-top'];
    if (kind === 'rudder' && st) foot = anchorNear(T, st[0], st[1], st[2], 8);   // 舵：掛在艉柱上 ⇒「腳」是舵頭旁的船尾（⛔ 往下找：舵底在 z 0，腳落到 z −1 ⇒ 開局就掉）
    if (foot < 0) { while (fz > 0 && !T.base.get(cx, cy, fz)) fz--; foot = VK.pack(cx, cy, fz); }   // 腳下那一格甲板（被打掉 ⇒ 掉下去）
    var hpm = kind === 'powder' ? powderHP() : kind === 'wheel' ? Math.round(GUN_HP * 0.6) : kind === 'model' ? 1 : GUN_HP;   // 細節設定的血量；舵輪 6 成；帆桁、舵跟砲一樣
    var mt = m.meta || {};
    return { T: T, k: k, name: m.name.split('/').pop(), path: m.name, kind: kind, hp: hpm, hpMax: hpm, mesh: m.mesh, origin: m.origin, bb: b, pts: m.points || {}, meta: mt,
      c: [(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2], foot: foot, alive: true,
      rot: 0, r0: (+mt.rotate_z_deg || 0) * Math.PI / 180, piv: pv, yk: mt.yard, sail: mt.sail };   // 帆桁：rot ＝ 在作品的角度（r0）之外又轉了多少（追風，30_rig_physics.js）
  });
  sh.yards = sh.models.filter(function (m) { return m.kind === 'yard' && m.piv; });
  // 砲：長砲（24 磅，兩舷各 14）、carronade（32 磅，兩舷各 12）、追擊砲（18 磅，船頭兩舷各 1）都是模型。
  // 砲軸 ＝ 固定點 muzzle − breech（格座標、水平）；砲口 ＝ muzzle 再往外 1.5 格（muzzle 在砲口內膛那一格）。
  // 程式裡的 'S'／'P' 照砲軸（+y ＝ S，跟模型名字一致）＝ 右舷／左舷（shipBaseMatrix 照雕刻引擎的手性鏡射過來）。給人看的走 sideName；A／D 照畫面的左右。
  sh.models.forEach(function (m) {
    if (!GUNS[m.kind]) return;
    var mz = m.pts.muzzle, br = m.pts.breech, ax;
    if (mz && br) ax = [mz[0] - br[0], mz[1] - br[1]];
    else { var sg0 = /-P\d*$|-P$/.test(m.name) ? -1 : 1; ax = [0, sg0]; mz = [m.c[0], sg0 > 0 ? m.bb[4] - 0.5 : m.bb[1] + 0.5, m.c[2]]; }   // 沒有固定點（舊的 .vxk）⇒ 外框外緣
    var al = Math.hypot(ax[0], ax[1]) || 1; ax = [ax[0] / al, ax[1] / al];
    sh.guns.push(m.gun = { name: m.name, type: m.kind, side: ax[1] >= 0 ? 'S' : 'P', model: m, ax: ax,
      muz: [mz[0] + ax[0] * 1.5, mz[1] + ax[1] * 1.5, mz[2]], alive: true, reload: rr(0, 1.2), box: BOX_N, needCart: false });   // box：砲旁藥箱裡的份數
  });
  sh.guns.sort(function (a, b) { return b.muz[0] - a.muz[0] || a.muz[1] - b.muz[1]; });
  sh.decks = gunDecks(sh); sh.weatherDeck = sh.decks.length ? sh.decks[sh.decks.length - 1].key : null;   // 砲甲板（照砲的高度分層）；最上面那層 ＝ 露天
  sh.deckZ = {}; sh.decks.forEach(function (D) { sh.deckZ[D.key] = D.zr; });
  sh.mags = makeMags(sh);                                                // 彈藥庫（23_powder.js）
  sh.stations = makeStations(sh);                                        // 兩層甲板的火藥與彈藥取用點（火藥桶也是模型，加在 sh.models 後面）
  sh.mIdx = modelIndex(sh.models);
  // 繩與帆：兩端（帆取最高那一排）各找最近的實心格當錨 —— 錨被打掉或跟船分家 ⇒ 繩斷、帆掉
  T.rig.ropes.forEach(function (r) {
    var n = r.pts.length / 3;
    sh.ropes.push({ pts: r.pts, col: r.color, bb: ropeBox(r.pts), a: anchorNear(T, r.pts[0], r.pts[1], r.pts[2], 5), b: anchorNear(T, r.pts[n * 3 - 3], r.pts[n * 3 - 2], r.pts[n * 3 - 1], 5), name: r.name, meta: r.meta || null });
  });
  linkRopes(T, sh.ropes, sh.models);
  T.rig.sails.forEach(function (s) {
    var vz = -1e9, ax = 0, ay = 0, az = 0, k = 0, j;
    for (j = 2; j < s.verts.length; j += 3) vz = Math.max(vz, s.verts[j]);
    for (j = 0; j < s.verts.length; j += 3) if (s.verts[j + 2] > vz - 2) { ax += s.verts[j]; ay += s.verts[j + 1]; az += s.verts[j + 2]; k++; }
    sh.sails.push(sailAnchors(sh, { verts: s.verts, tris: s.tris, col: s.color, name: s.name, meta: s.meta || null, bb: ropeBox(s.verts) }, [ax / k, ay / k, az / k]));
  });
  // 帆自己的繩（`<帆名>.sheet-S`、`.tack-P`…）：帆腳那一端綁在帆上 ⇒ 帆掉了或被帶走，它們跟著斷
  // （⛔ 只靠繩的依靠不夠：sheet 與 tack 互相掛著、另一端綁甲板，帆沒了也還浮在半空）
  sh.sails.forEach(function (s, k) { s.k = k; s.hp = s.hpMax = SAIL_HP; s.lines = []; sh.ropes.forEach(function (r, j) { if (sailRope(r, s.name)) s.lines.push(j); }); });
  sh.sails.forEach(function (s) {
    s.yards = sh.yards.filter(function (y) { return y.sail === s.name; });   // 掛這面帆的帆桁（spanker：gaff＋boom）
    // 帆腳跟著轉的帆桁：topsail 以上 ＝ 下一根（sheet 綁在它兩端）；course ＝ 沒有（綁甲板）；spanker（沒有帆腳，下緣綁 boom）＝ 低的那根
    var f = T.cloth[s.k] ? T.cloth[s.k].foot : -1, low = s.yards.slice().sort(function (a, b) { return a.piv[2] - b.piv[2]; });
    s.footYard = f >= 0 ? sh.models[f] : low.length > 1 ? low[0] : null;
    if (low.length > 1) s.yards = low.reverse();                          // 帆頂那根排第一（打中帆照它轉回作品角度）
  });
  ropeYards(sh);
  sh.ropes.forEach(function (r) { r.never = r.lz = !!r.dead; });        // 一開始就不畫的繩不會變成垂下來的繩（物理，見 physStep）
  sh.cl = T.cloth.map(function (C) { return { T: C, p: null, hidden: true }; }); sh.loose = []; sh.shreds = [];   // shreds：帆的布片（34_shreds.js）
  sh.sails.forEach(function (s) { s.flag = isFlag(s); s.area = s.flag ? 0 : sailArea(s); }); sh.sailArea0 = sh.sails.reduce(function (a, s) { return a + s.area; }, 0) || 1;   // 旗不算推力（面積 0）
  applySailSet(sh);
  T.masts.forEach(function (m) { sh.masts.push({ name: m.name, x: m.x, z0: m.z0, z1: m.z1, orig: m.orig, z0top: m.z0top, up: true }); });
  sh.crew = makeCrew(sh); sh.crew0 = sh.crew.length; sh.wounded = 0; sh.dead = 0; sh.kills = 0; sh.wounds = 0; sh.causes = {};   // kills／wounds：累計（廣播傷亡用；wounded 會在傷者陣亡時減回去）
  sh.news = { guns: [], t: -9, k: 0, w: 0, kr: {}, wr: {} };
  sh.M = shipMatrix(sh); sh.inv = M4.inv(sh.M);
  sh.fl = flNew(sh);                                                    // 進水：粒子模式（33_flood.js；公式模式 ⇒ null）
  return sh;
}
// 砲種（meta gun 的代碼 ⇒ 程式裡的種類）：名字、初速（m/s）、裝填倍率、彈大不大（洞大一點）、砲班滿編／最少、重量（噸，浮力用）、每發傷害（DMG 的鍵，細節設定）。
// 長砲 24 磅、carronade 32 磅、追擊砲 18 磅是憲法號的；32 磅長砲是給餘燼號的（basecamp TASK-0519：下層砲甲板 28 門，新做一門）；4 磅砲是夜隼號的（兩舷各 6）。
// hole：實心彈的洞大小倍率（沒寫 ＝ 1；big ＝ 1.25）。
var GUNS = {
  long: { code: '24l', name: '24 磅長砲', short: '長砲', V: V0, reload: 1, big: false, crew: 5, min: 3, mass: 2.5 },
  long32: { code: '32l', name: '32 磅長砲', short: '32 磅長砲', V: 172, reload: 1.15, big: true, crew: 6, min: 4, mass: 2.9 },
  carr: { code: '32c', name: '32 磅 carronade', short: ' carronade ', V: 140, reload: 0.7, big: true, crew: 3, min: 2, mass: 0.9 },
  chase: { code: '18chase', name: '18 磅追擊砲', short: '追擊砲', V: 165, reload: 1, big: false, crew: 3, min: 2, mass: 2.1 },
  long4: { code: '4l', name: '4 磅砲', short: '4 磅砲', V: 165, reload: 0.6, big: false, hole: 0.6, crew: 2, min: 1, mass: 0.5 }   // 夜隼號（summit）：輕、裝得快、洞小（彈徑約 24 磅的 0.55 倍）；0.5 噸 ⇒ 船殼格子 68 噸＋砲 6 噸，比設計水線低約 7 cm
};
var GUN_CODE = {}; Object.keys(GUNS).forEach(function (k) { GUN_CODE[GUNS[k].code] = k; });
/** 砲甲板：照舷側砲（不含追擊砲）的高度（外框底）分層 —— 排好之後相差 10 格以上就是另一層（甲板有舷弧，同一層前後差 6 格）；
 *  追擊砲再歸到最近的那一層（⛔ 一起排：船尾追擊砲的高度落在兩層之間，會把上下兩層砲甲板接成一層）。
 *  每層：站人的高度範圍 zr（照那一層第一門不是追擊砲的砲：carronade 那層 −6～+3、其他 −8～+5）、名字、最上面那層 ＝ 露天（陸戰隊、砲長的「甲板人員」）。
 *  憲法號：長砲 z 82–86＋追擊砲 88 ／ carronade 105–108 ⇒ 兩層，跟以前照砲種分（長砲＋追擊砲 ／ carronade）一樣；餘燼號兩層砲甲板都是長砲 ⇒ 照種類分不出來。 */
function gunDecks(sh) {
  var side = sh.guns.filter(function (g) { return g.type !== 'chase'; }); if (!side.length) side = sh.guns;
  var zs = side.map(function (g) { return Math.floor(g.model.bb[2]); }).sort(function (a, b) { return a - b; }), G = [];
  zs.forEach(function (z) { var L = G[G.length - 1]; if (L && z - L.z1 <= 10) L.z1 = z; else G.push({ z0: z, z1: z }); });
  var decks = G.map(function (L, i) { return { key: 'd' + i, z0: L.z0, z1: L.z1, guns: [] }; });
  sh.guns.forEach(function (g) {
    var z = Math.floor(g.model.bb[2]), D = null, bd = 1e9;
    decks.forEach(function (d) { var dd = z < d.z0 ? d.z0 - z : z > d.z1 ? z - d.z1 : 0; if (dd < bd) { bd = dd; D = d; } });   // 在那一層的範圍裡 ⇒ 0；不在 ⇒ 最近的那一層
    g.deck = D.key; D.guns.push(g);
  });
  var low = decks.length - (decks.length > 1 ? 1 : 0);
  decks.forEach(function (D, i) {
    var main = D.guns.filter(function (g) { return g.type !== 'chase'; })[0] || D.guns[0], a = Math.floor(main.model.bb[2]);
    D.zr = main.type === 'carr' ? [a - 6, a + 3] : [a - 8, a + 5];
    D.weather = i === decks.length - 1;
    D.name = D.weather && decks.length > 1 ? '上甲板' : low === 1 ? '砲甲板' : low === 2 ? (i === 0 ? '下層砲甲板' : '上層砲甲板') : '第 ' + (i + 1) + ' 層砲甲板';
  });
  return decks;
}
/** 格座標 P 附近 r 格內有沒有帆桁的網格（照佔用格）⇒ 回那根帆桁的模型編號（T.rig.models 的序號 ＝ sh.models 的序號），沒有 ⇒ -1。 */
function yardNear(T, P, r) {
  var ms = T.rig.models || [];
  for (var k = 0; k < ms.length; k++) {
    var m = ms[k], b = m.bbox; if (!m.meta || m.meta.kind !== 'yard') continue;
    if (P[0] < b[0] - r || P[0] > b[3] + r || P[1] < b[1] - r || P[1] > b[4] + r || P[2] < b[2] - r || P[2] > b[5] + r) continue;
    var oc = T.meshes[m.mesh] && T.meshes[m.mesh].occ; if (!oc) continue;
    var x0 = Math.floor(P[0] - m.origin[0]) + 1, y0 = Math.floor(P[1] - m.origin[1]) + 1, z0 = Math.floor(P[2] - m.origin[2]) + 1;
    for (var dz = -r; dz <= r; dz++) for (var dy = -r; dy <= r; dy++) for (var dx = -r; dx <= r; dx++) {
      var x = x0 + dx, y = y0 + dy, z = z0 + dz;
      if (x >= 0 && y >= 0 && z >= 0 && x < oc.nx && y < oc.ny && z < oc.nz && oc.a[x + oc.nx * (y + oc.ny * z)]) return k;
    }
  }
  return -1;
}
/** 繩的兩端各跟著哪根帆桁轉（-1 ＝ 不跟）：端點靠在帆桁上（綁在帆桁上的 brace、lift、footrope，topsail 以上的 sheet…）。
 *  course 的 sheet 與 tack 兩端都不在帆桁上（帆腳綁甲板繩栓）⇒ 不轉，跟帆腳一起留著（clothTemplate 的 clewYard）。同一型的兩艘共用一份（T.ropeYard）。 */
function ropeYards(sh) {
  var T = sh.T;
  if (!T.ropeYard) T.ropeYard = T.rig.ropes.map(function (r) { var n = r.pts.length / 3; return [yardNear(T, [r.pts[0], r.pts[1], r.pts[2]], 3), yardNear(T, [r.pts[n * 3 - 3], r.pts[n * 3 - 2], r.pts[n * 3 - 1]], 3)]; });
  sh.ropes.forEach(function (r, j) { r.pts0 = r.pts; r.ya = T.ropeYard[j][0]; r.yb = T.ropeYard[j][1]; });
  sh.yRopes = sh.ropes.filter(function (r) { return r.ya >= 0 || r.yb >= 0; });
}
/** 模型的種類：meta 優先（basecamp TASK-0517：kind／gun），沒有 meta 才照名字（舊的 .vxk；舵輪本來就沒有 meta）。 */
function modelKind(m) {
  var mt = m.meta || {};
  if (mt.kind === 'gun') return GUN_CODE[mt.gun] || 'long';           // 不認得的代碼 ⇒ 當長砲
  if (mt.kind === 'powder') return 'powder';
  if (mt.kind === 'yard') return 'yard';                              // 帆桁（basecamp 階段三十三：15 根各一件模型，可以繞轉軸轉）
  if (mt.kind === 'wheel') return 'wheel';                            // 餘燼號的舵輪叫「舵輪」、有 meta（⛔ 只照名字 ⇒ 認不出來，船只剩舵柄滑車的 35% 轉向）
  if (mt.kind === 'rudder') return 'rudder';                          // 夜隼號的舵是模型（summit：方艉船掛在艉板外）；憲法號、餘燼號的舵是船殼的格子
  return /carronade/.test(m.name) ? 'carr' : /chase/.test(m.name) ? 'chase' : /\/砲-[SP]\d+$/.test(m.name) ? 'long' : /wheel/.test(m.name) ? 'wheel' : 'model';
}
/** 模型照 x 分桶（每 16 格一桶，外框外擴 12 格登記）⇒ hitModel 只看砲彈所在那一桶（193 個模型 × 每顆砲彈每個小步全掃太貴）。
 *  桶裡照模型編號排 ⇒ 先碰到誰跟全掃一樣。 */
function modelIndex(models) {
  var idx = [];
  models.forEach(function (m) {
    for (var bx = Math.max(0, Math.floor((m.bb[0] - 12) / 16)); bx <= Math.floor((m.bb[3] + 12) / 16); bx++) (idx[bx] = idx[bx] || []).push(m);
  });
  return idx;
}
/** 兩端附近沒有實心格的繩（ratline 掛在 shroud 上）⇒ 掛在端點旁邊那條繩上：那條斷了它也斷、那條跟著桅倒它也跟著倒。 */
function linkRopes(T, ropes, models) {
  ropes.forEach(function (r, i) {
    if (r.a >= 0 && r.b >= 0) return;
    r.par = []; r.mods = [];
    var n = r.pts.length / 3;
    [[0, r.a, 'a'], [n - 1, r.b, 'b']].forEach(function (e) {
      if (e[1] >= 0) return;
      var P = [r.pts[e[0] * 3], r.pts[e[0] * 3 + 1], r.pts[e[0] * 3 + 2]], best = -1, bd = 9;      // 0.3 公尺內
      var yk = yardNear(T, P, 3);                                                // 帆桁：照網格（⛔ 照外框：轉過的帆桁外框很大，桅頂附近的 ratline 都會被當成綁在帆桁上）
      if (yk >= 0) { r.mods.push(yk); r['m' + e[2]] = yk; return; }
      var mod = models.filter(function (m) { var b = m.bb; if (m.station || m.kind === 'yard') return false; return P[0] > b[0] - 4 && P[0] < b[3] + 4 && P[1] > b[1] - 4 && P[1] < b[4] + 4 && P[2] > b[2] - 4 && P[2] < b[5] + 4; })[0];
      if (mod) { r.mods.push(mod.k); r['m' + e[2]] = mod.k; return; }   // 綁在模型上（舵索綁舵輪）⇒ 模型飛了才斷
      ropes.forEach(function (o, j) {
        if (j === i || P[0] < o.bb[0] - 3 || P[0] > o.bb[3] + 3 || P[1] < o.bb[1] - 3 || P[1] > o.bb[4] + 3 || P[2] < o.bb[2] - 3 || P[2] > o.bb[5] + 3) return;
        for (var k = 0; k + 5 < o.pts.length; k += 3) { var d = segDist2(P, o.pts[k], o.pts[k + 1], o.pts[k + 2], o.pts[k + 3], o.pts[k + 4], o.pts[k + 5]); if (d < bd) { bd = d; best = j; } }
      });
      if (best >= 0) { if (r.par.indexOf(best) < 0) r.par.push(best); r['p' + e[2]] = best; }   // 哪一端掛在哪條繩（垂下來的繩要知道是哪一端鬆了）
    });
    if (!r.par.length && !r.mods.length) r.dead = true;     // 哪裡都不靠（格、繩、模型都沒有）⇒ 不畫
  });
}
/** 帆的依靠：最高那一排、最低的前角與後角各找 0.6 公尺內的實心格；找不到就掛在 0.4 公尺內最近的繩（支索）上。 */
function sailAnchors(sh, sail, top) {
  var v = sail.verts, lo = 1e9, fx = null, bx = null, j;
  for (j = 2; j < v.length; j += 3) lo = Math.min(lo, v[j]);
  for (j = 0; j < v.length; j += 3) if (v[j + 2] < lo + 3) { if (!fx || v[j] > fx[0]) fx = [v[j], v[j + 1], v[j + 2]]; if (!bx || v[j] < bx[0]) bx = [v[j], v[j + 1], v[j + 2]]; }
  sail.as = []; sail.par = [];
  [top, fx, bx].forEach(function (P) {
    if (!P) return;
    var a = anchorNear(sh.T, P[0], P[1], P[2], 6);
    if (a >= 0) { if (sail.as.indexOf(a) < 0) sail.as.push(a); return; }
    var best = -1, bd = 16;
    sh.ropes.forEach(function (o, i) {
      var bb = o.bb; if (P[0] < bb[0] - 4 || P[0] > bb[3] + 4 || P[1] < bb[1] - 4 || P[1] > bb[4] + 4 || P[2] < bb[2] - 4 || P[2] > bb[5] + 4) return;
      for (var k = 0; k + 5 < o.pts.length; k += 3) { var d = segDist2(P, o.pts[k], o.pts[k + 1], o.pts[k + 2], o.pts[k + 3], o.pts[k + 4], o.pts[k + 5]); if (d < bd) { bd = d; best = i; } }
    });
    if (best >= 0 && sail.par.indexOf(best) < 0) sail.par.push(best);
  });
  sail.a = sail.as.length ? sail.as[0] : -1;
  return sail;
}
/** 這條繩（r：{ name, meta }）是不是這面帆自己的（帆腳的 sheet、tack）。
 *  照 meta（TASK-0539，造船規格 §9.1；Tim 2026-10-13「之後依 meta 判斷」）：繩的 meta 有 `sail` ⇒ 就是那面帆的（kind sheet／tack）。
 *  沒有 meta 的舊匯出才照名字：`<帆名>.xxx`（basecamp：憲法號、餘燼號）或 `<帆名>-sheet…`／`<帆名>-tack…`（summit：夜隼號）。
 *  ⛔ 只認 `<帆名>-` ⇒ `fore-topsail-lift-S`、`-brace-`、`-footrope-` 這些帆桁的繩也算進來。量過：新規則在憲法號、餘燼號一條都沒多認到。 */
function sailRope(r, sail) {
  if (r && r.meta && r.meta.sail) return r.meta.sail === sail;
  return sailRopeName(r && r.name, sail);
}
function sailRopeName(name, sail) { if (!name) return false; if (name.indexOf(sail + '.') === 0) return true; if (name.indexOf(sail + '-') !== 0) return false; var r = name.slice(sail.length + 1); return /^(sheet|tack)(-|$)/.test(r); }
function ropeBox(p) {
  var b = [1e9, 1e9, 1e9, -1e9, -1e9, -1e9];
  for (var j = 0; j < p.length; j += 3) for (var a = 0; a < 3; a++) { if (p[j + a] < b[a]) b[a] = p[j + a]; if (p[j + a] > b[a + 3]) b[a + 3] = p[j + a]; }
  return b;
}
function anchorNear(T, x, y, z, r) {                 // 船型 T 的原始格子裡，(x, y, z) 附近 r 格內最近的實心格
  var bx = Math.floor(x), by = Math.floor(y), bz = Math.floor(z), best = -1, bd = 1e9;
  for (var dz = -r; dz <= r; dz++) for (var dy = -r; dy <= r; dy++) for (var dx = -r; dx <= r; dx++) {
    if (!T.base.get(bx + dx, by + dy, bz + dz)) continue;
    var d = dx * dx + dy * dy + dz * dz; if (d < bd) { bd = d; best = VK.pack(bx + dx, by + dy, bz + dz); }
  }
  return best;
}
/** 桅（Tim 2026-10-13：照 meta 判斷）：帆桁的 meta `mast`（fore／main／mizzen；bowsprit 不算）⇒ 有哪幾根桅；
 *  那根桅最低的橫帆桁（course／crossjack；沒有 ⇒ 最低一根不是 boom 的）轉軸 (x, z) ⇒ 桅在哪、桅頂平台大約多高（桅頂就在它上面）。
 *  桅身那一段（打斷就倒，32_hull.js survey）＝ 那根帆桁往下 20–40 格（桅頂下面的下桅）；x ＝ 往下 10–40 格、中線上格子最多的那一欄（桅會往後傾）。
 *  z0top ＝ 桅頂水手從這個高度往上找平台（40_crew.js）。
 *  ⛔ 以前從帆的名字推 x、在固定的 z 250–290 找、打斷段三根都是 z 220–240：夜隼號只有一半高 ⇒ 前桅找在 x 223（找到的是別的東西）；
 *  憲法號的後桅頂在 241，250–290 量到的是上桅。改照 meta 之後憲法號、餘燼號的前桅與主桅 x 不變、後桅 195 → 198（下桅）；打斷段變成每根桅自己的高度。
 *  沒有帆桁 meta 的舊 .vxk ⇒ 照以前的辦法（findMastsOld）。 */
function findMasts(T) {
  var CY = T.cy, ys = {}, label = { fore: '前桅', main: '主桅', mizzen: '後桅' }; T.masts = [];
  (T.rig.models || []).forEach(function (m) { var mt = m.meta || {}, pv = (m.points || {}).pivot; if (mt.kind === 'yard' && mt.mast && mt.mast !== 'bowsprit' && pv) (ys[mt.mast] = ys[mt.mast] || []).push({ y: mt.yard, p: pv }); });
  var keys = Object.keys(ys); if (!keys.length) return findMastsOld(T);
  keys.sort(function (a, b) { var o = ['fore', 'main', 'mizzen']; return (o.indexOf(a) + 1 || 9) - (o.indexOf(b) + 1 || 9); });   // 照以前的順序（前、主、後）
  keys.forEach(function (k) {
    var L = ys[k].filter(function (q) { return q.y === 'course' || q.y === 'crossjack'; });
    if (!L.length) L = ys[k].filter(function (q) { return q.y !== 'boom'; }).sort(function (a, b) { return a.p[2] - b.p[2]; });
    if (!L.length) return;
    var P = L[0].p, Lz = Math.floor(P[2]), ax = Math.round(P[0]), mx = ax, bn = 0;
    for (var x = ax - 45; x <= ax + 45; x++) { var c = countBox(T.base, x, CY - 4, Lz - 40, x, CY + 4, Lz - 10); if (c > bn) { bn = c; mx = x; } }
    var z0 = Lz - 40, n = countBox(T.base, mx - 8, CY - 8, z0, mx + 8, CY + 8, z0 + 20);
    if (n > 20) T.masts.push({ name: label[k] || k, x: mx, z0: z0, z1: z0 + 20, orig: n, z0top: Lz });
  });
}
function findMastsOld(T) {  // 桅的 x 從帆的名字推（fore／main／mizzen），探針：桅身中段一小塊
  var acc = {}, CY = T.cy; T.masts = [];
  T.rig.sails.forEach(function (s) {
    var mm = /^(fore|main|mizzen)-(course|topsail|topgallant|royal)$/.exec(s.name); if (!mm) return; var k = mm[1];
    acc[k] = acc[k] || [0, 0];
    for (var j = 0; j < s.verts.length; j += 3) { acc[k][0] += s.verts[j]; acc[k][1]++; }
  });
  var label = { fore: '前桅', main: '主桅', mizzen: '後桅' };
  ['fore', 'main', 'mizzen'].forEach(function (k) {
    if (!acc[k]) return;
    var ax = Math.round(acc[k][0] / acc[k][1]), mx = ax, bn = 0, best = null;
    for (var x = ax - 45; x <= ax + 45; x++) { var c = countBox(T.base, x, CY - 4, 250, x, CY + 4, 290); if (c > bn) { bn = c; mx = x; } }   // 桅身：中線上一根直立的柱子
    for (var z0 = 220; z0 <= 420 && !best; z0 += 20) { var n = countBox(T.base, mx - 8, CY - 8, z0, mx + 8, CY + 8, z0 + 20); if (n > 20) best = { z0: z0, n: n }; }
    if (best) T.masts.push({ name: label[k], x: mx, z0: best.z0, z1: best.z0 + 20, orig: best.n });
  });
}
function countBox(g, x0, y0, z0, x1, y1, z1) { var n = 0; for (var x = x0; x <= x1; x++) for (var y = y0; y <= y1; y++) for (var z = z0; z <= z1; z++) if (g.get(x, y, z)) n++; return n; }
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/11_rig_gpu.js ──
// ───────────────────────── 繩與帆的 GPU 緩衝 ─────────────────────────
function buildRig(owner) {          // 還綁著的繩（靜態，照雕刻作品的形狀）；帆在 sailBuf、垂下來的繩在 looseBuf
  var L = [];
  owner.ropes.forEach(function (r) {
    if (r.dead) return;
    for (var j = 0; j + 5 < r.pts.length; j += 3) L.push(r.pts[j], r.pts[j + 1], r.pts[j + 2], r.col[0], r.col[1], r.col[2], r.pts[j + 3], r.pts[j + 4], r.pts[j + 5], r.col[0], r.col[1], r.col[2]);
  });
  owner.lines = upload(owner.lines, new Float32Array(L), 6, [[0, 3, 0], [2, 3, 3]]);
  owner.rigDirty = false;
}
/** 帆的網格（一個 owner 一份，索引畫）：頂點法線 ＝ 相鄰三角形的面積加權平均 ⇒ 布是圓的，不是一面一面的。
 *  關物理 ⇒ 位置就是雕刻作品那一刻（T.p0），只在 rigDirty 時重做；開物理 ⇒ 每一格畫面重做。
 *  帆的布片（34_shreds.js）接在帆後面、同一個緩衝 ⇒ 陰影、反射照帆畫。 */
var SBV = null, SBI = null, SBN = null, SBP = null;
function sailBuf(ow) {
  var nv = 0, ni = 0, isShip = !!ow.crew, F = isShip && PHYS && ow.shreds && ow.shreds.length ? ow.shreds : null;
  if (F) {                                                               // 緩衝照帆的模板配（30_rig_physics.js clothSetup）；多了布片不夠 ⇒ 加大
    var mv = 0, mi = 0; ow.cl.forEach(function (c) { mv += c.T.n; mi += c.T.tris.length; }); F.forEach(function (f) { mv += f.n; mi += f.T.sim.tris.length; });
    if (SBV.length < mv * 9) SBV = new Float32Array(mv * 12);
    if (SBI.length < mi) SBI = new Uint32Array(Math.ceil(mi * 1.33));
  }
  (ow.cl || []).forEach(function (c, k) {
    if (isShip) { var s = ow.sails[k]; if (PHYS ? (!c.p || c.hidden || c.gone) : (s.dead || s.furled)) return; }
    put((PHYS || !isShip) && c.p ? clothFine(c, SBP) : c.T.p0, c.T.n, c.T.tris, c.T.col, c.torn ? c.tv : null, c.T.vcol);
  });
  if (F) F.forEach(function (f) { put(f.p, f.n, f.T.sim.tris, f.col, null); });
  function put(p, n, tr, col, tv, vc) {                                  // tv：藏起來的細格點（撕開的洞）；vc：每個頂點的顏色（旗的貼圖，30_rig_physics.js texColors）
    var base = nv, j, i;
    SBN.fill(0, 0, n * 3);
    for (j = 0; j < tr.length; j += 3) {
      if (tv && (tv[tr[j]] || tv[tr[j + 1]] || tv[tr[j + 2]])) continue;
      var a = tr[j] * 3, b = tr[j + 1] * 3, d = tr[j + 2] * 3;
      var ux = p[b] - p[a], uy = p[b + 1] - p[a + 1], uz = p[b + 2] - p[a + 2], vx = p[d] - p[a], vy = p[d + 1] - p[a + 1], vz = p[d + 2] - p[a + 2];
      var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      SBN[a] += nx; SBN[a + 1] += ny; SBN[a + 2] += nz; SBN[b] += nx; SBN[b + 1] += ny; SBN[b + 2] += nz; SBN[d] += nx; SBN[d + 1] += ny; SBN[d + 2] += nz;
      SBI[ni++] = base + tr[j]; SBI[ni++] = base + tr[j + 1]; SBI[ni++] = base + tr[j + 2];
    }
    for (i = 0; i < n; i++) {
      var o = (base + i) * 9, q = i * 3;
      SBV[o] = p[q]; SBV[o + 1] = p[q + 1]; SBV[o + 2] = p[q + 2]; SBV[o + 3] = SBN[q]; SBV[o + 4] = SBN[q + 1]; SBV[o + 5] = SBN[q + 2];
      if (vc) { SBV[o + 6] = vc[q]; SBV[o + 7] = vc[q + 1]; SBV[o + 8] = vc[q + 2]; } else { SBV[o + 6] = col[0]; SBV[o + 7] = col[1]; SBV[o + 8] = col[2]; }
    }
    nv += n;
  }
  if (!ow.sb) {
    ow.sb = { vao: gl.createVertexArray(), vbo: gl.createBuffer(), ebo: gl.createBuffer(), n: 0 };
    gl.bindVertexArray(ow.sb.vao); gl.bindBuffer(gl.ARRAY_BUFFER, ow.sb.vbo);
    [[0, 0], [1, 3], [2, 6]].forEach(function (a) { gl.enableVertexAttribArray(a[0]); gl.vertexAttribPointer(a[0], 3, gl.FLOAT, false, 36, a[1] * 4); });
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ow.sb.ebo); gl.bindVertexArray(null);
  }
  gl.bindVertexArray(ow.sb.vao);
  gl.bindBuffer(gl.ARRAY_BUFFER, ow.sb.vbo); gl.bufferData(gl.ARRAY_BUFFER, SBV.subarray(0, nv * 9), gl.DYNAMIC_DRAW);
  gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, SBI.subarray(0, ni), gl.DYNAMIC_DRAW); gl.bindVertexArray(null);
  ow.sb.n = ni;
}
/** 細格的位置：照權重從物理的粗格內插（粗格就是細格 ⇒ 原樣）。 */
function clothFine(c, out) {
  var T = c.T, p = c.p, mi = T.mi, mw = T.mw;
  for (var i = 0; i < T.n; i++) {
    var o = i * 4, x = 0, y = 0, z = 0;
    for (var k = 0; k < 4; k++) { var w = mw[o + k]; if (!w) break; var q = mi[o + k] * 3; x += p[q] * w; y += p[q + 1] * w; z += p[q + 2] * w; }
    out[i * 3] = x; out[i * 3 + 1] = y; out[i * 3 + 2] = z;
  }
  return out;
}
/** 垂下來的繩（物理開著才有）：每一格畫面重做。 */
function looseBuf(sh) {
  var L = [];
  sh.loose.forEach(function (o) {
    var p = o.p, c = o.col;
    for (var i = 0; i + 1 < o.n; i++) { var a = i * 3; L.push(p[a], p[a + 1], p[a + 2], c[0], c[1], c[2], p[a + 3], p[a + 4], p[a + 5], c[0], c[1], c[2]); }
  });
  sh.ll = upload(sh.ll, new Float32Array(L), 6, [[0, 3, 0], [2, 3, 3]]);
}
function upload(o, data, stride, attrs) {
  if (!o) { o = { vao: gl.createVertexArray(), vbo: gl.createBuffer(), n: 0 }; gl.bindVertexArray(o.vao); gl.bindBuffer(gl.ARRAY_BUFFER, o.vbo);
    attrs.forEach(function (a) { gl.enableVertexAttribArray(a[0]); gl.vertexAttribPointer(a[0], a[1], gl.FLOAT, false, stride * 4, a[2] * 4); }); gl.bindVertexArray(null); }
  gl.bindBuffer(gl.ARRAY_BUFFER, o.vbo); gl.bufferData(gl.ARRAY_BUFFER, data, gl.DYNAMIC_DRAW); o.n = data.length / stride;
  return o;
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/12_effects.js ──
// ───────────────────────── 碎片（每格一顆小方塊，GPU instancing） ─────────────────────────
var DMAX = 45000, D = {
  n: 0, p: new Float32Array(DMAX * 3), v: new Float32Array(DMAX * 3), q: new Float32Array(DMAX * 4), w: new Float32Array(DMAX * 3),
  life: new Float32Array(DMAX), size: new Float32Array(DMAX), col: new Uint8Array(DMAX), st: new Uint8Array(DMAX), ship: new Int8Array(DMAX)
};
var DINST = new Float32Array(DMAX * 9);
// 碎木自己的亂數（轉軸、落水、落地）：⛔ 跟戰局共用 rnd() ⇒ 少生一顆碎木（物理分級），後面的亂數全部錯位、整局都變（09_phx.js）。開局跟 rs 一起重設（70_flow.js）
var RSD0 = 0x2545F491, rsD = SEED ^ RSD0, DEB_ACC = 0, PT_ACC = 0;   // DEB_ACC／PT_ACC：照分級少生的節拍（不抽亂數）
function rndD() { rsD |= 0; rsD = rsD + 0x6D2B79F5 | 0; var t = Math.imul(rsD ^ rsD >>> 15, 1 | rsD); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
function spawnDebris(p, v, col, size, life) {
  var k = DEB_KS[PHX.debris]; if (k < 1) { DEB_ACC += k; if (DEB_ACC < 1) return; DEB_ACC -= 1; }   // 物理分級：少生幾顆（呼叫端的亂數已經抽完 ⇒ 戰局不變）
  var i;
  if (D.n < DMAX) i = D.n++;
  else { i = (rndD() * DMAX) | 0; }     // 滿了 ⇒ 隨便頂掉一顆（只影響畫面，不影響模擬判定）
  D.p[i * 3] = p[0]; D.p[i * 3 + 1] = p[1]; D.p[i * 3 + 2] = p[2];
  D.v[i * 3] = v[0]; D.v[i * 3 + 1] = v[1]; D.v[i * 3 + 2] = v[2];
  var ax = norm([rndD() - 0.5, rndD() - 0.5, rndD() - 0.5]), sp = 4 + 14 * rndD();
  D.w[i * 3] = ax[0] * sp; D.w[i * 3 + 1] = ax[1] * sp; D.w[i * 3 + 2] = ax[2] * sp;
  D.q[i * 4] = 0; D.q[i * 4 + 1] = 0; D.q[i * 4 + 2] = 0; D.q[i * 4 + 3] = 1;
  D.life[i] = life; D.size[i] = size; D.col[i] = col; D.st[i] = 1; D.ship[i] = -1;
}
/** 碎木每一步：飛、轉、落水、落在甲板上。
 *  省時間（TASK-0531：殉爆噴一萬多顆，每步 10 ms 以上）：比最高的浪還高 ⇒ 不算 seaH；不在那艘船的格子外接球裡（格子盒的中心＋半對角線）⇒ 不換格座標查格子。結果跟全算一樣。 */
function stepDebris(dt) {
  var top = SEA_K > 0 ? 1.15 * SEA_K * WX.sea : 0, sc = SHIPS.map(function (sh) { var B = sh.T.base; return { c: M4.pt(sh.M, B.sx / 2, B.sy / 2, B.sz / 2), r2: Math.pow(0.5 * S * Math.hypot(B.sx, B.sy, B.sz) + 1, 2) }; });
  for (var i = 0; i < D.n; i++) {
    var st = D.st[i]; if (!st) continue;
    D.life[i] -= dt;
    if (D.life[i] <= 0) { kill(i); i--; continue; }
    var o = i * 3;
    if (st === 2) {                                            // 落在甲板上：跟著船（座標存的是格座標）；底下那一格沒了 ⇒ 重新掉
      var hs = SHIPS[D.ship[i]];
      if (hs.grid.get(D.p[o] | 0, D.p[o + 1] | 0, (D.p[o + 2] | 0) - 1)) continue;
      var wp = M4.pt(hs.M, D.p[o], D.p[o + 1], D.p[o + 2]);
      D.p[o] = wp[0]; D.p[o + 1] = wp[1]; D.p[o + 2] = wp[2]; D.v[o] = D.v[o + 1] = D.v[o + 2] = 0; D.st[i] = st = 1;
    }
    if (st === 1) { D.v[o + 1] -= G * dt; D.v[o] *= 1 - 0.15 * dt; D.v[o + 2] *= 1 - 0.15 * dt; }
    D.p[o] += D.v[o] * dt; D.p[o + 1] += D.v[o + 1] * dt; D.p[o + 2] += D.v[o + 2] * dt;
    // 轉
    var qi = i * 4, qx = D.q[qi], qy = D.q[qi + 1], qz = D.q[qi + 2], qw = D.q[qi + 3], wx = D.w[o] * dt * 0.5, wy = D.w[o + 1] * dt * 0.5, wz = D.w[o + 2] * dt * 0.5;
    var nx = qx + wx * qw + wy * qz - wz * qy, ny = qy + wy * qw + wz * qx - wx * qz, nz = qz + wz * qw + wx * qy - wy * qx, nw = qw - wx * qx - wy * qy - wz * qz, l = Math.hypot(nx, ny, nz, nw);
    D.q[qi] = nx / l; D.q[qi + 1] = ny / l; D.q[qi + 2] = nz / l; D.q[qi + 3] = nw / l;
    if (st === 1) {
      if (D.p[o + 1] < top && D.p[o + 1] < seaH(D.p[o], D.p[o + 2], SIMT)) {               // 落水：慢慢沉
        D.st[i] = 3; D.v[o] *= 0.1; D.v[o + 1] = -0.25; D.v[o + 2] *= 0.1; D.life[i] = Math.min(D.life[i], 4);
        if (rndD() < 0.04) spawnPt(add([D.p[o], 0.05, D.p[o + 2]], [0, 0, 0]), [0, 1.5, 0], 0.5, [0.9, 0.95, 1], 0.6, 0.6, 0, 1);
        wpDrop(D.p[o], D.p[o + 2]);                                     // 船邊水花（13_water.js）：幾滴、偶爾一小片白沫
        continue;
      }
      if (D.v[o + 1] < 0) for (var s = 0; s < SHIPS.length; s++) {       // 掉到甲板上 ⇒ 停住
        var q = sc[s], ex = D.p[o] - q.c[0], ey = D.p[o + 1] - q.c[1], ez = D.p[o + 2] - q.c[2]; if (ex * ex + ey * ey + ez * ez > q.r2) continue;
        var sh = SHIPS[s], L = M4.pt(sh.inv, D.p[o], D.p[o + 1], D.p[o + 2]);
        if (L[0] < 0 || L[2] < 0 || L[0] >= sh.grid.sx) continue;
        if (sh.grid.get(L[0] | 0, L[1] | 0, L[2] | 0)) {
          D.st[i] = 2; D.ship[i] = s; D.p[o] = L[0]; D.p[o + 1] = L[1]; D.p[o + 2] = Math.floor(L[2]) + 1.0 + D.size[i] * 5;
          D.life[i] = Math.min(D.life[i], 25 + 20 * rndD()); break;
        }
      }
    }
  }
}
function kill(i) {
  var j = D.n - 1;
  if (i !== j) {
    D.p.copyWithin(i * 3, j * 3, j * 3 + 3); D.v.copyWithin(i * 3, j * 3, j * 3 + 3); D.w.copyWithin(i * 3, j * 3, j * 3 + 3); D.q.copyWithin(i * 4, j * 4, j * 4 + 4);
    D.life[i] = D.life[j]; D.size[i] = D.size[j]; D.col[i] = D.col[j]; D.st[i] = D.st[j]; D.ship[i] = D.ship[j];
  }
  D.st[j] = 0; D.n--;
}

// ───────────────────────── 粒子（煙、水花、火光、砲彈） ─────────────────────────
var PMAX = 12000, PT = { n: 0, p: new Float32Array(PMAX * 3), v: new Float32Array(PMAX * 3), life: new Float32Array(PMAX), max: new Float32Array(PMAX),
  s0: new Float32Array(PMAX), s1: new Float32Array(PMAX), c: new Float32Array(PMAX * 3), a: new Float32Array(PMAX), grav: new Float32Array(PMAX), drag: new Float32Array(PMAX), ty: new Float32Array(PMAX) };
var PBUF = new Float32Array(PMAX * 9);
function spawnPt(p, v, life, col, a, s0, s1, grav, drag, ty) {
  if (PT_MUTE) return;                               // 船邊水花開著：原本的航跡與水花不放（呼叫端的亂數照樣抽完，13_water.js）
  var k = FX_KS[PHX.fx]; if (k < 1) { PT_ACC += k; if (PT_ACC < 1) return; PT_ACC -= 1; }   // 物理分級：少生幾顆（參數的亂數呼叫端已經抽完）
  if (PT.n >= PMAX) return;
  var i = PT.n++;
  PT.p[i * 3] = p[0]; PT.p[i * 3 + 1] = p[1]; PT.p[i * 3 + 2] = p[2]; PT.v[i * 3] = v[0]; PT.v[i * 3 + 1] = v[1]; PT.v[i * 3 + 2] = v[2];
  PT.life[i] = PT.max[i] = life; PT.c[i * 3] = col[0]; PT.c[i * 3 + 1] = col[1]; PT.c[i * 3 + 2] = col[2]; PT.a[i] = a; PT.s0[i] = s0; PT.s1[i] = s1; PT.grav[i] = grav || 0; PT.drag[i] = drag || 0;
  PT.ty[i] = (ty || 0) * 4 + ((i * 7) & 3);         // 類型 × 4 ＋ 變體
}
function stepPts(dt) {
  for (var i = 0; i < PT.n; i++) {
    PT.life[i] -= dt;
    if (PT.life[i] <= 0) {
      var j = --PT.n;
      if (i !== j) { PT.p.copyWithin(i * 3, j * 3, j * 3 + 3); PT.v.copyWithin(i * 3, j * 3, j * 3 + 3); PT.c.copyWithin(i * 3, j * 3, j * 3 + 3);
        PT.life[i] = PT.life[j]; PT.max[i] = PT.max[j]; PT.a[i] = PT.a[j]; PT.s0[i] = PT.s0[j]; PT.s1[i] = PT.s1[j]; PT.grav[i] = PT.grav[j]; PT.drag[i] = PT.drag[j]; PT.ty[i] = PT.ty[j]; }
      i--; continue;
    }
    var o = i * 3, k = 1 - PT.drag[i] * dt;
    PT.v[o] = PT.v[o] * k + WIND[0] * WX.wind * PT.drag[i] * dt; PT.v[o + 1] = PT.v[o + 1] * k - PT.grav[i] * dt; PT.v[o + 2] = PT.v[o + 2] * k + WIND[2] * WX.wind * PT.drag[i] * dt;   // 天氣：暴風雨煙飄得快
    PT.p[o] += PT.v[o] * dt; PT.p[o + 1] += PT.v[o + 1] * dt; PT.p[o + 2] += PT.v[o + 2] * dt;
    if (PT.grav[i] > 0 && PT.p[o + 1] < 0) PT.life[i] = Math.min(PT.life[i], 0.05);
  }
}
function smoke(p, dir, n, big) {
  for (var i = 0; i < n; i++) {
    var v = add(mul(dir, rr(2, big ? 9 : 14)), [gauss() * 1.2, rr(0.3, 1.6), gauss() * 1.2]);
    var g = rr(0.62, 0.86);
    // 2.5–5.5 秒就散：齊射的煙不要一直擋著看砲彈落點
    spawnPt(add(p, mul(dir, rr(0, 2))), v, rr(2.5, 5.5), [g, g, g * 0.98], rr(0.35, 0.55), rr(1.2, 2.2) * (big ? 1.6 : 1), rr(6, 11) * (big ? 1.5 : 1), -0.05, 1.1, 0);
  }
}
function flash(p, dir, n, big) {
  for (var i = 0; i < n; i++) spawnPt(p, add(mul(dir, rr(5, 30)), [gauss() * 3, gauss() * 3, gauss() * 3]), rr(0.08, 0.22), [1, rr(0.6, 0.85), 0.3], 1, rr(1, 2.5) * (big ? 2 : 1), 0.3, 0, 4, 1);
}
function splash(p, big) {
  PT_MUTE = PHX.water > 0;                         // 船邊水花開著（13_water.js）：下面這些照樣抽亂數、不放進去，換成 wpSplash
  var n = big ? 60 : 26;
  for (var i = 0; i < n; i++) spawnPt([p[0] + gauss() * 0.6, 0.1, p[2] + gauss() * 0.6], [gauss() * 1.6, rr(4, big ? 14 : 10), gauss() * 1.6], rr(0.8, 1.8), [0.92, 0.96, 1], 0.75, rr(0.4, 1.0), rr(0.8, 1.6), G, 0.3, 2);
  for (i = 0; i < 10; i++) spawnPt([p[0] + gauss() * 1.5, 0.15, p[2] + gauss() * 1.5], [gauss() * 0.4, 0.2, gauss() * 0.4], rr(1.5, 3), [0.95, 0.97, 1], 0.35, 1.5, 4, 0, 0.5, 2);
  PT_MUTE = false; wpSplash(p, big);
  sfx('splash', p, big ? 1.2 : 0.7);
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/13_water.js ──
// ───────────────────────── 船周圍的水（TASK-0524） ─────────────────────────
// 水滴（WS）從船身、砲彈落點、擦撞處飛出去，照重力落回海面 ⇒ 變成白沫（WF）；白沫是貼著浪的一片（60_render.js 畫，頂點照 seaHs 跟浪起伏），漂開、變大、散成細條、消失。
// 從哪裡來：
//   · 船身的水線（船型設計水線那一層、船殼最外那一格，兩舷各 48 點；wpRing）——每一步拿這一步與上一步的船矩陣算同一個船上的點的速度：
//     往外推水（水平速度在外法線上的分量 vn）⇒ 船頭浪；船殼對水面往下壓（船的垂直速度 − 水面的垂直速度，vz < 0）⇒ 拍浪（浪頭打上來、船頭栽進浪、沉船也算）。
//     推與拍都留白沫 ⇒ 船頭兩道往外散的白沫線。
//   · 船尾：照航速翻白沫（會轉的一片）、冒一點水滴。
//   · 擦撞（31_sailing.js collide）、砲彈與碎片與落水的人（12_effects.js splash）、碎木落水（stepDebris）。
// ⛔ 只給人看：自己的亂數 rndW（開局跟 rs 一起重設，70_flow.js）、不回寫任何模擬狀態 ⇒ 開與關同一個種子戰局逐字相同。
//   開著的時候，原本的航跡與水花（spawnPt）照樣由呼叫端抽完 rnd()、只是不放進去（PT_MUTE）⇒ 戰局的亂數順序不變。
// 關（09_phx.js「船邊水花」第 0 檔）⇒ 原本的樣子：航跡與水花照舊是 spawnPt 的點。
// 分級：ws／wf 水滴與白沫的上限、k 生的量、pts 每舷幾點、life 白沫活多久的倍率。
var WP_LV = [null, { ws: 2000, wf: 1000, k: 0.45, pts: 16, life: 0.55 }, { ws: 4500, wf: 2200, k: 0.75, pts: 24, life: 0.8 }, { ws: 8000, wf: 4000, k: 1, pts: 48, life: 1 }];
var WS_MAX = 8000, WF_MAX = 4000, WP_RING = 48;
var WS = { n: 0, p: new Float32Array(WS_MAX * 3), v: new Float32Array(WS_MAX * 3), life: new Float32Array(WS_MAX), max: new Float32Array(WS_MAX), s: new Float32Array(WS_MAX), a: new Float32Array(WS_MAX) };
var WF = { n: 0, p: new Float32Array(WF_MAX * 2), v: new Float32Array(WF_MAX * 2), life: new Float32Array(WF_MAX), max: new Float32Array(WF_MAX), s0: new Float32Array(WF_MAX), s1: new Float32Array(WF_MAX),
  a: new Float32Array(WF_MAX), rot: new Float32Array(WF_MAX), w: new Float32Array(WF_MAX), seed: new Float32Array(WF_MAX) };
var WP_HIDE = false, WFBUF = new Float32Array(WF_MAX * 8), WP_STAT = { spray: 0, foam: 0, src: {} }, FOAMG = null;
PBUF = new Float32Array((PMAX + WS_MAX + 64) * 9);          // 點精靈的緩衝多留水滴的份（12_effects.js；60_render.js 一起畫）
var WP_SRC = '', RSW0 = 0x1B873593, rsW = SEED ^ RSW0, PT_MUTE = false;   // PT_MUTE：spawnPt 收到也不放（亂數呼叫端已經抽完）
function rndW() { rsW |= 0; rsW = rsW + 0x6D2B79F5 | 0; var t = Math.imul(rsW ^ rsW >>> 15, 1 | rsW); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
function rgW(a, b) { return a + (b - a) * rndW(); }
function gsW() { var u = rndW() || 1e-9, v = rndW(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(6.2831853 * v); }
function wpLv() { return WP_LV[PHX.water] || null; }
function wsAdd(x, y, z, vx, vy, vz, life, s, a) {
  var L = wpLv(); if (!L || WS.n >= L.ws) return;
  WP_STAT.src[WP_SRC] = (WP_STAT.src[WP_SRC] || 0) + 1;
  var i = WS.n++, o = i * 3;
  WS.p[o] = x; WS.p[o + 1] = y; WS.p[o + 2] = z; WS.v[o] = vx; WS.v[o + 1] = vy; WS.v[o + 2] = vz;
  WS.life[i] = WS.max[i] = life; WS.s[i] = s; WS.a[i] = a; WP_STAT.spray++;
}
function wfAdd(x, z, vx, vz, life, s0, s1, a, w) {
  var L = wpLv(); if (!L) return;
  var i = WF.n < L.wf ? WF.n++ : (rndW() * WF.n) | 0;        // 滿了 ⇒ 隨便頂掉一片（⛔ 不收新的 ⇒ 船尾的舊白沫佔滿，船頭生不出來）
  WF.p[i * 2] = x; WF.p[i * 2 + 1] = z; WF.v[i * 2] = vx; WF.v[i * 2 + 1] = vz;
  WF.life[i] = WF.max[i] = life * L.life; WF.s0[i] = s0; WF.s1[i] = s1; WF.a[i] = a; WF.rot[i] = rndW() * 6.2832; WF.w[i] = w || 0; WF.seed[i] = rndW() * 64; WP_STAT.foam++;
}
/** 船型 T 的水線一圈（設計水線那一層、船殼最外那一格）：兩舷各 WP_RING 點 [x, y, 外法線 nx, ny]（格座標）。第一次用到時算。 */
function wpRing(T) {
  var G = T.base, ZW = T.zw, x0 = T.wl0, x1 = T.wl1, R = new Float32Array(WP_RING * 2 * 4), side, i, y;
  for (side = 0; side < 2; side++) {
    var k = side ? -1 : 1, ys = new Float32Array(WP_RING), xs = new Float32Array(WP_RING);
    for (i = 0; i < WP_RING; i++) {
      var x = Math.round(x0 + (x1 - x0) * (i + 0.5) / WP_RING), yo = T.cy;
      if (k > 0) { for (y = G.sy - 1; y > T.cy; y--) if (G.get(x, y, ZW)) { yo = y + 1; break; } }
      else { for (y = 0; y < T.cy; y++) if (G.get(x, y, ZW)) { yo = y; break; } }
      xs[i] = x + 0.5; ys[i] = yo;
    }
    for (i = 0; i < WP_RING; i++) {
      var a = Math.max(0, i - 1), b = Math.min(WP_RING - 1, i + 1), sl = (ys[b] - ys[a]) / ((xs[b] - xs[a]) || 1), l = Math.hypot(sl, 1), q = (side * WP_RING + i) * 4;
      R[q] = xs[i]; R[q + 1] = ys[i]; R[q + 2] = -k * sl / l; R[q + 3] = k / l;
    }
  }
  return R;
}
/** 每一步（50_sim.js，碎片與粒子之後）：船身與船尾生水花與白沫、水滴落海、白沫漂。關 ⇒ 清空。 */
/** only：'ship' ⇒ 只生（船身與船尾，照模擬的步：wpShip 拿這一步與上一步的船矩陣算速度）；'fly' ⇒ 只飛與散（殉爆慢動作時照畫面的時間走，73_slowmo.js）；沒給 ⇒ 都做。 */
function stepWater(dt, only) {
  var L = wpLv();
  if (!L) { WS.n = WF.n = 0; return; }
  if (only !== 'fly') SHIPS.forEach(function (sh) { wpShip(sh, dt, L); });
  if (only === 'ship') return;
  var hmax = 1.2 * SEA_K * WX.sea + 0.1, i, o, wx = WIND[0] * WX.wind * 0.12 * dt, wz = WIND[2] * WX.wind * 0.12 * dt, kd = 1 - 0.35 * dt;
  for (i = 0; i < WS.n; i++) {
    o = i * 3; WS.life[i] -= dt;
    var dead = WS.life[i] <= 0;
    if (!dead) {
      WS.v[o] = WS.v[o] * kd + wx; WS.v[o + 1] = WS.v[o + 1] * kd - G * dt; WS.v[o + 2] = WS.v[o + 2] * kd + wz;
      WS.p[o] += WS.v[o] * dt; WS.p[o + 1] += WS.v[o + 1] * dt; WS.p[o + 2] += WS.v[o + 2] * dt;
      if (WS.v[o + 1] < 0 && WS.p[o + 1] < hmax && WS.p[o + 1] < seaH(WS.p[o], WS.p[o + 2], SIMT)) {   // 落回海面 ⇒ 有的變成一小片白沫
        dead = true;
        if (WS.s[i] > 0.25 && rndW() < 0.05) wfAdd(WS.p[o], WS.p[o + 2], WS.v[o] * 0.15, WS.v[o + 2] * 0.15, rgW(4, 8), 0.3 + WS.s[i], 1.0 + 3 * WS.s[i], 0.55, 0);
      }
    }
    if (dead) {
      var j = --WS.n;
      if (i !== j) { WS.p.copyWithin(o, j * 3, j * 3 + 3); WS.v.copyWithin(o, j * 3, j * 3 + 3); WS.life[i] = WS.life[j]; WS.max[i] = WS.max[j]; WS.s[i] = WS.s[j]; WS.a[i] = WS.a[j]; }
      i--;
    }
  }
  var kf = 1 - 0.3 * dt;
  for (i = 0; i < WF.n; i++) {
    WF.life[i] -= dt;
    if (WF.life[i] <= 0) {
      var m = --WF.n;
      if (i !== m) { WF.p.copyWithin(i * 2, m * 2, m * 2 + 2); WF.v.copyWithin(i * 2, m * 2, m * 2 + 2); WF.life[i] = WF.life[m]; WF.max[i] = WF.max[m]; WF.s0[i] = WF.s0[m]; WF.s1[i] = WF.s1[m]; WF.a[i] = WF.a[m]; WF.rot[i] = WF.rot[m]; WF.w[i] = WF.w[m]; WF.seed[i] = WF.seed[m]; }
      i--; continue;
    }
    WF.p[i * 2] += WF.v[i * 2] * dt; WF.p[i * 2 + 1] += WF.v[i * 2 + 1] * dt; WF.v[i * 2] *= kf; WF.v[i * 2 + 1] *= kf; WF.rot[i] += WF.w[i] * dt; WF.w[i] *= kf;
  }
}
/** 一艘船：水線一圈的推與拍、船尾翻白沫、沉的時候冒氣。 */
function wpShip(sh, dt, L) {
  var T = sh.T, M = sh.M, Mp = sh.wpM; sh.wpM = M;
  if (!Mp || sh.sink > 30 || !(dt > 0)) return;
  var R = T.wpR || (T.wpR = wpRing(T)), st = WP_RING / L.pts | 0, ds = (T.wl1 - T.wl0) * S / WP_RING * st, zc = clamp(T.zw + (sh.sink - sh.lift - sh.bob) / S, 1, T.sz - 2);
  var acc = sh.wpAcc || (sh.wpAcc = new Float32Array(WP_RING * 4 + 4)), t0 = SIMT - dt;
  for (var q = 0; q < WP_RING * 2; q += st) {
    var r = q * 4, P = M4.pt(M, R[r], R[r + 1], zc), P0 = M4.pt(Mp, R[r], R[r + 1], zc), h = seaH(P[0], P[2], SIMT);
    if (P[1] - h > 0.6) continue;                                                 // 這一刻那一點離開水面（浪谷）⇒ 沒碰到水
    var nw = M4.dir(M, R[r + 2], R[r + 3], 0), nl = Math.hypot(nw[0], nw[2]) || 1, nx = nw[0] / nl, nz = nw[2] / nl;
    var vx = (P[0] - P0[0]) / dt, vy = (P[1] - P0[1]) / dt, vz = (P[2] - P0[2]) / dt, vs = (h - seaH(P[0], P[2], t0)) / dt;
    var vn = vx * nx + vz * nz, push = Math.max(0, vn - 0.35), slam = Math.max(0, vs - vy - 0.3), bw = vn > 0.2 ? 0.3 + 1.2 * (vn - 0.2) : 0;
    if (!(push > 0 || slam > 0 || bw > 0)) continue;
    acc[q] += (push * push * 2.5 + slam * slam * 25) * L.k * ds * dt; WP_SRC = push * push * 2.5 > slam * slam * 25 ? 'push' : 'slam';
    while (acc[q] >= 1) {                                                         // 水滴：往外、往上，帶一點船的速度
      acc[q] -= 1;
      var up = rgW(0.4, 1.1) * (push * 1.3 + slam * 1.7) + 0.3, out = rgW(0.3, 0.9) * vn + rgW(0, 0.6) * slam, cv = rgW(0.3, 0.7);
      var so = rgW(0.8, 1.5);                                                   // 生在船殼外飄的外面（⛔ 貼著水線 ⇒ 從上面看被船頭外飄的船殼蓋住）
      wsAdd(P[0] + nx * so + gsW() * 0.3, h + 0.05, P[2] + nz * so + gsW() * 0.3, nx * out + vx * cv + gsW() * 0.3, up, nz * out + vz * cv + gsW() * 0.3,
        rgW(0.9, 1.6), rgW(0.18, 0.4) * (1 + 0.4 * push), 0.6);
    }
    acc[q + WP_RING * 2] += (bw + slam * 2.0) * L.k * ds * dt;
    while (acc[q + WP_RING * 2] >= 1) {                                           // 白沫：船頭兩道往外散的線
      acc[q + WP_RING * 2] -= 1;
      var fo = rgW(0.8, 2.2);
      wfAdd(P[0] + nx * fo, P[2] + nz * fo, nx * Math.max(vn, 0) * 0.6 + vx * 0.15 + gsW() * 0.12, nz * Math.max(vn, 0) * 0.6 + vz * 0.15 + gsW() * 0.12, rgW(10, 18), rgW(0.5, 0.9), rgW(1.6, 2.8), rgW(0.65, 0.9), 0);
    }
  }
  // 船尾：照航速翻白沫（一片一片會轉）、冒一點水滴
  var sp = Math.abs(sh.spd), k2 = WP_RING * 4; WP_SRC = 'stern';
  if (sp > 0.3 && !sh.sunk) {
    acc[k2] += sp * 2.0 * L.k * dt;
    while (acc[k2] >= 1) {
      acc[k2] -= 1;
      var sx = T.wl0 + rgW(2, 14), sy = T.cy + gsW() * T.bowHalf * 0.3, S0 = M4.pt(M, sx, sy, zc);
      wfAdd(S0[0], S0[2], gsW() * 0.35, gsW() * 0.35, rgW(18, 30), rgW(0.9, 1.6), rgW(2.6, 4.4), rgW(0.5, 0.75), gsW() * 0.6);
    }
    acc[k2 + 1] += sp * 3 * L.k * dt;
    while (acc[k2 + 1] >= 1) {
      acc[k2 + 1] -= 1;
      var B = M4.pt(M, T.wl0 + rgW(1, 8), T.cy + gsW() * T.bowHalf * 0.25, zc), hb = seaH(B[0], B[2], SIMT);
      wsAdd(B[0], hb + 0.05, B[2], gsW() * 0.4, rgW(0.5, 1.6), gsW() * 0.4, rgW(0.8, 1.4), rgW(0.2, 0.35), 0.5);
    }
  }
  // 沉的時候：船殼一圈冒氣、翻大片白沫（往下壓的拍浪由上面那一圈照垂直速度算）
  if (sh.sinkingFinal && sh.sink < 30) {
    WP_SRC = 'sink';
    acc[k2 + 2] += (2 + sh.sinkV * 6) * L.k * dt;
    while (acc[k2 + 2] >= 1) {
      acc[k2 + 2] -= 1;
      var g = (rndW() * WP_RING * 2) | 0, gr = g * 4, C = M4.pt(M, R[gr] - R[gr + 2] * rgW(2, 40), R[gr + 1] - R[gr + 3] * rgW(2, 40), zc), hc = seaH(C[0], C[2], SIMT);
      for (var b = 0; b < 14 * L.k; b++) wsAdd(C[0] + gsW() * 0.6, hc + 0.05, C[2] + gsW() * 0.6, gsW() * 0.8, rgW(1.5, 5), gsW() * 0.8, rgW(0.8, 1.8), rgW(0.25, 0.5), 0.6);
      wfAdd(C[0], C[2], gsW() * 0.4, gsW() * 0.4, rgW(14, 24), rgW(1.5, 2.5), rgW(4, 7), 0.75, gsW() * 0.4);
    }
  }
}
/** 砲彈、碎片、落水的人（12_effects.js splash）：一圈冠狀的水滴、大的再一柱往上衝、落點一圈白沫。 */
function wpSplash(p, big) {
  var L = wpLv(); if (!L) return;
  var h = seaH(p[0], p[2], SIMT), n = (big ? 70 : 28) * L.k, i, a, r, u; WP_SRC = 'splash';
  for (i = 0; i < n; i++) {
    a = rndW() * 6.2832; r = rgW(0.2, 0.6) * (big ? 1.6 : 1); u = rgW(1.2, 3.5) * (big ? 1.4 : 1);
    wsAdd(p[0] + Math.cos(a) * r, h + 0.05, p[2] + Math.sin(a) * r, Math.cos(a) * u, rgW(3, big ? 11 : 7), Math.sin(a) * u, rgW(1.0, 2.4), rgW(0.15, 0.32) * (big ? 1.4 : 1), 0.75);
  }
  if (big) for (i = 0; i < 30 * L.k; i++) wsAdd(p[0] + gsW() * 0.25, h + 0.1, p[2] + gsW() * 0.25, gsW() * 0.6, rgW(7, 17), gsW() * 0.6, rgW(2, 3.5), rgW(0.3, 0.6), 0.8);
  for (i = 0; i < (big ? 14 : 6) * L.k; i++) { a = rndW() * 6.2832; u = rgW(0.6, 1.8); wfAdd(p[0] + Math.cos(a) * 0.5, p[2] + Math.sin(a) * 0.5, Math.cos(a) * u, Math.sin(a) * u, rgW(8, 14), rgW(0.8, 1.4), rgW(2.2, 3.4), 0.75, 0); }
}
/** 碎木落水（12_effects.js stepDebris）：幾滴、偶爾一小片白沫。 */
function wpDrop(x, z) {
  var L = wpLv(); if (!L || rndW() > 0.35 * L.k) return;
  var h = seaH(x, z, SIMT); WP_SRC = 'drop';
  for (var i = 0; i < 3; i++) wsAdd(x, h + 0.03, z, gsW() * 0.5, rgW(1, 3), gsW() * 0.5, rgW(0.5, 0.9), rgW(0.08, 0.15), 0.6);
  if (rndW() < 0.3) wfAdd(x, z, 0, 0, rgW(3, 5), 0.3, 0.8, 0.5, 0);
}
/** 艙內的水從破口往外流（33_flood.js，粒子模式）：洞口往外噴幾滴（量照每秒流出幾 m³）。只給人看。 */
function wpPour(P, out, rate) {
  var L = wpLv(); if (!L) return;
  var ol = Math.hypot(out[0], out[2]) || 1, n = Math.min(6, rate * 2) * L.k; WP_SRC = 'pour';
  for (var i = 0; i < n; i++) { var u = rgW(1, 3); wsAdd(P[0], P[1], P[2], out[0] / ol * u + gsW() * 0.3, rgW(-0.5, 0.8), out[2] / ol * u + gsW() * 0.3, rgW(0.8, 1.4), rgW(0.15, 0.3), 0.7); }
}
/** 擦撞（31_sailing.js collide，貼著的每一步）：兩艘之間往上、往兩舷噴，量照相對速度。 */
function wpBump(pa, pb, A, B) {
  var L = wpLv(); if (!L) return;
  var rel = Math.hypot(A.vel[0] - B.vel[0], A.vel[2] - B.vel[2]), tx = pb[2] - pa[2], tz = pa[0] - pb[0], tl = Math.hypot(tx, tz) || 1, mx = (pa[0] + pb[0]) / 2, mz = (pa[2] + pb[2]) / 2;
  tx /= tl; tz /= tl; WP_SRC = 'bump';
  A.wpBumpAcc = (A.wpBumpAcc || 0) + (40 + 60 * rel) * L.k * DT;
  while (A.wpBumpAcc >= 1) {
    A.wpBumpAcc -= 1;
    var s = gsW() * 4, x = mx + tx * s, z = mz + tz * s, h = seaH(x, z, SIMT), side = rndW() < 0.5 ? -1 : 1, o = rgW(1, 3) * (0.5 + rel);
    wsAdd(x, h + 0.05, z, (pa[0] - pb[0]) / 14 * side * o + gsW() * 0.5, rgW(2, 6) * (0.6 + 0.5 * rel), (pa[2] - pb[2]) / 14 * side * o + gsW() * 0.5, rgW(1.2, 2.2), rgW(0.2, 0.4), 0.7);
    if (rndW() < 0.2) wfAdd(x, z, gsW() * 0.4, gsW() * 0.4, rgW(10, 16), 1.0, 3.0, 0.7, gsW() * 0.5);
  }
}

// ── 畫：白沫是貼著浪的一片（5×5 頂點、每個頂點照 seaHs 起伏，跟海面網格同一個間距）；水滴跟粒子一起畫（點精靈，60_render.js） ──
function wpGL() {
  var N = 4, V = [], I = [], i, j;
  for (j = 0; j <= N; j++) for (i = 0; i <= N; i++) V.push(i / N * 2 - 1, j / N * 2 - 1);
  for (j = 0; j < N; j++) for (i = 0; i < N; i++) { var a = j * (N + 1) + i; I.push(a, a + 1, a + N + 2, a, a + N + 2, a + N + 1); }
  FOAMG = { vao: gl.createVertexArray(), ib: null, inst: gl.createBuffer(), n: I.length };
  gl.bindVertexArray(FOAMG.vao);
  var vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(V), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 8, 0);
  FOAMG.ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, FOAMG.ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(I), gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, FOAMG.inst); gl.bufferData(gl.ARRAY_BUFFER, WFBUF.byteLength, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 4, gl.FLOAT, false, 32, 0); gl.vertexAttribDivisor(1, 1);
  gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 32, 16); gl.vertexAttribDivisor(2, 1);
  gl.bindVertexArray(null);
  // 片段：兩層雜訊 × 圓的邊 ⇒ 一塊一塊的白沫；越舊門檻越高 ⇒ 散成細條。亮度照陽光與陰影（暴風雨暗），霧照距離。船艙裡的丟掉（跟海同一份遮罩）
  P.foam = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec2 aQ; layout(location=1) in vec4 iA; layout(location=2) in vec4 iB; uniform mat4 uVP; uniform vec2 uC, uSG;\n' + SEA_GLSL +
    'out vec2 vQ; out vec3 vW; out float vA; out float vS;\n' +
    'void main(){ float c=cos(iA.w), s=sin(iA.w); vec2 p=iA.xy+vec2(c*aQ.x-s*aQ.y, s*aQ.x+c*aQ.y)*iA.z; float r=length(p-uC);\n' +
    ' float h=seaHs(p,max(uSG.x,r*uSG.y))*(1.0-smoothstep(900.0,1600.0,r)); vW=vec3(p.x,h+0.06,p.y); vQ=aQ; vA=iB.x; vS=iB.y; gl_Position=uVP*vec4(vW,1.0); }\n',
    '#version 300 es\nprecision highp float; in vec2 vQ; in vec3 vW; in float vA; in float vS; uniform vec3 uEye,uFog; uniform float uFogD; out vec4 o;\n' + SHADOW_GLSL + HULL_GLSL +
    'float hs1(float n){ return fract(sin(n*12.9898)*43758.5453); }\n' +
    'float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f); float a=hs1(dot(i,vec2(1.0,57.0))), b=hs1(dot(i+vec2(1.0,0.0),vec2(1.0,57.0))), c=hs1(dot(i+vec2(0.0,1.0),vec2(1.0,57.0))), d=hs1(dot(i+vec2(1.0,1.0),vec2(1.0,57.0))); return mix(mix(a,b,f.x),mix(c,d,f.x),f.y); }\n' +
    'void main(){ if(' + HULL_HIT + ') discard;\n' +
    ' float m=(vn(vQ*1.7+vS)*0.65+vn(vQ*4.3+vS*1.7+3.1)*0.35)*(1.0-smoothstep(0.45,1.0,length(vQ))); float th=mix(0.62,0.22,vA);\n' +
    ' float a=smoothstep(th,th+0.12,m)*(0.35+0.65*vA); if(a<0.01) discard;\n' +
    ' vec3 col=vec3(0.84,0.88,0.9)*(0.55+0.45*shadowK(vW,vec3(0.0,1.0,0.0))); float fd=length(vW-uEye); o=vec4(mix(col,uFog,1.0-exp(-fd*uFogD)),a*0.9); }\n');
}
/** 畫白沫（海之後、粒子之前；不寫深度、往鏡頭拉一點免得跟海面打架）。hullU：船艙遮罩的 uniform（60_render.js，跟海同一份）。 */
function wpDrawFoam(hullU) {
  if (!WF.n || !P.foam || WP_HIDE) return;                               // WP_HIDE：量繪製成本用（__game.water({ hide: true })）
  var n = 0;
  for (var i = 0; i < WF.n; i++) {
    var f = WF.life[i] / WF.max[i], k = n * 8;
    WFBUF[k] = WF.p[i * 2]; WFBUF[k + 1] = WF.p[i * 2 + 1]; WFBUF[k + 2] = WF.s1[i] + (WF.s0[i] - WF.s1[i]) * f; WFBUF[k + 3] = WF.rot[i];
    WFBUF[k + 4] = WF.a[i] * Math.min(1, f * 2.5) * Math.min(1, (1 - f) * 12 + 0.3); WFBUF[k + 5] = WF.seed[i]; n++;
  }
  gl.useProgram(P.foam.prog); setCommon(P.foam); hullU(P.foam);
  var Lv = SEA_LV[GFX.sea];
  gl.uniform2f(P.foam.u.uC, Math.round(CAM.eye[0] / SEAG.snap) * SEAG.snap, Math.round(CAM.eye[2] / SEAG.snap) * SEAG.snap); gl.uniform2f(P.foam.u.uSG, Lv.min, 2 * Math.PI / Lv.seg);
  gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false); gl.enable(gl.POLYGON_OFFSET_FILL); gl.polygonOffset(-2, -8); gl.disable(gl.CULL_FACE);
  gl.bindVertexArray(FOAMG.vao); gl.bindBuffer(gl.ARRAY_BUFFER, FOAMG.inst); gl.bufferSubData(gl.ARRAY_BUFFER, 0, WFBUF, 0, n * 8);
  gl.drawElementsInstanced(gl.TRIANGLES, FOAMG.n, gl.UNSIGNED_SHORT, 0, n);
  gl.disable(gl.POLYGON_OFFSET_FILL); gl.depthMask(true);
}
/** 水滴放進點精靈的緩衝（60_render.js 的 pushPt）：天暗的時候跟著暗。 */
function wpPushSpray(pushPt) {
  if (!WS.n || WP_HIDE) return;
  var b = 0.55 + 0.45 * WX.sun, c = [0.9 * b, 0.94 * b, 0.98 * b];
  for (var i = 0; i < WS.n; i++) { var f = WS.life[i] / WS.max[i]; pushPt([WS.p[i * 3], WS.p[i * 3 + 1], WS.p[i * 3 + 2]], WS.s[i] * (1.3 - 0.3 * f), c, WS.a[i] * Math.min(1, f * 3), -1); }
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/14_rain.js ──
// ───────────────────────── 3D 雨滴（暴風雨 × 畫質的「雨滴（3D）」） ─────────────────────────
// Tim 2026-10-13：暴風雨的雨放進 3D 空間（平面的雨絲，不做立體的水滴）；畫質「高」用它取代整個畫面一層的雨（01_gl.js P.rain），
//   而且是畫質設定裡獨立的一項 ⇒ 自訂也能單獨開關（兩種一起開也行）。
// 雨滴住在鏡頭前方一個直立的圓柱裡：圓心 ＝ 鏡頭往看的方向水平推 RD_R × 0.6、半徑 RD_R、從海面到鏡頭上方 RD_TOP 公尺。
//   落速 RD_VY ×（0.88–1.12）＋ 風（風向 × 現在的風速 × RD_WK —— 照風速全斜，暴風雨的風會把雨絲吹到快躺平）；畫成沿速度方向的一條線（長 ＝ 速度 × RD_STREAK 秒）。
//   Tim 2026-10-13：雨絲拉長、落快一點 ⇒ 落速 9 → 15 m/s（比真的雨快：畫面上才看得出是雨）、線長 0.4 → 約 1 m。
//   跑出圓柱（鏡頭移走）⇒ 在圓柱裡重撒；落到海面（seaH）或打到船（格子有東西）⇒ 從頂上重生，鏡頭 30 m 內冒一個小水花（點精靈，RD_SPL 秒；畫質的「雨滴水花」可關）。
//   鏡頭 1.5 m 內與圓柱邊上的淡掉（太近的雨絲會橫過整個畫面、邊上的一進一出會閃）；遠的照霧。
// 每一格畫面走一次（90_main.js frame，畫面的 dt）；停格、說明打開時不動；縮圖（?still=1）不動 ⇒ 同一格畫面。
// 數量：少／中／多 ＝ RD_N（Tim 2026-10-13：原本 3000／6000／12000 太密 ⇒ 減半）。12000 滴量過：每一格走 0.95 ms、填緩衝＋畫 0.87 ms。
// ⛔ 只給人看：自己的亂數 rndR、不碰模擬的狀態（step() 讀不到）⇒ 開關不改戰局。
var RD_N = [0, 1500, 3000, 6000], RD_R = 45, RD_TOP = 28, RD_VY = 15, RD_WK = 0.35, RD_STREAK = 0.07, RD_SPL = 0.22, RS_MAX = 900;
var RD = { n: 0, p: null, k: null, c: [0, 0], top: 30, v: [0, -RD_VY, 0], buf: null, vao: null, vbo: null, drawn: 0 };
var RS = { n: 0, p: new Float32Array(RS_MAX * 3), life: new Float32Array(RS_MAX) }, rsR = 0x51ED270B, RD_STAT = { hitSea: 0, hitShip: 0 };
PBUF = new Float32Array(PBUF.length + RS_MAX * 9);          // 點精靈的緩衝多留雨的水花（60_render.js 一起畫）
function rndR() { rsR |= 0; rsR = rsR + 0x6D2B79F5 | 0; var t = Math.imul(rsR ^ rsR >>> 15, 1 | rsR); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
function rdCount() { return WX.rain > 0 ? RD_N[GFX.drops] || 0 : 0; }
function rdGL() {
  P.drop = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec3 aP; layout(location=1) in float aA; uniform mat4 uVP; uniform vec3 uEye; out float vA; out float vD;\n' +
    'void main(){ vA=aA; vD=length(aP-uEye); gl_Position=uVP*vec4(aP,1.0); }\n',
    '#version 300 es\nprecision highp float; in float vA; in float vD; uniform vec3 uCol,uFog; uniform float uFogD; out vec4 o;\n' +
    'void main(){ o=vec4(mix(uCol,uFog,1.0-exp(-vD*uFogD)),vA); }\n');
  RD.vao = gl.createVertexArray(); gl.bindVertexArray(RD.vao); RD.vbo = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, RD.vbo);
  RD.buf = new Float32Array(RD_N[RD_N.length - 1] * 8); gl.bufferData(gl.ARRAY_BUFFER, RD.buf.byteLength, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 16, 0); gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 1, gl.FLOAT, false, 16, 12);
  gl.bindVertexArray(null);
}
/** 第 i 滴撒在圓柱裡：top ⇒ 從頂上（剛落海、打到船的），否則整段高度隨便一處（開始下雨、鏡頭移走）。 */
function rdSpawn(i, top) {
  var a = rndR() * 6.2832, r = RD_R * Math.sqrt(rndR()), o = i * 3;
  RD.p[o] = RD.c[0] + Math.cos(a) * r; RD.p[o + 2] = RD.c[1] + Math.sin(a) * r;
  RD.p[o + 1] = top ? RD.top - rndR() * 3 : -1 + rndR() * (RD.top + 1); RD.k[i] = 0.88 + 0.24 * rndR();
}
function rdSplash(x, y, z) {
  if (!GFX.dropspl) return;
  var e = CAM.eye; if ((x - e[0]) * (x - e[0]) + (z - e[2]) * (z - e[2]) > 900) return;
  var i = RS.n < RS_MAX ? RS.n++ : (rndR() * RS_MAX) | 0;
  RS.p[i * 3] = x; RS.p[i * 3 + 1] = y; RS.p[i * 3 + 2] = z; RS.life[i] = RD_SPL;
}
/** 每一格畫面（停格、縮圖不走）：雨滴往下落、跟著風斜；圓柱跟著鏡頭。 */
function stepRain(dt) {
  var N = rdCount(), i;
  if (!N) { RD.n = RS.n = 0; return; }
  if (!RD.p || RD.p.length < N * 3) { RD.p = new Float32Array(N * 3); RD.k = new Float32Array(N); RD.n = 0; }
  var e = CAM.eye, l = CAM.look || CAM.tgt, dx = l[0] - e[0], dz = l[2] - e[2], dl = Math.hypot(dx, dz) || 1;
  RD.c = [e[0] + dx / dl * RD_R * 0.6, e[2] + dz / dl * RD_R * 0.6]; RD.top = Math.max(e[1], 8) + RD_TOP;
  if (RD.n !== N) { RD.n = N; for (i = 0; i < N; i++) rdSpawn(i, false); }
  var wl = Math.hypot(WIND[0], WIND[2]) || 1, ws = windKnots() / 1.944 * RD_WK, vx = WIND[0] / wl * ws, vz = WIND[2] / wl * ws, R2 = RD_R * RD_R, p = RD.p, cx = RD.c[0], cz = RD.c[1];
  RD.v = [vx, -RD_VY, vz];
  for (i = 0; i < N; i++) {
    var o = i * 3, k = RD.k[i] * dt, x = p[o] + vx * k, y = p[o + 1] - RD_VY * k, z = p[o + 2] + vz * k;
    if ((x - cx) * (x - cx) + (z - cz) * (z - cz) > R2) { rdSpawn(i, false); continue; }
    if (y < 8) { var sea = seaH(x, z, SIMT); if (y < sea) { rdSplash(x, sea, z); RD_STAT.hitSea++; rdSpawn(i, true); continue; } }
    var hit = false;
    for (var s = 0; s < SHIPS.length && !hit; s++) {
      var sh = SHIPS[s], cc = sh.center; if (!cc || (x - cc[0]) * (x - cc[0]) + (y - cc[1]) * (y - cc[1]) + (z - cc[2]) * (z - cc[2]) > sh.rad2) continue;
      var L = M4.pt(sh.inv, x, y, z); if (sh.grid.get(L[0] | 0, L[1] | 0, L[2] | 0)) hit = true;
    }
    if (hit) { rdSplash(x, y, z); RD_STAT.hitShip++; rdSpawn(i, true); continue; }
    p[o] = x; p[o + 1] = y; p[o + 2] = z;
  }
  if (!GFX.dropspl) RS.n = 0;
  for (i = 0; i < RS.n; i++) if ((RS.life[i] -= dt) <= 0) { var j = --RS.n; RS.p.copyWithin(i * 3, j * 3, j * 3 + 3); RS.life[i] = RS.life[j]; i--; }
}
/** 水花（60_render.js 的點精靈那一批）：一個淡白的小圓點，冒一下就散。 */
function rdPushSplash(pushPt) {
  if (!RD.n) return;
  for (var i = 0; i < RS.n; i++) { var f = RS.life[i] / RD_SPL; pushPt([RS.p[i * 3], RS.p[i * 3 + 1] + (1 - f) * 0.2, RS.p[i * 3 + 2]], 0.12 + 0.22 * (1 - f), [0.86, 0.9, 0.95], 0.5 * f); }
}
/** 雨絲（60_render.js，點精靈之後、整個畫面那一層雨之前）：做深度測試（船擋得住）、不寫深度、半透明。顏色照天色（閃電時跟著亮）。 */
function rdDraw() {
  var N = RD.n; if (!N) { RD.drawn = 0; return; }
  var b = RD.buf, p = RD.p, e = CAM.eye, v = RD.v, cx = RD.c[0], cz = RD.c[1], m = 0;
  for (var i = 0; i < N; i++) {
    var o = i * 3, x = p[o], y = p[o + 1], z = p[o + 2], d = Math.hypot(x - e[0], y - e[1], z - e[2]);
    var a = 0.34 * Math.min(1, (d - 1.5) / 3) * Math.min(1, (RD_R - Math.hypot(x - cx, z - cz)) / 6); if (a <= 0) continue;
    var t = RD_STREAK * RD.k[i], q = m * 8;
    b[q] = x; b[q + 1] = y; b[q + 2] = z; b[q + 3] = a; b[q + 4] = x - v[0] * t; b[q + 5] = y - v[1] * t; b[q + 6] = z - v[2] * t; b[q + 7] = a * 0.35; m++;
  }
  RD.drawn = m; if (!m) return;
  gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false);
  gl.useProgram(P.drop.prog); setCommon(P.drop); var c = lerp3(SKY, [0.82, 0.86, 0.9], 0.55); gl.uniform3f(P.drop.u.uCol, c[0], c[1], c[2]);
  gl.bindVertexArray(RD.vao); gl.bindBuffer(gl.ARRAY_BUFFER, RD.vbo); gl.bufferSubData(gl.ARRAY_BUFFER, 0, b, 0, m * 8);
  gl.drawArrays(gl.LINES, 0, m * 2); gl.depthMask(true);
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/20_shatter.js ──
// ───────────────────────── 拆格：砲彈打碎船殼 ─────────────────────────
var HARD = { 36: 3.5, 146: 3.5 };   // 鐵（砲身、錨、鑄鐵灰）比木頭難打穿
function removeVoxel(sh, x, y, z, seeds) {
  var c = sh.grid.set(x, y, z, 0);
  if (c <= 0) return 0;
  sh.rs.touch(x, y, z); sh.lost++;
  if (z < sh.T.sz) { sh.flood[z * 3]++; sh.flood[z * 3 + 1] += y > sh.T.cy ? 1 : -1; sh.flood[z * 3 + 2] += x > sh.T.cx ? 1 : -1; }
  if (sh.fl) floodTouch(sh, x, y, z);                                   // 粒子模式：水格與破口待重算（33_flood.js）
  if (seeds) { var s = sh.seeds; s.push(VK.pack(x + 1, y, z), VK.pack(x - 1, y, z), VK.pack(x, y + 1, z), VK.pack(x, y - 1, z), VK.pack(x, y, z + 1), VK.pack(x, y, z - 1)); }
  return c;
}
/** 一塊被打碎：形狀不規則（順著船長方向的木紋拉長、邊緣參差）、外緣有幾條順紋裂開；碎屑往砲彈前進的方向噴。回：打掉幾格的「硬度和」。 */
function shatter(sh, c, dirL, R, velW, debrisCap, grainK) {
  var cost = 0, n = 0, rI = Math.ceil(R * 1.6), cx = Math.floor(c[0]), cy = Math.floor(c[1]), cz = Math.floor(c[2]);
  var removed = [];
  for (var dz = -rI; dz <= rI; dz++) for (var dy = -rI; dy <= rI; dy++) for (var dx = -rI; dx <= rI; dx++) {
    var x = cx + dx, y = cy + dy, z = cz + dz, d = Math.sqrt(dx * dx * grainK + dy * dy + dz * dz);
    if (d > R * (0.6 + 0.62 * hash3(x, y, z))) continue;
    var col = removeVoxel(sh, x, y, z, true);
    if (col) { cost += HARD[col] || 1; n++; removed.push(x, y, z, col); }
  }
  // 順紋裂開：外緣挑幾點，沿船長方向把同色的那一條撕掉
  for (var k = 0; k < 3 && n > 8; k++) {
    var a = rnd() * 6.2832, rx = cx + Math.round(Math.cos(a) * R * 1.25), rzz = cz + Math.round(Math.sin(a) * R * 0.9), ry = cy, base = 0;
    for (var dyy = 0; dyy < 5 && !base; dyy++) { ry = cy + [0, 1, -1, 2, -2][dyy]; base = sh.grid.get(rx, ry, rzz); }
    if (!base) continue;
    var dirx = Math.cos(a) < 0 ? -1 : 1, L = (rr(3, 11)) | 0;
    for (var t = 0; t < L; t++) { var xx = rx + dirx * t; if (sh.grid.get(xx, ry, rzz) !== base) break; var cc = removeVoxel(sh, xx, ry, rzz, true); if (cc) { removed.push(xx, ry, rzz, cc); cost += 1; n++; } }
  }
  // 碎屑
  var keep = removed.length / 4, pr = Math.min(1, debrisCap / Math.max(1, keep)), sp = len(velW), vd = norm(velW);
  for (var j = 0; j < removed.length; j += 4) {
    if (rnd() > pr) continue;
    var w = M4.pt(sh.M, removed[j] + 0.5, removed[j + 1] + 0.5, removed[j + 2] + 0.5);
    var v = add(add(mul(vd, sp * rr(0.03, 0.2)), [gauss() * 3.2, rr(0.5, 5), gauss() * 3.2]), sh.vel);
    spawnDebris(w, v, removed[j + 3], rr(0.05, 0.11), rr(6, 14));
  }
  sh.impulse = add(sh.impulse, mul(vd, n));
  return { cost: cost, n: n };
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/21_gunnery.js ──
// ───────────────────────── 砲彈 ─────────────────────────
function fireGun(sh, g, target, ammo) {
  if (sh.struck || !g.alive || g.reload > 0 || gunRate(g) <= 0) return false;      // 砲要有人操作；降旗了就不開（排在齊射裡還沒開的也一樣）
  if (!bears(sh, g, target)) return false;                            // 目標不在這門砲的砲門射界 ⇒ 不開（呼叫端先用 gunTarget 挑好這門打得到的點）
  var mw = M4.pt(sh.M, g.muz[0], g.muz[1], g.muz[2]);
  var side = gunAxis(sh, g);
  var GS = GUNS[g.type], V = GS.V;                                    // 初速照砲種（carronade：32 磅、短砲身 ⇒ 初速低、彈大）
  var foe = aimShip(sh), rel = sub(foe.vel, sh.vel);              // 前置量：砲彈帶著本艦的船速 ⇒ 瞄對方「相對本艦」飛行時間後的位置（瞄的那艘，52_fleet.js）
  target = add(target, mul(rel, Math.hypot(target[0] - mw[0], target[2] - mw[2]) / V));
  var dx = target[0] - mw[0], dz = target[2] - mw[2], dy = target[1] - mw[1], d = Math.hypot(dx, dz);
  var v2 = V * V, disc = v2 * v2 - G * (G * d * d + 2 * dy * v2);
  var el = disc < 0 ? 0.26 : Math.atan((v2 - Math.sqrt(disc)) / (G * d));
  var az = Math.atan2(dz, dx), saz = Math.atan2(side[2], side[0]), da = Math.atan2(Math.sin(az - saz), Math.cos(az - saz));
  da = clamp(da, -0.45, 0.45); az = saz + da;                      // 砲門只容得下 ±26°
  var spread = sh.i === PLAYER_I && !AUTOFIRE ? 0.0045 : sh.aiSpread || 0.008;
  if (!sh.crew.some(function (c) { return c.role === ROLE.OFFICER && able(c); })) spread *= 1.7;   // 軍官全倒 ⇒ 沒人指揮，瞄得散
  spread *= [0.7, 0.75, 0.85, 1][sh.sailSet];                       // 帆收得越多，船越穩
  spread *= wxSpread(sh);                                          // 天氣：暴風雨裡船晃得越快，點火那一下差得越多（晴天 ×1）
  el = clamp(el + gauss() * spread, -0.17, 0.26); az += gauss() * spread;
  var dir = [Math.cos(el) * Math.cos(az), Math.sin(el), Math.cos(el) * Math.sin(az)];
  var b = { p: mw.slice(), v: add(mul(dir, V * rr(0.985, 1.015)), sh.vel), owner: sh.i, ammo: ammo, trav: 0, alive: true, age: 0, bounced: false, big: GS.big, hole: GS.hole, dmg: DMG[g.type] };   // dmg：每發傷害（砲種，細節設定）；hole：洞的倍率（4 磅彈小）
  BALLS.push(b); g.reload = sh.reloadT * GS.reload * rr(0.9, 1.1); g.firedAt = SIMT; sh.fired++;
  g.needCart = true;                                                // 下一發要從砲旁的藥箱拿一份火藥與彈藥（沒有 ⇒ 等送藥手，23_powder.js）
  flash(add(mw, mul(dir, 1)), dir, 14, false); smoke(add(mw, mul(dir, 1.5)), dir, 10, false);
  sh.rollV += g.side === 'P' ? 0.0012 : -0.0012;                      // 後座：船往反方向晃一下（開火那一舷抬起；roll 正 ＝ 右舷 S 那邊往下）
  sfx('boom', mw, sh.i === PLAYER_I ? 1 : 0.8);
  return true;
}
/** 齊射：各砲平行開火 —— 瞄準點跟著那門砲在船上的前後位置平移，整排落在對方船身上（⛔ 不是 14 發擠進同一個洞）。 */
function broadside(sh, ammo, careful) {                            // careful：電腦開的 ⇒ 隔著友船的那門不開（52_fleet.js；玩家自己按的照開）
  if (sh.struck) return 0;
  var k = 0, mid = 0, n = 0;
  sh.guns.forEach(function (g) { mid += g.muz[0]; n++; }); mid /= n || 1;
  var tgt = aimPoint(sh), FK = careful ? friendKeels(sh) : [];
  sh.guns.forEach(function (g) {
    if (!g.alive || g.reload > 0 || gunRate(g) <= 0 || !gunTarget(sh, g, tgt)) return;   // 兩舷都看：每一門自己判定，有機會打中敵艦的才排進齊射
    if (FK.length && friendInLine(FK, M4.pt(sh.M, g.muz[0], g.muz[1], g.muz[2]), tgt)) { sh.ffHold = (sh.ffHold || 0) + 1; return; }
    var off = (g.muz[0] - mid) * S * (ammo === 2 ? 0.15 : 1);      // 鏈彈是對著桅杆打的 ⇒ 往瞄準點收攏
    EVENTS.push({ t: SIMT + k * 0.075 + rr(0, 0.03), sh: sh.i, g: g, ammo: ammo, off: off }); k++;   // 瞄準點在開火那一刻才算（兩艘都在動）
  });
  if (k) { sh.salvo++; sh.salvoT = SIMT; }
  return k;
}
function fireOne(sh, ammo) {
  if (sh.struck) return;
  var tgt = aimPoint(sh), best = null, bd = 1e9;
  sh.guns.forEach(function (g) { if (!g.alive || g.reload > 0 || gunRate(g) <= 0 || !gunTarget(sh, g, tgt)) return; var w = M4.pt(sh.M, g.muz[0], g.muz[1], g.muz[2]), d = len(sub(w, tgt)); if (d < bd) { bd = d; best = g; } });
  if (best) fireGun(sh, best, gunTarget(sh, best, tgt), ammo);
}
/** 這門砲的砲軸（世界、水平）：模型的固定點 muzzle − breech（舷側砲 ＝ 那一舷的正橫；追擊砲 ＝ 正橫偏船頭 20°）。 */
function gunAxis(sh, g) {
  var a = M4.dir(sh.M, g.ax[0], g.ax[1], 0);
  return norm([a[0], 0, a[2]]);
}
/** 這門砲對不對得到 w：從砲口量，跟它的砲軸夾角 < 0.45 rad（砲門 ±26°）。 */
function bears(sh, g, w) {
  var m = M4.pt(sh.M, g.muz[0], g.muz[1], g.muz[2]), ax = gunAxis(sh, g);
  var a = Math.atan2(w[2] - m[2], w[0] - m[0]) - Math.atan2(ax[2], ax[0]);
  return Math.abs(Math.atan2(Math.sin(a), Math.cos(a))) < 0.45;
}
/** 這門砲打哪裡（每一門自己判定）：對得到 w ⇒ w；對不到 ⇒ 敵艦船身上（水線上那一段的中線、跟 w 同高，取 13 點）
 *  這門砲射界內、離 w 最近的那一點；整艘都在射界外 ⇒ null。⇒ 瞄準點在射界外，只要還有機會打中敵艦就開。 */
function gunTarget(sh, g, w) {
  if (bears(sh, g, w)) return w;
  var foe = aimShip(sh); if (!foe || !foe.M) return null;
  var z = clamp(toLocal(foe, w)[2], foe.T.geo.aimZ[0], foe.T.geo.aimZ[1]), best = null, bd = 1e18;   // 高度範圍照敵艦的船型（05_hull.js GEO0）
  for (var k = 0; k <= 12; k++) {
    var p = M4.pt(foe.M, foe.T.wl0 + 15 + (foe.T.wl1 - foe.T.wl0 - 30) * k / 12, foe.T.cy, z);
    if (!bears(sh, g, p)) continue;
    var d = (p[0] - w[0]) * (p[0] - w[0]) + (p[2] - w[2]) * (p[2] - w[2]); if (d < bd) { bd = d; best = p; }
  }
  return best;
}
/** 有沒有哪一門（還在、有人操作的）砲有機會打中敵艦（瞄準 w；對不到 w 就看敵艦船身）；side 給了只看那一舷。 */
function anyBears(sh, w, side) { return sh.guns.some(function (g) { return g.alive && gunRate(g) > 0 && (!side || g.side === side) && !!gunTarget(sh, g, w); }); }
function shipAxis(sh) { var ax = M4.dir(sh.M, 1, 0, 0); return norm([ax[0], 0, ax[2]]); }
function aimPoint(sh) {
  var foe = foeOf(sh);
  if (sh.i === PLAYER_I && !AUTOFIRE && sh.pMode && sh.pMode !== 'free') { var t = modeAim(foe, sh.pMode, false).t; return M4.pt(foe.M, t[0], t[1], t[2]); }   // 我艦手動的瞄準模式：那個模式的中心點（51_captain.js）
  if (sh.aim) { var on = aimShip(sh); return M4.pt(on.M, sh.aim[0], sh.aim[1], sh.aim[2]); }   // 瞄準點是那艘的格座標
  return M4.pt(foe.M, foe.T.cx, foe.T.cy, foe.T.geo.aim);
}

/** 砲彈這一步（每 5 cm 一小段：450 m/s 的彈一步 150 段）。
 *  省時間（TASK-0531：開戰第一輪對砲幾十顆彈同時飛，每格 240–320 ms，掉到 15 FPS 以下；判定一個都不能變）：
 *    · 海面：比最高的浪（七道振幅和 1.14 m × 浪 × 天氣）還高就不可能落水 ⇒ 不算 seaH。
 *    · 繩、帆、人、模型：進了某艘船的外接球，先挑出「這一步飛得到的範圍」（這一點起算、這一步最多飛 sp × dt）裡的（ballNear），
 *      後面的小段只看這幾個（順序照原本的；模型照原本的桶、只是跳過沒挑到的）⇒ 判定與亂數順序跟全看一模一樣。量過：同一個種子戰局讀數逐字相同。
 *    量過（觀戰種子 1797，第一輪對砲最慢的一格）：繩 120–160 → 12–17 ms、人 40–46 → 1–2 ms（之後再加帆與模型）。 */
function stepBall(b, dt) {
  b.age += dt;
  var sp = len(b.v), steps = Math.max(1, Math.ceil(sp * dt / 0.05)), h = dt / steps, top = SEA_K > 0 ? 1.15 * SEA_K * WX.sea : 0, near = null;
  for (var s = 0; s < steps && b.alive; s++) {
    b.v[1] -= G * h;
    b.p[0] += b.v[0] * h; b.p[1] += b.v[1] * h; b.p[2] += b.v[2] * h; b.trav += len(b.v) * h;
    var sea = b.p[1] < top ? seaH(b.p[0], b.p[2], SIMT) : -1e9;         // 水面跟著浪（08_sea.js）；比最高的浪還高 ⇒ 不用算
    if (b.p[1] < sea) {
      var spd = len(b.v), ang = Math.asin(-b.v[1] / spd);
      if (b.ammo === 0 && !b.bounced && ang < 0.11 && spd > 90) {       // 打水漂：低角度的實心彈會跳一下
        b.v[1] = -b.v[1] * 0.45; b.v[0] *= 0.7; b.v[2] *= 0.7; b.p[1] = sea + 0.01; b.bounced = true; splash(b.p, false); continue;
      }
      splash(b.p, true); b.alive = false; return;
    }
    for (var i = 0; i < SHIPS.length; i++) {
      var sh = SHIPS[i];
      if (i === b.owner && b.trav < 6) continue;
      var cc = sh.center, dx = b.p[0] - cc[0], dy = b.p[1] - cc[1], dz = b.p[2] - cc[2];
      if (dx * dx + dy * dy + dz * dz > sh.rad2) continue;
      var L = M4.pt(sh.inv, b.p[0], b.p[1], b.p[2]), nb = (near || (near = []))[i] || (near[i] = ballNear(sh, L, sp * dt));
      var hm = hitModel(sh, L, b.ammo === 2 ? 10 : 1.5, b.hitM, nb.id);          // 同一顆砲彈對同一個模型只算一次（穿過外框要好幾個小步；⛔ 每步都扣 ⇒ 一發扣好幾次血）
      if (hm) {                                                          // 打到模型：扣血（每發傷害 × 彈種對砲倍率；歸零整個飛出去），砲彈被擋掉一大半
        if (sh.i !== b.owner && !b.hitOnce) { SHIPS[b.owner].hits++; ffHit(sh, b); b.hitOnce = true; }
        (b.hitM = b.hitM || []).push(hm);
        damageModel(sh, hm, b.v, b.dmg * ammoK(b.ammo, VS_GUN));
        if (b.ammo === 1) { explode(b.p.slice(), sh, 0); blastModels(sh, L, 22, b.p, b.hitM, b.dmg); hurt(sh, L, 13, 30, null, '爆炸', crewBase(b)); b.alive = false; return; }   // 直接打中的那一門已經扣過，不再吃爆風
        b.v = mul(b.v, b.ammo === 2 ? 0.5 : 0.55);
        if (len(b.v) < 30) { ballToDebris(b); return; }
      }
      if (b.ammo === 2) cutRig(sh, L, 14, b, nb.ropes, nb.sails);
      else if ((s & 3) === 0) cutRig(sh, L, 3, b, nb.ropes, nb.sails);             // 實心與爆裂：細繩照斷、穿過帆會打洞（帆扣得少，見彈種倍率）
      if ((s & 3) === 1 && sh.i !== b.owner) hurt(sh, L, 4, 0, null, '砲彈', crewBase(b) * 2, nb.crew);      // 砲彈直接掠過：兩倍
      if (!sh.grid.get(L[0] | 0, L[1] | 0, L[2] | 0)) {
        if (b.ammo !== 2) continue;
        // 鏈彈：兩顆彈中間一條鏈、轉著飛，約 2.4 公尺寬 ⇒ 沿那條橫桿取樣，碰到哪裡就從哪裡咬下去
        var dL = norm(M4.dir(sh.inv, b.v[0], b.v[1], b.v[2])), sd = norm(cross(dL, [0, 0, 1])), hitL = null;
        for (var q = -12; q <= 12 && !hitL; q += 3) { var Lq = [L[0] + sd[0] * q, L[1] + sd[1] * q, L[2]]; if (sh.grid.get(Lq[0] | 0, Lq[1] | 0, Lq[2] | 0)) hitL = Lq; }
        if (!hitL) continue;                                              // 橫掃是以彈心為中心 ⇒ 照彈心那一點咬
      }
      impact(b, sh, L);
      if (!b.alive) return;
    }
  }
  if (b.age > 12) b.alive = false;
}
function impact(b, sh, L) {
  var dirL = norm(M4.dir(sh.inv, b.v[0], b.v[1], b.v[2])), sp = len(b.v), r, w = b.p.slice();
  if (sh.i !== b.owner) { SHIPS[b.owner].hits += (b.hitOnce ? 0 : 1); if (!b.hitOnce) ffHit(sh, b); } b.hitOnce = true;
  if (b.ammo === 1) {                                                   // 爆裂彈：第一下就炸
    r = shatter(sh, L, dirL, rr(10, 13) * Math.pow(sh.cfg.hard, -0.3), mul(b.v, 0.05), 650, 0.85);
    explode(w, sh, r.n); blastModels(sh, L, 22, w, null, b.dmg); hurt(sh, L, 13, 30, null, '爆炸', crewBase(b)); b.alive = false; return;
  }
  if (b.ammo === 2) {                                                   // 鏈彈：橫著的一片
    r = slab(sh, L, dirL, b);
    b.v = mul(b.v, Math.max(0, 1 - r.cost * 0.004 * sh.cfg.hard));
    if (r.n) hurt(sh, L, 9, 16, dirL, '鏈彈', crewBase(b));
    if (len(b.v) < 30) { ballToDebris(b); }
    if (r.n > 30) { sfx('crack', w, 0.9); smoke(w, [0, 0.2, 0], 3, false); }
    return;
  }
  var R = rr(3.4, 4.6) * (b.big ? 1.25 : b.hole || 1) * Math.pow(sh.cfg.hard, -0.25);
  r = shatter(sh, L, dirL, R, b.v, 260, 0.55);   // 實心彈：一口一口往裡鑽（carronade 的 32 磅彈洞大一點；越硬洞越小）
  if (r.n) hurt(sh, L, R * 1.1, R * 2.6, dirL, '碎木', crewBase(b));             // 碎木往前噴：船裡的人主要是被這個傷到的
  var nsp = sp - r.cost * 0.24 * sh.cfg.hard;
  if (r.n > 0) { sfx('crack', w, 0.6 + Math.min(1, r.n / 200)); if (r.n > 40) smoke(w, mul(norm(b.v), -0.3), 2, false); }
  if (nsp < 28) { ballToDebris(b); return; }
  b.v = mul(b.v, nsp / sp);
}
/** 格座標 L 落在哪個還在的模型外框裡（外擴 m 格）。 */
function hitModel(sh, L, m, skip, nb) {                                 // skip：這顆砲彈已經打過的（略過它、找後面那一個）；nb：只看蓋了這個戳記的（stepBall 的 ballNear；沒給 ⇒ 全看）
  var bk = L[0] >= 0 ? sh.mIdx[Math.floor(L[0] / 16)] : null; if (!bk) return null;   // 只看這一桶（modelIndex；登記時外擴 12 格 ≥ 鏈彈的 10）
  for (var i = 0; i < bk.length; i++) {
    if (nb && bk[i].nb !== nb) continue;
    var o = bk[i], b = o.bb, Q = o.rot ? unrotL(o, L) : L;                 // 轉過的帆桁：把彈點轉回作品裡的角度再比
    if (o.alive && !(skip && skip.indexOf(o) >= 0) && Q[0] > b[0] - m && Q[0] < b[3] + m && Q[1] > b[1] - m && Q[1] < b[4] + m && Q[2] > b[2] - m && Q[2] < b[5] + m &&
        (m > 2 || inMesh(o, Q))) return o;                               // 實心／爆裂彈：外框裡還要真的碰到砲身或砲架（鏈彈橫掃 2.4 m ⇒ 外框就算）
  }
  return null;
}
/** 繞帆桁的轉軸（鉛直）把格座標轉 a（弧度；+x 轉向 +y 為正，跟雕刻引擎同一個方向）。 */
function rotZ(P, piv, a) { var c = Math.cos(a), s = Math.sin(a), x = P[0] - piv[0], y = P[1] - piv[1]; return [piv[0] + x * c - y * s, piv[1] + x * s + y * c, P[2]]; }
function unrotL(o, L) { return rotZ(L, o.piv, -o.rot); }
/** 模型在船的格座標裡的擺法：平移到 origin；帆桁另外繞轉軸轉 rot。 */
function modelLocal(m) {
  if (!m.rot || !m.piv) return trans(m.origin[0], m.origin[1], m.origin[2]);
  var p = m.piv;
  return M4.mul(M4.mul(M4.mul(trans(p[0], p[1], p[2]), rotM([0, 0, 1], m.rot)), trans(-p[0], -p[1], -p[2])), trans(m.origin[0], m.origin[1], m.origin[2]));
}
/** 格座標 L 在不在這個模型的網格裡（佔用格，外擴一格 ≈ 砲彈半徑）。⛔ 只看外框：長砲的外框 1.3 × 3.1 m，空的角落也算 ⇒ 砲甲板一半的彈都打得到砲。 */
function inMesh(o, L) {
  var oc = o.T.meshes[o.mesh] && o.T.meshes[o.mesh].occ; if (!oc) return true;
  var x = Math.floor(L[0] - o.origin[0]) + 1, y = Math.floor(L[1] - o.origin[1]) + 1, z = Math.floor(L[2] - o.origin[2]) + 1;
  return x >= 0 && y >= 0 && z >= 0 && x < oc.nx && y < oc.ny && z < oc.nz && oc.a[x + oc.nx * (y + oc.ny * z)] === 1;
}
/** 網格 ⇒ 佔用格（每格 0.1 m，座標跟網格一樣相對模型的 origin、整體位移一格）：三角形每 0.4 格取一點，往法線反方向半格那一格算實心；再外擴一格。 */
function meshOcc(m) {
  var v = m.verts, mx = [0, 0, 0], j, a;
  for (j = 0; j < v.length; j += 3) for (a = 0; a < 3; a++) mx[a] = Math.max(mx[a], v[j + a]);
  var nx = Math.ceil(mx[0]) + 3, ny = Math.ceil(mx[1]) + 3, nz = Math.ceil(mx[2]) + 3, s = new Uint8Array(nx * ny * nz), o = new Uint8Array(nx * ny * nz);
  function mark(x, y, z) { x = Math.floor(x) + 1; y = Math.floor(y) + 1; z = Math.floor(z) + 1; if (x >= 0 && y >= 0 && z >= 0 && x < nx && y < ny && z < nz) s[x + nx * (y + ny * z)] = 1; }
  for (j = 0; j < m.tris.length; j += 3) {
    var A = m.tris[j] * 3, B = m.tris[j + 1] * 3, C = m.tris[j + 2] * 3;
    var e1 = [v[B] - v[A], v[B + 1] - v[A + 1], v[B + 2] - v[A + 2]], e2 = [v[C] - v[A], v[C + 1] - v[A + 1], v[C + 2] - v[A + 2]], n = norm(cross(e1, e2));
    var st = Math.max(1, Math.ceil(Math.max(len(e1), len(e2), len(sub(e1, e2))) / 0.4));
    for (var p = 0; p <= st; p++) for (var q = 0; q <= st - p; q++) {
      var u = p / st, w = q / st;
      mark(v[A] + e1[0] * u + e2[0] * w - n[0] * 0.5, v[A + 1] + e1[1] * u + e2[1] * w - n[1] * 0.5, v[A + 2] + e1[2] * u + e2[2] * w - n[2] * 0.5);
    }
  }
  for (var z = 0; z < nz; z++) for (var y = 0; y < ny; y++) for (var x = 0; x < nx; x++) {
    if (!s[x + nx * (y + ny * z)]) continue;
    for (var dz = -1; dz <= 1; dz++) for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++) {
      var X = x + dx, Y = y + dy, Z = z + dz; if (X >= 0 && Y >= 0 && Z >= 0 && X < nx && Y < ny && Z < nz) o[X + nx * (Y + ny * Z)] = 1;
    }
  }
  var cnt = 0; for (j = 0; j < o.length; j++) cnt += o[j];
  return { nx: nx, ny: ny, nz: nz, a: o, fill: cnt / o.length };
}
/** 模型整個飛出去：剛體（拋出、翻滾、落水）；綁在它身上的砲與繩一起失效。drop ＝ 腳下甲板沒了，只是掉下去。 */
function blowModel(sh, m, vel, drop) {
  if (!m.alive) return;
  m.alive = false;
  var M0 = M4.mul(sh.M, modelLocal(m)), c0 = M4.pt(sh.M, m.c[0], m.c[1], m.c[2]);
  var vd = norm(vel), sp = drop ? 0 : clamp(len(vel) * 0.07, 5, 16);
  FLY.push({ T: sh.T, mesh: m.mesh, M0: M0, c0: c0, c: c0.slice(), R: M4.ident(), t: 0, wet: false,
    v: add(drop ? [0, -0.5, 0] : add(mul(vd, sp), [gauss() * 2, rr(4, 9), gauss() * 2]), sh.vel),
    w: drop ? [gauss() * 0.4, 0, gauss() * 0.4] : [gauss() * 4, gauss() * 4, gauss() * 4] });
  sh.guns.forEach(function (g) { if (g.model === m) g.alive = false; });
  sh.ropes.forEach(function (r) { if (!r.dead && r.mods && r.mods.indexOf(m.k) >= 0) { r.dead = true; sh.rigDirty = true; } });
  if (!drop && m.kind !== 'powder') {
    hurt(sh, m.c, 7, 15, null, '砲被打飛', 140);
    flash(c0, vd, 10, false);
    for (var i = 0; i < 14; i++) spawnPt(c0, add(mul(vd, rr(3, 12)), [gauss() * 4, rr(1, 6), gauss() * 4]), rr(0.2, 0.5), [1, 0.85, 0.5], 1, 0.25, 0.1, G, 0.5, 3);
    sfx('crack', c0, 1.3);
  }
  if (m.kind === 'wheel') note(sh, '舵輪被打飛了');
  else if (m.kind === 'rudder') note(sh, drop ? '舵掉了' : '舵被打飛了');
  else if (m.kind === 'yard' && !drop) note(sh, '帆桁 ' + m.name.replace('yard-', '') + ' 被打斷');
  else if (GUNS[m.kind]) newsGun(sh, m, drop);                    // 廣播（同一刻好幾門 ⇒ 併成一行，見 61_hud.js）
}
/** 模型被打中：扣血（細節設定的砲血量；舵輪 6 成），歸零才整個飛出去。還撐得住 ⇒ 火星、聲音、旁邊的人被碎片波及。
 *  火藥桶另走 powderHit（歸零殉爆；拉滿 ＝ 不會爆 ⇒ 不扣）。 */
function damageModel(sh, m, vel, dmg) {
  if (!m.alive || !(dmg > 0)) return;
  if (m.kind === 'powder') { powderHit(sh, m, dmg); return; }
  if (m.gun) boxHit(sh, m.gun, dmg);                                    // 砲旁的藥箱（23_powder.js）
  m.hp -= dmg;
  if (m.hp <= 0) { blowModel(sh, m, vel); return; }
  var c0 = M4.pt(sh.M, m.c[0], m.c[1], m.c[2]), vd = norm(vel);
  for (var i = 0; i < 8; i++) spawnPt(c0, add(mul(vd, rr(-6, -2)), [gauss() * 3, rr(1, 4), gauss() * 3]), rr(0.15, 0.35), [1, 0.8, 0.45], 1, 0.2, 0.08, G, 0.5, 3);
  hurt(sh, m.c, 3, 8, null, '碎木', dmg * 0.7);
  sfx('crack', c0, 0.8);
}
/** 爆炸：r 格內的模型往外飛。傷害 ＝ 每發傷害 × 爆裂彈對砲倍率 × (1 − 0.75·d／r)。skip：直接打中的那一門（已經扣過）。 */
function blastModels(sh, L, r, w, skip, dmg) {
  var k = (dmg || 100) * ammoK(1, VS_GUN);
  sh.models.forEach(function (m) {
    if (!m.alive || (skip && skip.indexOf(m) >= 0)) return;
    var d = len(sub(m.c, L)); if (d > r) return;
    var cw = M4.pt(sh.M, m.c[0], m.c[1], m.c[2]);
    damageModel(sh, m, mul(norm(sub(cw, w)), 200 * (1 - d / r) + 60), k * (1 - 0.75 * d / r));
  });
}
/** 對人的基準傷害：1.4 × 每發傷害 × 彈種對人倍率（24 磅實心 ⇒ 140 ⇒ 碎木錐裡約 85% 當場陣亡，跟以前一樣）。 */
function crewBase(b) { return 1.4 * b.dmg * ammoK(b.ammo, VS_CREW); }
function stepFly(f, dt) {
  f.t += dt;
  f.v[1] -= G * dt;
  if (f.c[1] < seaH(f.c[0], f.c[2], SIMT)) {
    if (!f.wet) { f.wet = true; splash(f.c, true); }
    f.v = mul(f.v, 1 - 2.5 * dt); f.v[1] = Math.max(f.v[1], -1.0); f.w = mul(f.w, 1 - 2 * dt);
  }
  f.c = add(f.c, mul(f.v, dt));
  var a = len(f.w) * dt; if (a > 0) f.R = M4.mul(rotM(f.w, a), f.R);
  f.M = M4.mul(M4.mul(M4.mul(trans(f.c[0], f.c[1], f.c[2]), f.R), trans(-f.c0[0], -f.c0[1], -f.c0[2])), f.M0);
  return f.t < 25 && f.c[1] > -25;
}
function buildMeshes(H, C) {      // 船型 H 的每份模型網格一個 VAO：三角形展開、平面法線、材質色（P.tri 畫）；C ＝ 快取的 [{ tri, occ }]（06_cache.js）
  H.meshes = []; var keep = [];
  (H.rig.meshes || []).forEach(function (m, k) {
    var d = C ? C[k] : { tri: meshTris(m), occ: meshOcc(m) };
    var up = upload(null, d.tri, 9, [[0, 3, 0], [1, 3, 3], [2, 3, 6]]);
    up.occ = d.occ; H.meshes.push(up); keep.push(d);
  });
  if (H.keep) H.keep.models = keep;
}
function meshTris(m) {
  var v = m.verts, T = [];
  for (var j = 0; j < m.tris.length; j += 3) {
    var a = m.tris[j] * 3, b = m.tris[j + 1] * 3, d = m.tris[j + 2] * 3, c = m.mats[m.tmat[j / 3]];
    var n = norm(cross([v[b] - v[a], v[b + 1] - v[a + 1], v[b + 2] - v[a + 2]], [v[d] - v[a], v[d + 1] - v[a + 1], v[d + 2] - v[a + 2]]));
    T.push(v[a], v[a + 1], v[a + 2], n[0], n[1], n[2], c[0], c[1], c[2], v[b], v[b + 1], v[b + 2], n[0], n[1], n[2], c[0], c[1], c[2],
           v[d], v[d + 1], v[d + 2], n[0], n[1], n[2], c[0], c[1], c[2]);
  }
  return new Float32Array(T);
}
function ballToDebris(b) { spawnDebris(b.p, mul(b.v, 0.3), 36, 0.15, 20); b.alive = false; }
function slab(sh, L, dirL, b) {
  var side = norm(cross(dirL, [0, 0, 1])), cost = 0, n = 0, removed = [];
  for (var a = -13; a <= 13; a++) for (var h = -2; h <= 2; h++) for (var d = -2; d <= 2; d++) {
    if (Math.abs(a) > (10.5 + 2.5 * hash3(a, h, d + (L[2] | 0))) * Math.pow(sh.cfg.hard / 2, -0.25)) continue;   // 越硬撕開的那一片越窄
    var x = Math.floor(L[0] + side[0] * a + dirL[0] * d), y = Math.floor(L[1] + side[1] * a + dirL[1] * d), z = Math.floor(L[2] + h);
    var c = removeVoxel(sh, x, y, z, true); if (c) { cost += (HARD[c] || 1) * 2.4; n++; removed.push(x, y, z, c); }
  }
  for (var j = 0; j < removed.length; j += 4) if (rnd() < 0.5) {
    var w = M4.pt(sh.M, removed[j] + 0.5, removed[j + 1] + 0.5, removed[j + 2] + 0.5);
    spawnDebris(w, add(add(mul(norm(b.v), rr(4, 20)), [gauss() * 3, rr(0, 4), gauss() * 3]), sh.vel), removed[j + 3], rr(0.05, 0.11), rr(6, 12));
  }
  sh.impulse = add(sh.impulse, mul(norm(b.v), n * 2));
  return { cost: cost, n: n };
}
function explode(w, sh, n) {
  flash(w, [0, 1, 0], 50, true);
  for (var i = 0; i < 26; i++) spawnPt(w, [gauss() * 7, rr(1, 9), gauss() * 7], rr(0.3, 0.8), [1, rr(0.45, 0.7), 0.15], 0.9, rr(1.5, 3), rr(3, 5), 0, 2.5, 3);
  smoke(w, [0, 1, 0], 22, true); sfx('blast', w, 1.4);
}
/** 這顆彈這一步在 sh 上飛得到的範圍（格座標 L 起算、最多再飛 reach 公尺）裡的繩、帆、人、模型：碰得到這個範圍（再外擴 16 格 ≥ 斷繩的 14、
 *  傷人的 4、帆的 8、模型的 10）的才留，順序照原本的。繩與帆與模型的外框、帆桁的角度、人的位置在砲彈這一段都不會變（帆桁轉、人走路在別段）⇒ 用一整步。
 *  跟著帆桁轉的（帆、帆桁模型）：判定時把彈點繞轉軸轉回作品的角度 ⇒ 離轉軸的水平距離不變 ⇒ 用圓柱挑（轉軸到範圍的水平距離 ≤ 外框四角離轉軸最遠的 ＋ 外擴 × 1.5）。
 *  模型不另外列：蓋戳記（o.nb ＝ 這一次的編號），hitModel 照原本的桶走、沒戳記的跳過 ⇒ 打到哪一個的先後跟原本一樣。 */
var NB_ID = 0;
function ballNear(sh, L, reach) {
  var H = (reach + 0.5) / S + 16, xa = L[0] - H, xb = L[0] + H, ya = L[1] - H, yb = L[1] + H, za = L[2] - H, zb = L[2] + H, id = ++NB_ID;
  function box(bb, r) { return bb[0] - r <= xb && bb[3] + r >= xa && bb[1] - r <= yb && bb[4] + r >= ya && bb[2] - r <= zb && bb[5] + r >= za; }
  function cyl(p, bb, r) {
    if (bb[2] - r > zb || bb[5] + r < za) return false;
    var R = 0; [[bb[0], bb[1]], [bb[3], bb[1]], [bb[0], bb[4]], [bb[3], bb[4]]].forEach(function (q) { R = Math.max(R, Math.hypot(q[0] - p[0], q[1] - p[1])); });
    var dx = Math.max(xa - p[0], 0, p[0] - xb), dy = Math.max(ya - p[1], 0, p[1] - yb);
    return Math.hypot(dx, dy) <= R + r * 1.5;
  }
  sh.models.forEach(function (o) { if (o.alive && (o.rot && o.piv ? cyl(o.piv, o.bb, 10) : box(o.bb, 10))) o.nb = id; });
  return { id: id,
    ropes: sh.ropes.filter(function (rp) { return !rp.dead && box(rp.bb, 0); }),
    sails: sh.sails.filter(function (s) { var y0 = s.yards && s.yards[0]; return !s.dead && !s.furled && (y0 ? cyl(y0.piv, s.bb, 8) : box(s.bb, 8)); }),
    crew: sh.crew.filter(function (c) { var p = c.pos; return p[0] >= xa && p[0] <= xb && p[1] >= ya && p[1] <= yb && p[2] + 9 >= za && p[2] + 9 <= zb; }) };
}
/** 經過的繩（距離 < r 格）斷掉；鏈彈穿過帆 ⇒ 帆掉下來。ropes／sails：只看這幾條、這幾面（stepBall 先挑好的，ballNear；沒給 ⇒ 全部）。 */
function cutRig(sh, L, r, b, ropes, sails) {
  var r2 = r * r, changed = false;
  (ropes || sh.ropes).forEach(function (rp) {
    if (rp.dead) return;
    var bb = rp.bb;
    if (L[0] < bb[0] - r || L[0] > bb[3] + r || L[1] < bb[1] - r || L[1] > bb[4] + r || L[2] < bb[2] - r || L[2] > bb[5] + r) return;
    var p = rp.pts;
    for (var j = 0; j + 5 < p.length; j += 3) {
      if (segDist2(L, p[j], p[j + 1], p[j + 2], p[j + 3], p[j + 4], p[j + 5]) < r2) { rp.dead = true; rp.cutL = [L[0], L[1], L[2]]; changed = true; break; }   // cutL：垂下來的繩從這裡分成兩段
    }
  });
  // 帆：鏈彈纏上（彈心 0.8 m 內有頂點）；實心與爆裂穿過（0.4 m 內）也扣、打個小洞。扣 ＝ 每發傷害 × 彈種對帆倍率
  var chain = b.ammo === 2, rs2 = chain ? 64 : 16, rb = chain ? 8 : 4;
  (sails || sh.sails).forEach(function (s) {
    if (s.dead || s.furled) return;
    var v = s.verts, sb = s.bb;
    if (b.sails && b.sails.indexOf(s) >= 0) return;                    // 同一顆彈穿過一面帆要好幾個小步 ⇒ 只算一次（記帆本身：兩艘的同編號帆是不同的帆）
    // 帆跟著帆桁轉過 ⇒ 彈點轉回作品的角度再比（撕洞、布片照真正的彈點）。帆頂照自己的帆桁、帆腳照 footYard（course 沒有 ⇒ 0），中間照高度內插
    var y0 = s.yards && s.yards[0], aH = y0 ? y0.rot : 0, aF = s.footYard ? s.footYard.rot : 0, a = aF + (aH - aF) * clamp((L[2] - sb[2]) / Math.max(1, sb[5] - sb[2]), 0, 1);
    var Ls = y0 && a ? rotZ(L, y0.piv, -a) : L;
    if (Ls[0] < sb[0] - rb || Ls[0] > sb[3] + rb || Ls[1] < sb[1] - rb || Ls[1] > sb[4] + rb || Ls[2] < sb[2] - rb || Ls[2] > sb[5] + rb) return;
    for (var j = 0; j < v.length; j += chain ? 9 : 3) { var dx = v[j] - Ls[0], dy = v[j + 1] - Ls[1], dz = v[j + 2] - Ls[2]; if (dx * dx + dy * dy + dz * dz < rs2) {
      tearCloth(sh, s, L, chain ? 7 : 3, b); s.hp -= b.dmg * ammoK(b.ammo, VS_SAIL); (b.sails = b.sails || []).push(s);
      if (s.hp <= 0) dropSail(sh, s, true); else if (chain) shredSail(sh, s, L);   // 歸零才掉；還撐得住 ⇒ 撕下幾片（鏈彈）、少一份推力
      changed = true; break; } }
  });
  if (changed) sh.rigDirty = true;
}
function segDist2(p, ax, ay, az, bx, by, bz) {
  var vx = bx - ax, vy = by - ay, vz = bz - az, wx = p[0] - ax, wy = p[1] - ay, wz = p[2] - az, l2 = vx * vx + vy * vy + vz * vz;
  var t = l2 > 0 ? clamp((wx * vx + wy * vy + wz * vz) / l2, 0, 1) : 0, dx = wx - vx * t, dy = wy - vy * t, dz = wz - vz * t;
  return dx * dx + dy * dy + dz * dz;
}
/** 帆掉了：變成十來片大塊的平面布片（點精靈，不是 3D 碎屑 —— 不撞甲板、不轉四元數），飄著往下掉、碰水就沒。
 *  物理開著 ⇒ 布留著，掛在還綁著的地方擺（全鬆了就往下掉）；被打穿的那一塊已經在 tearCloth 變成真的布片（34_shreds.js）⇒ 不撒點精靈。
 *  ⛔ 亂數照抽、只是不撒 ⇒ 開或關物理，後面的亂數序列一樣（戰局不變）。 */
function dropSail(owner, s, torn) {
  s.dead = true; owner.rigDirty = true; sailLinesDie(owner, s);
  if (s.furled) return;                                              // 收在帆桁上的：跟著掉，沒有布片
  var cl = PHYS && owner.cl ? owner.cl[s.k] : null;
  if (cl && (!cl.p || cl.gone)) cl = null;
  if (cl) { cl.loose = true; clothPins(owner, s, cl); }
  var M = owner.M, v = s.verts, nv = v.length / 3, n = clamp(Math.round(nv / 90), 6, 16), c = s.col || [0.95, 0.92, 0.85];
  for (var k = 0; k < n; k++) {
    var j = ((rnd() * nv) | 0) * 3, w = M4.pt(M, v[j], v[j + 1], v[j + 2]), sz = rr(1.6, 3), t = rr(0.85, 1);
    var vel = [gauss() * 1.5, rr(-0.5, 1.5), gauss() * 1.5], life = rr(5, 9);
    if (!cl) spawnPt(w, vel, life, [c[0] * t, c[1] * t, c[2] * t], 1, sz, sz * 0.85, 3, 1.2, 4);   // 終端速度 ≈ 3／1.2 ＝ 2.5 m/s，跟著風飄
  }
}
/** 帆被打中但還撐得住：撕下幾片布（不掉）。物理開著、布在 ⇒ tearCloth 已經撕下真的布片（34_shreds.js），這裡照樣抽亂數、不放（PT_MUTE）。 */
function shredSail(owner, s, L) {
  var w = M4.pt(owner.M, L[0], L[1], L[2]), c = s.col || [0.95, 0.92, 0.85], cl = owner.cl && owner.cl[s.k];
  PT_MUTE = !!(PHYS && cl && cl.p);
  for (var k = 0; k < 3; k++) { var sz = rr(1.2, 2.2); spawnPt(w, [gauss() * 1.5, rr(-0.5, 1.5), gauss() * 1.5], rr(4, 7), c, 1, sz, sz * 0.85, 3, 1.2, 4); }
  PT_MUTE = false;
}
function sailLinesDie(owner, s) { (s.lines || []).forEach(function (j) { owner.ropes[j].dead = true; }); owner.rigDirty = true; }
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/22_pieces.js ──
// ───────────────────────── 斷開的一團：倒下、落水 ─────────────────────────
function isAnchor(x, y, z) { return z <= 12; }   // 龍骨（龍骨是直的 ⇒ 整條都在最底下）
function integrity(sh) {
  if (!sh.seeds.length) return;
  var seeds = sh.seeds; sh.seeds = [];
  var anchor = sh.keel ? function (x, y, z) { return z <= 12 && x >= sh.keel[0] && x <= sh.keel[1]; } : isAnchor;   // 船斷成兩截之後：龍骨的錨只留長的那半截（23_powder.js breakShip）
  var pieces = VK.detached(sh.grid, seeds, anchor, 900000);
  pieces.forEach(function (pc) { spawnPiece(sh, pc); });
}
function spawnPiece(sh, pc) {
  var n = pc.length, i, x, y, z, c;
  if (n < 40) {                                               // 小碎塊直接變碎屑
    for (i = 0; i < n; i++) { x = pc[i] & 1023; y = (pc[i] >> 10) & 1023; z = pc[i] >> 20; c = removeVoxel(sh, x, y, z, false);
      if (c) spawnDebris(M4.pt(sh.M, x + 0.5, y + 0.5, z + 0.5), add([gauss(), rr(-0.5, 1), gauss()], sh.vel), c, rr(0.06, 0.1), rr(8, 16)); }
    return;
  }
  var g = new VK.Grid([sh.T.base.sx, sh.T.base.sy, sh.T.base.sz]), sx = 0, sy = 0, sz = 0, minz = 1e9, set = new Set();
  for (i = 0; i < n; i++) {
    x = pc[i] & 1023; y = (pc[i] >> 10) & 1023; z = pc[i] >> 20; c = removeVoxel(sh, x, y, z, false);
    if (!c) continue; g.set(x, y, z, c); sx += x; sy += y; sz += z; if (z < minz) minz = z; set.add(pc[i]);
  }
  var px = 0, py = 0, pz = 0, pn = 0;
  for (i = 0; i < n; i++) { z = pc[i] >> 20; if (z <= minz + 2) { px += (pc[i] & 1023); py += (pc[i] >> 10) & 1023; pz += z; pn++; } }
  var rs2 = new VK.RegionSet(gl, g, QIDX); rsAllDirty(rs2);                 // 網格分批建（60_render.js remesh；⛔ buildAll ⇒ 十萬格的半截船那一格卡上百 ms）
  var M0 = sh.M, c0 = M4.pt(M0, sx / n + 0.5, sy / n + 0.5, sz / n + 0.5), pivot = M4.pt(M0, px / pn + 0.5, py / pn + 0.5, pz / pn);
  var imp = sh.impulse; imp = [imp[0], 0, imp[2]]; if (len(imp) < 1e-6) imp = [rnd() - 0.5, 0, rnd() - 0.5];
  var axis = norm(cross([0, 1, 0], norm(imp)));
  var piece = { T: sh.T, grid: g, rs: rs2, M0: M0, c0: c0, c: c0.slice(), R: M4.ident(), v: [0, 0, 0], w: mul(axis, rr(0.18, 0.35)), pivot: pivot, n: n,
    hinge: c0[1] - pivot[1] > 2.5, t: 0, wet: false, ropes: [], cl: [], rigDirty: true, lines: null, mods: [] };
  if (sh.keel && n > 60000) {                                 // 斷成兩截的那半截船：不繞斷口倒 —— 帶著船速漂、斷口那頭往下、慢慢沉
    var fw = M4.dir(sh.M, 1, 0, 0), sideK = (sx / n) > sh.breakX ? 1 : -1;
    piece.hinge = false; piece.hull = norm(mul(cross([fw[0], 0, fw[2]], [0, 1, 0]), sideK)); piece.v = sh.vel.slice();
  }
  // 繩與帆跟著走：兩端都在這一團 ⇒ 帶走（moved：不變成垂下來的繩）；只有一端 ⇒ 斷
  var moved = new Set();
  sh.ropes.forEach(function (r, j) {
    if (r.dead || r.par) return;
    var ia = set.has(r.a), ib = set.has(r.b);
    if (ia && ib) { piece.ropes.push({ pts: r.pts, col: r.col, bb: r.bb }); r.dead = true; r.moved = true; moved.add(j); }
    else if (ia || ib) r.dead = true;
  });
  sh.ropes.forEach(function (r, j) {
    if (r.dead || !r.par) return;
    var ends = [r.a, r.b].filter(function (a) { return a >= 0; });
    if (r.par.length && r.par.every(function (k) { return moved.has(k); }) && ends.every(function (a) { return set.has(a); })) { piece.ropes.push({ pts: r.pts, col: r.col, bb: r.bb }); r.dead = true; r.moved = true; moved.add(j); }
    else if (r.par.some(function (k) { return moved.has(k); }) || ends.some(function (a) { return set.has(a); })) r.dead = true;
  });
  sh.sails.forEach(function (s) {           // 依靠全在這一團（格在、掛的繩也被帶走）⇒ 跟著倒；只有一部分 ⇒ 掉下來
    if (s.dead) return;
    if (!s.furled && s.par.some(function (j) { return sh.ropes[j].dead && !moved.has(j); })) { dropSail(sh, s); return; }   // 掛的支索這一下斷了（沒被帶走）⇒ 現在就掉，不等下一次 survey；收著的帆不怕
    var inA = s.as.filter(function (a) { return set.has(a); }).length, inP = s.par.filter(function (j) { return moved.has(j); }).length;
    if (!inA && !inP) return;
    if (inA === s.as.length && inP === s.par.length) {
      s.dead = true; sailLinesDie(sh, s);
      var c = sh.cl[s.k];                                               // 帶著現在的形狀走（物理開著 ⇒ 被風吹鼓的那一刻）
      if (!s.furled) piece.cl.push({ T: c.T, p: PHYS && c.p ? Float32Array.from(c.p) : null, torn: !!c.torn, tv: c.tv });
      c.gone = c.moved = true;
    }
    else dropSail(sh, s);
  });
  sh.crew.forEach(function (c) { if (c.st < 3 && set.has(VK.pack(Math.floor(c.pos[0]), Math.floor(c.pos[1]), c.pos[2] - 1))) fall(sh, c, mul(axis, 2)); });
  sh.models.forEach(function (m) {                            // 腳下那一格在這一團裡的模型（砲、舵輪）跟著走（⛔ 不跟 ⇒ 下一次 survey 從漂走的半截船裡直直掉進海裡）
    if (!m.alive || !set.has(m.foot)) return;
    m.alive = false; m.moved = true; piece.mods.push({ mesh: m.mesh, L: modelLocal(m) });
    sh.guns.forEach(function (g) { if (g.model === m) g.alive = false; });
  });
  piece.sh = sh; piece.pivotL = M4.pt(sh.inv, pivot[0], pivot[1], pivot[2]);
  sh.rigDirty = true;
  PIECES.push(piece);
  if (n > 3000) { sfx('creak', c0, 1.4); note(sh, piece.hull ? '船斷成兩截！' : c0[1] - pivot[1] > 8 ? '桅杆斷了！' : '一大塊船體脫落', !!piece.hull); }
}
/** 倒下的那一團掃過甲板：沿著它倒下的那條線（斷口 → 2 倍重心距離）1.5 公尺內的人被壓到。 */
function crush(pc, r) {
  if (!pc.sh) return;
  var sh = pc.sh, a = pc.pivot, b = add(pc.pivot, mul(r, 2));
  sh.crew.forEach(function (c) {
    if (c.st > 1) return;
    var w = M4.pt(sh.M, c.pos[0], c.pos[1], c.pos[2] + 9);
    if (segDist2(w, a[0], a[1], a[2], b[0], b[1], b[2]) < 2.25) damageCrew(sh, c, 120 * rr(0.6, 1.4), '倒下的桅');   // 血量 100 時約七成壓死
  });
}
function stepPiece(pc, dt) {
  pc.t += dt;
  var g = [0, -G, 0];
  if (pc.hull) {                                                // 斷開的半截船：水平慢慢停下、斷口那頭往下翹（最多約 35°）、往下沉越來越快
    pc.v[0] *= 1 - 0.12 * dt; pc.v[2] *= 1 - 0.12 * dt; pc.v[1] = -Math.min(1.6, 0.12 + pc.t * 0.025);
    pc.c = add(pc.c, mul(pc.v, dt));
    var ang = Math.min(0.6, pc.t * 0.035) + Math.max(0, pc.t - 17) * 0.01;
    pc.R = rotM(pc.hull, ang);
    if (!pc.wet) { pc.wet = true; for (var k2 = 0; k2 < 6; k2++) splash(add(pc.c, [gauss() * 6, 0, gauss() * 6]), true); }
    pc.M = M4.mul(M4.mul(M4.mul(trans(pc.c[0], pc.c[1], pc.c[2]), pc.R), trans(-pc.c0[0], -pc.c0[1], -pc.c0[2])), pc.M0);
    return pc.c[1] > -60 && pc.t < 150;
  }
  if (pc.hinge) {                                               // 繞斷口倒：細棒繞端點 α ＝ (r × g)·3／(4|r|²)
    if (pc.sh) { var np = M4.pt(pc.sh.M, pc.pivotL[0], pc.pivotL[1], pc.pivotL[2]); pc.c = add(pc.c, sub(np, pc.pivot)); pc.pivot = np; }   // 斷口跟著船走（船在航行）
    var r = sub(pc.c, pc.pivot), r2 = dot(r, r), alpha = mul(cross(r, g), 3 / (4 * r2));
    pc.w = add(pc.w, mul(alpha, dt));
    var ang = len(pc.w) * dt;
    if (ang > 0) { var Rm = rotM(pc.w, ang); r = M4.dir(Rm, r[0], r[1], r[2]); pc.c = add(pc.pivot, r); pc.R = M4.mul(Rm, pc.R); }
    var tilt = Math.acos(clamp(r[1] / Math.sqrt(r2), -1, 1));
    if (tilt > 1.25 || pc.t > 6) { pc.hinge = false; pc.v = add(cross(pc.w, r), pc.sh ? pc.sh.vel : [0, 0, 0]); crush(pc, r); }
  } else {
    pc.v = add(pc.v, mul(g, dt));
    var sea = seaH(pc.c[0], pc.c[2], SIMT);
    if (pc.c[1] < sea) {
      var float = sea + (pc.t < 40 ? -0.6 : -0.6 - (pc.t - 40) * 0.8);                     // 浮在水面 40 秒，之後慢慢沉
      pc.v[1] += ((float - pc.c[1]) * 3 - pc.v[1] * 2.5) * dt + G * dt;
      pc.v = mul(pc.v, 1 - 1.6 * dt); pc.w = mul(pc.w, 1 - 1.8 * dt);
      if (!pc.wet) { pc.wet = true; for (var k = 0; k < Math.min(6, 1 + pc.n / 8000); k++) splash(add(pc.c, [gauss() * 4, 0, gauss() * 4]), true); } }
    pc.c = add(pc.c, mul(pc.v, dt));
    var a2 = len(pc.w) * dt; if (a2 > 0) pc.R = M4.mul(rotM(pc.w, a2), pc.R);
  }
  pc.M = M4.mul(M4.mul(M4.mul(trans(pc.c[0], pc.c[1], pc.c[2]), pc.R), trans(-pc.c0[0], -pc.c0[1], -pc.c0[2])), pc.M0);
  return pc.c[1] > -40 && pc.t < 120;
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/23_powder.js ──
// ───────────────────────── 彈藥庫與火藥桶（殉爆） ─────────────────────────
// 火藥桶是模型（basecamp 的 -magazine-aft／-fore 子作品，meta {kind:'powder', powder_lb:100}；後 22 桶、前 116 桶），
// 彈藥庫是關聯（meta {kind:'magazine', powder_lb}、固定點 blast ＝ 爆心）。
// 火藥桶的血量在細節設定（預設 675 ＝ 很難殉爆但有機率；拉滿 1000 ＝ 不會爆 ⇒ 完全不扣、不抽亂數 ⇒ 戰局跟沒有火藥桶一樣）。
//   ① 血量歸零 ⇒ 點燃，0.15–0.5 秒後炸（kegBoom）：炸掉半徑 KEG_R 的格、傷旁邊的人、旁邊的模型扣血（火藥桶 ⇒ 連鎖）。
//   ② 同一間彈藥庫炸掉 ≥ 30% 的桶 ⇒ 整間殉爆（magBoom）：剩下的桶一起炸，爆心 ＝ blast 固定點，
//      半徑 ∝ (磅數 × 殉爆威力)^(1/3)（前彈藥庫 11,600 磅、威力 1 ⇒ 9.5 m）。
//   ③ 半徑 ≥ 斷船門檻（8 m × (硬度／2)^0.15（硬度 3 ⇒ 8.5 m））⇒ 船從爆心那一截斷開：橫切一刀，短的那半截變成斷開的一團（漂走、翹起來、沉下去），
//      留下的那半截一定沉（進水速度 0 也沉）、算降旗（不再開砲）。
// 威力是能量 ⇒ 爆炸半徑照立方根縮放：0.25× ⇒ 0.63 倍半徑、4× ⇒ 1.59 倍。
var BOOMS = [], KEG_R = 9, KEG_REACH = 30, KEG_DMG = 300, MAG_R = 95, MAG_LB = 11600, BREAK_R = 80;
// 彈坑分幾步挖（TASK-0531，Tim：卡畫面的事件分散到不同幀）：一次挖掉三十幾萬格要 120–230 ms ⇒ 那一步卡住。
//   區塊照離爆心的距離排好，從爆心往外，每一步挖到 BLAST_STEP 格就停、下一步接著挖（BLASTS，step() 的 stepBlasts）⇒ 爆炸往外擴，三十幾萬格約 9 步（0.15 秒）挖完。
//   碎片照挖到的格抽樣、挖到那一步才噴。人、模型照舊在殉爆那一刻算；斷船（橫切那一刀）與廣播（含打掉幾格）挖完才做。
//   ⛔ 斷船在殉爆那一刻切 ⇒ 還沒挖到的彈坑格被連通判定一起搬進斷開的半截（半截船 27 萬格、上面沒有彈坑，量過）。
//   ⚠ 殉爆之後的戰局跟以前（一步挖完）不一樣；但跟慢動作、特寫開不開無關 ⇒ 開或關同一局。
var BLASTS = [], BLAST_STEP = 40000;
function blastK() { return Math.pow(BLAST_K, 1 / 3); }
/** 這一次爆炸的威力（能量倍率）：1 ± BLAST_V 之間（細節設定的「威力浮動」；0 ⇒ 每次一樣、不抽亂數）。半徑照立方根、傷害照原值乘。 */
function blastRoll() { return BLAST_V > 0 ? rr(1 - BLAST_V, 1 + BLAST_V) : 1; }
/** 這艘船的彈藥庫：關聯 meta kind=magazine ＋ 名字在它底下的火藥桶模型。 */
function makeMags(sh) {
  return (sh.T.h.parts || []).filter(function (p) { return p.meta && p.meta.kind === 'magazine'; }).map(function (p) {
    var kegs = sh.models.filter(function (m) { return m.kind === 'powder' && m.path.indexOf(p.path + '/') === 0; });
    var lb = kegs.reduce(function (a, m) { return a + (+m.meta.powder_lb || 100); }, 0) || +p.meta.powder_lb || 0;
    var bl = (p.points && p.points.blast) || [(p.box[0] + p.box[3]) / 2, (p.box[1] + p.box[4]) / 2, (p.box[2] + p.box[5]) / 2];
    var mag = { name: p.path, pos: p.meta.pos || '', box: p.box, blast: bl, pts: p.points || {}, lb: lb, kegs: kegs, boomed: 0, gone: false, lit: false };   // pos：關聯 meta 的前／中／後（TASK-0539）
    kegs.forEach(function (m) { m.mag = mag; });
    return mag;
  });
}
/** 火藥桶被打到（damageModel 轉過來）：拉滿 ＝ 不會爆 ⇒ 不扣。 */
function powderHit(sh, m, dmg) {
  if (powderNever() || m.lit || !m.alive) return;
  m.hp -= dmg;
  if (m.hp <= 0) ignite(sh, m, rr(0.15, 0.5));
}
function ignite(sh, m, delay) {
  if (m.lit || !m.alive) return;
  m.lit = true; BOOMS.push({ t: SIMT + delay, sh: sh, m: m });
  if (m.mag && !m.mag.lit) { m.mag.lit = true; note(sh, '<b style="color:#ffb35a">' + magTag(m.mag) + '彈藥庫起火！</b>', true); }
  if (m.station && !m.station.lit) { m.station.lit = true; note(sh, '<b style="color:#ffb35a">' + m.station.name + '的火藥桶起火！</b>', true); }
}
function stepPowder() {
  for (var i = 0; i < BOOMS.length; i++) { var e = BOOMS[i]; if (e.t > SIMT) continue; BOOMS.splice(i--, 1); kegBoom(e.sh, e.m); }
  for (i = 0; i < SELFB.length; i++) { e = SELFB[i]; if (e.t > SIMT) continue; SELFB.splice(i--, 1); selfBoom(e.sh, e.mag); }
}
// 自爆（遊戲內設定的按鈕；Tim 2026-10-13：相當於重開，但先看煙花）：我艦還在的彈藥庫由小到大一間一間引爆（間隔 SELF_GAP 之間隨機，最大那間最後 ⇒ 通常船斷開；
//   每間的威力照細節設定的「威力浮動」，每次都不一樣），
//   照殉爆走（慢動作與特寫照設定）；炸不斷（殉爆威力調小）也一定開始沉（進水倍率 0 ⇒ 不沉，跟斷船一樣）。結算寫「自爆」，之後照常重新開始。
var SELF_GAP = [0.6, 1.8], SELFB = [];
function canSelfDestruct() { var sh = SHIPS[PLAYER_I]; return !!(RUNNING && sh && !sh.sunk && !sh.selfD && sh.mags.some(function (m) { return !m.gone; })); }
function selfDestruct() {
  if (!canSelfDestruct()) return false;
  var sh = SHIPS[PLAYER_I]; sh.selfD = true;
  var t = SIMT;
  sh.mags.filter(function (m) { return !m.gone; }).sort(function (a, b) { return a.lb - b.lb; }).forEach(function (m, k) { if (k) t += rr(SELF_GAP[0], SELF_GAP[1]); SELFB.push({ t: t, sh: sh, mag: m }); });
  note(sh, '<b style="color:#ff9a7a">自爆！</b>', true);
  return true;
}
function selfBoom(sh, mag) {
  magBoom(sh, mag);
  sh.struck = true; sh.sinkingFinal = true; sh.fate = '自爆' + (sh.broken ? '（船斷成兩截）' : '');
}
/** 一桶炸了：小爆炸＋連鎖。 */
function kegBoom(sh, m) {
  if (!m.alive || sh.sink > 40) return;
  m.alive = false;
  var f = blastRoll(), k = blastK() * Math.cbrt(f), w = M4.pt(sh.M, m.c[0], m.c[1], m.c[2]), r = shatter(sh, m.c, [0, 0, 1], KEG_R * k, [0, 6, 0], 220, 1);
  explode(w, sh, r.n);
  hurt(sh, m.c, KEG_REACH * 0.4 * k, KEG_REACH * k, null, '殉爆', 300 * BLAST_K * f);
  var reach = KEG_REACH * k;
  sh.models.forEach(function (o) {                                    // 旁邊的模型（火藥桶 ⇒ 連鎖；砲 ⇒ 扣血或飛出去）
    if (!o.alive || o === m) return;
    var d = len(sub(o.c, m.c)); if (d > reach) return;
    var cw = M4.pt(sh.M, o.c[0], o.c[1], o.c[2]);
    damageModel(sh, o, mul(norm(sub(cw, w)), 220 * (1 - d / reach) + 60), KEG_DMG * BLAST_K * f * (1 - 0.75 * d / reach));
  });
  if (m.station) flashCheck(sh, m.c);                                  // 取用點的桶：火光可能順著艙口竄下彈藥庫
  var mag = m.mag;
  if (mag && !mag.gone && ++mag.boomed >= Math.ceil(mag.kegs.length * 0.3)) magBoom(sh, mag);
}
/** 整間彈藥庫殉爆。 */
function magBoom(sh, mag) {
  if (mag.gone || sh.sink > 40) return;
  mag.gone = true; mag.lit = true;
  mag.kegs.forEach(function (m) { m.alive = false; m.lit = true; });
  BOOMS = BOOMS.filter(function (e) { return e.m.mag !== mag; });
  var f = blastRoll(), k = blastK() * Math.cbrt(f), R = MAG_R * Math.pow(mag.lb / MAG_LB, 1 / 3) * k, c = mag.blast, w = M4.pt(sh.M, c[0], c[1], c[2]);
  // 畫面：火球、碎片往外噴、濃煙往上
  flash(w, [0, 1, 0], 200, true);
  for (var i = 0; i < 160; i++) spawnPt(add(w, [gauss() * R * 0.04, rr(0, R * 0.06), gauss() * R * 0.04]), [gauss() * 14, rr(6, 30), gauss() * 14], rr(0.8, 2.2), [1, rr(0.4, 0.75), 0.12], 0.95, rr(3, 7), rr(6, 12), 2, 1.5, 3);
  smoke(w, [0, 1, 0], 120, true); smoke(add(w, [0, R * 0.05, 0]), [0, 1, 0], 80, true);
  sfx('blast', w, 2); sfx('creak', w, 1.6);
  if (typeof slowKick === 'function') slowKick(sh, w, R);              // 殉爆的慢動作與特寫（73_slowmo.js；只動畫面的時間與鏡頭）
  // 爆心附近：人、模型
  hurt(sh, c, R * 0.85, R * 1.4, null, '殉爆', 1500 * BLAST_K * f);
  sh.models.forEach(function (o) {
    if (!o.alive) return;
    var d = len(sub(o.c, c)); if (d > R * 1.3) return;
    var cw = M4.pt(sh.M, o.c[0], o.c[1], o.c[2]);
    damageModel(sh, o, mul(norm(sub(cw, w)), 300 * (1 - d / (R * 1.3)) + 80), 5000);
  });
  // 斷船（橫切那一刀等彈坑挖完：blastStep）
  var brk = R >= BREAK_R * Math.pow(sh.cfg.hard / 2, 0.15);
  sh.struck = sh.struck || brk; sh.broken = sh.broken || brk;
  if (brk) { sh.fate = '殉爆（船斷成兩截）'; sh.sinkingFinal = true; }
  mag.R = R; mag.f = f; mag.removed = 0; mag.broke = brk;
  var job = crater(sh, c, R); job.w = w; job.mag = mag; BLASTS.push(job);
  blastStep(job);                                                      // 爆心那幾塊這一步就挖（其他的 stepBlasts 接著挖）
}
/** 每一步（step() 的殉爆排程之後）：還沒挖完的彈坑接著挖。 */
function stepBlasts() {
  for (var i = 0; i < BLASTS.length; i++) if (BLASTS[i].done || BLASTS[i].sh.sink > 40 || blastStep(BLASTS[i])) BLASTS.splice(i--, 1);
}
/** 挖一段：從上次停的那一塊接著，挖到 BLAST_STEP 格（或挖完）。挖到的格照抽樣噴碎片。挖完 ⇒ 廣播（含打掉幾格）、回 true。 */
function blastStep(J) {
  var sh = J.sh, g = sh.grid, c = J.c, R = J.R, n0 = J.n, sample = [];
  while (J.k < J.ch.length && J.n - n0 < BLAST_STEP) {
    var ci = J.ch[J.k++], tab = g.tab[ci]; if (!tab) continue;        // ⛔ 寫入會換掉 g.tab 那一格（共用資料先複製）：照原本那份走，每格只拆一次
    var cx = ci % g.nx, cy = Math.floor(ci / g.nx) % g.ny, cz = Math.floor(ci / (g.nx * g.ny));
    for (var li = 0; li < 4096; li++) {
      var col = tab[li]; if (!col) continue;
      var x = cx * 16 + (li & 15), y = cy * 16 + ((li >> 4) & 15), z = cz * 16 + (li >> 8), dx = x - c[0], dy = y - c[1], dz = z - c[2], d = Math.sqrt(dx * dx + dy * dy + dz * dz);
      if (d > R * (0.85 + 0.3 * hash3(x, y, z))) continue;
      if (removeVoxel(sh, x, y, z, d > R * 0.8)) { if (++J.n % J.est === 0) sample.push(x, y, z, col); }
    }
  }
  for (var j = 0; j < sample.length; j += 4) {
    var p = M4.pt(sh.M, sample[j] + 0.5, sample[j + 1] + 0.5, sample[j + 2] + 0.5), dir = norm(sub(p, J.w));
    spawnDebris(p, add(add(mul(dir, rr(8, 40)), [0, rr(4, 22), 0]), sh.vel), sample[j + 3], rr(0.06, 0.16), rr(8, 16));
  }
  J.mag.removed = J.n;
  if (J.k < J.ch.length) return false;
  J.done = true;
  if (J.mag.broke) breakShip(sh, c[0]);                                   // 彈坑挖完才切（下一步的連通判定把短的那半截變成斷開的一團）
  note(sh, '<b style="color:#ffb35a">' + magTag(J.mag) + '彈藥庫殉爆！</b>（' + J.mag.lb.toLocaleString() + ' 磅、半徑 ' + (R * S).toFixed(1) + ' m、打掉 ' + J.n.toLocaleString() + ' 格）' + (J.mag.broke ? '　船斷成兩截' : ''), true);
  return true;
}
/** 彈坑（邊緣參差：0.85～1.15 倍半徑）的工作：只走有東西、而且碰得到球的區塊（⛔ 照 shatter 的三重迴圈：9.5 m 的球要走兩千八百萬格），
 *  照區塊離爆心最近的距離排（同距離照編號）⇒ blastStep 從爆心往外挖。est：大約每幾格抽一顆碎片（全部約 2,400 顆）。
 *  邊緣那一圈才推連通的種子（裡面的鄰格也都打掉了）。 */
function crater(sh, c, R) {
  var g = sh.grid, ch = [], R2 = R * 1.15, cx0 = Math.max(0, Math.floor((c[0] - R2) / 16)), cx1 = Math.min(g.nx - 1, Math.floor((c[0] + R2) / 16));
  var cy0 = Math.max(0, Math.floor((c[1] - R2) / 16)), cy1 = Math.min(g.ny - 1, Math.floor((c[1] + R2) / 16)), cz0 = Math.max(0, Math.floor((c[2] - R2) / 16)), cz1 = Math.min(g.nz - 1, Math.floor((c[2] + R2) / 16));
  for (var cz = cz0; cz <= cz1; cz++) for (var cy = cy0; cy <= cy1; cy++) for (var cx = cx0; cx <= cx1; cx++) {
    var ci = g.ci(cx, cy, cz); if (!g.tab[ci]) continue;
    var ex = Math.max(cx * 16 - c[0], 0, c[0] - (cx * 16 + 15)), ey = Math.max(cy * 16 - c[1], 0, c[1] - (cy * 16 + 15)), ez = Math.max(cz * 16 - c[2], 0, c[2] - (cz * 16 + 15)), d = Math.sqrt(ex * ex + ey * ey + ez * ez);
    if (d <= R2) ch.push([d, ci]);
  }
  ch.sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
  return { sh: sh, c: c, R: R, ch: ch.map(function (e) { return e[1]; }), k: 0, n: 0, est: Math.max(1, Math.round(4 / 3 * Math.PI * R * R * R * 0.08 / 2400)) };
}
/** 船從 x ＝ xb 那一截斷開：橫切一刀（切面參差 ±0.5～1.2 m），龍骨的錨只留長的那半截 ⇒ 短的那半截在下一步的連通判定裡變成斷開的一團。 */
function breakShip(sh, xb) {
  var g = sh.grid, cut = 0;
  for (var cz = 0; cz < g.nz; cz++) for (var cy = 0; cy < g.ny; cy++) for (var cx = Math.max(0, Math.floor((xb - 14) / 16)); cx <= Math.min(g.nx - 1, Math.floor((xb + 14) / 16)); cx++) {
    var tab = g.tab[g.ci(cx, cy, cz)]; if (!tab) continue;
    for (var li = 0; li < 4096; li++) {
      if (!tab[li]) continue;
      var x = cx * 16 + (li & 15), y = cy * 16 + ((li >> 4) & 15), z = cz * 16 + (li >> 8);
      if (Math.abs(x - xb) < 5 + 7 * hash3(y >> 2, z >> 2, 977)) { if (removeVoxel(sh, x, y, z, true)) cut++; }
    }
  }
  var keepAft = xb - sh.T.wl0 >= sh.T.wl1 - xb;                               // 留長的那半截
  sh.keel = keepAft ? [0, xb - 15] : [xb + 15, 1 << 12];
  sh.breakX = xb; sh.breakSide = keepAft ? 1 : -1;                     // 斷開的那一團在 +x（船頭）那邊 ⇒ 1
  return cut;
}

// ───────────────────────── 取用點與送藥手（火藥與彈藥的補給） ─────────────────────────
// 史實：火藥桶不離開彈藥庫 —— 砲手長在裡面把火藥裝成藥包，從掛著濕毛氈的小艙口遞出來，送藥童一次一包、裝在皮筒裡跑上砲甲板；
//   彈丸擺在砲旁與艙口邊的彈架上。遊戲為了讓火藥在戰鬥裡「打得到」，兩層甲板（砲甲板、spar deck）在兩間彈藥庫的上方各放一個
//   取用點（3 桶火藥＋彈藥；Tim 2026-10-12），送藥手碰一下火藥桶就算拿了火藥與彈藥（簡化；一次 CARRY_N 份），送到砲旁的藥箱（每門最多 BOX_N 份；兩個都在細節設定）。
//   砲開火後要從藥箱拿一份才開始裝填；藥箱空了 ⇒ 等送藥手（HUD △）。
// 危險（火藥血量拉滿 ＝ 全都不會爆；預設 675 ⇒ 藥包 203（一般命中要擲到偏高）、火光一次 300，要三次）：藥包（送藥手手上、砲旁藥箱）的血量 ＝ 火藥桶的 30%，吃到一下夠重的就著火爆炸；
//   取用點的桶被打到照火藥桶算；爆炸離取用點 3 m 內 ⇒ 火光竄下艙口：彈藥庫裡靠門最近的 6 桶各扣 300 × 威力 ⇒ 可能整間殉爆。
var CART_K = 0.3, MONKEY_SP = 26, FILL_T = 0.8, FLASH_R = 30, FLASH_DMG = 300, FLASH_CD = 3;
/** 彈藥庫是前／中／後哪一間（照關聯名字：彈藥庫-前／-中／-後；餘燼號只有一間中央的）。 */
/** 彈藥庫叫「前／中／後」：照關聯 meta `pos=fore／mid／aft`（TASK-0539）；沒有 ⇒ 照關聯名裡的字（舊匯出），都沒有 ⇒ 後。 */
var MAG_POS = { fore: '前', mid: '中', aft: '後' };
function magTag(mag) { if (MAG_POS[mag.pos]) return MAG_POS[mag.pos]; return mag.name.indexOf('前') >= 0 ? '前' : mag.name.indexOf('中') >= 0 ? '中' : '後'; }
/** 取用點：每層砲甲板（sh.decks，照砲的高度分，10_ship.js gunDecks）× 每間彈藥庫一個，放在彈藥庫正上方、中線旁一塊平的空地（9×9 格、頭上 8 格空、不碰砲）。 */
function makeStations(sh) {
  var T = sh.T, BASE = T.base, CY = T.cy;
  var keg = sh.mags.length && sh.mags[0].kegs[0]; if (!keg || !T.rig.meshes[keg.mesh]) return [];
  var V = T.rig.meshes[keg.mesh].verts, mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9], j, a;
  for (j = 0; j < V.length; j += 3) for (a = 0; a < 3; a++) { mn[a] = Math.min(mn[a], V[j + a]); mx[a] = Math.max(mx[a], V[j + a]); }
  var guns = sh.models.filter(function (m) { return GUNS[m.kind] || m.kind === 'wheel'; }), out = [];
  function clear(x, y, z) {
    for (var dy = 0; dy <= 9; dy += 3) for (var dx = 0; dx <= 9; dx += 3) { var zz = standZ(BASE, x + dx, y + dy, z - 1, z + 1, 8); if (zz < 0) return false; }
    return !guns.some(function (m) { var b = m.bb; return x + 11 > b[0] && x - 2 < b[3] && y + 11 > b[1] && y - 2 < b[4] && z + 8 > b[2] && z - 3 < b[5]; });
  }
  /** 從 x0 找一塊空地。dir 0 ⇒ 先在正上方 ±30 格找，找不到再往船頭、船尾兩邊找；dir ±1 ⇒ 只往那一頭找（x0 起算）。 */
  function findSpot(x0, dir, zr) {
    var spot = null, ex, e2, oy;
    if (!dir) for (var r = 0; r <= 30 && !spot; r += 2) for (var s = -1; s <= 1 && !spot; s += 2) for (var dx = -r; dx <= r && !spot; dx += 2) {
      var x = x0 + dx, y = s > 0 ? CY + 6 + (r - Math.abs(dx)) : CY - 15 - (r - Math.abs(dx)), z = standZ(BASE, x + 4, y + 4, zr[0], zr[1], 8);
      if (z >= 0 && clear(x, y, z)) spot = [x, y, z];
    }
    // 正上方沒有甲板（餘燼號的中央彈藥庫在船腰，上甲板那一段是開的）⇒ 沿那一層往船頭、船尾找最近的一塊空地
    // ⛔ 不找 ⇒ 那一層沒有取用點，送藥手只拿自己那一層的（stationFor）⇒ 上甲板 18 門 carronade 打完藥箱的兩發就永遠停了
    for (ex = dir ? 0 : 32; ex <= 400 && !spot; ex += dir ? 2 : 4) for (e2 = -1; e2 <= 1 && !spot; e2 += 2) for (oy = 0; oy < 4 && !spot; oy++) {
      if (dir && e2 !== dir) continue;
      var x2 = x0 + e2 * ex, y2 = [CY + 6, CY - 15, CY + 16, CY - 25][oy], z2 = standZ(BASE, x2 + 4, y2 + 4, zr[0], zr[1], 8);
      if (z2 >= 0 && clear(x2, y2, z2)) spot = [x2, y2, z2];
    }
    return spot;
  }
  // 只有一間彈藥庫（餘燼號的中央彈藥庫）⇒ 每層前後各一個取用點：從彈藥庫前端往船頭、後端往船尾各退 1.6 m 找（Tim 2026-10-13：「取用點分到前後兩處」）。
  //   ⛔ 一層只有一個、疊在彈藥庫正上方 ⇒ 那一層的送藥手全擠在船中段，電腦的瞄準點也在船中段 ⇒ 第一輪齊射就連炸（餘燼號對打 180 秒 2／3 場殉爆、一場第 4.5 秒）。
  //   兩間以上（憲法號前後兩間）⇒ 照舊每間正上方一個。送藥手照要送的那門砲挑最近的取用點（stationFor）⇒ 自然分成前後兩批。
  function anchors(mag) {
    if (sh.mags.length !== 1) return [{ x: Math.round(mag.blast[0]), dir: 0, tag: magTag(mag) }];
    return [{ x: Math.round(mag.box[3]) + 16, dir: 1, tag: '前' }, { x: Math.round(mag.box[0]) - 16, dir: -1, tag: '後' }];
  }
  sh.decks.forEach(function (D) {
    var deck = D.key, zr = D.zr;
    sh.mags.forEach(function (mag) { anchors(mag).forEach(function (A) {
      var spot = findSpot(A.x, A.dir, zr);
      if (!spot) return;
      var st = { deck: deck, mag: mag, name: D.name + A.tag + '取用點', kegs: [], pos: [spot[0] + 4.5, spot[1] + 4.5, spot[2] + 3], flashT: -9 };
      [[0, 0], [5, 0], [0, 5]].forEach(function (o, i) {
        var org = [spot[0] + o[0], spot[1] + o[1], spot[2]], bb = [org[0] + mn[0], org[1] + mn[1], org[2] + mn[2], org[0] + mx[0], org[1] + mx[1], org[2] + mx[2]];
        var m = { T: T, k: sh.models.length, name: st.name + '-' + (i + 1), path: st.name + '/' + (i + 1), kind: 'powder', station: st, hp: powderHP(), hpMax: powderHP(), mesh: keg.mesh, origin: org, bb: bb, pts: {}, meta: { kind: 'powder', powder_lb: 100 },
          c: [(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2], foot: VK.pack(org[0] + 2, org[1] + 2, org[2] - 1), alive: true };
        sh.models.push(m); st.kegs.push(m);
      });
      st.at = [spot[0] + 5.5, spot[1] + 5.5, spot[2]];                 // 送藥手站在三桶圍出來的那一角
      // 站位：那一角＋桶堆外圍幾格（站得住、不在砲裡）；同時好幾個人來拿 ⇒ 各站一格（⛔ 全站同一點 ⇒ 幾張人疊在一起、姿勢不同，看起來像一個人在抖）
      st.slots = [st.at].concat([[13, 5.5], [5.5, 13], [13, 13], [13, -2], [-2, 13], [5.5, -3], [-3, 5.5], [-3, -3]].map(function (o) {   // 齊射後同一個取用點最多 8 人在路上或在拿
        var x = Math.floor(spot[0] + o[0]), y = Math.floor(spot[1] + o[1]), z = standZ(BASE, x, y, spot[2] - 1, spot[2] + 1, 8);
        if (z < 0 || guns.some(function (m) { var b = m.bb; return x > b[0] - 2 && x < b[3] + 2 && y > b[1] - 2 && y < b[4] + 2 && z + 8 > b[2] && z - 3 < b[5]; })) return null;
        return [x + 0.5, y + 0.5, z];
      }).filter(Boolean));
      out.push(st);
    }); });
  });
  return out;
}
/** 送藥手：每一對砲（同一層、同一個 x 的兩舷）一個，站在那一對砲中間靠中線；砲記著自己的送藥手（g.pm）與放藥箱的位置（g.drop：砲尾後面）。 */
function makeMonkeys(sh, crew, taken, add) {
  var pairs = {}, BASE = sh.T.base, CY = sh.T.cy;
  sh.guns.forEach(function (g) { var k = gunDeck(g) + ':' + Math.round(g.muz[0]); (pairs[k] = pairs[k] || []).push(g); });
  Object.keys(pairs).forEach(function (k, i) {
    var gs = pairs[k], deck = gunDeck(gs[0]), zr = sh.deckZ[deck], x = Math.round(gs[0].muz[0]);
    gs.forEach(function (g) {
      var br = g.model.pts.breech || g.model.c, sg = g.side === 'P' ? -1 : 1;
      g.drop = standNear(BASE, Math.floor(br[0]) + 3, Math.floor(br[1] - sg * 7), zr[0], zr[1], 12, {}) || (g.spots.length ? g.spots[g.spots.length - 1].at : null);
    });
    var at = standNear(BASE, x, CY + (i % 2 ? 9 : -9), zr[0], zr[1], 12, taken); if (!at) return;
    add(ROLE.POWDER, at, null, 1);
    var c = crew[crew.length - 1]; c.deck = deck; c.guns = gs; c.pm = { st: 'idle', t: 0 }; c.cart = false;
    gs.forEach(function (g) { g.pm = c; });
  });
}
/** 別的送藥手已經要送去 g 的份數（在去拿、在拿、拿著送的；拿著的照手上的份數）。 */
function incoming(sh, c, g) {
  var n = 0;
  sh.crew.forEach(function (o) { if (o !== c && o.pm && o.pm.g === g && o.pm.st !== 'idle' && able(o)) n += o.pm.st === 'carry' ? o.cart || 0 : CARRY_N; });
  return n;
}
/** 下一份送去哪門：同一層、還在、藥箱（算上別人已經在送的）沒滿、是自己的或送藥手倒了的砲；先送等著的、空的、有人操作的、自己的、近的。
 *  ⛔ 不算別人在送的 ⇒ 沒有送藥手的砲一缺，整層的送藥手全跑去拿（量到 8 個），沒搶到的拿著藥包站在桶邊等十幾秒。 */
function needGun(sh, c) {
  var best = null, bs = 1e9;
  sh.guns.forEach(function (g) {
    if (!g.alive || !g.drop || gunDeck(g) !== c.deck || g.box >= BOX_N || (g.pm && g.pm !== c && able(g.pm))) return;
    if (g.box + incoming(sh, c, g) >= BOX_N) return;
    var s = g.box * 10 + (g.needCart ? 0 : 5) + (g.pm === c ? 0 : 3) + (gunRate(g) > 0 ? 0 : 20) + Math.abs(g.muz[0] - c.pos[0]) / 40;
    if (s < bs) { bs = s; best = g; }
  });
  return best;
}
/** 去哪個取用點拿：同一層、彈藥庫還在的，離要送的那門最近的（一間殉爆了 ⇒ 跑另一間）。 */
function stationFor(sh, c, g) {
  var best = null, bd = 1e9;
  sh.stations.forEach(function (st) { if (st.deck !== c.deck || st.mag.gone) return; var d = Math.abs(st.at[0] - g.muz[0]); if (d < bd) { bd = d; best = st; } });
  return best;
}
/** 在取用點站哪一格：別人（去拿、在拿）最少的那格，一樣多挑近的。 */
function slotFor(sh, c, st) {
  var best = st.at, bs = 1e9;
  (st.slots || [st.at]).forEach(function (s) {
    var n = sh.crew.filter(function (o) { return o !== c && o.pm && o.pm.src === st && o.pm.at === s && (o.pm.st === 'fetch' || o.pm.st === 'fill') && able(o); }).length;
    var v = n * 1e4 + Math.hypot(s[0] - c.pos[0], s[1] - c.pos[1]);
    if (v < bs) { bs = v; best = s; }
  });
  return best;
}
/** 走直線到 to（格座標）；高度跟著甲板。到了回 true。 */
function monkeyTo(sh, c, to, dt) {
  var dx = to[0] - c.pos[0], dy = to[1] - c.pos[1], l = Math.hypot(dx, dy);
  if (l < 0.6) { c.pos = to.slice(); c.moving = false; return true; }
  var s = Math.min(l, MONKEY_SP * dt); c.pos[0] += dx / l * s; c.pos[1] += dy / l * s; c.moving = true;
  var zr = sh.deckZ[c.deck], z = standZ(sh.grid, Math.floor(c.pos[0]), Math.floor(c.pos[1]), zr[0], zr[1], 6); if (z >= 0) c.pos[2] = z;
  return false;
}
function stepMonkey(sh, c, dt) {
  var P = c.pm; if (!P) return;
  if (sh.struck || sh.sunk) { c.moving = false; return; }
  if (P.st === 'idle') {
    var g = needGun(sh, c), st = g && stationFor(sh, c, g);
    if (!st) { monkeyTo(sh, c, c.home, dt); return; }                  // 都滿了（或沒地方拿）⇒ 回自己那一對砲中間等
    P.st = 'fetch'; P.src = st; P.g = g; P.at = slotFor(sh, c, st);
  }
  if (P.st === 'fetch') {
    if (P.src.mag.gone) { P.st = 'idle'; return; }
    if (monkeyTo(sh, c, P.at, dt)) { P.st = 'fill'; P.t = FILL_T; }
    return;
  }
  if (P.st === 'fill') { c.moving = false; if ((P.t -= dt) <= 0) { c.cart = CARRY_N; P.st = 'carry'; } return; }
  if (P.st === 'carry') {
    if (!c.cart) { P.st = 'idle'; return; }                            // 藥包炸掉或掉了
    if (!P.g || !P.g.alive || P.g.box >= BOX_N) P.g = needGun(sh, c);
    if (!P.g) { monkeyTo(sh, c, c.home, dt); return; }                 // 都滿了 ⇒ 拿著回自己那一對砲中間等（⛔ 不站在桶邊：擋住下一個來拿的）
    if (monkeyTo(sh, c, P.g.drop, dt)) {                               // 放進藥箱（放得下多少放多少）；手上還有 ⇒ 送下一門
      var put = Math.min(c.cart, BOX_N - P.g.box); P.g.box += put; c.cart -= put;
      if (c.cart <= 0) { c.cart = 0; P.st = 'idle'; } else P.g = null;
    }
  }
}
/** 送藥手手上的藥包吃到一下（damageCrew 轉過來）：夠重 ⇒ 著火爆炸。 */
function cartHit(sh, c, dmg) {
  if (powderNever() || dmg < powderHP() * CART_K) return;
  var n = c.cart; c.cart = 0; cartBoom(sh, [c.pos[0], c.pos[1], c.pos[2] + 9], n, '送藥手手上的藥包炸了');
}
/** 砲旁的藥箱（damageModel 打到砲時轉過來）。 */
function boxHit(sh, g, dmg) {
  if (!(g.box > 0) || powderNever() || dmg < powderHP() * CART_K) return;
  var n = g.box; g.box = 0; cartBoom(sh, g.model.c, n, sideName(g.side) + GUNS[g.type].short + '旁的藥箱炸了');
}
/** 藥包爆炸（n 份）：小洞、旁邊的人與模型（取用點的桶 ⇒ 連鎖）、可能竄下艙口。 */
function cartBoom(sh, L, n, what) {
  if (sh.sink > 40) return;
  sh.cartN = (sh.cartN || 0) + 1;                                       // 讀數：藥包炸了幾次
  var f = blastRoll(), k = blastK() * Math.cbrt(n * f), w = M4.pt(sh.M, L[0], L[1], L[2]), r = shatter(sh, L, [0, 0, 1], 3.5 * k, [0, 4, 0], 60, 1), reach = 18 * k;
  explode(w, sh, r.n);
  hurt(sh, L, 8 * k, 22 * k, null, '火藥', 200 * BLAST_K * f * Math.cbrt(n));
  sh.models.forEach(function (o) {
    if (!o.alive) return;
    var d = len(sub(o.c, L)); if (d > reach) return;
    var cw = M4.pt(sh.M, o.c[0], o.c[1], o.c[2]);
    damageModel(sh, o, mul(norm(sub(cw, w)), 120 * (1 - d / reach) + 40), 150 * BLAST_K * f * Math.cbrt(n) * (1 - 0.75 * d / reach));
  });
  if (what) note(sh, '<b style="color:#ffb35a">' + what + '</b>');
  flashCheck(sh, L);
}
/** 爆炸離取用點 3 m 內 ⇒ 火光順著艙口竄下彈藥庫：靠門最近的 6 桶各扣 300 × 威力（**同一間彈藥庫** 3 秒內只算一次）。
 *  ⛔ 以前照取用點算：下層、上層砲甲板的取用點上下疊著（相距 2.3 m），一次爆炸同時在兩個的 3 m 內 ⇒ 竄下兩次、門邊的桶吃 600
 *  ⇒ 娛樂 450 一次就整間殉爆（「要竄下去幾次才會著」的設計整個沒了）；餘燼號對打第 4.8 秒、憲法號也一樣會中。 */
function flashCheck(sh, L) {
  (sh.stations || []).forEach(function (st) {
    if (st.mag.gone || SIMT - (st.mag.flashT === undefined ? -99 : st.mag.flashT) < FLASH_CD || len(sub(L, st.pos)) > FLASH_R) return;
    st.flashT = st.mag.flashT = SIMT;
    var door = (st.mag.pts && st.mag.pts.door) || st.mag.blast;
    var near = st.mag.kegs.filter(function (m) { return m.alive && !m.lit; }).sort(function (a, b) { return len(sub(a.c, door)) - len(sub(b.c, door)); }).slice(0, 6);
    if (!near.length) return;
    note(sh, '<b style="color:#ff9a7a">火光竄下' + magTag(st.mag) + '彈藥庫的艙口！</b>', true);
    near.forEach(function (m) { powderHit(sh, m, FLASH_DMG * BLAST_K); });
  });
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/30_rig_physics.js ──
// ───────────────────────── 帆與繩的物理（可關） ─────────────────────────
// 開（PHYS）：帆是一塊布（質點＋距離約束，Verlet），被「相對風」（真風 − 船速）吹鼓 —— 轉向、頂風時帆會往另一邊鼓；
//   斷掉的繩與掉下來的帆不消失：掛在還綁著的那一端擺，整個鬆脫就往下掉，落到甲板上會停住。
//   帆被打穿：洞裡那一塊布切成布片，照同一套布的物理飄下去（34_shreds.js）。
// 關：跟以前一樣 —— 帆停在雕刻作品模擬的那一刻、斷掉的就不見。
// ⛔ 物理只管畫出來的樣子：航速、命中、帆算不算數照原本的規則（s.dead／s.furled），而且這一段不碰 rnd()
//   ⇒ 開或關，同一個種子走出同一局。
// 座標：船的格座標（跟繩與帆的資料同一套）；重力與相對風用 sh.inv 換進來（1 格 ＝ S 公尺，速度單位 格/秒）。
var WIND_SAIL = 10;           // 推帆的風速（m/s）；WIND 的大小是煙飄的速度，只共用方向。Tim 2026-10-12：7 太不明顯 ⇒ 10，再乘細節設定的風壓（WIND_K）
var GUST = [0.24, 0.12, 0.06], FLUTTER = 0.35, SLACK = 1.02;   // 陣風三個頻率的幅度、布上走過去的波紋（風壓 ±35%）、布比作品的形狀鬆 2%（鼓得深一點）
var KW = 0.05;                // 風壓：加速度（格/秒²）＝ KW ×（相對風在法線上的分量）²
var KD = 0.3, DAMP = 0.985;   // 繩的空氣阻力（1/秒）、每一步的速度保留
var SEG = 6;                  // 布與繩的迭代次數、帆幾步走一次、垂繩上限照物理分級（09_phx.js rigLv：高 ＝ 4 次、隔一步（30 Hz）、500 條）
var CACC = null, CCNT = null, PHYS_MS = 0, PROF = { cloth: 0, rope: 0, shred: 0, buf: 0 };
// 帆桁追風（物理開著才轉）：方帆桁讓帆的法線落在「相對風吹去的方向」與船頭的角平分線上，最多轉離正橫 40°（再多就頂到支索與 shroud）；
//   gaff／boom（後桅縱帆）往下風擺，帆面跟船身的夾角 ＝ (180° − 相對風角)／2，8°–80°；頂風 ±25° 內不換邊（遲滯）。每秒最多轉 8°。
//   帆的綁點、帆腳與綁在帆桁上的繩跟著轉（繩照弧長在兩端之間內插：一端綁甲板的 brace 就只有帆桁那一頭轉）。
//   ⚠ 帆桁轉了，砲彈打到帆桁的位置跟著變 ⇒ 物理開或關不再走出逐格同一局（只差在打到帆桁的那幾下）。
var BRACE_MAX = 0.70, BOOM_MIN = 0.14, BOOM_MAX = 1.40, BRACE_RATE = 0.14, BRACE_HYST = 2.7;
function braceYards(sh, wl, dt) {
  var psi = Math.atan2(wl[1], wl[0]);                                // 相對風吹去的方向（格座標、從船頭往 +y 量）：0 ＝ 正後方來的風
  if (Math.abs(psi) < BRACE_HYST || !sh.braceSide) sh.braceSide = psi >= 0 ? 1 : -1;
  sh.yards.forEach(function (m) {
    if (!m.alive) return;
    var tgt = m.yk === 'gaff' || m.yk === 'boom' ? -sh.braceSide * clamp((Math.PI - Math.abs(psi)) / 2, BOOM_MIN, BOOM_MAX)
      : Math.abs(psi) < BRACE_HYST ? clamp(psi / 2, -BRACE_MAX, BRACE_MAX) : sh.braceSide * BRACE_MAX;
    m.rot += clamp(tgt - m.r0 - m.rot, -BRACE_RATE * dt, BRACE_RATE * dt);
  });
  sh.psi = psi;
}
/** 綁在帆桁上的繩重算形狀（帆桁轉了 0.25° 以上才算；物理關掉時 rot 歸零 ⇒ 回到作品的形狀）。 */
function yardRopes(sh, force) {
  var moved = force || sh.yards.some(function (m) { return Math.abs(m.rot - (m.rotA || 0)) > 0.004; });
  if (!moved) return;
  sh.yards.forEach(function (m) { m.rotA = m.rot; });
  sh.yRopes.forEach(function (r) {
    var A = r.ya >= 0 ? sh.models[r.ya] : null, B = r.yb >= 0 ? sh.models[r.yb] : null;
    if ((!A || !A.rot) && (!B || !B.rot)) { r.pts = r.pts0; r.bb = ropeBox(r.pts); return; }
    var p0 = r.pts0, n = p0.length / 3, acc = new Float32Array(n), tot = 0, j;
    for (j = 1; j < n; j++) { tot += Math.hypot(p0[j * 3] - p0[j * 3 - 3], p0[j * 3 + 1] - p0[j * 3 - 2], p0[j * 3 + 2] - p0[j * 3 - 1]); acc[j] = tot; }
    var out = new Float32Array(p0.length);
    for (j = 0; j < n; j++) {
      var P0 = [p0[j * 3], p0[j * 3 + 1], p0[j * 3 + 2]], t = tot > 0 ? acc[j] / tot : 0;
      var pa = A && A.rot ? rotZ(P0, A.piv, A.rot) : P0, pb = B && B.rot ? rotZ(P0, B.piv, B.rot) : P0;
      if (A && B && A === B) pb = pa;
      out[j * 3] = pa[0] * (1 - t) + pb[0] * t; out[j * 3 + 1] = pa[1] * (1 - t) + pb[1] * t; out[j * 3 + 2] = P0[2];
    }
    r.pts = out; r.bb = ropeBox(out);
  });
  sh.rigDirty = true;
}
/** 綁著的布點跟著帆桁轉（每一步都放回「作品的位置繞轉軸轉 rot」；鬆開的點交給物理）。 */
function yardPins(sh, c) {
  var T = c.T.sim, yk = T.yk; if (!yk) return;
  for (var i = 0; i < T.n; i++) {
    if (!c.pin[i] || yk[i] < 0) continue;
    var m = sh.models[yk[i]]; if (!m.rot) { if (!c.yr) continue; }
    var o = i * 3, w = rotZ([T.p0[o], T.p0[o + 1], T.p0[o + 2]], m.piv, m.rot);
    c.p[o] = c.q[o] = w[0]; c.p[o + 1] = c.q[o + 1] = w[1];
  }
  c.yr = sh.yards.some(function (m) { return m.rot; });
}
/** 一面帆的布（兩艘船共用；載入時算一次）：
 *  只留一層 —— 雕刻作品的帆是正反兩層、相差 0.11 格，兩層都畫遠看會互相打架成棋盤格；
 *  邊（距離約束）＋ 同一條格線上隔一點的兩點（跨點約束，布不會揉成一團）；
 *  外緣在轉角（> 29°）處切成幾段：筆直的那幾段是綁在帆桁／支索／斜桁上的邊（作品裡整條固定在線段上；鼓起來的自由邊不會直），
 *  綁邊上的點各自找靠的格（0.6 m 內）或繩（0.4 m 內）—— 帆桁被打掉一截，只有那一截的布鬆開；
 *  不在綁邊上的角 ＝ 帆腳：綁在帆自己的繩（sheet／tack，端點 1 m 內）、旁邊的格或繩上。
 *  hk：0 不綁、1 格、2 繩、3 找不到靠的（帆還在就綁著）、4 模型（帆桁：綁邊靠在帆桁的網格上）。
 *  sim.yk：每個綁著的粗格點跟著哪根帆桁轉（帆桁追風，見 braceYards；-1 ＝ 不轉）。 */
function clothTemplate(H, s) {                         // H：船型（帆的布模板、繩的外框在 H.cloth／H.rbox）
  var v = s.verts, tr = s.tris, nv = v.length / 3, h = nv >> 1, T = [], one = nv % 2 === 0, i, j, k;
  for (j = 0; j < tr.length; j += 3) {
    var lo = tr[j] < h;
    if ((tr[j + 1] < h) !== lo || (tr[j + 2] < h) !== lo) one = false;
    if (lo) T.push(tr[j], tr[j + 1], tr[j + 2]);
  }
  if (!one || T.length * 2 !== tr.length) { T = Array.prototype.slice.call(tr); h = nv; }
  var n = h, p0 = new Float32Array(v.slice(0, n * 3));
  function P(q) { return [p0[q * 3], p0[q * 3 + 1], p0[q * 3 + 2]]; }
  var E = new Map(), ea = [], eb = [], use = [];
  for (j = 0; j < T.length; j += 3) for (k = 0; k < 3; k++) {
    var a = T[j + k], b = T[j + (k + 1) % 3], kk = a < b ? a * 65536 + b : b * 65536 + a, e = E.get(kk);
    if (e === undefined) { e = ea.length; E.set(kk, e); ea.push(a); eb.push(b); use.push(0); }
    use[e]++;
  }
  // 外緣：只被一個三角形用到的邊，接成一圈
  var bn = []; for (i = 0; i < n; i++) bn.push([]);
  ea.forEach(function (a, e) { if (use[e] === 1) { bn[a].push(eb[e]); bn[eb[e]].push(a); } });
  var loop = [], st = -1; for (i = 0; i < n; i++) if (bn[i].length === 2) { st = i; break; }
  if (st >= 0) { var pv = -1, cu = st; do { loop.push(cu); var nx = bn[cu][0] === pv ? bn[cu][1] : bn[cu][0]; pv = cu; cu = nx; } while (cu !== st && cu !== undefined && loop.length <= n); }
  var L = loop.length, corner = [];
  for (k = 0; k < L; k++) { var A = P(loop[(k + L - 1) % L]), M = P(loop[k]), C = P(loop[(k + 1) % L]); if (dot(norm(sub(M, A)), norm(sub(C, M))) < Math.cos(0.5)) corner.push(k); }
  var hk = new Int8Array(n), hv = new Int32Array(n).fill(-1), sides = [];
  for (k = 0; k < corner.length; k++) {
    var side = [], k1 = corner[(k + 1) % corner.length];
    for (var t = corner[k]; ; t = (t + 1) % L) { side.push(loop[t]); if (t === k1 && side.length > 1) break; if (side.length > L) break; }
    var a0 = P(side[0]), a1 = P(side[side.length - 1]), ch = len(sub(a1, a0)), md = 0;
    side.forEach(function (q) { var w = P(q); md = Math.max(md, Math.sqrt(segDist2(w, a0[0], a0[1], a0[2], a1[0], a1[1], a1[2]))); });
    var bound = ch > 25 && md < 0.75;
    sides.push({ n: side.length, len: +ch.toFixed(1), dev: +md.toFixed(2), bound: bound });
    if (bound) side.forEach(function (q) { hk[q] = 3; });
  }
  function ropeNear(w, r2) {
    var best = -1, bd = r2, r = Math.sqrt(r2);
    H.rig.ropes.forEach(function (o, j2) {
      var b2 = H.rbox[j2]; if (w[0] < b2[0] - r || w[0] > b2[3] + r || w[1] < b2[1] - r || w[1] > b2[4] + r || w[2] < b2[2] - r || w[2] > b2[5] + r) return;
      for (var q = 0; q + 5 < o.pts.length; q += 3) { var d = segDist2(w, o.pts[q], o.pts[q + 1], o.pts[q + 2], o.pts[q + 3], o.pts[q + 4], o.pts[q + 5]); if (d < bd) { bd = d; best = j2; } }
    });
    return best;
  }
  for (i = 0; i < n; i++) {
    if (hk[i] !== 3) continue;
    var yw = yardNear(H, P(i), 3); if (yw >= 0) { hk[i] = 4; hv[i] = yw; continue; }   // 綁在帆桁上（帆桁改成模型之後，那裡已經沒有格）
    var w = P(i), an = anchorNear(H, w[0], w[1], w[2], 6);
    if (an >= 0) { hk[i] = 1; hv[i] = an; } else { var rp = ropeNear(w, 16); if (rp >= 0) { hk[i] = 2; hv[i] = rp; } }
  }
  var own = []; H.rig.ropes.forEach(function (r, j2) { if (sailRope(r, s.name)) own.push(j2); });   // 帆自己的 sheet、tack（10_ship.js sailRope：照 meta，沒有才照名字）
  var clews = 0, clewYard = {};                          // 帆腳 → 跟哪根帆桁轉（-1 ＝ 不轉）
  corner.forEach(function (kc) {
    var q = loop[kc]; if (hk[q]) return;
    var w = P(q), best = -1, bd = 100, end = null;
    own.forEach(function (j2) { var pts = H.rig.ropes[j2].pts; [0, pts.length - 3].forEach(function (o) { var dx = pts[o] - w[0], dy = pts[o + 1] - w[1], dz = pts[o + 2] - w[2], d = dx * dx + dy * dy + dz * dz; if (d < bd) { bd = d; best = j2; end = [pts[o], pts[o + 1], pts[o + 2]]; } }); });
    clewYard[q] = end ? yardNear(H, end, 3) : -1;        // 帆自己的 sheet 靠帆那一端在哪根帆桁上（topsail 以上：下一根帆桁的兩端）；course 的綁甲板繩栓 ⇒ 不轉（basecamp 2026-10-12）
    if (best < 0) { var an = anchorNear(H, w[0], w[1], w[2], 6); if (an >= 0) { hk[q] = 1; hv[q] = an; clews++; return; } best = ropeNear(w, 16); }
    if (best >= 0) { hk[q] = 2; hv[q] = best; clews++; }
  });
  var pins = 0; for (i = 0; i < n; i++) if (hk[i]) pins++;
  // 物理在粗格上算（規則格 ⇒ 隔一點取一點：25×25 → 13×13，約束少 4 倍）；畫的時候細格照權重從粗格內插回來
  var cg = coarseOf(n, T), sim = meshCons(cg.idx.map(P), cg.tris);
  sim.fine = cg.idx; sim.hk = new Int8Array(cg.idx.length); sim.hv = new Int32Array(cg.idx.length);
  cg.idx.forEach(function (f, ci) { sim.hk[ci] = hk[f]; sim.hv[ci] = hv[f]; });
  // 跟著哪根帆桁轉：綁邊上的點 ＝ 這面帆的帆桁（meta sail）裡離這一點最近的那根（線段：方帆桁 arm-P–arm-S、gaff／boom pivot–end）；
  //   帆腳 ＝ 它的 sheet 綁在哪根帆桁上（上面的 clewYard）。course 的帆腳綁在甲板繩栓上、不轉 ⇒ 帆桁轉了，帆頂跟著轉、帆腳留著，中間的布交給物理。
  //   ⛔ 帆腳跟著自己的帆桁轉 ⇒ course 整面被拖著轉、sheet 與 tack 也被拖離繩栓（2026-10-12 的版本）。
  var ys = []; (H.rig.models || []).forEach(function (m, k) {
    var mt = m.meta || {}, pt = m.points || {}; if (mt.kind !== 'yard' || mt.sail !== s.name || !pt.pivot) return;
    var a = pt['arm-P'] || pt.pivot, b = pt['arm-S'] || pt.end || pt.pivot; ys.push({ k: k, a: a, b: b });
  });
  sim.yk = new Int16Array(cg.idx.length).fill(-1);
  if (ys.length) cg.idx.forEach(function (f, ci) {
    if (!sim.hk[ci]) return;
    if (f in clewYard) { sim.yk[ci] = clewYard[f]; return; }
    var w = P(f), bi = -1, bd = 1e18;
    ys.forEach(function (y) { var d = segDist2(w, y.a[0], y.a[1], y.a[2], y.b[0], y.b[1], y.b[2]); if (d < bd) { bd = d; bi = y.k; } });
    sim.yk[ci] = bi;
  });
  var foot = -1; Object.keys(clewYard).forEach(function (q) { if (clewYard[q] >= 0) foot = clewYard[q]; });
  var vcol = texColors(s.texture, n);                   // 有貼圖（旗）⇒ 每個頂點照 UV 取貼圖的顏色；整面的顏色（布片、碎布）取平均
  return { name: s.name, col: vcol ? vcol.avg : s.color || [0.95, 0.92, 0.85], vcol: vcol ? vcol.c : null, n: n, p0: p0, tris: new Uint16Array(T), sim: sim, mi: cg.mi, mw: cg.mw, grid: cg.kind,
    hk: hk, hv: hv, sides: sides, pins: pins, clews: clews, foot: foot };   // foot：帆腳跟著轉的帆桁（-1 ＝ 不轉；砲彈打帆照高度內插轉角用）
}
/** 旗的貼圖（.vxk 帆的 texture：w×h 的 RGBA、base64，uv 每個頂點一對）⇒ 前 n 個頂點（正面那一份）的顏色：每個頂點取它四周一格布寬的平均（不透明的才算）。
 *  Tim 2026-10-13：夜隼號的旗變成白旗 —— 遊戲畫帆只用一個顏色，夜隼號那面旗的顏色欄是帆布白（憲法號的是紅）。沒有貼圖 ⇒ null（照舊單色）。 */
function texColors(tx, n) {
  if (!tx || !tx.rgba || !tx.uv || tx.uv.length < n * 2 || !tx.w || !tx.h) return null;
  var b = atob(tx.rgba), W = tx.w, H = tx.h, am = tx.alpha_min || 0, f = 0.5 / Math.sqrt(n), c = new Float32Array(n * 3), avg = [0, 0, 0], i;
  if (b.length < W * H * 4) return null;
  for (i = 0; i < n; i++) {
    var u = tx.uv[i * 2], v = tx.uv[i * 2 + 1], x0 = clamp(Math.floor((u - f) * W), 0, W - 1), x1 = clamp(Math.ceil((u + f) * W) - 1, x0, W - 1);
    var y0 = clamp(Math.floor((v - f) * H), 0, H - 1), y1 = clamp(Math.ceil((v + f) * H) - 1, y0, H - 1), r = 0, g = 0, bl = 0, k = 0;
    for (var y = y0; y <= y1; y++) for (var x = x0; x <= x1; x++) { var o = (y * W + x) * 4; if (b.charCodeAt(o + 3) < am) continue; r += b.charCodeAt(o); g += b.charCodeAt(o + 1); bl += b.charCodeAt(o + 2); k++; }
    if (!k) { r = g = bl = 242; k = 1; }
    c[i * 3] = r / k / 255; c[i * 3 + 1] = g / k / 255; c[i * 3 + 2] = bl / k / 255; avg[0] += c[i * 3] / n; avg[1] += c[i * 3 + 1] / n; avg[2] += c[i * 3 + 2] / n;
  }
  return { c: c, avg: avg };
}
/** 一塊布的約束：邊（三角形的邊）＋ 跨點（同一條格線上隔一點的兩點，布不會揉成一團）；靜止長度 ＝ 雕刻作品那一刻的距離。 */
function meshCons(pos, T) {
  var n = pos.length, E = new Map(), ea = [], eb = [], adj = [], te = [], i, j, k;
  for (i = 0; i < n; i++) adj.push([]);
  for (j = 0; j < T.length; j += 3) for (k = 0; k < 3; k++) {
    var a = T[j + k], b = T[j + (k + 1) % 3], kk = a < b ? a * 65536 + b : b * 65536 + a, e = E.get(kk);
    if (e === undefined) { e = ea.length; E.set(kk, e); ea.push(a); eb.push(b); adj[a].push(b); adj[b].push(a); }
    te.push(e);
  }
  var B = new Set(), ba = [], bb = [];
  for (i = 0; i < n; i++) for (j = 0; j < adj[i].length; j++) for (k = j + 1; k < adj[i].length; k++) {
    var x = adj[i][j], y = adj[i][k];
    if (dot(norm(sub(pos[x], pos[i])), norm(sub(pos[y], pos[i]))) > -0.9) continue;
    var kb = x < y ? x * 65536 + y : y * 65536 + x; if (B.has(kb)) continue; B.add(kb); ba.push(x); bb.push(y);
  }
  var p0 = new Float32Array(n * 3), rest = new Float32Array(ea.length), brest = new Float32Array(ba.length);
  pos.forEach(function (w, q) { p0[q * 3] = w[0]; p0[q * 3 + 1] = w[1]; p0[q * 3 + 2] = w[2]; });
  for (i = 0; i < ea.length; i++) rest[i] = len(sub(pos[ea[i]], pos[eb[i]])) * SLACK;
  for (i = 0; i < ba.length; i++) brest[i] = len(sub(pos[ba[i]], pos[bb[i]])) * SLACK;
  return { n: n, p0: p0, tris: T, te: new Uint16Array(te), ea: new Uint16Array(ea), eb: new Uint16Array(eb), rest: rest, ba: new Uint16Array(ba), bb: new Uint16Array(bb), brest: brest };
}
/** 細格 → 粗格：方帆 N×N、三角帆（第 r 列 N−r 點）、N 是單數 ⇒ 取偶數列偶數行；其他形狀 ⇒ 不縮（粗格 ＝ 細格）。
 *  回：idx（粗格點 → 細格點）、tris（粗格三角形）、mi／mw（每個細格點由哪幾個粗格點、各佔多少內插）。 */
function coarseOf(n, T) {
  var N = Math.round(Math.sqrt(n)), M = Math.round((Math.sqrt(8 * n + 1) - 1) / 2), kind = null, off = null, i, j, k;
  function ok(rc) {
    for (j = 0; j < T.length; j += 3) for (k = 0; k < 3; k++) { var a = rc(T[j + k]), b = rc(T[j + (k + 1) % 3]); if (Math.abs(a[0] - b[0]) > 1 || Math.abs(a[1] - b[1]) > 1) return false; }
    return true;
  }
  var sq = function (q) { return [Math.floor(q / N), q % N]; };
  if (N * N === n && N % 2 && ok(sq)) kind = 'sq';
  else if (M * (M + 1) / 2 === n && M % 2) {
    off = []; for (i = 0; i <= M; i++) off.push(i * M - i * (i - 1) / 2);
    var row = new Int32Array(n); for (i = 0; i < M; i++) for (j = off[i]; j < off[i + 1]; j++) row[j] = i;
    var tr = function (q) { return [row[q], q - off[row[q]]]; };
    if (ok(tr)) { kind = 'tri'; N = M; }
  }
  var mi = new Int32Array(n * 4), mw = new Float32Array(n * 4);
  if (!kind) {
    for (i = 0; i < n; i++) { mi[i * 4] = i; mw[i * 4] = 1; }
    return { kind: 'full', idx: Array.from({ length: n }, function (_, q) { return q; }), tris: Array.prototype.slice.call(T), mi: mi, mw: mw };
  }
  var Nc = (N + 1) / 2, idx = [], ct = [], R, C;
  var offc = []; for (R = 0; R <= Nc; R++) offc.push(kind === 'sq' ? R * Nc : R * Nc - R * (R - 1) / 2);
  function rowLen(R) { return kind === 'sq' ? Nc : Nc - R; }
  function fine(r, c) { return kind === 'sq' ? r * N + c : off[r] + c; }
  function cc(r, c) { return offc[r / 2] + c / 2; }                    // 細格 (r, c)（都是偶數）在粗格的編號
  for (R = 0; R < Nc; R++) for (C = 0; C < rowLen(R); C++) idx.push(fine(2 * R, 2 * C));
  for (R = 0; R + 1 < Nc; R++) for (C = 0; C + 1 < rowLen(R); C++) {
    var a = offc[R] + C;
    if (kind === 'sq') { ct.push(a, a + 1, a + Nc + 1, a, a + Nc + 1, a + Nc); continue; }
    ct.push(a, a + 1, offc[R + 1] + C);
    if (C + 2 < rowLen(R)) ct.push(a + 1, offc[R + 1] + C + 1, offc[R + 1] + C);
  }
  for (var r = 0; r < N; r++) for (var c = 0; c < (kind === 'sq' ? N : N - r); c++) {
    var f = fine(r, c) * 4, w = [];
    if (!(r & 1) && !(c & 1)) w = [[r, c]];
    else if (!(r & 1)) w = [[r, c - 1], [r, c + 1]];
    else if (!(c & 1)) w = [[r - 1, c], [r + 1, c]];
    else w = kind === 'sq' ? [[r - 1, c - 1], [r - 1, c + 1], [r + 1, c - 1], [r + 1, c + 1]] : [[r - 1, c + 1], [r + 1, c - 1]];   // 三角帆的對角線是 (r+1, c)–(r, c+1) 那一斜
    w.forEach(function (x, q) { mi[f + q] = cc(x[0], x[1]); mw[f + q] = 1 / w.length; });
  }
  return { kind: kind, idx: idx, tris: ct, mi: mi, mw: mw };
}
function clothSetup(H, C) {                            // 船型 H 的布模板；暫存區（兩艘、各型共用）照目前最大的那一型配；C ＝ 快取的記錄（06_cache.js：rbox、cloth）
  H.rbox = C ? C.rbox : H.rig.ropes.map(function (r) { return ropeBox(r.pts); });
  H.cloth = C ? C.cloth : H.rig.sails.map(function (s) { return clothTemplate(H, s); });
  var mv = 1, mc = 1, sv = 0, si = 0;
  H.cloth.forEach(function (C) { mv = Math.max(mv, C.n); mc = Math.max(mc, C.sim.n); sv += C.n; si += C.tris.length; });
  if (!CACC || CACC.length < mc * 3) { CACC = new Float32Array(mc * 3); CCNT = new Uint8Array(mc); }
  if (!SBV || SBV.length < Math.max(1, sv) * 9) SBV = new Float32Array(Math.max(1, sv) * 9);
  if (!SBI || SBI.length < Math.max(1, si)) SBI = new Uint32Array(Math.max(1, si));
  if (!SBN || SBN.length < mv * 3) { SBN = new Float32Array(mv * 3); SBP = new Float32Array(mv * 3); }
}
/** 張開的帆從雕刻作品那一刻的形狀開始（開局、收帆後再張、物理剛打開）。 */
function clothInit(c) {
  var T = c.T.sim; c.p = Float32Array.from(T.p0); c.q = Float32Array.from(T.p0);
  c.pin = new Uint8Array(T.n); for (var i = 0; i < T.n; i++) c.pin[i] = T.hk[i] ? 1 : 0;
  c.brk = new Uint8Array(T.ea.length); c.bbrk = new Uint8Array(T.ba.length); c.tv = new Uint8Array(c.T.n); c.torn = false; c.loose = false; c.free = 0; c.gone = false; c.npin = -1;
}
/** 靠的東西還在不在：格（被打掉 ⇒ 不在）、繩（斷了）、模型（飛了）；3 ＝ 帆還算數就在。 */
function holds(sh, s, k, v) { return k === 1 ? gp(sh.grid, v) > 0 : k === 2 ? !sh.ropes[v].dead : k === 3 ? !!s && !s.dead : k === 4 ? sh.models[v].alive : false; }
function clothPins(sh, s, c) {
  var T = c.T.sim, n = 0;
  for (var i = 0; i < T.n; i++) if (c.pin[i]) { if (holds(sh, s, T.hk[i], T.hv[i])) n++; else c.pin[i] = 0; }
  c.npin = n;
}
/** 撕開：打到的那一點 r 格內的邊斷掉（布上開一個洞，大一點就裂成兩半）。r：鏈彈 7、實心與爆裂穿過 3。
 *  洞裡那一塊布不是消失：切成布片、照物理飄下去（34_shreds.js shredCut；b ＝ 砲彈）。 */
function tearCloth(sh, s, L, r, b) {
  var c = sh.cl && sh.cl[s.k]; if (!PHYS || !c || !c.p) return;
  var old = Uint8Array.from(c.tv);                                     // 撕之前藏著的（之前的洞）⇒ 只有這一發新藏的才變布片
  var T = c.T.sim, p = c.p, r2 = (r || 7) * (r || 7), bi = 0, bd = 1e9, i;
  for (i = 0; i < T.n; i++) { var dx = p[i * 3] - L[0], dy = p[i * 3 + 1] - L[1], dz = p[i * 3 + 2] - L[2], d = dx * dx + dy * dy + dz * dz; if (d < bd) { bd = d; bi = i; } }   // 照布現在的位置
  var cx = p[bi * 3], cy = p[bi * 3 + 1], cz = p[bi * 3 + 2];
  function near(q) { var dx = p[q * 3] - cx, dy = p[q * 3 + 1] - cy, dz = p[q * 3 + 2] - cz; return dx * dx + dy * dy + dz * dz < r2; }
  for (i = 0; i < T.ea.length; i++) if (near(T.ea[i]) || near(T.eb[i])) c.brk[i] = 1;
  for (i = 0; i < T.ba.length; i++) if (near(T.ba[i]) || near(T.bb[i])) c.bbrk[i] = 1;
  // 畫的那層：碰到斷掉約束的粗格點，從它內插的細格點都不畫（洞的邊緣多吃一圈）。
  // ⛔ 只藏彈點附近的細格點：粗格點間距約 1 m，常常只切斷一個粗格點 —— 它沒了約束一直往下掉，
  //   旁邊沒藏到的細格三角形還從它內插，被拉成一條條直到海裡的布帶（Tim 2026-10-12 截到）。
  var touch = new Uint8Array(T.n), mi = c.T.mi, mw = c.T.mw;
  for (i = 0; i < T.ea.length; i++) if (c.brk[i]) { touch[T.ea[i]] = 1; touch[T.eb[i]] = 1; }
  for (i = 0; i < c.T.n; i++) for (var k = 0; k < 4; k++) { var o = i * 4 + k; if (!mw[o]) break; if (touch[mi[o]]) { c.tv[i] = 1; break; } }
  c.torn = true;
  if (b) shredCut(sh, c, old, b);
}
function solve(ea, eb, rest, brk, p, pin, k) {
  for (var e = 0; e < ea.length; e++) {
    if (brk && brk[e]) continue;
    var a = ea[e], b = eb[e], wa = pin[a] ? 0 : 1, wb = pin[b] ? 0 : 1; if (!(wa + wb)) continue;
    var ia = a * 3, ib = b * 3, dx = p[ib] - p[ia], dy = p[ib + 1] - p[ia + 1], dz = p[ib + 2] - p[ia + 2], l = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (l < 1e-9) continue;
    var f = (l - rest[e]) / l * k / (wa + wb);
    if (wa) { p[ia] += dx * f; p[ia + 1] += dy * f; p[ia + 2] += dz * f; }
    if (wb) { p[ib] -= dx * f; p[ib + 1] -= dy * f; p[ib + 2] -= dz * f; }
  }
}
/** 落在格子裡（甲板、船殼）⇒ 退回上一步的位置（上一步本來就在格子裡的不管：繩頭從錨格裡長出來）。 */
function hitGrid(g, p, q, o) {
  if (g.get(Math.floor(p[o]), Math.floor(p[o + 1]), Math.floor(p[o + 2])) && !g.get(Math.floor(q[o]), Math.floor(q[o + 1]), Math.floor(q[o + 2]))) { p[o] = q[o]; p[o + 1] = q[o + 1]; p[o + 2] = q[o + 2]; }
}
function clothStep(sh, c, wl, gv) {                    // c.kw：風壓倍率（帆的布片，34_shreds.js；帆 ＝ 1）
  var T = c.T.sim, n = T.n, p = c.p, q = c.q, pin = c.pin, tr = T.tris, A = CACC, N = CCNT, HC = rigLv().every * DT, dt2 = HC * HC, inv = 1 / (3 * HC), dmp = DAMP * DAMP, kw = KW * (c.kw || 1), i, j, x;
  A.fill(0, 0, n * 3); N.fill(0, 0, n);
  for (j = 0; j < tr.length; j += 3) {           // 風壓：每個三角形沿法線推，大小 ∝（相對風在法線上的分量）²，相對風扣掉布自己的速度
    if (c.torn && (c.brk[T.te[j]] || c.brk[T.te[j + 1]] || c.brk[T.te[j + 2]])) continue;
    var a = tr[j] * 3, b = tr[j + 1] * 3, d = tr[j + 2] * 3;
    var ux = p[b] - p[a], uy = p[b + 1] - p[a + 1], uz = p[b + 2] - p[a + 2], vx = p[d] - p[a], vy = p[d + 1] - p[a + 1], vz = p[d + 2] - p[a + 2];
    var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx, l = Math.sqrt(nx * nx + ny * ny + nz * nz);
    if (l < 1e-9) continue;
    nx /= l; ny /= l; nz /= l;
    var rx = wl[0] - (p[a] - q[a] + p[b] - q[b] + p[d] - q[d]) * inv, ry = wl[1] - (p[a + 1] - q[a + 1] + p[b + 1] - q[b + 1] + p[d + 1] - q[d + 1]) * inv, rz = wl[2] - (p[a + 2] - q[a + 2] + p[b + 2] - q[b + 2] + p[d + 2] - q[d + 2]) * inv;
    var dn = rx * nx + ry * ny + rz * nz, f = kw * dn * Math.abs(dn);
    f *= 1 + FLUTTER * Math.sin((p[a] * 0.9 + p[a + 2]) * 0.06 - SIMT * 5.5);   // 一道一道走過布面的風（不抽亂數）
    var fx = f * nx, fy = f * ny, fz = f * nz;
    A[a] += fx; A[a + 1] += fy; A[a + 2] += fz; A[b] += fx; A[b + 1] += fy; A[b + 2] += fz; A[d] += fx; A[d + 1] += fy; A[d + 2] += fz;
    N[a / 3]++; N[b / 3]++; N[d / 3]++;
  }
  for (i = 0; i < n; i++) {
    if (pin[i]) continue;
    var o = i * 3, kk = N[i] ? 1 / N[i] : 0;
    for (x = 0; x < 3; x++) { var cur = p[o + x], vel = (cur - q[o + x]) * dmp; q[o + x] = cur; p[o + x] = cur + vel + (A[o + x] * kk + gv[x]) * dt2; }
    if (c.loose) hitGrid(sh.grid, p, q, o);
  }
  for (var it = 0, itn = rigLv().it; it < itn; it++) { solve(T.ea, T.eb, T.rest, c.torn ? c.brk : null, p, pin, 1); if (it & 1) solve(T.ba, T.bb, T.brest, c.torn ? c.bbrk : null, p, pin, 0.5); }
}
/** 剛斷的繩 ⇒ 垂下來的繩：重新取樣（每段 ≤ SEG 格，原本的弧度與鬆緊照留），兩端各記著靠什麼；被打斷的從斷點分成兩段。 */
function spawnLoose(sh, r) {
  var src = r.pts, m = src.length / 3, P = [], i, t;
  for (i = 0; i + 1 < m; i++) {
    var a = [src[i * 3], src[i * 3 + 1], src[i * 3 + 2]], b = [src[i * 3 + 3], src[i * 3 + 4], src[i * 3 + 5]], k = Math.max(1, Math.ceil(len(sub(b, a)) / SEG));
    for (t = 0; t < k; t++) P.push(lerp3(a, b, t / k));
  }
  P.push([src[m * 3 - 3], src[m * 3 - 2], src[m * 3 - 1]]);
  function end(an, mk, pr) { return an >= 0 ? [1, an] : mk !== undefined ? [4, mk] : pr !== undefined ? [2, pr] : [0, -1]; }
  var ea = end(r.a, r.ma, r.pa), eb = end(r.b, r.mb, r.pb), parts = [[P, ea, eb]];
  if (r.cutL) {
    var bi = 0, bd = 1e9;
    for (i = 0; i + 1 < P.length; i++) { var d = segDist2(r.cutL, P[i][0], P[i][1], P[i][2], P[i + 1][0], P[i + 1][1], P[i + 1][2]); if (d < bd) { bd = d; bi = i; } }
    parts = [[P.slice(0, bi + 1), ea, [0, -1]], [P.slice(bi + 1), [0, -1], eb]];
  }
  parts.forEach(function (pt) {
    var Q = pt[0], n = Q.length; if (n < 2) return;
    var p = new Float32Array(n * 3), rest = new Float32Array(n - 1);
    Q.forEach(function (w, j) { p[j * 3] = w[0]; p[j * 3 + 1] = w[1]; p[j * 3 + 2] = w[2]; if (j) rest[j - 1] = len(sub(w, Q[j - 1])); });
    var o = { p: p, q: Float32Array.from(p), rest: rest, n: n, pin: new Uint8Array(n), hk: [pt[1][0], pt[2][0]], hv: [pt[1][1], pt[2][1]], col: r.col, free: 0 };
    o.pin[0] = o.hk[0] ? 1 : 0; o.pin[n - 1] = o.hk[1] ? 1 : 0;
    ropePins(sh, o); sh.loose.push(o);
  });
  if (sh.loose.length > rigLv().loose) {                                  // 太多 ⇒ 先丟已經整條鬆掉的，再丟最早的
    var drop = sh.loose.findIndex(function (o) { return !o.pin[0] && !o.pin[o.n - 1]; });
    sh.loose.splice(drop >= 0 ? drop : 0, 1);
  }
}
function ropePins(sh, o) {
  if (o.pin[0] && !holds(sh, null, o.hk[0], o.hv[0])) o.pin[0] = 0;
  if (o.pin[o.n - 1] && !holds(sh, null, o.hk[1], o.hv[1])) o.pin[o.n - 1] = 0;
}
function ropeStep(sh, o, wl, gv) {
  var p = o.p, q = o.q, n = o.n, pin = o.pin, dt2 = DT * DT, i, x;
  for (i = 0; i < n; i++) {
    if (pin[i]) continue;
    var j = i * 3;
    for (x = 0; x < 3; x++) { var cur = p[j + x], vel = (cur - q[j + x]) * DAMP; q[j + x] = cur; p[j + x] = cur + vel + (gv[x] + KD * (wl[x] - vel / DT)) * dt2; }
    hitGrid(sh.grid, p, q, j);
  }
  for (var it = 0, itn = rigLv().it; it < itn; it++) for (i = 0; i + 1 < n; i++) {
    var wa = pin[i] ? 0 : 1, wb = pin[i + 1] ? 0 : 1; if (!(wa + wb)) continue;
    var ia = i * 3, ib = ia + 3, dx = p[ib] - p[ia], dy = p[ib + 1] - p[ia + 1], dz = p[ib + 2] - p[ia + 2], l = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (l < 1e-9) continue;
    var f = (l - o.rest[i]) / l / (wa + wb);
    if (wa) { p[ia] += dx * f; p[ia + 1] += dy * f; p[ia + 2] += dz * f; }
    if (wb) { p[ib] -= dx * f; p[ib + 1] -= dy * f; p[ib + 2] -= dz * f; }
  }
}
function underWater(sh, p, i) { var w = M4.pt(sh.M, p[i * 3], p[i * 3 + 1], p[i * 3 + 2]); return w[1] < seaH(w[0], w[2], SIMT) - 0.5; }
/** 每一步：相對風與重力換進船的格座標 → 剛斷的繩變成垂下來的繩 → 每面帆、每條垂下來的繩各走一步；每 0.1 秒量一次靠的東西還在不在。 */
function physStep(sh) {
  var W = norm(WIND), ws = WIND_SAIL * WIND_K * (1 + GUST[0] * Math.sin(SIMT * 0.9 + sh.phase) + GUST[1] * Math.sin(SIMT * 2.7 + 1.3) + GUST[2] * Math.sin(SIMT * 6.1 + sh.phase * 2)) * WX.wind * WIND_SPD;   // 陣風（不用亂數）；天氣：暴風雨 ×2.2；風速會變（08_weather.js）
  var wl = M4.dir(sh.inv, W[0] * ws - sh.vel[0], W[1] * ws - sh.vel[1], W[2] * ws - sh.vel[2]), gv = M4.dir(sh.inv, 0, -G, 0);
  var si = Math.round(SIMT / DT), chk = si % 6 === 0, i;
  if (sh.yards.length) { braceYards(sh, wl, DT); if (chk) yardRopes(sh); }
  for (i = 0; i < sh.ropes.length; i++) { var r = sh.ropes[i]; if (r.dead && !r.lz) { r.lz = true; if (!r.moved) spawnLoose(sh, r); } }
  sh.sails.forEach(function (s, k) {
    var c = sh.cl[k];
    if (c.gone) return;
    if (s.dead && !c.loose) {                                         // 物理打開之前就掉了的（late）⇒ 現在才垂下來；收著的時候掉的 ⇒ 不畫
      if (!c.late || s.furled) { c.gone = true; return; }
      clothInit(c); c.hidden = false; c.loose = true;
    }
    c.late = false;
    if (s.furled && !s.dead) { c.hidden = true; return; }
    if (c.hidden || !c.p) { var keep = c.p && c.torn ? { brk: c.brk, bbrk: c.bbrk, tv: c.tv } : null; clothInit(c); c.hidden = false; if (keep) { c.brk = keep.brk; c.bbrk = keep.bbrk; c.tv = keep.tv; c.torn = true; } }   // 收帆再張：形狀重來、破洞留著
    if (chk || c.npin < 0) clothPins(sh, s, c);
    yardPins(sh, c);
    var ev = rigLv().every;
    if ((si + k + sh.i + 1) % ev === 0) { var t0 = DEBUG ? performance.now() : 0; clothStep(sh, c, wl, gv); if (DEBUG) PROF.cloth += performance.now() - t0; }
    if (chk && c.loose && !c.npin) { c.free += 0.1; if (c.free > 12 || underWater(sh, c.p, 0) && underWater(sh, c.p, c.T.sim.n >> 1)) c.gone = true; }
  });
  for (i = 0; i < sh.loose.length; i++) {
    var o = sh.loose[i];
    if (chk) {
      ropePins(sh, o);
      if (!o.pin[0] && !o.pin[o.n - 1]) { o.free += 0.1; if (o.free > 15 || underWater(sh, o.p, 0) && underWater(sh, o.p, o.n - 1)) { sh.loose.splice(i--, 1); continue; } }
    }
    var t1 = DEBUG ? performance.now() : 0; ropeStep(sh, o, wl, gv); if (DEBUG) PROF.rope += performance.now() - t1;
  }
  var t2 = DEBUG ? performance.now() : 0; shredStep(sh, wl, gv, si, chk); if (DEBUG) PROF.shred += performance.now() - t2;   // 帆的布片（34_shreds.js）
}
/** 開關物理（選單、B 鍵、下方按鈕）：開 ⇒ 帆從雕刻作品那一刻的形狀開始動；之前就斷掉的繩、掉下來的帆也垂下來
 *  （被斷開的那一團帶走的、一開始就不畫的除外）。關 ⇒ 回到靜態。 */
function setPhys(on) {
  PHYS = on;
  if (on && !PHX.rig) PHX.rig = PHX_RIG_LAST; else if (!on && PHX.rig) { PHX_RIG_LAST = PHX.rig; PHX.rig = 0; }   // 物理分級的「帆與繩」跟著走（09_phx.js）
  $('physT').classList.toggle('on', on); if (typeof phxShow === 'function' && $('phxB')) phxShow();
  SHIPS.forEach(function (sh) {
    sh.loose = []; sh.shreds = [];
    if (!on) { (sh.yards || []).forEach(function (m) { m.rot = 0; }); if (sh.yRopes) yardRopes(sh, true); }   // 關 ⇒ 帆桁回到作品的角度
    sh.ropes.forEach(function (r) { r.lz = !!(r.never || r.moved); });
    sh.cl.forEach(function (c, k) { c.p = null; c.hidden = true; c.loose = false; c.torn = false; c.gone = !!c.moved; c.late = sh.sails[k].dead; });
    sh.rigDirty = true;
  });
  if (RUNNING && SHIPS.length) note(SHIPS[PLAYER_I], on ? '帆與繩的物理：開（帆被風吹鼓、斷掉的會垂下來）' : '帆與繩的物理：關（靜態）');
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/31_sailing.js ──
// ───────────────────────── 航行 ─────────────────────────
// 航速 ＝ VMAX × 還在的帆面積比例 × 風向係數（POLAR）×（進水越多越慢）；降旗 ⇒ 停船（heave to），沉了 ⇒ 0。加減速時間常數 20 秒（船重）。
// 自動操舵：讓敵艦保持在 sh.side 那一舷的正橫（sh.side ＝ 敵艦現在在哪一舷，見 chooseSide），太遠往敵艦偏、太近偏開
// ⇒ 兩艘都用同一舷 ⇒ 繞著彼此轉；一艘一舷 ⇒ 並肩同向。兩舷各有砲班、各自開火，船不必為了開火換舷。
// 手動操舵（我艦）：A／D ＝ 畫面上的左轉／右轉（打滿與回正各要 0.7 秒），轉向率 ＝ 舵角 × 最大轉向率。
// 轉向率跟航速成正比（舵要有水流過）；舵輪被打飛 ⇒ 改用舵柄滑車，只剩 35%。
// 帆裝三段（W／S）：收帆（三面上桅帆＋jib）／戰鬥帆（再加上桅頂帆、後桅縱帆、前支索帆）／滿帆（全部，預設）；
// 收起來的帆不畫、鏈彈打不到、不算航速；帆收得越多瞄得越穩。
// 頂風失速（只管手動操舵；電腦操舵照舊 —— 它不會搶風，失速會卡死）：風從船頭兩側 60° 以內吹來 ⇒ 帆被吹回來，
//   推力 ×(1 − 失速)；船頭被風推開（往原本那一舷倒，航速一半以下推得動、越慢越大）⇒ 帶著速度才轉得過去（搶風 tack），
//   太慢就卡住、被推回原本那一舷；往下風轉一圈（順風換舷 wear）永遠轉得過去。45° 以內全失速、45–60° 漸變。
//   量過（2026-10-13，滿帆、舵打滿往風裡轉）：寫實 ⇒ 從近迎風（風從船頭 65°）卡住、從橫風帶 6.5 節 71 秒搶過；娛樂 ⇒ 從近迎風 48 秒搶過。
//   失速 ＝ 細節設定的「頂風失速」（0 ＝ 頂風只是慢，係數 0.25 靠慣性帶過去）× 玩法的加成（娛樂 0.4）。
var VMAX = 3.6;                                                    // m/s（約 7 節）：滿帆、側順風
var NOGO_DEG = 60, NOGO_FULL = 45, IRONS_PUSH = 0.02;              // 頂風失速：開始、全失速的角度（風從船頭偏幾度）、船頭被推開的轉向率（rad/s，船停住時）
var POLAR = [[0, 0.72], [45, 1], [90, 0.92], [112, 0.6], [125, 0.32], [180, 0.25]];   // 船頭跟「風吹去的方向」的夾角（度）→ 係數
function polar(deg) {
  for (var i = 1; i < POLAR.length; i++) if (deg <= POLAR[i][0]) { var a = POLAR[i - 1], b = POLAR[i]; return a[1] + (b[1] - a[1]) * (deg - a[0]) / (b[0] - a[0]); }
  return POLAR[POLAR.length - 1][1];
}
function pointName(deg) { return deg < 30 ? '順風' : deg < 70 ? '側順風' : deg < 105 ? '橫風' : deg < 125 ? '迎風' : '頂風'; }
function sailArea(s) {
  var v = s.verts, A = 0;
  for (var j = 0; j < s.tris.length; j += 3) {
    var a = s.tris[j] * 3, b = s.tris[j + 1] * 3, d = s.tris[j + 2] * 3;
    A += len(cross([v[b] - v[a], v[b + 1] - v[a + 1], v[b + 2] - v[a + 2]], [v[d] - v[a], v[d + 1] - v[a + 1], v[d + 2] - v[a + 2]])) / 2;
  }
  return A;
}
/** 船型 T 的水線（z ＝ T.zw）上船體的前後端（中線附近，T.wl0／wl1）與船頭浪位置的半寬（T.bowHalf）。⛔ 用外框 ⇒ 船頭浪出現在船首前面 24 m 的水上。 */
function waterline(T) {
  var x0 = 1e9, x1 = -1, x, y, lo = 1e9, hi = -1, G = T.base, CY = T.cy, ZW = T.zw;
  for (x = 0; x < G.sx; x++) for (y = CY - 60; y <= CY + 60; y++) if (G.get(x, y, ZW)) { if (x < x0) x0 = x; if (x > x1) x1 = x; break; }
  T.wl0 = x0; T.wl1 = x1;
  for (y = 0; y < G.sy; y++) if (G.get(x1 - 25, y, ZW)) { if (y < lo) lo = y; if (y > hi) hi = y; }
  T.bowHalf = hi >= lo ? (hi - lo) / 2 + 3 : 20;
}
function fwd(yaw) { return [Math.cos(yaw), 0, -Math.sin(yaw)]; }          // 船頭（格 +x）在世界的方向；yaw 變大 ＝ 往格 −y（左舷 P）那一側轉 ＝ 畫面上的左轉
function sideName(side) { return side === 'S' ? '右舷' : '左舷'; }        // 模型的 S（格 +y）＝ 右舷（shipBaseMatrix 照雕刻引擎的手性）
var SAILSETS = ['全收', '收帆', '戰鬥帆', '滿帆'];
/** 帆裝 k 張不張這面帆：0 全收（一面都不張）／1 收帆（三面上桅帆＋jib）／2 戰鬥帆（再加上桅頂帆、後桅縱帆、前支索帆）／3 滿帆。
 *  收起來的帆不畫、不算航速、鏈彈打不到、依靠的格或繩斷了也不掉 —— 只有桅斷了（依靠跟著斷開的那一團走）才跟著走。 */
/** 帆裝（W／S）：這面帆最少在哪一段打開（1 收帆、2 戰鬥帆、3 滿帆）。
 *  照 meta（TASK-0539，造船規格 §9.1）：有 `set` ⇒ 照它；否則照種類 `sail` 的預設（topsail、jib 1；topgallant、gaff 2；其他 3）。
 *  沒有 meta 的舊匯出照名字（以前的規則，一一對應：結尾 topsail、jib ⇒ 1；結尾 topgallant、spanker、fore-topmast-staysail ⇒ 2；其他 3）。 */
var SAIL_SET0 = { topsail: 1, jib: 1, topgallant: 2, gaff: 2 };
function sailSetLevel(s) {
  var m = s.meta;
  if (m && m.kind === 'sail' && m.sail) return +m.set || SAIL_SET0[m.sail] || 3;
  var name = s.name;
  if (/topsail$/.test(name) || name === 'jib') return 1;
  if (/topgallant$/.test(name) || name === 'spanker' || name === 'fore-topmast-staysail') return 2;
  return 3;
}
function setHas(s, k) {
  if (k >= 3) return true;
  if (k <= 0) return false;
  return sailSetLevel(s) <= k;
}
/** 旗（餘燼號階段十九：船尾旗 ensign、主桅長旗 pennant；繩帆格式裡也是「帆」，沒有 meta ⇒ 照名字）：不收、不算推力；降旗時船尾旗降下來（strikeColors）。 */
/** 旗：照 meta `kind=flag`（TASK-0539）；有 meta 但不是 flag ⇒ 不是；沒有 meta 的舊匯出照名字（ensign／pennant／flag 開頭）。 */
function isFlag(s) { var m = s.meta; if (m && m.kind) return m.kind === 'flag'; return /^(ensign|pennant|flag)/.test(s.name); }
/** 降旗：降船尾旗（meta `flag=ensign`；沒有 meta ⇒ 名字叫 ensign 的那面）。 */
function strikeColors(sh) { sh.sails.forEach(function (s) { if (s.flag && (s.meta && s.meta.kind ? s.meta.flag === 'ensign' : s.name === 'ensign')) { s.furled = true; s.struck = true; } }); sh.rigDirty = true; }
function applySailSet(sh) { sh.sails.forEach(function (s) { s.furled = s.flag ? !!s.struck : !setHas(s, sh.sailSet); }); sh.rigDirty = true; }
function setSails(sh, k) {
  k = clamp(k, 0, SAILSETS.length - 1); if (k === sh.sailSet) return;
  sh.sailSet = k; applySailSet(sh); note(sh, '帆裝：' + SAILSETS[k]);
}
function sideGuns(sh, side) { return sh.guns.filter(function (g) { return g.alive && gunRate(g) > 0 && g.side === side; }).length; }   // 這一舷開得動的砲
function sail(sh, dt) {
  var F = fwd(sh.yaw), W = norm(WIND), deg = Math.acos(clamp(dot(F, W), -1, 1)) * 57.2958;
  var UP = sh.cfg.upwind || 1, dU = UP === 1 || deg <= 90 ? deg : 90 + (deg - 90) / UP;   // 逆風性能：迎風那一半的角度壓縮（1.25 ⇒ 風從船頭 52.5° 才開始失速、45° 跑得像 36° 的船…）；1 ⇒ 一位元都不動
  sh.sailFrac = sh.sails.reduce(function (a, s) { return a + (s.dead || s.furled ? 0 : s.area * s.hp / s.hpMax); }, 0) / sh.sailArea0;   // 被打中還沒掉的帆：照剩下的血量算推力
  sh.pos = pointName(deg);
  var stop = SAIL === 'off', manual = SAIL === 'manual' && sh.i === PLAYER_I;
  sh.manual = manual;
  var SPK = sh.cfg.speed * playK('speed') * WX.speed;                 // 航速倍率（船隻設定 × 玩法的加成 × 天氣：暴風雨風大 ×1.15）
  var nogo = manual && !stop && !sh.sunk ? STALL_K * playK('stall') * clamp((NOGO_DEG - (180 - dU)) / (NOGO_DEG - NOGO_FULL), 0, 1) : 0;   // 頂風失速的程度
  sh.irons = nogo;
  var target = sh.sunk || stop ? 0 : VMAX * SPK * Math.sqrt(WIND_SPD) * sh.sailFrac * polar(dU) * (1 - nogo) * (1 - clamp(sh.sink / 9, 0, 0.8)) * (sh.struck ? 0.15 : 1);
  if (sh.spd0) { sh.spd = target; sh.spd0 = false; }                    // 開局就在走
  sh.spd += (target - sh.spd) * Math.min(1, dt / (stop ? 6 : 20));     // 停船：收帆、轉進風裡，6 秒內停下
  // 舵
  var foe = foeOf(sh), tY = sh.yaw, rate = 0;
  var wheel = sh.models.some(function (m) { return m.kind === 'wheel' && m.alive; });
  var rud = sh.models.filter(function (m) { return m.kind === 'rudder'; }), rudK = rud.length && !rud.some(function (m) { return m.alive; }) ? 0.12 : 1;   // 舵是模型（夜隼號）而且被打掉了 ⇒ 只剩調帆轉向
  var rmax = (0.012 + 0.016 * sh.spd / SPK) * (wheel ? 1 : 0.35) * rudK * (UP === 1 ? 1 : 1 + (UP - 1) * clamp((deg - 90) / 45, 0, 1)) * sh.cfg.agile * playK('agile') * WX.agile;   // 天氣：暴風雨浪大、舵難使 ×0.8。⛔ 用 sh.spd 直接算 ⇒ 調快航速連帶變得更會轉
  if (stop) { sh.rudder = 0; rate = 0; }
  else if (manual && !sh.struck && !sh.sunk) {
    var want = (KEYS.l ? 1 : 0) - (KEYS.r ? 1 : 0);                    // 舵角正 ＝ yaw 變大 ＝ 畫面上左轉
    sh.rudder += clamp(want - sh.rudder, -1.5 * dt, 1.5 * dt);
    rate = sh.rudder * rmax;
    if (nogo > 0) {                                                     // 船頭被風推開：往讓船頭離開風的那一側（正頂風 ⇒ 照上次那一側）
      var off = -Math.sin(sh.yaw) * W[0] - Math.cos(sh.yaw) * W[2];     // d(船頭·風吹去的方向)/d(yaw)：正 ＝ yaw 變大會離開風
      if (Math.abs(off) > 0.02) sh.ironSide = off > 0 ? 1 : -1;
      rate += (sh.ironSide || 1) * nogo * IRONS_PUSH * clamp(1 - sh.spd / (VMAX * SPK * 0.5), 0, 1);
      if (nogo > 0.5 && !(SIMT - (sh.ironsT || -99) < 20)) { sh.ironsT = SIMT; note(sh, '頂風失速：帆被吹回來了 —— 帶著速度轉過去，或往下風轉一圈'); }
    }
  } else {
    if (!sh.struck && !sh.sunk && foe) {
      // 這一舷的砲都開不了、另一舷還有 ⇒ 把另一舷轉向敵艦
      var other = sh.side === 'S' ? 'P' : 'S', present = sideGuns(sh, sh.side) || !sideGuns(sh, other) ? sh.side : other, sg = present === 'P' ? 1 : -1;   // sg：敵艦要在畫面左邊（左舷 P）⇒ +1
      var dx = foe.px - sh.px, dz = foe.pz - sh.pz, d = Math.hypot(dx, dz) || 1;
      tY = (sg > 0 ? Math.atan2(-dx / d, -dz / d) : Math.atan2(dx / d, dz / d)) + sg * clamp((d - DIST) / DIST * 1.5, -0.4, 0.4);   // 敵艦在那一舷正橫的航向 ＋ 距離修正
    }
    if (!sh.struck && !sh.sunk) { var av = friendAvoid(sh); if (av !== null) tY = av; }   // 讓友船（52_fleet.js；沒有友船 ⇒ null）
    var e = Math.atan2(Math.sin(tY - sh.yaw), Math.cos(tY - sh.yaw));
    rate = clamp(e * 0.5, -rmax, rmax); sh.rudder = rmax > 0 ? rate / rmax : 0;
  }
  sh.yawRate += (rate - sh.yawRate) * Math.min(1, dt / 2);
  sh.yaw += sh.yawRate * dt;
  F = fwd(sh.yaw);
  sh.vel = mul(F, sh.spd);
  sh.px += sh.vel[0] * dt; sh.pz += sh.vel[2] * dt;
  // 航跡：船尾留一條白沫、船頭兩側推出的浪（點精靈，不撞任何東西）；船邊水花開著 ⇒ 換成 13_water.js 的（這裡照樣抽亂數、不放進去）
  if ((sh.wakeT -= dt) <= 0 && sh.spd > 0.4 && sh.sink < 6) {
    sh.wakeT = 0.12; PT_MUTE = PHX.water > 0;
    var T = sh.T, st = M4.pt(sh.M, T.wl0 - 4, T.cy, T.zw);
    spawnPt([st[0] + gauss() * 0.8, seaH(st[0], st[2], SIMT) + 0.06, st[2] + gauss() * 0.8], [0, 0, 0], rr(9, 13), [0.93, 0.96, 1], 0.3 * Math.min(1, sh.spd / 2), rr(1.2, 2), rr(4, 6), 0, 0, 2);
    [1, -1].forEach(function (k) {
      var bw = M4.pt(sh.M, T.wl1 - 25, T.cy + k * T.bowHalf, T.zw), out = M4.dir(sh.M, 0, k, 0); out = norm([out[0], 0, out[2]]);
      spawnPt([bw[0], seaH(bw[0], bw[2], SIMT) + 0.08, bw[2]], mul(out, rr(0.4, 1) * sh.spd * 0.4), rr(1.5, 2.5), [0.95, 0.97, 1], 0.5, rr(0.8, 1.3), rr(2, 3), 0, 0, 2);
    });
    PT_MUTE = false;
  }
}

/** 兩艘的龍骨線（各取 7 點）最近不到 14 公尺 ⇒ 沿那個方向各推開一半、航速掉一點（⛔ 不推 ⇒ 手動開過去會穿船）。
 *  任兩艘都算（TASK-0537；照 SHIPS 的順序兩兩配對，一對一 ＝ 以前那一對）；龍骨線每艘只算一次。 */
function collide() {
  if (SHIPS.length < 2) return;
  function keel(sh) { var T = sh.T, r = []; for (var k = 0; k < 7; k++) r.push(M4.pt(sh.M, T.wl0 + 15 + (T.wl1 - T.wl0 - 30) * k / 6, T.cy, T.zw)); return r; }
  var K = SHIPS.map(keel);
  for (var i = 0; i < SHIPS.length; i++) for (var j = i + 1; j < SHIPS.length; j++) collidePair(SHIPS[i], SHIPS[j], K[i], K[j]);
}
function collidePair(A, B, ka, kb) {
  var best = 1e9, pa = null, pb = null;
  ka.forEach(function (a) { kb.forEach(function (b) { var d = Math.hypot(a[0] - b[0], a[2] - b[2]); if (d < best) { best = d; pa = a; pb = b; } }); });
  if (best >= 14) return;
  var n = best > 1e-3 ? [(pa[0] - pb[0]) / best, 0, (pa[2] - pb[2]) / best] : [0, 0, 1], push = (14 - best) / 2;
  A.px += n[0] * push; A.pz += n[2] * push; B.px -= n[0] * push; B.pz -= n[2] * push;
  A.spd *= 0.97; B.spd *= 0.97;
  wpBump(pa, pb, A, B);                                                // 船邊水花（13_water.js；只給人看）
  if (SIMT - (A.bumpT || -9) > 5) { A.bumpT = SIMT; sfx('crack', pa, 1); note(SHIPS[PLAYER_I], '兩艘擦撞'); }
}
/** 敵艦在哪一舷（給自動操舵用；有遲滯，不在正前／正後來回跳）。只影響操舵 —— 開火是每門砲各自看對不對得到。 */
function chooseSide(sh) {
  var foe = foeOf(sh); if (!foe || !foe.center || sh.struck || sh.sunk) return;   // 開局逐艘量的時候，另一艘可能還沒算過位置
  var st = M4.dir(sh.M, 0, 1, 0), dx = foe.center[0] - sh.center[0], dz = foe.center[2] - sh.center[2];
  var k = (dx * st[0] + dz * st[2]) / ((Math.hypot(dx, dz) || 1) * (Math.hypot(st[0], st[2]) || 1));
  var want = k > 0.2 ? 'S' : k < -0.2 ? 'P' : sh.side;
  if (want === sh.side) return;
  sh.side = want;
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/32_hull.js ──
// ───────────────────────── 進水、傾斜、沉沒、減重上浮 ─────────────────────────
// 減重上浮（Tim 2026-10-12：打爛的船變輕、浮起來 ⇒ 彈藥庫有機會露出水面被打到）：
//   船的重量 ＝ 格（每格 0.7 kg，木頭）＋ 砲（砲種表：24 磅長砲 2.5 噸、32 磅長砲 2.9、carronade 0.9、追擊砲 2.1，乘船隻設定「砲的重量」）＋ 火藥桶（50 kg）
//   ＋ 壓艙物（細節設定；不會被打掉的重量：壓艙鐵與石、水、糧、彈丸…）。
//   浮在哪 ＝ 排水剛好等於重量的那一層（HYD：原本船殼每一層的體積，每個 x 照最外兩格之間的寬，從設計水線往下、往上積）：
//   設計水線（ZW）以下 ＝ 2,156 噸（史料約 2,200）⇒ 比它輕就浮高、重就吃水深。預設壓艙物 1,075 噸 ⇒ 開戰時剛好在設計水線；
//   壓艙物調輕 ⇒ 一開始就浮得高（0 噸 ⇒ 約 1.9 m，彈藥庫頂離水面不到半公尺）；砲調重 ⇒ 吃水深、砲被打飛浮得多。
//   打掉的格（含跟著斷開的一團走的）、不在船上的模型（飛掉、炸掉）⇒ 少掉那些重量 ⇒ 慢慢浮上去（每半秒量一次、3 秒浮到；開戰那一刻直接放好）。
//   打掉 10 萬格 ＝ 70 噸 ⇒ 浮 0.12 m。量過：預設浮 0.04–0.2 m、照樣會沉；壓艙物 0 ⇒ 浮 2.0–2.25 m、洞都離水、420 秒沒沉，彈藥庫也沒被打到（電腦瞄水線上 2.7 m）。
//   進水跟著浮起來的水線算（Tim）：洞浮出水面就不進水。開始沉的門檻照舊只看進水（sh.sink）。斷成兩截、開始沉之後不再往上浮。
//   ⛔ 先做過放大倍率（Tim：不用到 4 倍）：16 倍 ⇒ 打得最爛的船整艘浮到 6.3 m；4 倍 ⇒ 浮 0.5–0.9 m —— 兩種都讓水線附近的洞全部離水，三種子 420 秒沒有一艘沉（不浮 240–350 秒沉）。
//     又做過「總重固定、壓艙物只改每格多重」：拉桿幾乎沒感覺，而且壓艙物少了船卻沒浮高 —— 不像壓艙物。
var VOX_T = 0.0007, KEG_T = 0.05, RHO_W = 1.025, LIFT_TAU = 3;   // 砲的重量在砲種表（GUNS，10_ship.js）
/** 船型 T 的浮力表：T.hyd[z] ＝ 原本船殼 z 層到設計水線（T.zw）之間的體積（m³；水線上的層 ⇒ 負的），z ＝ 0 … zw＋60（水線上 6 m：粒子模式的進水要算到下沉 4.2 m 以上，33_flood.js）；T.disp ＝ 設計水線的排水量（噸）。載入時算一次。 */
function hydrostatics(T) {
  var BASE = T.base, ZW = T.zw, sx = BASE.sx, top = Math.min(BASE.sz, ZW + 60), lo = new Int16Array(sx * top).fill(-1), hi = new Int16Array(sx * top), A = new Float64Array(top), z;
  BASE.each(function (x, y, z) { if (z >= top) return; var k = z * sx + x; if (lo[k] < 0 || y < lo[k]) lo[k] = y; if (y > hi[k]) hi[k] = y; });
  for (z = 0; z < top; z++) { var a = 0; for (var x = 0; x < sx; x++) { var k = z * sx + x; if (lo[k] >= 0) a += hi[k] - lo[k] + 1; } A[z] = a * S * S * S; }   // 那一層的體積
  var HYD = T.hyd = new Float32Array(top + 1);
  for (z = ZW - 1; z >= 0; z--) HYD[z] = HYD[z + 1] + A[z];
  for (z = ZW + 1; z <= top; z++) HYD[z] = HYD[z - 1] - A[z - 1];
  T.disp = HYD[0] * RHO_W;                                                        // 設計水線的排水量（噸）
}
function modelT(m, gunw) { return m.kind === 'powder' ? KEG_T : (GUNS[m.kind] ? GUNS[m.kind].mass : 0) * gunw; }   // 模型的重量（砲乘船隻設定的倍率）
/** 開戰時的重量（噸）：格 ＋ 模型 ＋ 壓艙物。 */
function shipT(sh) { var t = sh.orig * VOX_T + sh.cfg.ballast; sh.models.forEach(function (m) { t += modelT(m, sh.cfg.gunw); }); return t; }
/** 少掉的重量（噸）：格（被打掉、跟著斷開的一團走）＋ 不在船上的模型（飛掉、炸掉、跟著斷開的一團走）。帆桁不算。 */
function massLost(sh) {
  var t = (sh.orig - sh.grid.count) * VOX_T;
  sh.models.forEach(function (m) { if (!m.alive || m.moved) t += modelT(m, sh.cfg.gunw); });
  return t;
}
/** 船型 T 比設計水線的排水輕 t 噸（負 ＝ 重）⇒ 浮高幾公尺（負 ＝ 吃水深）；還沒有船型 ⇒ null。 */
function liftFor(T, t) {
  if (!T || !T.hyd) return null;
  var HYD = T.hyd, ZW = T.zw, dv = t / RHO_W, n = HYD.length - 1, z;
  if (dv >= HYD[0]) return ZW * S;
  for (z = 0; z < n; z++) if (HYD[z + 1] <= dv) return (ZW - z - (HYD[z] - dv) / (HYD[z] - HYD[z + 1])) * S;
  return (ZW - n) * S;
}
function stepShip(sh, dt) {
  // 進水：水線下每個破洞的流量 ∝ √(水深)（貼著水面的洞進得慢）；抽水機每秒抽掉一點 ⇒ 小洞撐得住
  var wz = Math.min(sh.T.sz - 1, Math.floor(sh.T.zw + (sh.sink - sh.lift - sh.bob) / S)), N = 0, Q = 0, Dsp = 0, Dbs = 0;
  for (var z = 0; z <= wz; z++) { var c = sh.flood[z * 3]; if (!c) continue; N += c; Q += c * Math.sqrt((wz - z) * S + 0.05); Dsp += sh.flood[z * 3 + 1]; Dbs += sh.flood[z * 3 + 2]; }
  sh.inflow = N;
  var fk = sh.broken ? Math.max(sh.cfg.flood, 0.6) : sh.cfg.flood;                       // 斷成兩截 ⇒ 一定沉（進水速度 0 也沉）
  var fl = sh.fl && !sh.broken ? sh.fl : null;                                   // 粒子模式（33_flood.js）：進水、下沉、傾斜照艙內的水；斷成兩截照舊用公式（一定沉）
  if (fl && !sh.sinkingFinal && !sh.sunk) floodStep(sh, fl, dt);                 // 開始沉之後不再算水（船要下去了；⛔ 照算 ⇒ 沉掉的船積到 8 萬噸、白耗 CPU）
  if (!sh.sunk) {
    if (fl) { if (!sh.sinkingFinal) sh.sink += (floodSinkT(sh, fl) - sh.sink) * Math.min(1, dt / FL_TAU); }   // 照艙內的水該多吃水多少，慢慢跟過去
    else sh.sink = Math.max(0, sh.sink + Math.min(Q * 1.1e-5 - 0.004, 0.25) * fk * dt);   // 進水與抽水一起照滑桿縮放（⛔ 只縮進水 ⇒ 調慢之後抽水永遠贏、永遠不沉）；
                                                                              // 上限 0.25 m/s：彈藥庫殉爆打掉三十幾萬格 ⇒ 不設上限兩秒就沉完，看不到船斷開
    if (sh.sink > 4.2 && !sh.sinkingFinal && fk > 0) { sh.sinkingFinal = true; note(sh, '進水太多，開始沉了'); }
    if (sh.sinkingFinal) { sh.sinkV += 0.06 * fk * dt; sh.sink += sh.sinkV * dt; }
    if (sh.sink > 9) { sh.sunk = true; note(sh, '沉沒', true); }
  } else { sh.sinkV = Math.min(sh.sinkV + 0.05 * dt, 1.2); sh.sink += sh.sinkV * dt; }
  // 傾斜：破洞那一舷往下（格座標 +y ＝ 船體 +Z（右舷）；繞 +X 轉正角時 +Z 那邊下沉）；粒子模式照水的重心（33_flood.js floodTilt）
  var tl = fl ? floodTilt(sh, fl) : null;
  var rollT = tl ? tl[0] : clamp(Dsp / (N + 900), -1, 1) * (sh.sinkingFinal ? 0.55 : 0.21);
  var pitchT = tl ? tl[1] : -clamp(Dbs / (N + 1500), -1, 1) * 0.07;
  sh.rollV += ((rollT - sh.rollA) * 0.9 - sh.rollV * 0.8) * dt;
  sh.rollA += sh.rollV * dt;
  sh.pitchA += (pitchT - sh.pitchA) * 0.3 * dt;
  stepWaves(sh, dt);                                                            // 浪：起伏、縱搖、橫搖（08_sea.js；以前是兩條固定的正弦）
  sh.lift += (sh.liftT - sh.lift) * Math.min(1, dt / LIFT_TAU);                    // 減重上浮：慢慢浮上去（目標每半秒在 survey 量一次）
  sh.M = M4.mul(shipMatrix(sh), M4.ident()); sh.inv = M4.inv(sh.M);
  sh.center = shipCenter(sh); sh.rad2 = 62 * 62;
  manning(sh);
  for (var i = 0; i < sh.guns.length; i++) {
    var g = sh.guns[i]; if (!(g.reload > 0)) continue;
    if (g.needCart) { if (g.box > 0 && gunRate(g) > 0) { g.box--; g.needCart = false; } else continue; }   // 裝填要一份火藥與彈藥：藥箱空了 ⇒ 等送藥手（不倒數）
    g.reload -= dt * gunRate(g);                                    // 人少裝填慢、沒人不裝填
  }
}
function survey(sh) {               // 每半秒量一次：砲還在不在、桅還在不在、繩與帆的錨還在不在、少掉多少重量
  var alive = 0;
  sh.models.forEach(function (m) {
    if (!m.alive) return;
    var f = m.foot, x = f & 1023, y = (f >> 10) & 1023, z = f >> 20;
    if (!countBox(sh.grid, x - 2, y - 2, z - 1, x + 2, y + 2, z)) blowModel(sh, m, [0, -1, 0], true);   // 腳下的甲板被打掉 ⇒ 掉下去
  });
  sh.guns.forEach(function (g) { if (g.alive) g.alive = g.model.alive; if (g.alive) alive++; });   // 砲都是模型：模型飛了（血量歸零、腳下甲板沒了）砲就沒了
  sh.gunsAlive = alive;
  var up = 0;
  sh.masts.forEach(function (m) { if (m.up) { m.up = countBox(sh.grid, m.x - 8, sh.T.cy - 8, m.z0, m.x + 8, sh.T.cy + 8, m.z1) > m.orig * 0.3; if (!m.up) note(sh, m.name + '倒了'); } if (m.up) up++; });
  sh.mastsUp = up;
  sh.ropes.forEach(function (r) { if (r.dead) return; if ((r.a >= 0 && !gp(sh.grid, r.a)) || (r.b >= 0 && !gp(sh.grid, r.b))) { r.dead = true; sh.rigDirty = true; } });
  sh.ropes.forEach(function (r) { if (!r.dead && r.par && r.par.some(function (j) { return sh.ropes[j].dead; })) { r.dead = true; sh.rigDirty = true; } });
  sh.sails.forEach(function (s) {
    if (!s.dead && !s.furled && (s.as.some(function (a) { return !gp(sh.grid, a); }) || s.par.some(function (j) { return sh.ropes[j].dead; }) ||
        (s.yards || []).some(function (y) { return !y.alive && !y.moved; }))) dropSail(sh, s);   // 掛它的帆桁被打斷或掉了 ⇒ 帆掉
  });
  sh.crew.forEach(function (c) {   // 腳下 3×3 都沒了 ⇒ 掉下去（走路中的不算：途中跨過艙口邊）
    if (c.st >= 3 || c.walk || c.moving) return;
    var x = Math.floor(c.pos[0]), y = Math.floor(c.pos[1]);
    if (!countBox(sh.grid, x - 1, y - 1, c.pos[2] - 1, x + 1, y + 1, c.pos[2] - 1)) fall(sh, c);
  });
  if (sh.mass0 === undefined) sh.mass0 = shipT(sh);                               // 開戰時的重量（壓艙物、砲的重量照開戰時的設定）
  if (!sh.broken && !sh.sinkingFinal && !sh.sunk) sh.liftT = liftFor(sh.T, sh.T.disp - sh.mass0 + massLost(sh)) || 0;   // 斷了、開始沉 ⇒ 不再往上浮
  if (!sh.liftSet) { sh.lift = sh.liftT; sh.liftSet = true; }                    // 開戰那一刻直接放在浮的位置（不從設計水線慢慢浮過去）
  if (sh.fl) sh.flBase = sh.T.disp - sh.mass0 + massLost(sh);                     // 粒子模式：浮力表上水以外的部分（33_flood.js floodSinkT）
  drownCheck(sh);                                                     // 船殼通海了 ⇒ 被水淹過頭的人浮上來（43_swim.js）
  chooseSide(sh); reassign(sh); manning(sh); callHands(sh);   // callHands：預備水手補位（42_hands.js）
  sh.able = sh.crew.filter(able).length;
  sh.gunsManned = sh.guns.filter(function (g) { return g.alive && gunRate(g) > 0; }).length;
  strikeCheck(sh);
}
/** 降旗：規則在選單設定（STRIKE），每半秒量一次。死傷 ＝ 1 − 還能動的／開戰時的人數（傷與亡都算）。
 *  全員倒下一定停（死傷門檻上限就是 100%）—— 那不是投降，是沒人能打了。 */
function strikeCheck(sh) {
  if (sh.struck || sh.sunk) return;
  var cas = 1 - sh.able / sh.crew0, pc = '死傷 ' + Math.round(cas * 100) + '%';
  if (sh.gunsManned > 0) sh.silentT = -1; else if (sh.silentT < 0) sh.silentT = SIMT;   // 砲全啞：毀了或沒人操作
  var why = null;
  if (sh.able === 0) why = '全員倒下';
  else if (cas >= STRIKE.cas) why = '降旗（' + pc + '）';
  else if (STRIKE.guns && sh.silentT >= 0 && SIMT - sh.silentT >= 10) why = '降旗（砲全啞 10 秒）';
  else if (STRIKE.masts && sh.mastsUp === 0 && cas >= 0.33) why = '降旗（桅全倒、' + pc + '）';
  else if (STRIKE.officers && cas >= 0.25 && !sh.crew.some(function (c) { return c.role === ROLE.OFFICER && able(c); })) why = '降旗（軍官全倒、' + pc + '）';
  if (!why) return;
  sh.struck = true; sh.fate = why; note(sh, why, true); strikeColors(sh);
}
/** 選單與結算畫面用的一句話：現在的降旗規則。 */
function strikeText() {
  var r = [];
  if (STRIKE.cas < 1) r.push('死傷 ' + Math.round(STRIKE.cas * 100) + '%');
  if (STRIKE.guns) r.push('砲全啞 10 秒');
  if (STRIKE.masts) r.push('桅全倒且死傷 ≥ 33%');
  if (STRIKE.officers) r.push('軍官全倒且死傷 ≥ 25%');
  return r.length ? '任一條成立就降旗：' + r.join('／') : '不降旗：打到沉或全員倒下';
}
function gp(g, p) { return g.get(p & 1023, (p >> 10) & 1023, p >> 20); }
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/33_flood.js ──
// ───────────────────────── 進水：粒子模式（TASK-0525） ─────────────────────────
// 兩種模式（Tim 2026-10-13）：物理效果的「進水」第 0 檔 ＝ 公式（32_hull.js：水線下破洞數 × √水深）；1–3 檔 ＝ 粒子（粗／中／細）。全開 ＝ 細。
// 粒子模式：進水量、下沉、傾斜完全由艙內的水決定 ——
//   · 破口：船殼最外那一層被打掉、而且往艙內一路通到原本是空的地方（flHoleRedo），每 c × c 格算一塊（面積 ＝ 通的格數 × S²）。
//     流量照 Torricelli：FL_C × 面積 × √(2g × 水頭差) × 滑桿／預設（細節設定的「進水速度」；預設 0.35 ⇒ ×1 ＝ 物理的流量）。
//     水頭差 ＝ 外面的水面（seaH，照浪）減艙內在那個洞的水面，兩邊都不低於洞本身 ⇒ 浮出水面的洞不進水；艙內的水比外面高 ⇒ 往外流。
//   · 流進來的水是粒子（每顆帶 vj m³）：從洞往艙內噴（初速 √(2g × 水頭差)），照重力在船的座標裡落下，碰到船體或水面就併進水格。粒子滿了 ⇒ 直接併進洞旁那一格。
//   · 水格（每格 c 格見方，存水量 m³）：往下流（照那一格最密的那一層開著幾成：甲板擋、艙口與破洞讓水下去）；滿了往上擠；
//     往旁邊流照水面的世界高度（船的矩陣，含傾斜與浪的搖晃）⇒ 船一傾斜，水往低的那一舷跑，再把船壓得更斜（自由液面）。
//   · 抽水機：每秒從最低的那一層水抽掉 FL_PUMP ×（滑桿／預設）m³（約每分鐘 18 噸：四台鏈式抽水機全力抽）。
//     ⛔ 照公式那邊的抽水換算（0.004 m/s × 水線面積 ≈ 每秒 0.84 m³）⇒ 比水線附近那幾個洞進得還快，戰鬥 420 秒艙裡一滴水都留不住（量過）。
//   · 船：艙內的水 ＝ 加上去的重量 ⇒ 照浮力表（32_hull.js liftFor）算多吃水多少，sh.sink 照它慢慢跟過去（FL_TAU 秒）；
//     水的重心偏哪一舷 ⇒ 往那邊傾斜（穩心高 FL_GM，見下）、偏船頭船尾 ⇒ 縱傾（FL_GML）；上限跟公式一樣（開始沉之前 0.21 rad、縱傾 0.07）。
//     開始沉（下沉 4.2 m）之後照舊加速沉下去；斷成兩截照舊（公式，一定沉）。
// 精細等級 FL_LV：c 水格邊長幾格、ev 幾步算一次水格、jn 粒子上限（每艘）、vj 每顆帶多少 m³、dn 每次最多重算幾格被打壞的水格與破口。
// 戰局：自己的亂數 rndF（開局重設）；各檔水格不同 ⇒ 各檔是各自的一局（同一個種子各自逐字重現）。⛔ 不碰 rnd()、不讀畫面的設定。
//   進水模式開戰時決定（FLOOD_LV，70_flow.js），戰鬥中改了下一場生效。
var FL_LV = [null, { c: 10, ev: 4, jn: 300, vj: 0.25, dn: 120 }, { c: 7, ev: 2, jn: 800, vj: 0.08, dn: 200 }, { c: 5, ev: 2, jn: 2000, vj: 0.03, dn: 300 }];
// FL_GM 穩心高（Tim 2026-10-13：傾斜收一點）：1.1 m（巡防艦的量級）⇒ 水往低的那一舷跑（自由液面），一舷有洞積 200 噸就斜到上限 12°、兩舷都有洞也一樣；
//   4 m ⇒ 一舷有洞 180／380／600／840 噸時 1.9°／4.7°／8.4°／12°，兩舷都有洞 1,140 噸才 3.7°（沙盒 60 秒量的；2 m、3 m 還是很快頂到上限，5 m 一舷 830 噸才 8.3°）。
var FL_C = 1.0, FL_PUMP = 0.3, FL_GM = 4, FL_GML = 60, FL_TAU = 2;
var FL_HIDE = false, FLOOD_LV = 0, RSF0 = 0x3C6EF372, rsF = SEED ^ RSF0;
function rndF() { rsF |= 0; rsF = rsF + 0x6D2B79F5 | 0; var t = Math.imul(rsF ^ rsF >>> 15, 1 | rsF); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
function rgF(a, b) { return a + (b - a) * rndF(); }
/** 船型 T 的水格（邊長 c 格；第一次用到時算，掛在 T.flc[c]）：兩舷船殼最外那一格（yP／yM，每個 (x, z)）、每格能裝多少（cap：艙內空的比例）、往下通多少（pd：最密那一層開著的比例）。 */
function flType(T, c) {
  var K = T.flc || (T.flc = {}); if (K[c]) return K[c];
  var B = T.base, zTop = Math.min(B.sz, T.zw + 46), x0 = Math.max(0, T.wl0 - 4), x1 = Math.min(B.sx - 1, T.wl1 + 4), cy = T.cy, TW = T.hullTW, HB = T.hullHB;
  var nxv = x1 - x0 + 1, yP = new Int16Array(nxv * zTop).fill(-1), yM = new Int16Array(nxv * zTop).fill(-1), ylo = 1e9, yhi = -1, x, y, z;
  for (z = 0; z < Math.min(zTop, T.hullTH); z++) for (x = x0; x <= x1; x++) {
    var hb = HB[z * TW + x]; if (!hb) continue;
    var k = z * nxv + x - x0;
    for (y = Math.min(B.sy - 1, Math.ceil(cy + hb)); y > cy; y--) if (B.get(x, y, z)) { yP[k] = y; break; }
    for (y = Math.max(0, Math.floor(cy - hb - 1)); y < cy; y++) if (B.get(x, y, z)) { yM[k] = y; break; }
    if (yP[k] < 0 || yM[k] < 0) { yP[k] = yM[k] = -1; continue; }
    if (yM[k] < ylo) ylo = yM[k]; if (yP[k] > yhi) yhi = yP[k];
  }
  var NX = Math.ceil(nxv / c), NY = Math.ceil((yhi - ylo + 1) / c), NZ = Math.ceil(zTop / c), N = NX * NY * NZ;
  var F = { c: c, X0: x0, Y0: ylo, NX: NX, NY: NY, NZ: NZ, N: N, nxv: nxv, zTop: zTop, yP: yP, yM: yM, cap: new Float32Array(N), pd: new Float32Array(N) };
  var intC = new Int32Array(N), solC = new Int32Array(N), intL = new Int32Array(N * c), solL = new Int32Array(N * c);
  for (z = 0; z < zTop; z++) for (x = x0; x <= x1; x++) {
    var kk = z * nxv + x - x0, a = yM[kk] + 1, b = yP[kk] - 1; if (yP[kk] < 0 || b < a) continue;
    var cxi = ((x - x0) / c) | 0, czi = (z / c) | 0, lz = z % c;
    for (var cyi = ((a - ylo) / c) | 0; cyi <= (((b - ylo) / c) | 0); cyi++) {
      var lo = Math.max(a, ylo + cyi * c), hi = Math.min(b, ylo + cyi * c + c - 1), cell = (czi * NY + cyi) * NX + cxi;
      intC[cell] += hi - lo + 1; intL[cell * c + lz] += hi - lo + 1;
    }
  }
  B.each(function (x, y, z) {
    if (z >= zTop || x < x0 || x > x1) return;
    var kk = z * nxv + x - x0; if (!(y > yM[kk] && y < yP[kk])) return;
    var cell = (((z / c) | 0) * NY + (((y - ylo) / c) | 0)) * NX + (((x - x0) / c) | 0); solC[cell]++; solL[cell * c + z % c]++;
  });
  for (var i = 0; i < N; i++) {
    F.cap[i] = (intC[i] - solC[i]) / (c * c * c);
    var p = 1, any = false;
    for (var l = 0; l < c; l++) { var il = intL[i * c + l]; if (il > 0) { any = true; p = Math.min(p, (il - solL[i * c + l]) / il); } }
    F.pd[i] = any ? p : 0;
  }
  return K[c] = F;
}
/** 開一艘船的進水狀態（makeShip；公式模式 ⇒ null）。 */
function flNew(sh) {
  var L = FL_LV[FLOOD_LV]; if (!L) return null;
  var F = flType(sh.T, L.c), N = F.N, H = 2 * F.NX * F.NZ;
  return { L: L, F: F, cap: F.cap.slice(), pd: F.pd.slice(), A: new Float32Array(N), on: new Uint8Array(N), act: new Int32Array(4096), actN: 0, dmark: new Uint8Array(N), dirty: [],
    hA: new Float32Array(H), hX: new Float32Array(H), hY: new Float32Array(H), hZ: new Float32Array(H), hYi: new Float32Array(H), hAcc: new Float32Array(H), hmark: new Uint8Array(H), hon: new Uint8Array(H), hdirty: [], holes: [],
    J: { n: 0, p: new Float32Array(L.jn * 3), v: new Float32Array(L.jn * 3), vol: new Float32Array(L.jn), life: new Float32Array(L.jn) },
    vol: 0, area: 0, open: 0, inQ: 0, outQ: 0, inTot: 0, outTot: 0, pumped: 0, comX: 0, comY: 0, sinkT: 0, step: 0, gen: 0, mesh: null };
}
function flAct(fl, i) {
  if (fl.on[i]) return; fl.on[i] = 1;
  if (fl.actN >= fl.act.length) { var a = new Int32Array(fl.act.length * 2); a.set(fl.act); fl.act = a; }
  fl.act[fl.actN++] = i;
}
/** 打掉一格（20_shatter.js removeVoxel）：那一格所在的水格、靠近船殼的話那一塊破口，記下來待重算。 */
function floodTouch(sh, x, y, z) {
  var fl = sh.fl, F = fl.F, c = F.c;
  if (z >= F.zTop || z < 0 || x < F.X0 || x >= F.X0 + F.nxv) return;
  var iy = ((y - F.Y0) / c) | 0, bx = ((x - F.X0) / c) | 0, bz = (z / c) | 0;
  if (y >= F.Y0 && iy < F.NY) { var i = (bz * F.NY + iy) * F.NX + bx; if (!fl.dmark[i]) { fl.dmark[i] = 1; fl.dirty.push(i); } }
  var k = z * F.nxv + x - F.X0, yp = F.yP[k]; if (yp < 0) return;
  var side = Math.abs(y - yp) <= Math.abs(y - F.yM[k]) ? 0 : 1, d = side ? y - F.yM[k] : yp - y;
  if (d > 30 || d < -2) return;
  var h = (side * F.NX + bx) * F.NZ + bz; if (!fl.hmark[h]) { fl.hmark[h] = 1; fl.hdirty.push(h); }
}
/** 被打壞的水格重算（照現在的格）：能裝多少、往下通多少。 */
function flCellRedo(sh, fl, i) {
  var F = fl.F, c = F.c, ix = i % F.NX, iy = ((i / F.NX) | 0) % F.NY, iz = (i / (F.NX * F.NY)) | 0, Gd = sh.grid, it = 0, st = 0, p = 1, any = false;
  for (var l = 0; l < c; l++) {
    var z = iz * c + l, il = 0, sl = 0; if (z >= F.zTop) break;
    for (var dx = 0; dx < c; dx++) {
      var x = F.X0 + ix * c + dx; if (x - F.X0 >= F.nxv) break;
      var k = z * F.nxv + x - F.X0; if (F.yP[k] < 0) continue;
      var a = Math.max(F.yM[k] + 1, F.Y0 + iy * c), b = Math.min(F.yP[k] - 1, F.Y0 + iy * c + c - 1);
      for (var y = a; y <= b; y++) { il++; if (Gd.get(x, y, z)) sl++; }
    }
    it += il; st += sl; if (il > 0) { any = true; p = Math.min(p, (il - sl) / il); }
  }
  fl.cap[i] = (it - st) / (c * c * c); fl.pd[i] = any ? p : 0;
}
/** 一塊破口重算：c × c 個船殼最外的點，每點從外往裡走，先碰到還在的格 ⇒ 不通；先走到原本是空的（艙內）⇒ 通。面積 ＝ 通的點數 × S²，記下中心與艙內那一側。 */
function flHoleRedo(sh, fl, h) {
  var F = fl.F, c = F.c, side = (h / (F.NX * F.NZ)) | 0, r = h % (F.NX * F.NZ), bx = (r / F.NZ) | 0, bz = r % F.NZ, Gd = sh.grid, B = sh.T.base, s = side ? 1 : -1;
  var n = 0, sx = 0, sy = 0, sz = 0, si = 0;
  for (var dz = 0; dz < c; dz++) for (var dx = 0; dx < c; dx++) {
    var x = F.X0 + bx * c + dx, z = bz * c + dz; if (x - F.X0 >= F.nxv || z >= F.zTop) continue;
    var k = z * F.nxv + x - F.X0, y0 = side ? F.yM[k] : F.yP[k]; if (y0 < 0) continue;
    for (var t = 0; t < 30; t++) { var y = y0 + s * t; if (Gd.get(x, y, z)) break; if (!B.get(x, y, z)) { n++; sx += x; sy += y0; sz += z; si += y; break; } }
  }
  fl.hA[h] = n * S * S;
  if (n) { fl.hX[h] = sx / n + 0.5; fl.hY[h] = sy / n + 0.5; fl.hZ[h] = sz / n + 0.5; fl.hYi[h] = si / n + 0.5; if (!fl.hon[h]) { fl.hon[h] = 1; fl.holes.push(h); } }
}
/** 艙內那一點 (x, y, z)（格座標）所在的水格；不在格子範圍 ⇒ −1。 */
function flCell(F, x, y, z) {
  var ix = Math.floor((x - F.X0) / F.c), iy = Math.floor((y - F.Y0) / F.c), iz = Math.floor(z / F.c);
  if (ix < 0 || iy < 0 || iz < 0 || ix >= F.NX || iy >= F.NY || iz >= F.NZ) return -1;
  return (iz * F.NY + iy) * F.NX + ix;
}
/** 水併進第 i 格（那一格裝不了水 ⇒ 往上找三格）。 */
function flDeposit(fl, i, v) {
  var NXY = fl.F.NX * fl.F.NY;
  for (var t = 0; t < 4 && i >= 0 && i < fl.F.N; t++, i += NXY) if (fl.cap[i] > 0.02) { fl.A[i] += v; flAct(fl, i); return; }
  fl.lost = (fl.lost || 0) + v;
}
/** 每一步（32_hull.js stepShip，粒子模式）：粒子飛、每 ev 步算一次水格（破口進出水、往下往旁邊流、抽水、讀數）。 */
function floodStep(sh, fl, dt) {
  if (!(dt > 0)) return;
  var F = fl.F, L = fl.L, J = fl.J, Vc = Math.pow(F.c * S, 3), gL = M4.dir(sh.inv, 0, -G, 0), i, o;
  // 粒子：照重力（船的座標，格／秒²）落下；碰到船體、滿的水格、出界或活太久 ⇒ 併進上一個位置的水格
  for (i = 0; i < J.n; i++) {
    o = i * 3;
    var px = J.p[o], py = J.p[o + 1], pz = J.p[o + 2], c0 = flCell(F, px, py, pz);
    J.v[o] += gL[0] * dt; J.v[o + 1] += gL[1] * dt; J.v[o + 2] += gL[2] * dt;
    J.p[o] += J.v[o] * dt; J.p[o + 1] += J.v[o + 1] * dt; J.p[o + 2] += J.v[o + 2] * dt; J.life[i] -= dt;
    var c1 = flCell(F, J.p[o], J.p[o + 1], J.p[o + 2]);
    if (J.life[i] <= 0 || c1 < 0 || sh.grid.get(Math.floor(J.p[o]), Math.floor(J.p[o + 1]), Math.floor(J.p[o + 2])) || fl.A[c1] >= fl.cap[c1] * Vc * 0.95) {
      flDeposit(fl, c0 >= 0 ? c0 : c1, J.vol[i]);
      var j = --J.n;
      if (i !== j) { J.p.copyWithin(o, j * 3, j * 3 + 3); J.v.copyWithin(o, j * 3, j * 3 + 3); J.vol[i] = J.vol[j]; J.life[i] = J.life[j]; }
      i--;
    }
  }
  if (++fl.step % L.ev) return;
  flTick(sh, fl, dt * L.ev);
}
function flTick(sh, fl, dtc) {
  var F = fl.F, L = fl.L, J = fl.J, c = F.c, NX = F.NX, NY = F.NY, NXY = NX * NY, N = F.N, A = fl.A, cap = fl.cap, pd = fl.pd, M = sh.M, Vc = Math.pow(c * S, 3), hc = c * S, fk = sh.cfg.flood / LIM.flood[2], i, k, m;   // 滑桿／預設：預設 ⇒ 物理的流量
  // 0. 被打壞的水格、破口（每次最多 dn 個 ⇒ 一發殉爆不會卡一下）
  for (k = 0; k < L.dn && fl.dirty.length; k++) { i = fl.dirty.shift(); fl.dmark[i] = 0; flCellRedo(sh, fl, i); }
  for (k = 0; k < L.dn && fl.hdirty.length; k++) { var hd = fl.hdirty.shift(); fl.hmark[hd] = 0; flHoleRedo(sh, fl, hd); }
  // 水面的世界高度：格 (ix, iy, iz) 的底 ＋ 裝了幾成 × 格高
  var h0 = M[1] * (F.X0 + 0.5 * c) + M[5] * (F.Y0 + 0.5 * c) + M[13], dhx = M[1] * c, dhy = M[5] * c, dhz = M[9] * c;
  function head(i) { var ix = i % NX, iy = ((i / NX) | 0) % NY, iz = (i / NXY) | 0; return h0 + ix * dhx + iy * dhy + iz * dhz + (cap[i] > 0 ? A[i] / (cap[i] * Vc) : 0) * hc; }
  // 1. 破口：外面的水面 vs 艙內在洞那裡的水面（都不低於洞）⇒ 進或出
  var inQ = 0, outQ = 0, area = 0, open = 0;
  for (k = 0; k < fl.holes.length; k++) {
    var h = fl.holes[k], ar = fl.hA[h]; if (!(ar > 0)) continue;
    area += ar; open++;
    var side = (h / (NX * F.NZ)) | 0, s = side ? 1 : -1, P = M4.pt(M, fl.hX[h], fl.hY[h], fl.hZ[h]), hOut = seaH(P[0], P[2], SIMT);
    var ci = flCell(F, fl.hX[h], fl.hYi[h] + s * 0.5 * c, fl.hZ[h]), hIn = -1e9;
    if (ci >= 0 && A[ci] > 1e-6) { var q = ci; while (q + NXY < N && A[q] >= cap[q] * Vc * 0.98 && A[q + NXY] > 1e-6) q += NXY; hIn = head(q); }
    var d = Math.max(hOut, P[1]) - Math.max(hIn, P[1]);
    if (d > 0.001) {
      var dv = FL_C * ar * Math.sqrt(2 * G * d) * fk * dtc; inQ += dv;
      fl.hAcc[h] += dv;
      var sp = Math.sqrt(2 * G * d) / S;                                        // 噴進來的速度（格／秒）
      while (fl.hAcc[h] >= L.vj) {
        fl.hAcc[h] -= L.vj;
        if (J.n < L.jn) {
          var jo = J.n * 3; J.p[jo] = fl.hX[h] + rgF(-0.4, 0.4) * c; J.p[jo + 1] = fl.hYi[h] + s; J.p[jo + 2] = fl.hZ[h] + rgF(-0.4, 0.4) * c;
          J.v[jo] = rgF(-0.25, 0.25) * sp; J.v[jo + 1] = s * rgF(0.5, 1.0) * sp; J.v[jo + 2] = rgF(-0.1, 0.25) * sp; J.vol[J.n] = L.vj; J.life[J.n] = 3; J.n++;
        } else if (ci >= 0) flDeposit(fl, ci, L.vj);
      }
    } else if (d < -0.001 && ci >= 0) {
      var ov = Math.min(FL_C * ar * Math.sqrt(2 * G * -d) * fk * dtc, A[ci]); A[ci] -= ov; outQ += ov;
      if (PHX.water && ov > 0.01) wpPour(P, M4.dir(M, 0, -s, 0), ov / dtc);    // 往外流：只給人看（13_water.js，自己的亂數）
    }
  }
  fl.inQ = inQ / dtc; fl.outQ = outQ / dtc; fl.inTot += inQ; fl.outTot += outQ; fl.area = area; fl.open = open;
  // 2. 水格：往下（照這一格往下通幾成）、滿了往上擠、往旁邊（照水面的世界高度；來回換方向走 ⇒ 不偏一邊）
  var n0 = fl.actN, act = fl.act, dir = fl.gen & 1, t, j;
  for (t = 0; t < n0; t++) {
    i = act[t]; var a = A[i]; if (a <= 1e-7) continue;
    if (i >= NXY && pd[i] > 0.02) { j = i - NXY; var room = cap[j] * Vc - A[j]; if (room > 0) { m = Math.min(a, room) * Math.min(1, pd[i] * 4); A[i] -= m; A[j] += m; flAct(fl, j); } }
    var ex = A[i] - cap[i] * Vc;
    if (ex > 1e-6 && i + NXY < N && cap[i + NXY] > 0.02 && pd[i + NXY] > 0.02) { A[i] -= ex; A[i + NXY] += ex; flAct(fl, i + NXY); }
  }
  for (t = 0; t < n0; t++) {
    i = act[dir ? n0 - 1 - t : t]; if (A[i] <= 1e-7 || !(cap[i] > 0.02) || A[i] / (cap[i] * Vc) < 0.03) continue;
    var hi = head(i), ix = i % NX, iy = ((i / NX) | 0) % NY;
    for (var nb = 0; nb < 4; nb++) {
      j = nb === 0 ? (ix > 0 ? i - 1 : -1) : nb === 1 ? (ix < NX - 1 ? i + 1 : -1) : nb === 2 ? (iy > 0 ? i - NX : -1) : (iy < NY - 1 ? i + NX : -1);
      if (j < 0 || !(cap[j] > 0.02)) continue;
      var dh = hi - head(j); if (dh <= 1e-4) continue;
      m = Math.min(0.5 * dh / hc * Math.min(cap[i], cap[j]) * Vc * 0.25, A[i] * 0.25);
      A[i] -= m; A[j] += m; flAct(fl, j); hi = head(i);
    }
  }
  // 3. 抽水：從最低的那幾層抽（⛔ act 要重拿：上面 flAct 可能換過一條更長的陣列）
  act = fl.act;
  var need = FL_PUMP * fk * dtc, lowz = 1e9;
  for (t = 0; t < fl.actN; t++) if (A[act[t]] > 1e-7) lowz = Math.min(lowz, (act[t] / NXY) | 0);
  for (var zz = lowz; zz < lowz + 3 && need > 0 && lowz < 1e9; zz++) for (t = 0; t < fl.actN && need > 0; t++) {
    i = act[t]; if (((i / NXY) | 0) !== zz || A[i] <= 0) continue; m = Math.min(A[i], need); A[i] -= m; need -= m; fl.pumped += m;
  }
  // 4. 收掉空的格；讀數：水量、重心（公尺，離船型中線：x 往船頭、y 往格 +y 那一舷為正）
  var w = 0, mx = 0, my = 0, keep = 0, cx = sh.T.cx, cy = sh.T.cy;
  for (t = 0; t < fl.actN; t++) {
    i = act[t];
    if (A[i] <= 1e-7) { A[i] = 0; fl.on[i] = 0; continue; }
    act[keep++] = i; w += A[i];
    mx += A[i] * (F.X0 + ((i % NX) + 0.5) * c - cx); my += A[i] * (F.Y0 + ((((i / NX) | 0) % NY) + 0.5) * c - cy);
  }
  fl.actN = keep;
  for (t = 0; t < J.n; t++) { w += J.vol[t]; mx += J.vol[t] * (J.p[t * 3] - cx); my += J.vol[t] * (J.p[t * 3 + 1] - cy); }
  fl.vol = w; fl.comX = w > 0 ? mx / w * S : 0; fl.comY = w > 0 ? my / w * S : 0; fl.gen++;
}
/** 艙內的水 ⇒ 該多吃水多少（m）：浮力表上「少掉的重量 − 水」跟「少掉的重量」的差。 */
function floodSinkT(sh, fl) {
  if (sh.flBase === undefined) return 0;
  var W = fl.vol * RHO_W, a = liftFor(sh.T, sh.flBase), b = liftFor(sh.T, sh.flBase - W);
  return fl.sinkT = a === null || b === null ? 0 : Math.max(0, a - b);
}
/** 水的重心 ⇒ 橫傾、縱傾的目標（rad；正負跟公式一樣：水在格 +y 那一舷 ⇒ 正 ⇒ 那一舷（右舷）往下；水在船頭 ⇒ 負 ⇒ 船頭往下）。 */
function floodTilt(sh, fl) {
  var W = fl.vol * RHO_W, D = (sh.mass0 || shipT(sh)) + W, lim = sh.sinkingFinal ? 0.55 : 0.21;
  return [clamp(Math.atan(W * fl.comY / (D * FL_GM)), -lim, lim), -clamp(Math.atan(W * fl.comX / (D * FL_GML)), -0.07, 0.07)];
}

// ── 畫：艙內的水面（每一格水柱的頂，四個角照同一個世界高度擺 ⇒ 船傾斜時水面還是平的）；噴進來的粒子跟點精靈一起畫 ──
function flGL() {
  P.pool = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec4 aP; uniform mat4 uModel,uVP; out vec3 vW; out float vF; void main(){ vec4 w=uModel*vec4(aP.xyz,1.0); vW=w.xyz; vF=aP.w; gl_Position=uVP*w; }\n',
    '#version 300 es\nprecision highp float; in vec3 vW; in float vF; uniform vec3 uEye,uSun,uFog,uSky; uniform float uFogD,uSeaT,uX; out vec4 o;\n' + SHADOW_GLSL +
    'void main(){ vec2 r=vec2(sin(vW.x*3.1+uSeaT*2.3)+sin(vW.z*4.3-uSeaT*1.7),cos(vW.z*2.7-uSeaT*1.9)+cos(vW.x*3.7+uSeaT*2.1))*0.03; vec3 n=normalize(vec3(r.x,1.0,r.y));\n' +
    ' vec3 v=normalize(uEye-vW); float fr=0.04+0.96*pow(1.0-max(dot(n,v),0.0),5.0), sk=shadowK(vW,n);\n' +
    ' vec3 c=mix(vec3(0.08,0.27,0.3)*(0.45+0.55*sk),uSky*0.75,clamp(fr*0.8+0.08,0.0,1.0))+vec3(1.0,0.92,0.75)*pow(max(dot(reflect(-v,n),uSun),0.0),90.0)*(0.25+sk);\n' +
    ' if(uX>0.5) c=mix(c,vec3(0.2,0.6,0.95),0.45);\n' +
    ' float fd=length(vW-uEye); o=vec4(mix(c,uFog,1.0-exp(-fd*uFogD)),uX>0.5?0.62:0.78); }\n');
}
/** 艙內水面的網格（格座標，每個頂點帶「裝了幾成」）：水格有算過才重做。 */
function flMesh(sh, fl) {
  var F = fl.F, c = F.c, NX = F.NX, NY = F.NY, NXY = NX * NY, A = fl.A, cap = fl.cap, M = sh.M, Vc = Math.pow(c * S, 3), hc = c * S;
  var me = fl.mesh || (fl.mesh = { vao: gl.createVertexArray(), vb: gl.createBuffer(), buf: new Float32Array(6 * 4 * 512), n: 0, cap: 0, gen: -1 });
  if (me.gen === fl.gen) return me;
  var h0 = M[1] * (F.X0 + 0.5 * c) + M[5] * (F.Y0 + 0.5 * c) + M[13], q = 0, t, i, u;
  // 先找每一根水柱最上面那一格水面的世界高度（同一根有兩層水 ⇒ 只記上面那層）；四個角取周圍水柱的平均 ⇒ 水面連成一片，⛔ 一格一個高度 ⇒ 像一階一階的方塊
  var CH = me.ch && me.ch.length === NX * NY ? me.ch : (me.ch = new Float32Array(NX * NY)), CZ = me.cz && me.cz.length === NX * NY ? me.cz : (me.cz = new Int16Array(NX * NY));
  CZ.fill(-1); var tops = me.tops || (me.tops = []); tops.length = 0;
  for (t = 0; t < fl.actN; t++) {
    i = fl.act[t]; if (!(cap[i] > 0.02) || A[i] < 0.02 * cap[i] * Vc) continue;
    u = i + NXY; if (u < F.N && cap[u] > 0.02 && A[u] >= 0.02 * cap[u] * Vc) continue;          // 上面那一格也有水 ⇒ 不是水面
    var ix = i % NX, iy = ((i / NX) | 0) % NY, iz = (i / NXY) | 0, col = iy * NX + ix;
    var hw = h0 + ix * M[1] * c + iy * M[5] * c + iz * M[9] * c + Math.min(1, A[i] / (cap[i] * Vc)) * hc;
    tops.push(i, hw); if (iz > CZ[col]) { CZ[col] = iz; CH[col] = hw; }
  }
  function corner(ix, iy, iz, hw) {                                         // 角 (ix, iy) 周圍四根水柱裡、跟這一格差不到半格的水面平均
    var s = 0, n = 0;
    for (var a = ix - 1; a <= ix; a++) for (var b = iy - 1; b <= iy; b++) {
      if (a < 0 || b < 0 || a >= NX || b >= NY) continue; var k = b * NX + a;
      if (CZ[k] >= 0 && Math.abs(CZ[k] - iz) <= 1 && Math.abs(CH[k] - hw) < 0.6 * hc) { s += CH[k]; n++; }
    }
    return n ? s / n : hw;
  }
  for (t = 0; t < tops.length; t += 2) {
    i = tops[t]; var hw0 = tops[t + 1], jx = i % NX, jy = ((i / NX) | 0) % NY, jz = (i / NXY) | 0, f = Math.min(1, A[i] / (cap[i] * Vc));
    var x0 = F.X0 + jx * c, y0 = F.Y0 + jy * c, zl = jz * c - 0.5 * c, zh = jz * c + 1.5 * c;
    var cs = [[x0, y0, corner(jx, jy, jz, hw0)], [x0 + c, y0, corner(jx + 1, jy, jz, hw0)], [x0 + c, y0 + c, corner(jx + 1, jy + 1, jz, hw0)], [x0, y0 + c, corner(jx, jy + 1, jz, hw0)]];
    if ((q + 6) * 4 > me.buf.length) { var nb = new Float32Array(me.buf.length * 2); nb.set(me.buf); me.buf = nb; }
    [0, 1, 2, 0, 2, 3].forEach(function (e) {
      var p = cs[e], z = clamp((p[2] - (M[1] * p[0] + M[5] * p[1] + M[13])) / M[9], zl, zh);   // 同一個世界高度 ⇒ 船傾斜時水面還是平的
      me.buf[q * 4] = p[0]; me.buf[q * 4 + 1] = p[1]; me.buf[q * 4 + 2] = z; me.buf[q * 4 + 3] = f; q++;
    });
  }
  gl.bindVertexArray(me.vao); gl.bindBuffer(gl.ARRAY_BUFFER, me.vb);
  if (q * 4 > me.cap) { me.cap = me.buf.length; gl.bufferData(gl.ARRAY_BUFFER, me.cap * 4, gl.DYNAMIC_DRAW); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 4, gl.FLOAT, false, 16, 0); }
  if (q) gl.bufferSubData(gl.ARRAY_BUFFER, 0, me.buf, 0, q * 4);
  gl.bindVertexArray(null);
  me.n = q; me.gen = fl.gen; return me;
}
/** 畫艙內的水面（海與白沫之後；開始沉、斷了就不畫 —— 那時候海已經畫進船艙）。 */
function flDraw() {
  if (!P.pool || FL_HIDE) return;                                           // FL_HIDE：對照用（__game.flood(i, { hide: true })）
  var any = false;
  SHIPS.forEach(function (sh) {
    var fl = sh.fl; if (!fl || !fl.actN || sh.broken || sh.sinkingFinal || sh.sunk) return;
    var me = flMesh(sh, fl); if (!me.n) return;
    if (!any) { any = true; gl.useProgram(P.pool.prog); setCommon(P.pool); gl.uniform1f(P.pool.u.uX, FLX3 ? 1 : 0); gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false); gl.disable(gl.CULL_FACE); if (FLX3) gl.disable(gl.DEPTH_TEST); }   // 停格的「🔍 透視」開著 ⇒ 隔著船殼看得到（72_floodui.js）
    gl.uniformMatrix4fv(P.pool.u.uModel, false, sh.M); gl.bindVertexArray(me.vao); gl.drawArrays(gl.TRIANGLES, 0, me.n);
  });
  if (any) { gl.depthMask(true); gl.enable(gl.DEPTH_TEST); }
}
/** 噴進來的粒子放進點精靈的緩衝（60_render.js 的 pushPt）。 */
function flPushJets(pushPt) {
  var b = 0.55 + 0.45 * WX.sun, col = [0.72 * b, 0.84 * b, 0.9 * b];
  SHIPS.forEach(function (sh) {
    var fl = sh.fl; if (!fl || !fl.J.n || sh.broken || sh.sinkingFinal || sh.sunk) return;
    var J = fl.J, M = sh.M;
    for (var i = 0; i < J.n; i++) { var o = i * 3; pushPt(M4.pt(M, J.p[o], J.p[o + 1], J.p[o + 2]), 0.12 + 0.6 * Math.cbrt(J.vol[i]), col, 0.75, -1); }
  });
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/34_shreds.js ──
// ───────────────────────── 帆的布片（帆與繩的物理開著才有） ─────────────────────────
// Tim 2026-10-13：物理開著時帆被打破，不撒點精靈，改成真的從帆上撕下來、照物理飄落的布。
// 從哪裡來：tearCloth（30_rig_physics.js）這一發新藏起來的細格三角形 ＝ 被打掉的那一塊布（方帆一發約 108 個三角形、30–40 m²；三角帆 48–80 個）。
//   切成幾片：亂數挑幾個種子三角形，其他照作品形狀上的重心歸到最近的那一顆 ⇒ 不規則的碎片（一片平均 SH_TRI 個三角形，鏈彈碎一點）。
//   每片是一小塊布：細格點 ＋ 邊與跨點約束（meshCons，長度照撕下來那一刻），跟帆走同一套 clothStep ——
//   風壓沿法線、大小 ∝（相對風在法線上的分量）²（攤平的時候慢慢飄、側過來掉得快）、重力、阻尼、碰到甲板擋住（hitGrid）。
//   風壓 ×SH_KW：帆的 KW 攤平落下是 4.4 m/s、一片 1.5 m 的布從 14 m 高 2 秒就落海（量過：每秒 5–9 m）⇒ ×3 ⇒ 攤平約 2.5 m/s，風一吹就跟著風走。
//   初速：被砲彈往前帶（彈的方向 1.5–4 m/s，鏈彈到 6）＋ 亂撒一點 ＋ 轉（每點加 ω × 離重心的距離 ⇒ 翻著飛）。
// 座標：船的格座標（跟帆一樣用 sh.M 畫、接在帆的緩衝後面（11_rig_gpu.js sailBuf）⇒ 陰影、反射都有）；相對風已扣掉船速 ⇒ 離開船就被吹向船尾。
// 落水（中間那一點碰到海面、而且不在船殼外形裡）：不再算物理，停在海上（格座標裡每一步退回船走的那一段）、慢慢往下沉，SH_WET 秒後拿掉。
// 落在甲板上：躺著；SH_LIFE 秒後拿掉。上限照物理分級（09_phx.js RIG_LV 的 shred：每艘幾片；滿了先丟落水的、再丟最早的）。
// ⛔ 只給人看：自己的亂數 rndC（開局重設，70_flow.js）、不碰 rnd()、不回寫模擬 ⇒ 開或關同一個種子戰局逐字相同。
//   原本的點精靈布片（21_gunnery.js dropSail／shredSail）在布片接手時照樣抽完 rnd()、只是不放。
var SH_TRI = 10, SH_KW = 3, SH_LIFE = 40, SH_WET = 3, SH_SINK = 0.3;
var RSC0 = 0x2B79F5A1, rsC = SEED ^ RSC0, SH_STAT = { cut: 0, tris: 0 }, SHT = null;
function rndC() { rsC |= 0; rsC = rsC + 0x6D2B79F5 | 0; var t = Math.imul(rsC ^ rsC >>> 15, 1 | rsC); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
function rgC(a, b) { return a + (b - a) * rndC(); }
function gsC() { var u = rndC() || 1e-9, v = rndC(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(6.2831853 * v); }
/** tearCloth 撕開之後：這一發新藏起來的三角形（old ＝ 撕之前的 c.tv）切成布片。b ＝ 砲彈（世界座標的速度）。 */
function shredCut(sh, c, old, b) {
  var lv = rigLv(); if (!lv.shred || !sh.shreds) return;
  var T = c.T, tr = T.tris, tv = c.tv, P0 = T.p0, nt = [], j, i, k;
  for (j = 0; j < tr.length; j += 3) if ((tv[tr[j]] || tv[tr[j + 1]] || tv[tr[j + 2]]) && !(old[tr[j]] || old[tr[j + 1]] || old[tr[j + 2]])) nt.push(j);
  if (!nt.length) return;
  if (!SHT || SHT.length < T.n * 3) SHT = new Float32Array(T.n * 3);
  var P = clothFine(c, SHT), chain = b.ammo === 2;
  // 分片：種子（亂數挑、不重複）＋ 每個三角形歸到重心最近的種子（作品形狀上量 ⇒ 被風吹皺了也照布上的位置分）
  var cen = nt.map(function (j) { var a = tr[j] * 3, e = tr[j + 1] * 3, d = tr[j + 2] * 3; return [(P0[a] + P0[e] + P0[d]) / 3, (P0[a + 1] + P0[e + 1] + P0[d + 1]) / 3, (P0[a + 2] + P0[e + 2] + P0[d + 2]) / 3]; });
  var K = clamp(Math.round(nt.length / (SH_TRI * (chain ? 0.6 : 1) * rgC(0.7, 1.3))), 1, nt.length), ord = nt.map(function (_, q) { return q; });
  for (i = 0; i < K; i++) { k = i + ((rndC() * (ord.length - i)) | 0); var tmp = ord[i]; ord[i] = ord[k]; ord[k] = tmp; }
  var grp = []; for (i = 0; i < K; i++) grp.push([]);
  cen.forEach(function (w, q) {
    var bi = 0, bd = 1e18;
    for (var g = 0; g < K; g++) { var s = cen[ord[g]], dx = w[0] - s[0], dy = w[1] - s[1], dz = w[2] - s[2], d = dx * dx + dy * dy + dz * dz; if (d < bd) { bd = d; bi = g; } }
    grp[bi].push(nt[q]);
  });
  var bv = M4.dir(sh.inv, b.v[0], b.v[1], b.v[2]), bl = len(bv) || 1, HC = lv.every * DT, col = T.col;
  grp.forEach(function (g) {
    if (!g.length) return;
    var map = new Map(), pos = [], lt = [];
    g.forEach(function (j) { for (var q = 0; q < 3; q++) { var f = tr[j + q], v = map.get(f); if (v === undefined) { v = pos.length; map.set(f, v); pos.push([P[f * 3], P[f * 3 + 1], P[f * 3 + 2]]); } lt.push(v); } });
    var n = pos.length, cons = meshCons(pos, new Uint16Array(lt)), cx = 0, cy = 0, cz = 0;
    pos.forEach(function (w) { cx += w[0] / n; cy += w[1] / n; cz += w[2] / n; });
    var sp = rgC(1.5, chain ? 6 : 4) / S, v0 = [bv[0] / bl * sp + gsC() / S, bv[1] / bl * sp + gsC() / S, bv[2] / bl * sp + gsC() / S];
    var om = [gsC(), gsC(), gsC()], ok = rgC(1, 4) / (len(om) || 1); om = mul(om, ok);   // 轉速 1–4 rad/s
    var p = new Float32Array(n * 3), q = new Float32Array(n * 3), t = rgC(0.82, 1);
    pos.forEach(function (w, u) {
      var rx = w[0] - cx, ry = w[1] - cy, rz = w[2] - cz, vx = v0[0] + om[1] * rz - om[2] * ry, vy = v0[1] + om[2] * rx - om[0] * rz, vz = v0[2] + om[0] * ry - om[1] * rx;
      p[u * 3] = w[0]; p[u * 3 + 1] = w[1]; p[u * 3 + 2] = w[2]; q[u * 3] = w[0] - vx * HC; q[u * 3 + 1] = w[1] - vy * HC; q[u * 3 + 2] = w[2] - vz * HC;
    });
    if (!CACC || CACC.length < n * 3) { CACC = new Float32Array(n * 3); CCNT = new Uint8Array(n); }
    sh.shreds.push({ T: { sim: cons }, p: p, q: q, pin: new Uint8Array(n), n: n, col: [col[0] * t, col[1] * t, col[2] * t], torn: false, loose: true, kw: SH_KW, age: 0, wet: 0 });
    SH_STAT.cut++; SH_STAT.tris += g.length;
  });
  var F = sh.shreds;
  while (F.length > lv.shred) { k = F.findIndex(function (f) { return f.wet; }); F.splice(k >= 0 ? k : 0, 1); }
}
/** 中間那一點碰到海面、而且不在船殼外形裡（掉進艙口的不算）⇒ 落水。 */
function shredWet(sh, f) {
  var p = f.p, o = (f.n >> 1) * 3, w = M4.pt(sh.M, p[o], p[o + 1], p[o + 2]);
  if (w[1] > seaH(w[0], w[2], SIMT)) return false;
  var T = sh.T, x = p[o] | 0, z = p[o + 2] | 0, hb = T.hullHB;
  return !(hb && x >= 0 && x < T.hullTW && z >= 0 && z < T.hullTH && Math.abs(p[o + 1] + 0.5 - T.cy) < hb[z * T.hullTW + x]);
}
/** 每一步（physStep 的最後）：在空中與甲板上的照布算（跟帆同一個節拍）、每 0.1 秒看落水與壽命；落水的停在海上往下沉。 */
function shredStep(sh, wl, gv, si, chk) {
  var F = sh.shreds; if (!F || !F.length) return;
  var go = (si + sh.i) % rigLv().every === 0, d = null, i, j;
  for (i = 0; i < F.length; i++) {
    var f = F[i];
    if (f.wet) {
      if (!d) d = M4.dir(sh.inv, -sh.vel[0] * DT, (-sh.vel[1] - SH_SINK) * DT, -sh.vel[2] * DT);   // 海上不動的一點，在船的格座標裡每一步往回退船走的那一段
      for (j = 0; j < f.n * 3; j += 3) { f.p[j] += d[0]; f.p[j + 1] += d[1]; f.p[j + 2] += d[2]; }
      if (chk && (f.wet += 0.1) > SH_WET) F.splice(i--, 1);
      continue;
    }
    if (go) clothStep(sh, f, wl, gv);
    if (!chk) continue;
    f.age += 0.1;
    if (f.age > SH_LIFE) { F.splice(i--, 1); continue; }
    if (shredWet(sh, f)) f.wet = 0.01;
  }
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/40_crew.js ──
// ───────────────────────── 船員（billboard） ─────────────────────────
// 一個人 ＝ 一張面向鏡頭、但永遠直立的貼圖。位置存格座標（腳底那一格的上緣），畫的時候用船的矩陣換到世界。
// 砲要有人操作：人數 < 最少人數就不能開；裝填速度 ∝ (人數／滿編)^0.85。死傷的人不再操作；
// 人不夠時，倖存者集中到還開得動的砲 ⇒ 其餘的砲沒人操作（HUD ○）。調度見 reassign。
var ROLE = { GUN: 0, POWDER: 1, OFFICER: 2, MARINE: 3, TOP: 4, HELM: 5, HAND: 6 }, NROLE = 6;   // NROLE：貼圖照職位的列數（HAND 預備水手沒有自己那一列，畫成砲手；42_hands.js）
var FR = { IDLE: 0, WORK_A: 1, WORK_B: 2, FIRE: 3, RUN_A: 4, RUN_B: 5, WOUNDED: 6, DEAD: 7 }, NFR = 8;
// 砲班：滿編／最少照砲種表（GUNS 的 crew／min，10_ship.js）—— 兩舷各一班；24 磅長砲一班 12 人＋送藥童 ⇒ 一個人物約兩人
// Tim 2026-10-12：砲班減一人（長砲 6 → 5、追擊砲 4 → 3），多出來的去搬火藥與彈藥（送藥手，23_powder.js）；射速照舊（裝填 ∝ 在崗／滿編）
var ROLE_NAME = ['砲手', '送藥手', '軍官', '陸戰隊', '桅頂水手', '舵手', '水手'];
var ART_CAPTAIN = 6, NART = 7;                    // 貼圖的列：0–5 照職位，6 船長（每艘船第一個軍官；職位照舊是軍官）
function standZ(g, x, y, z0, z1, head) {          // (x, y) 這一柱裡，z0..z1 之間可以站的高度（腳下實心、頭上 head 格空）；沒有 ⇒ -1
  for (var z = z1; z >= z0; z--) {
    if (!g.get(x, y, z - 1) || g.get(x, y, z)) continue;
    var ok = true;
    for (var h = 1; h < head; h++) if (g.get(x, y, z + h)) { ok = false; break; }
    if (ok) return z;
  }
  return -1;
}
var CREW_BLOCK = [];                               // 站位要避開的模型（砲、舵輪）：外框外擴 1 格、而且高度對得上那一層甲板
function blocked(x, y, z) {
  for (var i = 0; i < CREW_BLOCK.length; i++) {
    var b = CREW_BLOCK[i].bb;
    if (x >= Math.floor(b[0]) - 1 && x <= Math.ceil(b[3]) + 1 && y >= Math.floor(b[1]) - 1 && y <= Math.ceil(b[4]) + 1 && z >= b[2] - 3 && z <= b[5]) return true;
  }
  return false;
}
function standNear(g, x, y, z0, z1, head, taken) {   // (x, y) 附近 4 格內找一個可以站、還沒人站、不在模型裡的位置
  for (var r = 0; r <= 4; r++) for (var dy = -r; dy <= r; dy++) for (var dx = -r; dx <= r; dx++) {
    if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue;
    var k = (x + dx) + ',' + (y + dy); if (taken[k]) continue;
    var z = standZ(g, x + dx, y + dy, z0, z1, head);
    if (z >= 0 && !blocked(x + dx, y + dy, z)) { taken[k] = 1; return [x + dx + 0.5, y + dy + 0.5, z]; }
  }
  return null;
}
function makeCrew(sh) {
  var g = sh.T.base, CY = sh.T.cy, HULL_X0 = sh.T.hx0, HULL_X1 = sh.T.hx1, taken = {}, crew = [];
  // ⛔ 以前用平面的 taken 標模型外框：長砲改成模型之後，砲甲板的砲把上面 spar deck 的站位也佔掉了；火藥桶（艙底）更把大半個平面佔掉
  CREW_BLOCK = sh.models.filter(function (m) { return m.kind !== 'powder' || m.station; });   // 取用點的桶在甲板上 ⇒ 要避
  function add(role, at, gun, face) { if (at) crew.push({ role: role, home: at, pos: at.slice(), gun: gun, face: face || 1, st: 0, t: rnd() * 10, walk: null, fireT: 0, shotT: rr(2, 6), lost: 0, hp: CREW_HP, hitT: 0 }); }
  sh.guns.forEach(function (gn) {
    var b = gn.model.bb.map(Math.floor), z0, z1, i, n = GUNS[gn.type].crew;
    if (gn.type === 'chase') { z0 = b[2] - 3; z1 = b[2] + 3; }
    else if (gn.type === 'carr') { z0 = b[2] - 6; z1 = b[2] + 3; }
    else { z0 = b[2] - 8; z1 = b[2] + 3; }                            // 長砲（24、32 磅）
    var cx = Math.floor((b[0] + b[3]) / 2), sg = gn.side === 'P' ? -1 : 1, y0 = sg > 0 ? b[1] : b[4], spots;
    if (Math.abs(gn.ax[0]) <= Math.abs(gn.ax[1])) {
      // 往舷外開的砲（舷側砲、偏正橫的追擊砲）：砲的兩側（沿 x）、砲尾後面（inboard：S 那一舷的砲是 y 小的那邊、P 那一舷的砲是 y 大的那邊）
      spots = [[b[0] - 3, y0 + 10 * sg], [b[3] + 3, y0 + 10 * sg], [b[0] - 3, y0 + 4 * sg], [b[3] + 3, y0 + 4 * sg], [b[0] - 2, y0 - 3 * sg], [b[3] + 2, y0 - 3 * sg], [cx, y0 - 6 * sg], [cx - 5, y0 - 10 * sg]];
    } else {
      // 往船頭／船尾開的砲（餘燼號的船尾追擊砲：砲軸 −170°～−175°）：同一個排法轉 90° —— 砲的兩側（沿 y）、砲尾往船裡那一頭（沿 x）。
      // ⛔ 照上面那組排 ⇒ 站位落在船尾板外面或砲身上，四門船尾追擊砲各只找到 1 個位置、一個砲手都分不到（0／3），永遠開不了
      var ex = gn.ax[0] > 0 ? 1 : -1, x0 = ex > 0 ? b[0] : b[3], cyg = Math.floor((b[1] + b[4]) / 2);
      spots = [[x0 + 10 * ex, b[1] - 3], [x0 + 10 * ex, b[4] + 3], [x0 + 4 * ex, b[1] - 3], [x0 + 4 * ex, b[4] + 3], [x0 - 3 * ex, b[1] - 2], [x0 - 3 * ex, b[4] + 2], [x0 - 6 * ex, cyg], [x0 - 10 * ex, cyg - 5]];
    }
    gn.crewFull = n; gn.crewMin = GUNS[gn.type].min; gn.spots = [];
    for (i = 0; i < n; i++) {
      var at = standNear(g, spots[i][0], spots[i][1], z0, z1, 14, taken);
      if (!at) continue;
      add(ROLE.GUN, at, gn, 1); var c = crew[crew.length - 1]; c.deck = gunDeck(gn); c.side = gn.side; gn.spots.push({ at: at, who: c });
    }
    if (gn.spots[1]) gn.spots[1].who.rammer = true;                  // 只給畫用：裝填時拿推彈桿的那一個（41_crew_art.js 手持物）
  });
  // 送藥手：每一對砲（同一個 x 的兩舷）一個，從那一層的取用點搬火藥與彈藥到要裝填的砲（23_powder.js makeMonkeys／stepMonkey）
  makeMonkeys(sh, crew, taken, add);
  // spar deck 的高度：從 carronade 推；陸戰隊沿 S 那一舷（格 +y）的舷牆、軍官在後甲板、舵手在舵輪旁
  var carr = sh.models.filter(function (m) { return m.kind === 'carr'; }), wheel = sh.models.filter(function (m) { return m.kind === 'wheel'; })[0];
  var GZ = sh.T.geo, sz0 = carr.length ? Math.floor(carr[0].bb[2]) - 6 : GZ.spar ? GZ.spar[0] : 100, sz1 = carr.length || !GZ.spar ? sz0 + 9 : GZ.spar[1];   // 沒有 carronade ⇒ 船型給的高度（05_hull.js GEO0；夜隼號主甲板到後甲板）
  for (var x = HULL_X0 + GZ.marines[0]; x < HULL_X1 - GZ.marines[1] && crew.filter(function (c) { return c.role === ROLE.MARINE; }).length < 12; x += 37) {
    // 從中線往外走到舷牆前一格（⛔ 從外往裡掃會先碰到舷外的 channels 平台）
    var last = -1, m0 = sz0, m1 = sz1;
    if (GZ.spar) {   // 船型給了站人的範圍（夜隼號 z 28–47：主甲板到後甲板，舷側的繫繩欄、錨鏈台頂也在裡面 ⇒ 陸戰隊站到船殼外 y 113–116）⇒ 只看這一段甲板 −1～+2 格
      var zd = -1; for (var z = sz0; z <= sz1 && zd < 0; z++) if (standZ(g, x, CY + 10, z, z, 14) >= 0) zd = z;   // 最低那一層 ＝ 甲板（甲板上的東西都比它高）
      if (zd < 0) continue; m0 = zd - 1; m1 = zd + 2;
    }
    for (var y = CY + 4; y < CY + 80; y++) { if (standZ(g, x, y, m0, m1, 14) >= 0) last = y; else if (last >= 0) break; }
    if (last >= 0) add(ROLE.MARINE, standNear(g, x, last - 2, m0, m1, 14, taken), null, 1);
  }
  var qx = wheel ? Math.floor(wheel.c[0]) : HULL_X0 + 160;
  [[qx + 22, CY + 8], [qx + 30, CY - 6], [qx + 40, CY + 14], [qx + 14, CY - 12]].forEach(function (p) { add(ROLE.OFFICER, standNear(g, p[0], p[1], sz0, sz1, 14, taken), null, 1); });
  var cap = crew.filter(function (c) { return c.role === ROLE.OFFICER; })[0]; if (cap) cap.art = ART_CAPTAIN;   // 船長：只換貼圖
  if (wheel) { var wx = Math.floor(wheel.bb[0]) - 3; [[wx, CY + 3], [wx, CY - 3]].forEach(function (p) { add(ROLE.HELM, standNear(g, p[0], p[1], sz0, sz1, 14, taken), null, -1); }); }   // 舵輪後面（⛔ 舵輪中心往後 4 格還在舵輪的外框裡 ⇒ 以前一個舵手都站不上去）
  // 桅頂：每根桅最低的那層平台（從那根桅最低的橫帆桁往上，第一層有 6 個以上站得住的點；沒有帆桁 meta ⇒ 從 z 200）上分散站四個人；頭頂 1.4 m 空（同一般站位）。
  //   憲法號：前桅 263、主桅 286、後桅 241（帆桁 254／276／232 ⇒ 跟以前從 200 找一樣）；夜隼號：前桅 127、主桅 137。
  //   ⛔ 從 250 找 ⇒ 跳過後桅的桅頂；⛔ 不夠四個就往上找 ⇒ 站到 377–465 的高處橫桁上；⛔ 頭頂只看 0.6 m
  var TOP_A = [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15], TOP_R = [12, 15, 9, 18];   // 角度照「先對角、再補中間」排 ⇒ 四個人分散在平台四周
  function topSpot(m, k, r, z) {
    var a = k / 16 * 6.2832, px = Math.round(m.x + Math.cos(a) * r), py = Math.round(CY + Math.sin(a) * r);
    if (taken[px + ',' + py + ',' + z] || !g.get(px, py, z - 1) || g.get(px, py, z)) return null;
    for (var h = 1; h < 14; h++) if (g.get(px, py, z + h)) return null;
    return [px, py];
  }
  sh.masts.forEach(function (m) {
    for (var z = m.z0top || 200; z < 470; z++) {
      var n = 0; TOP_A.forEach(function (k) { TOP_R.forEach(function (r) { if (topSpot(m, k, r, z)) n++; }); });
      if (n < 6) continue;
      var found = 0;
      TOP_A.forEach(function (k) {
        for (var i = 0; i < TOP_R.length && found < 4; i++) { var p = topSpot(m, k, TOP_R[i], z); if (p) { taken[p[0] + ',' + p[1] + ',' + z] = 1; add(ROLE.TOP, [p[0] + 0.5, p[1] + 0.5, z], null, 1); found++; return; } }
      });
      return;
    }
  });
  makeHands(sh, crew, add);                                          // 預備水手：最後才生（數量 0 ⇒ 跟以前一樣，rnd() 一個都不多抽）
  return crew;
}
function able(c) { return c.st === 0; }
/** 每門砲現在有幾個人在崗（走過去的路上不算）。 */
function manning(sh) {
  sh.guns.forEach(function (g) { g.manned = 0; });
  sh.crew.forEach(function (c) { if (able(c) && c.gun && !c.walk) c.gun.manned++; });
}
/** 重新分派（每半秒），每層甲板各自來：
 *  ① 開得動的砲（在崗 ≥ crewMin）留著，人不動；
 *  ② 開不了的砲照在崗人數多到少，向「最近的空閒的人、或同樣開不了的砲」借人，借到能開就留下 ⇒ 人只走到隔壁幾門；
 *  ③ 借不夠的砲人放出來；空閒的人夠一整門才去開空砲，剩下的補滿留下的砲（都挑最近的）。
 *  只有換砲的人才走路。每層砲甲板（照砲的高度分，sh.decks）各自調度：憲法號 ＝ 砲甲板（長砲＋追擊砲）／上甲板（carronade）。 */
function reassign(sh) {
  sh.crew.forEach(function (c) { if (c.gun && (!able(c) || !c.gun.alive || c.gun.wet)) leaveGun(c); });   // wet：砲口泡在水裡（43_swim.js）
  var ds2 = []; sh.decks.forEach(function (D) { ds2.push([D.key, 'S'], [D.key, 'P']); });
  ds2.forEach(function (ds) {                                          // 每層甲板、每一舷各自調度
    var deck = ds[0], side = ds[1];
    var gs = sh.guns.filter(function (g) { return g.alive && !g.wet && g.side === side && gunDeck(g) === deck; });
    var men = sh.crew.filter(function (c) { return able(c) && c.role === ROLE.GUN && c.deck === deck && c.side === side; });
    var cur = new Map(); gs.forEach(function (g) { cur.set(g, 0); });
    men.forEach(function (c) { if (c.gun) cur.set(c.gun, cur.get(c.gun) + 1); });
    var kept = new Set(gs.filter(function (g) { return cur.get(g) >= g.crewMin; }));
    function short(c) { return !c.gun || (!kept.has(c.gun) && cur.get(c.gun) < c.gun.crewMin); }
    function move(c, g) {                        // c 換到 g
      if (c.gun) { cur.set(c.gun, cur.get(c.gun) - 1); leaveGun(c); }
      c.gun = g; cur.set(g, cur.get(g) + 1); goToGun(sh, c, g);
    }
    function nearest(list, g) { var bi = 0, bd = 1e9; list.forEach(function (c, i) { var d = Math.abs(g.muz[0] - c.pos[0]); if (d < bd) { bd = d; bi = i; } }); return list.splice(bi, 1)[0]; }
    gs.filter(function (g) { return !kept.has(g) && cur.get(g) > 0; })
      .sort(function (a, b) { return cur.get(b) - cur.get(a) || gs.indexOf(a) - gs.indexOf(b); })
      .forEach(function (g) {
        if (!cur.get(g)) return;                                           // 已經被別門借光
        var pool = men.filter(function (c) { return c.gun !== g && short(c); });
        if (cur.get(g) + pool.length < g.crewMin) return;                  // 借不夠 ⇒ 這門是借出去的那一方
        while (cur.get(g) < g.crewMin) move(nearest(pool, g), g);
        kept.add(g);
      });
    men.forEach(function (c) { if (c.gun && !kept.has(c.gun)) { cur.set(c.gun, cur.get(c.gun) - 1); leaveGun(c); } });
    var free = men.filter(function (c) { return !c.gun; });
    gs.forEach(function (g) {
      if (kept.has(g) || free.length < g.crewMin) return;
      while (cur.get(g) < g.crewMin) move(nearest(free, g), g);
      kept.add(g);
    });
    kept.forEach(function (g) { while (cur.get(g) < g.crewFull && free.length) move(nearest(free, g), g); });
  });
}
function gunDeck(g) { return g.deck; }                  // 那門砲在哪一層（10_ship.js gunDecks）
/** 離開原本那門砲：站位讓出來（⛔ 不清 ⇒ 幾輪之後每個站位都被兩個人佔著）。 */
function leaveGun(c) {
  if (c.gun && c.gun.spots) c.gun.spots.forEach(function (s) { if (s.who === c) s.who = null; });
  c.gun = null;
}
/** 走去新砲：挑一個沒人、腳下還有甲板的站位；都沒有 ⇒ 在第一個站位附近重新找站得住的格（⛔ 退路不能落在砲身裡）。 */
function goToGun(sh, c, g) {
  var spot = (g.spots || []).filter(function (s) {
    if (s.who && able(s.who) && s.who.gun === g) return false;
    var x = Math.floor(s.at[0]), y = Math.floor(s.at[1]);
    return countBox(sh.grid, x - 1, y - 1, s.at[2] - 1, x + 1, y + 1, s.at[2] - 1) > 0;
  })[0];
  var to = spot ? spot.at : null;
  if (!to && g.spots && g.spots.length) { var a = g.spots[0].at; to = standNear(sh.grid, Math.floor(a[0]), Math.floor(a[1]), a[2] - 2, a[2] + 2, 14, {}); }
  if (!to) to = c.pos;
  if (spot) spot.who = c;
  c.walk = { to: to.slice(), sp: 18 };
}
/** 這一點附近的人扣血（r 格數）：rKill 內吃滿基準傷害 base，rKill～rWound 從 0.55 遞減到 0.1，再乘 0.6～1.4 的隨機。
 *  base ＝ 1.4 × 每發傷害 × 彈種對人倍率（crewBase）⇒ 24 磅實心 140：rKill 內約 85% 當場陣亡（跟以前的 0.85 對齊）。
 *  dir（格座標的單位向量）給了 ⇒ 前方（碎屑噴的方向）的範圍拉長。list：只看這幾個人（砲彈掠過，21_gunnery.js ballNear 先挑好的；沒給 ⇒ 全船）。 */
function hurt(sh, L, rKill, rWound, dir, cause, base, list) {
  var n = 0;
  (list || sh.crew).forEach(function (c) {
    if (c.st > 1) return;
    var d = sub([c.pos[0], c.pos[1], c.pos[2] + 9], L), dist = len(d);
    if (dir) { var along = dot(d, dir); if (along > 0) dist = Math.sqrt(Math.max(0, dist * dist - along * along * 0.75)); }  // 前方的碎屑錐
    if (dist >= Math.max(rKill, rWound)) return;
    var f = dist < rKill ? 1 : 0.55 - 0.45 * (dist - rKill) / (rWound - rKill);
    damageCrew(sh, c, base * f * rr(0.6, 1.4), cause); n++;
  });
  return n;
}
/** 船員扣血：歸零陣亡；掉到一半以下受傷倒下（之後再被打到照樣扣，歸零才算陣亡）；一半以上照常作戰，只閃紅。 */
function damageCrew(sh, c, dmg, cause) {
  if (c.st > 1 || !(dmg > 0)) return;
  if (c.cart) cartHit(sh, c, dmg);                   // 手上的藥包：吃到夠重的一下就著火（23_powder.js）
  c.hp -= dmg; c.hitT = 0.4;
  if (c.hp <= 0) killCrew(sh, c, cause);
  else if (c.hp < CREW_HP * 0.5 && c.st === 0) woundCrew(sh, c, cause);
}
function woundCrew(sh, c, cause) { if (c.st !== 0) return; c.st = 1; c.t = 0; c.walk = null; c.cart = false; c.moving = false; sh.wounded++; sh.wounds++; sh.causes[cause] = (sh.causes[cause] || 0) + 1; newsCrew(sh, c, false, cause); }
function killCrew(sh, c, cause) {
  if (c.st >= 2) return;
  if (c.st === 1) sh.wounded--;
  c.fromW = c.st === 1;                               // 只給畫用：從跪著倒下（不是從站直倒）
  c.st = 2; c.t = 0; c.walk = null; c.cart = false; c.moving = false; c.hp = Math.min(c.hp, 0); sh.dead++; sh.kills++; sh.causes[cause] = (sh.causes[cause] || 0) + 1; newsCrew(sh, c, true, cause);
}
/** 掉下去：腳下那一格沒了（甲板被打穿、桅頂跟著桅倒）⇒ 換成世界座標的落體，落水算失蹤（亡）。 */
function fall(sh, c, v) {
  if (c.st >= 2 && c.st !== 2) return;
  var w = M4.pt(sh.M, c.pos[0], c.pos[1], c.pos[2]);
  if (c.st < 2 && DROWN_T > 0) { if (c.st === 1) { sh.wounded--; c.hurtSwim = true; } c.fellAlive = true; }   // 落水求生（43_swim.js）：先不算陣亡，落到水裡變成在游
  else if (c.st < 2) { if (c.st === 1) sh.wounded--; sh.dead++; sh.kills++; sh.causes['落水'] = (sh.causes['落水'] || 0) + 1; newsCrew(sh, c, true, '落水'); }
  c.st = 4; c.fw = w; c.fv = add(v || [gauss(), rr(0, 2), gauss()], sh.vel); c.t = 0; c.walk = null; c.cart = false; c.moving = false;
}
function stepCrew(sh, dt) {
  sh.navN = HAND_PATHS;                                 // 預備水手這一步還能找幾次路（42_hands.js）
  sh.crew.forEach(function (c) {
    c.t += dt; if (c.hitT > 0) c.hitT -= dt;            // hitT：被打中但沒倒下的閃紅
    if (c.st === 4) {                                   // 落體
      c.fv[1] -= G * dt; c.fw = add(c.fw, mul(c.fv, dt));
      if (c.fw[1] < seaH(c.fw[0], c.fw[2], SIMT)) { if (!c.splashed) { c.splashed = true; splash(c.fw, false); } if (c.fellAlive) { c.fellAlive = false; toSwim(sh, c, [c.fw[0], c.fw[1] - 1.2, c.fw[2]]); } else c.st = 3; }
      return;
    }
    if (c.st === 5) { stepSwim(sh, c, dt); return; }      // 在水裡（43_swim.js）
    if (c.st === 1 && c.t > 12) { c.st = 3; return; }    // 傷者被抬下去
    if (c.st !== 0) return;
    if (c.role === ROLE.HAND) { stepHand(sh, c, dt); return; }   // 預備水手：走路、爬梯子、補位（42_hands.js）
    if (c.walk) {
      var d = sub(c.walk.to, c.pos), l = Math.hypot(d[0], d[1]);
      if (l < 0.6) { c.pos = c.walk.to.slice(); c.home = c.pos.slice(); c.walk = null; }
      else { var s = Math.min(l, c.walk.sp * dt); c.pos[0] += d[0] / l * s; c.pos[1] += d[1] / l * s; }
    } else if (c.role === ROLE.POWDER) stepMonkey(sh, c, dt);   // 送藥手：取用點 ⇄ 砲
    if ((c.role === ROLE.MARINE || c.role === ROLE.TOP) && !sh.sunk && !sh.struck && !(MODE === 'sandbox' && sh.i !== PLAYER_I)) {   // 陸戰隊與桅頂水手：火槍（沙盒的敵艦不還手）
      c.shotT -= dt; c.fireT -= dt;
      if (c.shotT <= 0) { c.shotT = rr(4, 8); musket(sh, c); }
    }
  });
  if (sh.xfer) swimXfer(sh);                            // 游到敵艦的人換名單（43_swim.js；跑完 forEach 才換）
}
/** 火槍：打對方露天的人（spar deck、桅頂），距離越遠越難中。 */
function musket(sh, c) {
  var foe = foeOf(sh), w = M4.pt(sh.M, c.pos[0], c.pos[1], c.pos[2] + 14);
  if (!foe) return;
  var cand = foe.crew.filter(function (o) { return o.st === 0 && (o.role !== ROLE.GUN && o.role !== ROLE.POWDER && o.role !== ROLE.HAND || o.deck === foe.weatherDeck); });   // 露天的人（最上面那層砲甲板的砲班、走到那一層的預備水手也算）
  c.fireT = 0.4;
  spawnPt(w, [WIND[0] * 0.3, 0.4, WIND[2] * 0.3], rr(1.5, 2.5), [0.85, 0.85, 0.85], 0.35, 0.3, 1.4, -0.03, 0.8);
  if (!cand.length) return;
  var o = cand[(rnd() * cand.length) | 0], ow = M4.pt(foe.M, o.pos[0], o.pos[1], o.pos[2]), dist = len(sub(ow, w));
  if (rnd() < clamp(0.05 * 100 / dist, 0.01, 0.12)) damageCrew(foe, o, rr(40, 125), '火槍');   // 血量 100 時約三成一槍斃命（跟以前的 0.3 對齊）
}
/** 一門砲：在崗的人數決定能不能開、裝填多快。 */
function gunRate(g) { return g.wet ? 0 : g.manned >= g.crewMin ? Math.pow(Math.min(1, g.manned / g.crewFull), 0.85) : 0; }
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/41_crew_art.js ──
// ───────────────────────── 船員貼圖：替代品（程式畫）／美術（#art-crew） ─────────────────────────
// 格子：每格 CELL_W × CELL_H（寬:高 ＝ 1:2）；列 ＝ 角色×隊伍（role*2 + team，0 藍 1 紅）；人一律朝右畫，腳底在格子底邊中間。
// 欄：**單圖**（1 欄，每個角色一張；預設）⇒ 動作全由程式做（crewPose：晃、上下、縮放、傾斜、躺倒）；
//     或 8 欄（每欄一個動作 FR，以後有逐格美術時用）⇒ 照欄選格，程式動作只疊輕的一層。
var CELL_W = 64, CELL_H = 128, CREW_TEX = null, CREW_ART = false, CREW_COLS = 1, CREW_ROWS = NART, BBVAO = null, BBBUF = null, BBMAX = 1400, BBS = 16, BB = new Float32Array(BBMAX * BBS);
var FX_TEX = null, HUD_ART = null;
function drawFigure(g, ox, oy, role, team, f) {
  var blue = team === 0, skin = '#d9a77c', pants = '#e6dfcc', shoe = '#1b1b1b';
  var jacket = role === ROLE.MARINE ? (blue ? '#1f3a6e' : '#b8322a') : role === ROLE.OFFICER ? (blue ? '#1b2a4d' : '#4f1616') : role === ROLE.TOP ? '#d8d2c0' : (blue ? '#2c4f8f' : '#9c2f2f');
  var hat = role === ROLE.OFFICER ? '#111' : role === ROLE.MARINE ? (blue ? '#0f1e3d' : '#1b1b1b') : (blue ? '#16294d' : '#4a1212');
  var sc = role === ROLE.POWDER ? 0.74 : 1;
  g.save(); g.translate(ox + CELL_W / 2, oy + CELL_H - 2);
  if (f === FR.DEAD) { g.translate(-26, -3); g.rotate(-Math.PI / 2); g.scale(0.58, 0.58); }
  else if (f === FR.WOUNDED) { g.translate(0, 0); }
  g.scale(sc, sc);
  function rect(x, y, w, h, c) { g.fillStyle = c; g.fillRect(x, y, w, h); }
  function line(x0, y0, x1, y1, w, c) { g.strokeStyle = c; g.lineWidth = w; g.lineCap = 'round'; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); }
  var sitting = f === FR.WOUNDED, hip = sitting ? -22 : -52, top = hip - 38;
  // 腿
  if (sitting) { line(-4, hip, 20, -6, 6, pants); line(2, hip, 26, -4, 6, pants); rect(20, -9, 9, 5, shoe); }
  else {
    var a = f === FR.RUN_A ? 0.45 : f === FR.RUN_B ? -0.45 : f === FR.WORK_A ? 0.25 : 0.06;
    line(-3, hip, -3 - Math.sin(a) * 50, hip + Math.cos(a) * 50, 6, pants); line(3, hip, 3 + Math.sin(a) * 50, hip + Math.cos(a) * 50, 6, pants);
    rect(-3 - Math.sin(a) * 50 - 4, hip + Math.cos(a) * 50 - 3, 10, 5, shoe); rect(3 + Math.sin(a) * 50 - 2, hip + Math.cos(a) * 50 - 3, 10, 5, shoe);
  }
  // 身體（彎腰：推彈、搬東西）
  var lean = f === FR.WORK_A ? 0.35 : sitting ? 0.25 : 0;
  g.save(); g.translate(0, hip); g.rotate(lean);
  rect(-10, -38, 20, 40, jacket);
  if (role === ROLE.MARINE) { line(-9, -36, 9, -2, 3, '#f2efe6'); line(9, -36, -9, -2, 3, '#f2efe6'); }
  if (role === ROLE.OFFICER) { rect(-12, -38, 6, 4, '#e2b84a'); rect(6, -38, 6, 4, '#e2b84a'); }
  if (role === ROLE.TOP) { for (var k = -32; k < 0; k += 8) rect(-10, k, 20, 3, blue ? '#2c4f8f' : '#9c2f2f'); }
  if (sitting) rect(-6, -26, 10, 9, '#9c1c1c');                         // 傷
  // 手臂
  var sh0 = [8, -34];
  if (f === FR.WORK_A) { line(sh0[0], sh0[1], 30, -16, 5, jacket); line(-6, -34, 26, -12, 5, jacket); line(18, -18, 40, -12, 3, '#6b4a2a'); }      // 推彈桿
  else if (f === FR.WORK_B) { line(sh0[0], sh0[1], 18, -64, 5, jacket); line(-6, -34, 8, -66, 5, jacket); }                                        // 拉砲索
  else if (f === FR.FIRE && (role === ROLE.MARINE || role === ROLE.TOP)) { line(sh0[0], sh0[1], 26, -32, 5, jacket); line(-6, -34, 22, -30, 5, jacket); line(4, -30, 46, -34, 3, '#4b3621'); }  // 舉槍
  else if (f === FR.FIRE && role === ROLE.OFFICER) { line(sh0[0], sh0[1], 26, -54, 5, jacket); line(24, -52, 40, -78, 2, '#cfd6dc'); }               // 舉劍
  else if (f === FR.FIRE) { line(sh0[0], sh0[1], 28, -50, 5, jacket); }                                                                             // 砲長：手一揮
  else if (sitting) { line(sh0[0], sh0[1], 2, -22, 5, jacket); }
  else { line(sh0[0], sh0[1], 11, -2, 5, jacket); line(-8, -34, -11, -2, 5, jacket); if (role === ROLE.MARINE) line(14, 2, 14, -60, 3, '#4b3621'); }
  // 頭、帽子
  g.fillStyle = skin; g.beginPath(); g.arc(1, -47, 8, 0, 6.2832); g.fill();
  if (role === ROLE.OFFICER) { g.fillStyle = hat; g.beginPath(); g.ellipse(1, -55, 15, 5, 0, 0, 6.2832); g.fill(); rect(-3, -62, 8, 6, hat); }
  else if (role === ROLE.MARINE) rect(-7, -68, 16, 14, hat);
  else if (role !== ROLE.POWDER) { rect(-9, -57, 20, 4, hat); rect(-6, -63, 14, 7, hat); }
  g.restore();
  g.restore();
}
/** 替代品：每列（職位＋船長）、每個隊伍一張待命的站姿（單圖 ⇒ 1 欄）；船長那一列畫成軍官。 */
function crewPlaceholder() {
  var c = document.createElement('canvas'); c.width = CELL_W; c.height = NART * 2 * CELL_H;
  var g = c.getContext('2d');
  for (var r = 0; r < NART; r++) for (var team = 0; team < 2; team++) drawFigure(g, 0, (r * 2 + team) * CELL_H, r < NROLE ? r : ROLE.OFFICER, team, FR.IDLE);
  return c;
}
/** n 列的 crew.png（鍵色版）⇒ 2n 列（每個角色一列藍隊、一列紅隊）：鍵色 #FF00FF／#C000C0／#800080 換成隊色的亮／中／暗。 */
function teamRecolor(im, cw, ch, n) {
  var c = document.createElement('canvas'); c.width = im.width; c.height = ch * n * 2;
  var g = c.getContext('2d');
  var TEAM = [[[111, 155, 255], [62, 104, 196], [33, 60, 128]], [[255, 111, 111], [196, 62, 62], [128, 33, 33]]];
  for (var r = 0; r < n; r++) for (var t = 0; t < 2; t++) g.drawImage(im, 0, r * ch, im.width, ch, 0, (r * 2 + t) * ch, im.width, ch);
  var d = g.getImageData(0, 0, c.width, c.height), px = d.data;
  for (var i = 0; i < px.length; i += 4) {
    if (px[i + 1] > 8 || px[i] !== px[i + 2]) continue;
    var k = px[i] === 255 ? 0 : px[i] === 192 ? 1 : px[i] === 128 ? 2 : -1; if (k < 0) continue;
    var row = Math.floor(i / 4 / c.width / ch), col = TEAM[row & 1][k];
    px[i] = col[0]; px[i + 1] = col[1]; px[i + 2] = col[2];
  }
  g.putImageData(d, 0, 0);
  return c;
}
function texFrom(src) {
  var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src); gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return t;
}
/** 美術交件了就換上：寬:高 1:2 的格子，1 欄（單圖）或 8 欄（逐格動作）；列 ＝ 7 個角色（含船長）或舊的 6 個，各一列（鍵色換隊色）或藍紅各一列；
 *  沒交、或尺寸不對 ⇒ 留著替代品，並在讀數裡說為什麼。 */
function loadArt() {
  CREW_TEX = texFrom(crewPlaceholder()); CREW_COLS = 1; CREW_ROWS = NART;
  var why = [];
  var p1 = VK.embeddedImage('art-crew').then(function (im) {
    if (!im) { why.push('船員：替代品（art/crew.png 沒交）'); return; }
    var ok = [NART, NROLE, NART * 2, NROLE * 2];
    var cols = [1, NFR].filter(function (n) { var cw = im.width / n, rows = im.height / (cw * 2); return im.width % n === 0 && ok.indexOf(rows) >= 0; })[0];
    if (!cols) { why.push('船員：替代品（art/crew.png 是 ' + im.width + '×' + im.height + '；要每格寬:高 ＝ 1:2、1 欄（單圖）或 ' + NFR + ' 欄、' + ok.join('／') + ' 列）'); console.warn('art/crew.png 尺寸不對，改用替代品'); return; }
    var cw = im.width / cols, ch = cw * 2, rows = im.height / ch, keyed = rows === NART || rows === NROLE;
    CREW_TEX = texFrom(keyed ? teamRecolor(im, cw, ch, rows) : im); CREW_ART = true; CREW_COLS = cols; CREW_ROWS = keyed ? rows : rows / 2;
    why.push('船員：美術 ' + im.width + '×' + im.height + (cols === 1 ? '（單圖，動作由程式做）' : '（' + cols + ' 欄逐格）') + (keyed ? '（鍵色換隊色）' : '') + (CREW_ROWS < NART ? '（沒有船長那一列：用軍官）' : ''));
  });
  var p2 = VK.embeddedImage('art-fx').then(function (im) {
    if (!im) { why.push('特效：替代品'); return; }
    if (im.width !== im.height) { why.push('特效：替代品（art/fx.png 要是正方形 4×4 格）'); return; }
    FX_TEX = texFrom(im); why.push('特效：美術 ' + im.width + '×' + im.height);
  });
  var p3 = VK.embeddedImage('art-hud').then(function (im) {
    if (!im) { why.push('HUD：文字符號'); return; }
    HUD_ART = { src: im.src, cw: im.width / 8, ch: im.height / 2 }; why.push('HUD：美術 ' + im.width + '×' + im.height);
  });
  return Promise.all([p1, p2, p3]).then(function () { return why.join('、'); });
}
/** billboard：一個人 ＝ 一張直立、面向鏡頭的貼圖。每個實例：iP（腳底、高）、iU（貼圖格）、iS（寬、明暗、傾斜、上下）、iA（閃紅）。
 *  傾斜繞腳底轉（在貼圖平面上）⇒ 前傾、後仰都是同一個旋轉；上下是整個人抬高或壓低。
 *  倒下的人（iA.yzw ＝ 倒向，世界座標）：身體從直立轉向那個固定的方向（iS.z ＝ 倒下了幾度），貼圖繞身體那條軸轉向鏡頭
 *  ⇒ 躺的方向不跟著鏡頭轉，但還是面向鏡頭（Tim 2026-10-12；⛔ 以前躺倒也是在貼圖平面上轉 ⇒ 鏡頭一轉，屍體跟著在甲板上轉）。 */
function bbSetup() {
  P.bb = VK.compile(gl,
    '#version 300 es\nlayout(location=0) in vec2 aQ; layout(location=1) in vec4 iP; layout(location=2) in vec4 iU; layout(location=3) in vec4 iS; layout(location=4) in vec4 iA;\n' +
    'uniform mat4 uVP; uniform vec3 uRight,uEye; out vec2 vUV; out vec3 vW; out float vS; out float vF;\n' +
    'void main(){ vec2 q=vec2(aQ.x*iS.x,aQ.y*iP.w); vec3 w;\n' +
    ' if(dot(iA.yzw,iA.yzw)>0.0){ vec3 d=normalize(iA.yzw), a=normalize(vec3(0.0,cos(iS.z),0.0)+d*sin(iS.z)), sx=cross(a,normalize(uEye-iP.xyz)); float l=length(sx); sx=l>1e-4?sx/l:uRight;\n' +
    '   w=iP.xyz+sx*q.x+a*q.y+vec3(0.0,iS.w,0.0); }\n' +
    ' else { float c=cos(iS.z), s=sin(iS.z); q=vec2(c*q.x-s*q.y,s*q.x+c*q.y); w=iP.xyz+uRight*q.x+vec3(0.0,q.y+iS.w,0.0); }\n' +
    ' vW=w; vUV=vec2(mix(iU.x,iU.z,aQ.x+0.5),mix(iU.w,iU.y,aQ.y)); vS=iS.y; vF=iA.x; gl_Position=uVP*vec4(w,1.0); }\n',
    '#version 300 es\nprecision highp float; in vec2 vUV; in vec3 vW; in float vS; in float vF; uniform sampler2D uTex; uniform vec3 uEye,uFog; uniform float uFogD,uLum; out vec4 o;\n' +
    'void main(){ vec4 t=texture(uTex,vUV); if(t.a<0.5) discard; vec3 c=mix(t.rgb*vS*uLum,vec3(1.0,0.12,0.08),vF*0.8); if(vW.y<0.0) c=mix(c,vec3(0.04,0.18,0.22),0.6);\n' +
    ' float fd=length(vW-uEye); o=vec4(mix(c,uFog,1.0-exp(-fd*uFogD)),1.0); }\n');
  BBVAO = gl.createVertexArray(); gl.bindVertexArray(BBVAO);
  var q = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, q); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-0.5, 0, 0.5, 0, 0.5, 1, -0.5, 0, 0.5, 1, -0.5, 1]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 8, 0);
  BBBUF = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, BBBUF); gl.bufferData(gl.ARRAY_BUFFER, BB.byteLength, gl.DYNAMIC_DRAW);
  [[1, 0], [2, 16], [3, 32], [4, 48]].forEach(function (a) { gl.enableVertexAttribArray(a[0]); gl.vertexAttribPointer(a[0], 4, gl.FLOAT, false, BBS * 4, a[1]); gl.vertexAttribDivisor(a[0], 1); });
  gl.bindVertexArray(null);
  ITVAO = gl.createVertexArray(); gl.bindVertexArray(ITVAO);                        // 手持物：同一個 billboard 程式、另一份實例
  gl.bindBuffer(gl.ARRAY_BUFFER, q); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 8, 0);
  ITBUF = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, ITBUF); gl.bufferData(gl.ARRAY_BUFFER, ITB.byteLength, gl.DYNAMIC_DRAW);
  [[1, 0], [2, 16], [3, 32], [4, 48]].forEach(function (a) { gl.enableVertexAttribArray(a[0]); gl.vertexAttribPointer(a[0], 4, gl.FLOAT, false, BBS * 4, a[1]); gl.vertexAttribDivisor(a[0], 1); });
  gl.bindVertexArray(null);
  ITEM_TEX = itemAtlas();
}
// ───── 手持物（Tim 2026-10-12）─────
// 送藥手搬的時候抱著藥筒、上面一顆彈丸；陸戰隊與桅頂水手瞄準、開槍時舉平火槍；軍官與船長齊射時舉劍；裝填中的砲班每門一個人拿推彈桿往前推。
// 立繪照舊（Tim：立繪不用改）⇒ 陸戰隊身上那把直立的槍、軍官腰上的劍還在，手持物是另外疊的一層、只在那個動作時出現。
// 點陣圖在程式裡畫（方塊清單 ⇒ 小畫布 ⇒ 最近點取樣），1 格 ＝ 1/46 m（約水手立繪的兩個像素）；每件都朝右畫，握的地方在 pv（格）。
// 畫的時候跟著人：手的位置（身高的比例）照人的縮放與傾斜轉，再加道具自己的角度（朝前 0、往上為正）；跟人同一個面 ⇒ 往鏡頭挪 6 cm。⛔ 只管畫、不碰 rnd()。
var ITEM_PPM = 46, ITEM_TEX = null, ITEM_UV = {}, ITMAX = 600, ITB = new Float32Array(ITMAX * BBS), ITVAO = null, ITBUF = null, FIG_K = 164 / 192;   // FIG_K：站著的人佔格高的比例（make_crew.py 的 H_PX）
var ITEM_DEF = {
  musket: { w: 64, h: 7, pv: [2, 4], r: [[0, 2, 5, 4, '#5a3a1e'], [0, 2, 1, 4, '#c9a44a'], [5, 2, 8, 3, '#6b4423'], [5, 5, 2, 1, '#5a3a1e'], [13, 3, 38, 2, '#6b4423'],   // 火槍 1.4 m：槍托、槍身、槍管、槍機、扳機護弓、銅箍、通條
    [11, 2, 53, 1, '#3b3d42'], [22, 1, 42, 1, '#5d6168'], [10, 1, 4, 2, '#9aa0a8'], [12, 5, 4, 1, '#c9a44a'], [48, 3, 2, 2, '#c9a44a'], [16, 5, 30, 1, '#3a2414']] },
  sword: { w: 40, h: 5, pv: [4, 2], r: [[0, 1, 2, 3, '#c9a44a'], [2, 1, 4, 3, '#2b1d12'], [6, 0, 2, 5, '#c9a44a'], [8, 1, 29, 2, '#c3cad1'], [8, 1, 29, 1, '#eef2f5'], [37, 2, 2, 1, '#c3cad1']] },   // 劍 0.87 m
  carry: { w: 14, h: 22, pv: [7, 15], r: [[1, 9, 12, 13, '#7a5230'], [3, 9, 2, 13, '#946a40'], [1, 12, 12, 1, '#4a2e17'], [1, 19, 12, 1, '#4a2e17'], [0, 8, 14, 2, '#5a3a1e'],   // 藥筒（裝一份火藥的木筒）＋上面一顆彈丸
    [5, 0, 4, 1, '#232428'], [4, 1, 6, 1, '#232428'], [3, 2, 8, 4, '#232428'], [4, 6, 6, 1, '#232428'], [5, 7, 4, 1, '#232428'], [5, 2, 2, 1, '#6a6d73']] },
  rammer: { w: 100, h: 4, pv: [40, 2], r: [[5, 1, 89, 2, '#9a7a4c'], [94, 0, 6, 4, '#4a3a2a'], [0, 0, 5, 4, '#d8cfb8']] }   // 推彈桿 2.2 m（一頭推彈、一頭海綿）
};
function itemAtlas() {
  var W = 0, H = 0, k, x = 0;
  for (k in ITEM_DEF) { W += ITEM_DEF[k].w + 2; H = Math.max(H, ITEM_DEF[k].h); }
  var c = document.createElement('canvas'); c.width = W; c.height = H; var g = c.getContext('2d');
  for (k in ITEM_DEF) {
    var d = ITEM_DEF[k], x0 = x;
    d.r.forEach(function (r) { g.fillStyle = r[4]; g.fillRect(x0 + r[0], r[1], r[2], r[3]); });
    ITEM_UV[k] = [x0 / W, 0, (x0 + d.w) / W, d.h / H];                               // 跟人的格子同一個排法：[左 u, 上 v, 右 u, 下 v]
    x += d.w + 2;
  }
  var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, c);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);   // 點陣：最近點，不糊（不做 mipmap：細的槍在遠處不會被平均掉）
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return t;
}
/** 這個人手上拿什麼：{ id, hx, hy（手：往前、往上，身高的比例）, a（道具的角度：朝前 0、往上為正）}；沒有 ⇒ null。 */
function heldItem(sh, c, f) {
  if (c.st !== 0) return null;                                                      // 受傷、陣亡、墜落 ⇒ 手上的東西掉了
  if (c.role === ROLE.POWDER) return c.cart > 0 ? { id: 'carry', hx: 0.17, hy: 0.52, a: 0 } : null;
  if (c.role === ROLE.MARINE || c.role === ROLE.TOP) {                              // 開槍前一秒舉槍瞄準、開完 0.4 秒放下（沙盒的敵艦、降旗、沉了不開槍）
    var aim = (c.fireT > 0 || c.shotT < 1) && !sh.struck && !sh.sunk && !(MODE === 'sandbox' && sh.i !== PLAYER_I);
    return aim ? { id: 'musket', hx: 0.04, hy: 0.78, a: 0.04 } : null;
  }
  if (c.role === ROLE.OFFICER) return sh.salvoT && SIMT - sh.salvoT < 1.2 ? { id: 'sword', hx: 0.12, hy: 0.86, a: 1.05 } : null;   // 齊射：舉劍
  if (c.role === ROLE.GUN && c.rammer && (f === FR.WORK_A || f === FR.WORK_B)) {      // 裝填：推彈桿一推一收（跟裝填姿勢同一個節奏）
    var w = 0.5 + 0.5 * Math.sin(c.t * 6.2832 * 1.1); return { id: 'rammer', hx: 0.06 + 0.16 * w, hy: 0.5, a: -0.06 };
  }
  return null;
}
/** 這個人現在在做什麼（FR）：單圖時決定程式動作，8 欄時也是選哪一格。 */
function crewFrame(sh, c) {
  if (c.st === 5) return c.swim && c.swim.dead ? FR.DEAD : Math.floor(c.t * 1.6) & 1 ? FR.RUN_A : FR.RUN_B;   // 在水裡：划水（43_swim.js）
  if (c.st === 2 || c.st === 4) return c.st === 4 ? FR.RUN_A : FR.DEAD;
  if (c.st === 1) return FR.WOUNDED;
  var ph = Math.floor(c.t * 2.5) & 1;
  if (c.walk || c.moving) return ph ? FR.RUN_A : FR.RUN_B;
  if (c.role === ROLE.POWDER && c.pm && c.pm.st === 'fill') return ph ? FR.WORK_A : FR.WORK_B;   // 在取用點拿火藥與彈藥
  if (c.role === ROLE.GUN && c.gun) {
    if (SIMT - (c.gun.firedAt || -9) < 0.7) return FR.FIRE;
    if (c.gun.reload > 0 && c.gun.manned >= c.gun.crewMin) return ph ? FR.WORK_A : FR.WORK_B;
    return FR.IDLE;
  }
  if (c.role === ROLE.MARINE || c.role === ROLE.TOP) return c.fireT > 0 && !sh.struck && !sh.sunk ? FR.FIRE : c.role === ROLE.TOP ? (Math.floor(c.t * 0.7) & 1 ? FR.WORK_B : FR.IDLE) : FR.IDLE;
  if (c.role === ROLE.OFFICER) return sh.salvoT && SIMT - sh.salvoT < 1.2 ? FR.FIRE : FR.IDLE;
  if (c.role === ROLE.HELM) return FR.WORK_B;
  return FR.IDLE;
}
/** 程式動作：lean（往面向的那邊傾，弧度；負 ＝ 往後仰）、bob（整個人上下，公尺）、sx／sy（寬、高的倍率）。
 *  c.t：活著的人是自己的時鐘（開局給了亂數相位，大家不會同步晃）；受傷、陣亡、墜落那一刻歸零 ⇒ 也拿來算閃紅。
 *  ⛔ 只管畫：不碰 rnd()、不回寫模擬。 */
function crewPose(sh, c, f) {
  var t = c.t, P2 = 6.2832, k = { lean: 0, bob: 0, sx: 1, sy: 1 };
  if (c.st === 4) { k.lean = t * 7; return k; }                                       // 墜落：翻滾
  if (c.st === 5) { k.lean = c.swim && c.swim.dead ? -0.9 : 0.22 + 0.06 * Math.sin(t * 5); return k; }   // 在水裡：往前趴著划；溺水往後仰
  if (f === FR.DEAD) {                                                                // 往後倒、躺平（抬一點 ⇒ 身體不陷進甲板）
    var d = Math.min(1, t / 0.35), d2 = d * d;
    if (c.fromW) { k.lean = -0.18 + (-1.5708 + 0.18) * d2; k.sy = 0.7 + 0.3 * d; k.sx = 1.06 - 0.06 * d; k.bob = 0.18 * d; return k; }   // 受傷跪著的人：從跪姿倒下
    k.lean = -1.5708 * d2; k.bob = 0.18 * d; return k;
  }
  if (f === FR.WOUNDED) { k.sy = 0.7; k.sx = 1.06; k.lean = -0.18 + 0.04 * Math.sin(t * 9); return k; }        // 跪下、發抖（倒下時從這個姿勢接，見上面 fromW）
  if (f === FR.RUN_A || f === FR.RUN_B) {                                             // 跑：彈跳、前傾、落地壓扁
    var r = Math.abs(Math.sin(t * P2 * 2.2)); k.bob = 0.09 * r; k.lean = 0.16 + 0.05 * Math.sin(t * P2 * 2.2); k.sy = 0.94 + 0.06 * r; k.sx = 1.04 - 0.04 * r; return k;
  }
  if (f === FR.FIRE) {                                                                 // 開砲／開槍／揮劍：一下後座往後仰、壓扁，慢慢回來
    var since = c.role === ROLE.GUN && c.gun ? SIMT - (c.gun.firedAt || -9) : c.role === ROLE.OFFICER ? SIMT - (sh.salvoT || -9) : 0.4 - c.fireT;
    var e = Math.exp(-Math.max(0, since) * 6);
    if (c.role === ROLE.OFFICER) { k.lean = -0.1 * e; k.sy = 1 + 0.08 * e; return k; }    // 軍官：挺直、往上拉
    k.lean = -0.28 * e; k.sy = 1 - 0.12 * e; k.sx = 1 + 0.08 * e; return k;
  }
  if (f === FR.WORK_A || f === FR.WORK_B) {                                            // 裝填：有節奏地前傾下壓（推彈、拉砲索）
    var w = 0.5 + 0.5 * Math.sin(t * P2 * 1.1); k.lean = 0.12 + 0.28 * w; k.sy = 1 - 0.1 * w; k.sx = 1 + 0.05 * w; k.bob = -0.04 * w;
    if (c.role === ROLE.HELM) { k.lean = 0.06 * Math.sin(t * 0.8); k.sy = 1; k.sx = 1; k.bob = 0; }          // 舵手：跟著舵輪輕晃
    if (c.role === ROLE.TOP) { k.lean = 0.1 * Math.sin(t * 1.3); k.sy = 1; k.sx = 1; k.bob = 0; }            // 桅頂：跟著桅晃
    return k;
  }
  k.sy = 1 + 0.022 * Math.sin(t * P2 * 0.32); k.lean = 0.035 * Math.sin(t * 0.9);   // 待命：呼吸、輕晃
  if (c.role === ROLE.TOP) k.lean = 0.09 * Math.sin(t * 1.3);
  return k;
}
var CREW_H = 2.1;                                  // 人物高（公尺）：1.75 → 2.1（Tim 2026-10-12：放大 1.2 倍，遠一點也看得清）
function drawCrew() {
  var n = 0, ni = 0, fw = norm([CAM.look[0] - CAM.eye[0], 0, CAM.look[2] - CAM.eye[2]]), right = [-fw[2], 0, fw[0]], frames = CREW_COLS > 1;
  SHIPS.forEach(function (sh) {
    var gone = sh.sink > 40;                           // 沉了：船上的不畫，在水裡的照畫（43_swim.js）
    if (gone && !sh.swims) return;
    var team = teamIdx(sh), faceW = M4.dir(sh.M, 0, 1, 0);
    sh.crew.forEach(function (c) {
      if (c.st === 3 || n >= BBMAX || (gone && c.st !== 5) || cutHides(sh, c)) return;             // cutHides：剖面、隱藏甲板拿掉的那一邊（74_cutaway.js）
      var art = c.art !== undefined && c.art < CREW_ROWS ? c.art : c.role;   // 船長那一列沒有 ⇒ 用職位那一列
      var w = c.st === 4 || c.st === 5 ? c.fw : M4.pt(sh.M, c.pos[0], c.pos[1], c.pos[2]), f = crewFrame(sh, c), row = art * 2 + team;
      var wt = c.walk ? c.walk.to : c.hand && c.moving ? c.hand.to : null;   // 要去的那一點（預備水手：照路走、爬梯子，42_hands.js）
      var fd = c.st === 5 && (c.fv[0] || c.fv[2]) ? [c.fv[0], 0, c.fv[2]] : wt ? M4.dir(sh.M, wt[0] - c.pos[0], wt[1] - c.pos[1], 0) : mul(faceW, c.face), flip = dot(fd, right) < 0;   // 在水裡：面向游的方向（世界座標）
      var col = frames ? f : 0, u0 = col / CREW_COLS, u1 = (col + 1) / CREW_COLS, v0 = row / (CREW_ROWS * 2), v1 = (row + 1) / (CREW_ROWS * 2), k = n * BBS, h = CREW_H;
      var ps = crewPose(sh, c, f), amp = frames ? 0.35 : 1;                            // 8 欄逐格：姿勢在圖裡，程式只疊輕的一層（不再躺、不再跪）
      if (frames && (f === FR.DEAD || f === FR.WOUNDED) && c.st !== 4) ps = { lean: 0, bob: 0, sx: 1, sy: 1 };
      var lean = ps.lean * (c.st === 4 ? 1 : amp), sy = 1 + (ps.sy - 1) * amp, sx = 1 + (ps.sx - 1) * amp;
      var flash = Math.max(c.st === 1 || c.st === 2 || c.st === 4 ? Math.max(0, 1 - c.t / 0.4) : 0, c.hitT > 0 ? c.hitT / 0.4 : 0);   // 被打中那一下閃紅（倒下：c.t 在那一刻歸零；沒倒下：hitT）
      BB[k] = w[0]; BB[k + 1] = w[1]; BB[k + 2] = w[2]; BB[k + 3] = h * sy;
      BB[k + 4] = flip ? u1 : u0; BB[k + 5] = v0; BB[k + 6] = flip ? u0 : u1; BB[k + 7] = v1;
      BB[k + 8] = h * CELL_W / CELL_H * sx; BB[k + 9] = c.st === 1 ? 0.85 : 1; BB[k + 10] = flip ? lean : -lean; BB[k + 11] = ps.bob * amp;   // 往面向的那邊傾：面右 ⇒ 順時針
      BB[k + 12] = flash; BB[k + 13] = 0; BB[k + 14] = 0; BB[k + 15] = 0;
      if (c.st === 2 && f === FR.DEAD && !frames) {                                // 倒下：躺向固定的方向（不跟著鏡頭轉），見 bbSetup
        if (!c.fallD) { var fa = hash3(c.home[0] * 4 | 0, c.home[1] * 4 | 0, c.home[2] | 0) * 6.2832; c.fallD = [Math.cos(fa), Math.sin(fa)]; }   // 只給畫用：照站位的雜湊挑一個方向（不碰 rnd()）
        var dw = norm(M4.dir(sh.M, c.fallD[0], c.fallD[1], 0));
        BB[k + 4] = u0; BB[k + 6] = u1; BB[k + 10] = -lean; BB[k + 13] = dw[0]; BB[k + 14] = dw[1]; BB[k + 15] = dw[2];   // 倒下了幾度 ＝ −lean（往後倒是負的）
      }
      n++;
      var it = c.st === 0 && ni < ITMAX ? heldItem(sh, c, f) : null;
      if (it) {                                                                       // 手持物：在「朝右」的座標裡算（往前 x、往上 y、逆時針為正），朝左再鏡射
        var d = ITEM_DEF[it.id], uv = ITEM_UV[it.id], fh = h * FIG_K * (art === ROLE.POWDER ? 0.75 : 1), iw = d.w / ITEM_PPM, ih = d.h / ITEM_PPM;
        var pqx = (d.pv[0] + 0.5) / ITEM_PPM - iw / 2, pqy = ih - (d.pv[1] + 0.5) / ITEM_PPM;   // 握的地方在貼圖裡的位置（貼圖的轉軸是底邊中間）
        var be = -lean, cb = Math.cos(be), sb = Math.sin(be), hx = it.hx * fh * sx, hy = it.hy * fh * sy;   // 人往前傾 lean ⇒ 朝右時順時針
        var Hx = cb * hx - sb * hy, Hy = sb * hx + cb * hy + ps.bob * amp, al = it.a + be, ca = Math.cos(al), sa = Math.sin(al);
        var Bx = Hx - (ca * pqx - sa * pqy), By = Hy - (sa * pqx + ca * pqy), bx = flip ? -Bx : Bx, q = ni * BBS;
        ITB[q] = w[0] + right[0] * bx - fw[0] * 0.06; ITB[q + 1] = w[1] + By; ITB[q + 2] = w[2] + right[2] * bx - fw[2] * 0.06; ITB[q + 3] = ih;
        ITB[q + 4] = flip ? uv[2] : uv[0]; ITB[q + 5] = uv[1]; ITB[q + 6] = flip ? uv[0] : uv[2]; ITB[q + 7] = uv[3];
        ITB[q + 8] = iw; ITB[q + 9] = 1; ITB[q + 10] = flip ? -al : al; ITB[q + 11] = 0;
        ITB[q + 12] = flash; ITB[q + 13] = 0; ITB[q + 14] = 0; ITB[q + 15] = 0; ni++;
      }
    });
  });
  if (!n) return;
  gl.useProgram(P.bb.prog); setCommon(P.bb); gl.uniform3fv(P.bb.u.uRight, right);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, CREW_TEX); gl.uniform1i(P.bb.u.uTex, 0);
  gl.bindVertexArray(BBVAO); gl.bindBuffer(gl.ARRAY_BUFFER, BBBUF); gl.bufferSubData(gl.ARRAY_BUFFER, 0, BB, 0, n * BBS);
  gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, n); gl.bindVertexArray(null);
  if (ni && ITEM_TEX) {
    gl.bindTexture(gl.TEXTURE_2D, ITEM_TEX); gl.bindVertexArray(ITVAO); gl.bindBuffer(gl.ARRAY_BUFFER, ITBUF); gl.bufferSubData(gl.ARRAY_BUFFER, 0, ITB, 0, ni * BBS);
    gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, ni); gl.bindVertexArray(null);
  }
  ITEMS_N = ni;
}
var ITEMS_N = 0;                                   // 讀數：上一格畫了幾件手持物
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/42_hands.js ──
// ───────────────────────── 預備水手（缺人手時補位；平常在水線下的甲板待命，也會上別層甲板走動） ─────────────────────────
// Tim 2026-10-13：通用水手待在水線下的甲板待命，缺人手時補上；也可以在其他甲板遊蕩。
// 補哪些位：砲班（每層、每一舷補回開戰時的人數；砲沒了就少補）、送藥手（每層補回開戰時的人數）、舵手（舵輪還在）。交戰的那一舷先補。
//   每半秒（survey）點一次名：缺幾個就派幾個最近的閒著的水手；走到那一層甲板（爬完梯子那一刻）就換成那個職位，
//   之後照原本的調度走（砲班 reassign、送藥手 stepMonkey）；舵手先走到倒下那位的站位再換。
// 梯子照模型的 meta（basecamp：關聯 meta kind=ladders，固定點 <梯名>.foot／lo／hi／head ＝ 腳踩的那一格）：
//   走到 foot → 沿 lo、hi 爬 → 在 head 下梯；一座梯子一次上一個人（前一個爬了 LADDER_GAP 秒，下一個才上）。
//   沒有梯子的 meta（舊的 .vxk）⇒ 預備水手待在最下層的砲甲板，只補那一層。
// 走得到的甲板 ＝ 砲甲板（sh.decks）＋梯子的一頭落在砲甲板以外的高度（憲法號：住艙甲板，地板在設計水線下 0.3 m）；待命 ＝ 最下面那層。
// 走路格：每層每 NAV_C 格一點，站得住（頭上 1.2 m 空）、不在砲與舵輪裡、跟最大那一片連得通（相鄰高低差 ≤ NAV_DZ：憲法號砲甲板 x 570 有一階 0.3 m，⛔ 2 格 ⇒ 前段整片接不上）；
//   找路 ＝ 走路格上的 BFS 再拉直。
//   ⛔ 走路格只照開戰時的船：甲板被打穿照樣走過去（跟砲班換砲一樣），站著不動時腳下沒了才掉（survey）。
// 一個人物 ＝ 一個預備水手（數量在細節設定，0 ＝ 沒有）；開戰時的人數算進 crew0（降旗的死傷 % 跟著算）。
var NAV_C = 2, NAV_HEAD = 12, NAV_DZ = 3, HAND_SP = [11, 20], CLIMB_SP = [6, 9], LADDER_GAP = 0.9, HAND_PATHS = 2, HAND_ROAM = 0.25, HAND_BACK = 0.6, CLIMB_LIFT = 2;
var NAV_DX = [1, -1, 0, 0, 1, 1, -1, -1], NAV_DY = [0, 0, 1, -1, 1, -1, 1, -1];
/** 梯子：關聯 meta kind=ladders 的固定點 <梯名>.foot／lo／hi／head（格中心）⇒ [{ name, pts }]（站位座標：x、y 照格中心，z ＝ 腳踩的那一格；foot 在下）。 */
function shipLadders(T) {
  var out = [];
  (T.h.parts || []).forEach(function (p) {
    if (!p.meta || (p.meta.kind !== 'ladders' && p.meta.kind !== 'ladder')) return;
    var by = {};
    Object.keys(p.points || {}).forEach(function (k) {
      var i = k.lastIndexOf('.'), nm = i < 0 ? '' : k.slice(0, i), w = i < 0 ? k : k.slice(i + 1), v = p.points[k];
      (by[nm] = by[nm] || {})[w] = [v[0], v[1], Math.floor(v[2])];
    });
    Object.keys(by).forEach(function (nm) {
      var b = by[nm]; if (!b.foot || !b.head) return;
      var pts = [b.foot, b.lo, b.hi, b.head].filter(Boolean); if (b.foot[2] > b.head[2]) pts.reverse();
      out.push({ name: (p.path || '') + (nm ? '/' + nm : ''), pts: pts });
    });
  });
  return out;
}
function lvOf(Ls, z) { for (var i = 0; i < Ls.length; i++) if (z >= Ls[i].zr[0] && z <= Ls[i].zr[1]) return i; return -1; }
/** 走得到的甲板（由下往上）：砲甲板＋梯子一頭落在砲甲板以外的高度（相差 8 格內併成一層，上下各留 5 格的舷弧，不蓋到砲甲板）。 */
function navLevels(sh, lads) {
  var Ls = sh.decks.map(function (D) { return { key: D.key, name: D.name, zr: D.zr }; }), ext = [];
  lads.forEach(function (l) {
    [l.pts[0], l.pts[l.pts.length - 1]].forEach(function (p) {
      if (lvOf(Ls, p[2]) >= 0) return;
      var e = ext.filter(function (e) { return p[2] >= e[0] - 8 && p[2] <= e[1] + 8; })[0];
      if (e) { e[0] = Math.min(e[0], p[2]); e[1] = Math.max(e[1], p[2]); } else ext.push([p[2], p[2]]);
    });
  });
  var low = Ls.length ? Ls[0].zr[0] : 1e9;
  ext.forEach(function (e, i) {
    var zr = [e[0] - 5, e[1] + 5];
    Ls.forEach(function (L) { if (L.zr[0] > e[1] && zr[1] >= L.zr[0]) zr[1] = L.zr[0] - 1; if (L.zr[1] < e[0] && zr[0] <= L.zr[1]) zr[0] = L.zr[1] + 1; });
    Ls.push({ key: 'h' + i, name: e[1] < low ? '住艙甲板' : '甲板（z ' + e[0] + '）', zr: zr });
  });
  return Ls.sort(function (a, b) { return a.zr[0] - b.zr[0]; });
}
/** a 往 d 方向走一格 ⇒ 那一格（站不住、高低差太大、斜走切到角 ⇒ -1）。邊上一圈一定站不住 ⇒ 不用另外查界。 */
function navStep(N, a, d) {
  var Z = N.Z, b = a + NAV_DX[d] + NAV_DY[d] * N.nx;
  if (Z[b] < 0 || Math.abs(Z[b] - Z[a]) > NAV_DZ) return -1;
  if (d >= 4 && (Z[a + NAV_DX[d]] < 0 || Z[a + NAV_DY[d] * N.nx] < 0)) return -1;
  return b;
}
/** 一層的走路格（照船型與那一層的高度記在 T 上：兩艘同型共用、重開一場不重算）。 */
function navBuild(sh, L) {
  var T = sh.T, g = T.base, C = T.navC || (T.navC = {}), key = L.zr.join(',') + ':' + sh.models.length;
  if (C[key]) return C[key];
  var x0 = Math.max(0, T.hx0 - 4), nx = Math.ceil((Math.min(g.sx, T.hx1 + 5) - x0) / NAV_C) + 1, ny = Math.ceil(g.sy / NAV_C), n = nx * ny, i, x, y;
  var Z = new Int16Array(n).fill(-1);
  for (y = 1; y < ny - 1; y++) for (x = 1; x < nx - 1; x++) {
    var gx = x0 + x * NAV_C, gy = y * NAV_C; if (gx >= g.sx || gy >= g.sy) continue;
    var z = standZ(g, gx, gy, L.zr[0], L.zr[1], NAV_HEAD);
    if (z >= 0 && !blocked(gx, gy, z)) Z[x + y * nx] = z;
  }
  var N = { x0: x0, nx: nx, ny: ny, Z: Z }, comp = new Int32Array(n).fill(-1), q = new Int32Array(n), best = -1, bestN = 0, nc = 0;   // 連通（8 鄰）；留最大那一片
  for (i = 0; i < n; i++) {
    if (Z[i] < 0 || comp[i] >= 0) continue;
    var h = 0, t = 0; q[t++] = i; comp[i] = nc;
    while (h < t) { var a = q[h++]; for (var d = 0; d < 8; d++) { var b = navStep(N, a, d); if (b >= 0 && comp[b] < 0) { comp[b] = nc; q[t++] = b; } } }
    if (t > bestN) { bestN = t; best = nc; }
    nc++;
  }
  var ok = new Uint8Array(n), cells = new Int32Array(bestN), k = 0;
  for (i = 0; i < n; i++) if (comp[i] === best) { ok[i] = 1; cells[k++] = i; }
  N.ok = ok; N.cells = cells; N.parts = nc;
  return C[key] = N;
}
function navCell(N, p) { var x = Math.round((p[0] - 0.5 - N.x0) / NAV_C), y = Math.round((p[1] - 0.5) / NAV_C); return x < 0 || y < 0 || x >= N.nx || y >= N.ny ? -1 : x + y * N.nx; }
function navPos(N, i) { return [N.x0 + (i % N.nx) * NAV_C + 0.5, ((i / N.nx) | 0) * NAV_C + 0.5, N.Z[i]]; }
/** p 附近 r 點內、連得通的最近那一點（高度差一格 ＝ 遠 8 點的平面距離²；4 格以上最後才挑）；沒有 ⇒ -1。
 *  ⛔ 只看平面距離 ⇒ 梯子 head（甲板 z 82）吸到旁邊艙口圍欄的頂上（z 85），人下梯往上跳一下。 */
function navSnap(N, p, r) {
  var cx = Math.round((p[0] - 0.5 - N.x0) / NAV_C), cy = Math.round((p[1] - 0.5) / NAV_C), best = -1, bd = 1e9;
  for (var dy = -r; dy <= r; dy++) for (var dx = -r; dx <= r; dx++) {
    var x = cx + dx, y = cy + dy; if (x < 0 || y < 0 || x >= N.nx || y >= N.ny) continue;
    var i = x + y * N.nx; if (!N.ok[i]) continue;
    var dz = Math.abs(N.Z[i] - p[2]), d = dx * dx + dy * dy + dz * 8 + (dz > 3 ? 1e4 : 0); if (d < bd) { bd = d; best = i; }
  }
  return best;
}
var NQ = null, NP = null, NV = null, NSTAMP = 0;
/** 走路格上 a → b 的路（BFS，8 鄰）；走不到 ⇒ null。 */
function navPath(N, a, b) {
  var n = N.nx * N.ny, u, v, d;
  if (!NQ || NQ.length < n) { NQ = new Int32Array(n); NP = new Int32Array(n); NV = new Uint32Array(n); NSTAMP = 0; }
  var s = ++NSTAMP, h = 0, t = 0; NQ[t++] = a; NV[a] = s; NP[a] = -1;
  while (h < t) {
    u = NQ[h++]; if (u === b) break;
    for (d = 0; d < 8; d++) { v = navStep(N, u, d); if (v >= 0 && N.ok[v] && NV[v] !== s) { NV[v] = s; NP[v] = u; NQ[t++] = v; } }
  }
  if (NV[b] !== s) return null;
  var p = []; for (u = b; u >= 0; u = NP[u]) p.push(u);
  return p.reverse();
}
/** a、b 之間直直走過去，每一點都連得通？ */
function navSee(N, a, b) {
  var nx = N.nx, ax = a % nx, ay = (a / nx) | 0, bx = b % nx, by = (b / nx) | 0, n = Math.max(Math.abs(bx - ax), Math.abs(by - ay)) * 2, prev = a;
  for (var k = 1; k <= n; k++) {
    var c = Math.round(ax + (bx - ax) * k / n) + Math.round(ay + (by - ay) * k / n) * nx; if (c === prev) continue;
    if (!N.ok[c] || Math.abs(N.Z[c] - N.Z[prev]) > NAV_DZ) return false;
    var dx = c % nx - prev % nx, dy = ((c / nx) | 0) - ((prev / nx) | 0);
    if (dx && dy && (!N.ok[prev + dx] || !N.ok[prev + dy * nx])) return false;
    prev = c;
  }
  return true;
}
/** 拉直：從每一點往前找看得到的最遠那一點（最多往前 80 點）。 */
function navSmooth(N, p) {
  var out = [p[0]], i = 0;
  while (i < p.length - 1) {
    var j = Math.min(p.length - 1, i + 80);
    while (j > i + 1 && !navSee(N, p[i], p[j])) j--;
    out.push(p[j]); i = j;
  }
  return out;
}
/** 層 a → 層 b 經過哪幾層（梯子連著的才算；走不到 ⇒ null）。 */
function lvPath(H, a, b) {
  var prev = {}, q = [a]; prev[a] = -1;
  while (q.length) {
    var u = q.shift(); if (u === b) break;
    H.ladders.forEach(function (L) { var v = L.lo === u ? L.hi : L.hi === u ? L.lo : -1; if (v >= 0 && !(v in prev)) { prev[v] = u; q.push(v); } });
  }
  if (!(b in prev)) return null;
  var p = []; for (var u = b; u >= 0; u = prev[u]) p.push(u);
  return p.reverse();
}
/** 從 from 層（x）去 to 層（目的地 tx）的走法：每換一層 ＝ 走到梯子那一頭＋爬；梯子挑「走過去＋從那裡再走＋排在前面的人」最短的那座
 *  （L.q：路上要爬這座的人數，一個人 ＝ 等 LADDER_GAP 秒 ⇒ 換算成跑得到的格數；⛔ 不算 ⇒ 開戰第一輪 26 個人全擠後梯子，10 秒只補上 2 個）。 */
function handRoute(sh, from, to, x, tx) {
  var H = sh.nav, path = lvPath(H, from, to); if (!path) return null;
  var legs = [];
  for (var i = 0; i + 1 < path.length; i++) {
    var a = path[i], b = path[i + 1], best = -1, bd = 1e9;
    H.ladders.forEach(function (L, k) { if ((L.lo === a && L.hi === b) || (L.lo === b && L.hi === a)) { var d = Math.abs(x - L.x) + Math.abs(L.x - tx) + L.q * LADDER_GAP * HAND_SP[1]; if (d < bd) { bd = d; best = k; } } });
    var L = H.ladders[best], up = L.lo === a;
    legs.push({ w: a, to: up ? L.ia : L.ib }, { c: best, up: up }); x = L.x; L.q++;
  }
  return legs;
}
/** 開戰時：建走路格、接梯子、記各職位開戰時的人數（補到這個數），在待命那一層生 HANDS 個預備水手（彼此隔 3 點以上）。 */
function makeHands(sh, crew, add) {
  sh.nav = null;
  if (HANDS <= 0 && DROWN_T <= 0) return;                               // 落水的人爬回船上也要走路格（43_swim.js board）
  var t0 = performance.now(), lads = shipLadders(sh.T), Ls = navLevels(sh, lads), LD = [];
  Ls.forEach(function (L) { L.N = navBuild(sh, L); });
  lads.forEach(function (l) {
    var a = l.pts[0], b = l.pts[l.pts.length - 1], la = lvOf(Ls, a[2]), lb = lvOf(Ls, b[2]);
    if (la < 0 || lb < 0 || la === lb) return;
    var ia = navSnap(Ls[la].N, a, 5), ib = navSnap(Ls[lb].N, b, 5); if (ia < 0 || ib < 0) return;   // 兩頭接不上走路格（10 格內）⇒ 這座不用
    var mid = l.pts.slice(1, -1).map(function (q) { return [q[0], q[1], q[2] + CLIMB_LIFT]; });   // lo、hi 抬 0.2 m：兩點連線會切過踏板的前緣（量過：腳在踏板裡 24／71 點 ⇒ 10）
    LD.push({ name: l.name, lo: la, hi: lb, ia: ia, ib: ib, pts: [navPos(Ls[la].N, ia), a].concat(mid, [b, navPos(Ls[lb].N, ib)]), x: (a[0] + b[0]) / 2, t0: -9, n: 0, q: 0 });
  });
  var home = -1;
  LD.forEach(function (L) { if (home < 0 || L.lo < home) home = L.lo; });
  if (home < 0) home = lvOf(Ls, sh.decks.length ? sh.decks[0].zr[0] : 0);
  if (home < 0) return;
  var H = sh.nav = { levels: Ls, ladders: LD, home: home, reach: [], gun0: {}, pm0: {}, helm0: 0, called: 0, joined: 0, ms: 0 };
  Ls.forEach(function (L, i) { if (lvPath(H, home, i)) H.reach.push(i); });
  crew.forEach(function (c) {
    if (c.role === ROLE.GUN) H.gun0[c.deck + c.side] = (H.gun0[c.deck + c.side] || 0) + 1;
    else if (c.role === ROLE.POWDER) H.pm0[c.deck] = (H.pm0[c.deck] || 0) + 1;
    else if (c.role === ROLE.HELM) H.helm0++;
  });
  var N = Ls[home].N, used = [];
  var NH = Math.round(HANDS * sh.T.geo.handsK);                       // 船型的倍率（05_hull.js GEO0；夜隼號 ¼：小船）
  if (N.cells.length) for (var k = 0; k < NH; k++) {
    var i = -1;
    for (var tries = 0; tries < 12; tries++) {
      i = N.cells[(rnd() * N.cells.length) | 0];
      var ix = i % N.nx, iy = (i / N.nx) | 0;
      if (!used.some(function (u) { return Math.abs(u % N.nx - ix) < 3 && Math.abs(((u / N.nx) | 0) - iy) < 3; })) break;
    }
    used.push(i);
    add(ROLE.HAND, navPos(N, i), null, rnd() < 0.5 ? 1 : -1);
    var c = crew[crew.length - 1]; c.art = ROLE.GUN; c.deck = Ls[home].key; c.hand = { lv: home, wait: rr(0, 6), legs: [], wp: null, k: 0, climb: null, job: null, to: null };
  }
  H.ms = performance.now() - t0;
}
/** 每一步：爬梯子、照路走、出發下一段、到了就補位；閒著 ⇒ 站一會兒再走去別處（待命那一層多、偶爾上別層）。 */
function stepHand(sh, c, dt) {
  var H = c.hand, NV = sh.nav, fast = H.job ? 1 : 0;
  if (H.climb) {                                                         // 爬：沿 foot → lo → hi → head 一段一段走（三維）
    var P = H.climb.pts, to = P[H.climb.k], d = sub(to, c.pos), l = len(d), s = CLIMB_SP[fast] * dt;
    c.moving = true; H.to = to;
    if (l <= s) {
      c.pos = to.slice();
      if (++H.climb.k >= P.length) {
        H.lv = H.climb.lv; c.deck = NV.levels[H.lv].key; H.climb = null; c.moving = false;
        if (c.backRole !== undefined) { c.role = c.backRole; c.backRole = undefined; c.hand = null; c.home = c.pos.slice(); }   // 爬回船上的軍官、陸戰隊（43_swim.js board）：回原職
      }
    }
    else c.pos = add(c.pos, mul(d, s / l));
    return;
  }
  if (H.wp) {                                                            // 走：照拉直過的路一點一點走，高度跟著甲板
    var w = H.wp[H.k], dx = w[0] - c.pos[0], dy = w[1] - c.pos[1], dl = Math.hypot(dx, dy), st = HAND_SP[fast] * dt;
    c.moving = true; H.to = w;
    if (dl <= st) { c.pos = w.slice(); if (++H.k >= H.wp.length) { H.wp = null; c.moving = false; c.home = c.pos.slice(); } return; }
    c.pos[0] += dx / dl * st; c.pos[1] += dy / dl * st;
    var N = NV.levels[H.lv].N, ci = navCell(N, c.pos); if (ci >= 0 && N.Z[ci] >= 0) c.pos[2] = N.Z[ci];
    return;
  }
  c.moving = false;
  if (H.legs.length) { legStart(sh, c); return; }
  if (H.job) { handJoin(sh, c); return; }
  if (sh.struck || sh.sunk || (H.wait -= dt) > 0) return;
  wander(sh, c);
}
/** 出發下一段：走（要一次找路的額度，每艘每步 HAND_PATHS 次）或爬（梯子空出來才上）。走不到 ⇒ 整段作廢、站一會兒。 */
function legStart(sh, c) {
  var H = c.hand, NV = sh.nav, leg = H.legs[0];
  if (leg.c !== undefined) {
    var L = NV.ladders[leg.c]; if (SIMT - L.t0 < LADDER_GAP) return;
    L.t0 = SIMT; L.n++; L.q = Math.max(0, L.q - 1); H.legs.shift();
    H.climb = { pts: leg.up ? L.pts : L.pts.slice().reverse(), k: 0, lv: leg.up ? L.hi : L.lo };
    return;
  }
  if (sh.navN <= 0) return;
  sh.navN--;
  var N = NV.levels[leg.w].N, a = navSnap(N, c.pos, 4), p = a >= 0 ? navPath(N, a, leg.to) : null;
  if (!p) { H.legs = []; H.wait = 1; return; }                          // 走不到（站在走路格外、被隔開）⇒ 放棄這一趟（有任務 ⇒ 下一拍 handJoin 照現在的層判斷）
  H.legs.shift();
  H.wp = navSmooth(N, p).map(function (i) { return navPos(N, i); }); H.k = 0;
}
/** 閒著：在待命那一層 HAND_ROAM 的機會上別層；在別層 HAND_BACK 的機會回待命那一層；其餘在這一層隨便挑一點走過去。 */
function wander(sh, c) {
  var H = c.hand, NV = sh.nav, lv = H.lv, tl = lv;
  if (lv === NV.home) { if (NV.reach.length > 1 && rnd() < HAND_ROAM) { var o = NV.reach.filter(function (i) { return i !== NV.home; }); tl = o[(rnd() * o.length) | 0]; } }
  else if (rnd() < HAND_BACK && NV.reach.indexOf(lv) >= 0) tl = NV.home;
  var N = NV.levels[tl].N, to = N.cells[(rnd() * N.cells.length) | 0], legs = handRoute(sh, lv, tl, c.pos[0], navPos(N, to)[0]);
  H.wait = rr(3, 9);
  if (!legs) return;
  H.legs = legs.concat([{ w: tl, to: to }]);
}
/** 點名（每半秒，survey）：照開戰時的人數算每一格缺幾個，派最近的閒著的水手（交戰那一舷的砲班先、再來送藥手與舵手、另一舷最後）。 */
function callHands(sh) {
  var NV = sh.nav; if (!NV || sh.struck || sh.sunk) return;
  NV.ladders.forEach(function (L) { L.q = 0; });                       // 排隊的人數每半秒重數（倒下、放棄的路不會一直佔著）
  sh.crew.forEach(function (c) { if (c.role === ROLE.HAND && able(c)) c.hand.legs.forEach(function (l) { if (l.c !== undefined) NV.ladders[l.c].q++; }); });
  var idle = sh.crew.filter(function (c) { return c.role === ROLE.HAND && able(c) && !c.hand.job && !c.hand.climb; }); if (!idle.length) return;
  var going = {}, need = [];
  sh.crew.forEach(function (c) { if (c.role === ROLE.HAND && able(c) && c.hand.job) { var k = c.hand.job.kind + c.hand.job.key; going[k] = (going[k] || 0) + 1; } });
  sh.decks.forEach(function (D) {
    var lv = lvOf(NV.levels, D.zr[0]); if (NV.reach.indexOf(lv) < 0) return;
    ['S', 'P'].forEach(function (side) {
      var gs = sh.guns.filter(function (g) { return g.alive && !g.wet && g.deck === D.key && g.side === side; }); if (!gs.length) return;
      var want = Math.min(NV.gun0[D.key + side] || 0, gs.reduce(function (a, g) { return a + g.crewFull; }, 0));
      var have = sh.crew.filter(function (c) { return c.role === ROLE.GUN && able(c) && c.deck === D.key && c.side === side; }).length;
      var n = want - have - (going['gun' + D.key + side] || 0), wx = 0, ww = 0;
      gs.forEach(function (g) { var m = Math.max(0, g.crewFull - g.manned); wx += g.muz[0] * m; ww += m; });
      if (n > 0) need.push({ kind: 'gun', key: D.key + side, deck: D.key, side: side, lv: lv, n: n, x: ww ? wx / ww : gs[0].muz[0], pri: side === sh.side ? 0 : 2 });
    });
    var pm = sh.crew.filter(function (c) { return c.role === ROLE.POWDER && able(c) && c.deck === D.key; }).length, pn = (NV.pm0[D.key] || 0) - pm - (going['pm' + D.key] || 0);
    if (pn > 0 && sh.stations.some(function (s) { return s.deck === D.key && !s.mag.gone; })) need.push({ kind: 'pm', key: D.key, deck: D.key, lv: lv, n: pn, x: sh.T.cx, pri: 1 });
  });
  var wheel = sh.models.filter(function (m) { return m.kind === 'wheel'; })[0], hd = sh.crew.filter(function (c) { return c.role === ROLE.HELM && !able(c) && !c.relieved; });
  var hn = Math.min(hd.length, NV.helm0 - sh.crew.filter(function (c) { return c.role === ROLE.HELM && able(c); }).length - (going.helm || 0));
  if (wheel && wheel.alive && hn > 0) {
    var lvh = lvOf(NV.levels, hd[0].home[2]);
    if (NV.reach.indexOf(lvh) >= 0) for (var j = 0; j < hn; j++) need.push({ kind: 'helm', key: '', lv: lvh, n: 1, x: hd[j].home[0], spot: hd[j].home, pri: 1, who: hd[j] });
  }
  need.sort(function (a, b) { return a.pri - b.pri; });
  need.forEach(function (q) {
    for (var k = 0; k < q.n && idle.length; k++) {
      var bi = -1, bd = 1e9;
      idle.forEach(function (c, i) { var d = Math.abs(c.pos[0] - q.x) + 150 * Math.abs(c.hand.lv - q.lv); if (d < bd) { bd = d; bi = i; } });
      var c = idle[bi], H = c.hand, legs = handRoute(sh, H.lv, q.lv, c.pos[0], q.x);
      idle.splice(bi, 1); if (!legs) continue;
      if (q.kind === 'helm') { var si = navSnap(NV.levels[q.lv].N, q.spot, 4); if (si < 0) continue; legs.push({ w: q.lv, to: si }); q.who.relieved = true; }
      H.job = { kind: q.kind, key: q.key, deck: q.deck, side: q.side, lv: q.lv, spot: q.spot };
      H.legs = legs; H.wp = null; c.moving = false; NV.called++;
    }
  });
}
/** 到了：換成那個職位（砲班 ⇒ 下一拍 reassign 分砲；送藥手 ⇒ 接倒下那位的砲；舵手 ⇒ 站到舵輪後）。不在那一層（路斷了）⇒ 任務作廢、照常閒晃。 */
function handJoin(sh, c) {
  var H = c.hand, J = H.job, NV = sh.nav;
  if (H.lv !== J.lv) { H.job = null; H.wait = 1; return; }
  c.walk = null; c.moving = false; c.home = c.pos.slice(); c.hand = null; NV.joined++;
  if (J.kind === 'gun') { c.role = ROLE.GUN; c.deck = J.deck; c.side = J.side; c.gun = null; return; }
  if (J.kind === 'helm') { c.role = ROLE.HELM; c.deck = sh.weatherDeck; c.face = -1; return; }
  var dead = sh.crew.filter(function (o) { return o.role === ROLE.POWDER && o.deck === J.deck && !able(o) && !o.relieved; })[0];
  c.role = ROLE.POWDER; c.deck = J.deck; c.pm = { st: 'idle', t: 0 }; c.cart = false; c.guns = dead ? dead.guns : [];
  if (dead) { dead.relieved = true; c.home = dead.home.slice(); }
  c.guns.forEach(function (g) { if (!g.pm || !able(g.pm)) g.pm = c; });
}
/** HUD 一段：預備水手（閒著的／在路上補位的）。 */
function handsText(sh) {
  if (!sh.nav) return '';
  var h = sh.crew.filter(function (c) { return c.role === ROLE.HAND && able(c); }), go = h.filter(function (c) { return c.hand.job; }).length;
  return '　預備 ' + (h.length - go) + (go ? '（補位中 ' + go + '）' : '');
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/43_swim.js ──
// ───────────────────────── 落水求生（水淹過頭 ⇒ 浮上水面、往自己的船游、太久溺水） ─────────────────────────
// Tim 2026-10-13：水完全淹沒水手時讓他漂浮到水面上，然後可以嘗試游回船上，太久會溺水。
// Tim（TASK-0536）：主要是要處理「船沉到水中的那一段，船員還能裝填、開砲」。
// 什麼時候算「淹過頭」（drownCheck，每半秒 survey）：頭頂（腳底往上 1.7 m）低於當地的海面，而且那一層通海 ——
//   砲甲板以上（有砲門）一律通；住艙以下（封閉）⇒ 船開始沉、沉了或斷了才算 —— 之前艙內那一格的水滿了九成（粒子模式）⇒ 預備水手往上一層躲（evacuate），
//   待命的那一層也搬上去（⛔ 也當成落水 ⇒ 艙內的人穿過船殼浮到海面、再游回船邊爬上來）；
//   每 2 秒查一次（Tim：效能為主，只是避免太離譜 —— 每四次 survey 一次）、連兩次都在水下才算（⛔ 一次就算 ⇒ 暴風雨的浪頭掃過就有人平白落水）；
//   從高處掉下去（fall：桅倒、甲板被打穿、斷開的那一團）落到海裡也一樣 —— 細節設定「溺水時間」0 ⇒ 照以前（落水當場算陣亡、淹到的跟著船沉）。
//   ⚠ 船殼完好、只是艙內進水淹到人：還沒做（艙內的水面在甲板之間，往上浮會撞到上一層甲板）。
// 在水裡（c.st 5，世界座標 c.fw，跟墜落一樣不跟著船走）：先浮上來（SWIM_UP），到水面露出頭肩（腳在水面下 SWIM_SUB）、跟著浪起伏，
//   往自己的船游（SWIM_SP）：船舷水線那一點（同一個 x、靠自己這一舷）；到了 SWIM_REACH 內、船速低於 SWIM_GRAB ⇒ 沿船舷爬上最上面那層甲板（42_hands.js 的爬法），
//   軍官、陸戰隊回原職，其他人當預備水手（之後照常被派去補位）。船開得比人游得快 ⇒ 追不上。
//   自己的船在沉、沉了或斷了 ⇒ 往敵艦游（TASK-0536，Tim：可以到敵艦上變成敵方船員）：爬上去 ⇒ 從原本那艘的船員名單移到敵艦的（隊色、調度都換），
//   當敵艦的預備水手；兩艘都上不去 ⇒ 只能踩水。換邊在那一艘的每一步跑完才做（swimXfer；⛔ 邊跑 forEach 邊改陣列 ⇒ 下一個人被跳過）。
//   撐的時間 ＝ 溺水時間 × 0.6～1.2（受傷的再減半）；到了 ⇒ 溺水（算陣亡，原因「溺水」），沉下去。
// 在水裡的不算「還能動的」（降旗的死傷 % 照算）、打不到也不會被打（hurt／火槍只看甲板上的）。
var SWIM_UP = 1.2, SWIM_SP = 1.1, SWIM_SUB = 1.5, SWIM_REACH = 1.6, SWIM_HEAD = 17, SWIM_GRAB = 3;   // SWIM_GRAB：船速（m/s）超過這個抓不住船殼（⛔ 不限 ⇒ 7.7 節開著走，推下去 6 個爬回 5 個）
/** 變成在水裡（w ＝ 腳的世界座標）：離開砲與藥包；受傷的不再算在「傷」裡（在水裡另算）。 */
function toSwim(sh, c, w) {
  if (c.st === 1) { sh.wounded--; c.hurtSwim = true; }
  c.walk = null; c.moving = false; c.cart = false; leaveGun(c);
  sh.guns.forEach(function (g) { if (g.pm === c) g.pm = null; });     // 送藥手：那幾門砲改由同一層別的送藥手送（⛔ 留著 ⇒ 人換到敵艦後照樣「能動」，這幾門砲沒人送）
  c.swim = { t: 0, life: DROWN_T * rr(0.6, 1.2) * (c.hurtSwim ? 0.5 : 1), dead: false, role: c.role, no: [] };
  c.st = 5; c.fw = w.slice(); c.fv = [0, 0, 0];
  sh.swims = (sh.swims || 0) + 1;
}
/** 每 2 秒（survey 每四次一次）：頭頂連兩次在海面下、而且那一層通海的人變成在水裡；砲口連兩次在海面下的砲浸水（gunWet）。 */
function drownCheck(sh) {
  if (DROWN_T <= 0 || (sh.dkN = (sh.dkN || 0) + 1) % 4) return;           // 每 2 秒一次
  gunWet(sh);
  var open = sh.sinkingFinal || sh.sunk || sh.broken, low = sh.decks.length ? sh.decks[0].zr[0] : -1e9, fl = sh.fl;
  sh.crew.forEach(function (c) {
    if (c.st > 1) return;
    var h = M4.pt(sh.M, c.pos[0], c.pos[1], c.pos[2] + SWIM_HEAD);
    if (h[1] >= seaH(h[0], h[2], SIMT)) { c.wetN = 0; return; }
    if (open || c.pos[2] >= low) { if ((c.wetN = (c.wetN || 0) + 1) >= 2) toSwim(sh, c, M4.pt(sh.M, c.pos[0], c.pos[1], c.pos[2])); return; }   // 砲甲板以上有砲門 ⇒ 通海
    var i = fl ? flCell(fl.F, c.pos[0], c.pos[1], c.pos[2] + SWIM_HEAD) : -1;   // 住艙以下：艙內那一格的水滿了九成（公式模式看不到艙內的水 ⇒ 不管）
    if (!(i >= 0 && fl.cap[i] > 0.02 && fl.A[i] >= 0.9 * fl.cap[i] * Math.pow(fl.F.c * S, 3))) { c.wetN = 0; return; }
    if ((c.wetN = (c.wetN || 0) + 1) < 2) return;
    if (c.role === ROLE.HAND && sh.nav) evacuate(sh, c); else toSwim(sh, c, M4.pt(sh.M, c.pos[0], c.pos[1], c.pos[2]));
  });
}
/** 艙內淹過頭的預備水手：往上一層（梯子）躲；淹了的那一層不再去（走得到的層拿掉它），待命的是那一層 ⇒ 改成上一層。在爬、在去補位的照走（補位一定往上）。 */
function evacuate(sh, c) {
  var NV = sh.nav, H = c.hand, lv = H.lv, up = -1;
  NV.reach.forEach(function (i) { if (NV.levels[i].zr[0] > NV.levels[lv].zr[1] && (up < 0 || i < up)) up = i; });
  if (up < 0) { toSwim(sh, c, M4.pt(sh.M, c.pos[0], c.pos[1], c.pos[2])); return; }
  if (NV.reach.indexOf(lv) >= 0) { NV.reach = NV.reach.filter(function (i) { return i !== lv; }); NV.flooded = (NV.flooded || []).concat([lv]); }
  if (NV.home === lv) NV.home = up;
  c.wetN = 0;
  if (H.climb || H.job || (H.legs.length && H.legs[H.legs.length - 1].w !== lv)) return;   // 已經在往上走
  var legs = handRoute(sh, lv, up, c.pos[0], c.pos[0]);
  H.wp = null; c.moving = false; H.legs = legs || []; H.wait = rr(2, 5);
}
/** 砲浸水（TASK-0536）：砲口連兩次在海面下 ⇒ 浸水（g.wet：不能裝填、不能開，砲班離開；藥箱的火藥濕了、裝好的要重裝）；連兩次在海面上 ⇒ 乾了（等送藥手送火藥再裝）。 */
function gunWet(sh) {
  sh.guns.forEach(function (g) {
    if (!g.alive) return;
    var w = M4.pt(sh.M, g.muz[0], g.muz[1], g.muz[2]), under = w[1] < seaH(w[0], w[2], SIMT);
    g.wetN = under ? Math.min(2, (g.wetN || 0) + 1) : Math.max(0, (g.wetN || 0) - 1);
    if (!g.wet && g.wetN >= 2) { g.wet = true; g.box = 0; g.needCart = true; if (!(g.reload > 0)) g.reload = sh.reloadT * GUNS[g.type].reload; sh.wetGuns = (sh.wetGuns || 0) + 1; }
    else if (g.wet && g.wetN === 0) g.wet = false;
  });
}
/** 往哪裡游：自己的船還浮著 ⇒ 船舷水線上、同一個 x（夾在船身裡）、靠自己這一舷那一點（世界座標）；在沉、沉了、斷了 ⇒ null。 */
function boardPoint(sh, w) {
  if (sh.sinkingFinal || sh.sunk || sh.broken) return null;
  var T = sh.T, l = toLocal(sh, w), x = clamp(Math.round(l[0]), T.wl0 + 30, T.wl1 - 30), hb = T.hullHB[T.zw * T.hullTW + x] || 20, s = l[1] >= T.cy ? 1 : -1;
  return M4.pt(sh.M, x, T.cy + s * (hb + 2), T.zw);
}
/** 每一步：浮上來 → 踩水、往船游 → 到了爬上去；撐不住 ⇒ 溺水、沉下去。 */
function stepSwim(sh, c, dt) {
  var S2 = c.swim, w = c.fw, top = seaH(w[0], w[2], SIMT) - SWIM_SUB;
  S2.t += dt;
  if (S2.dead) { w[1] -= 0.8 * dt; if (S2.t > S2.life + 4) c.st = 3; return; }
  if (S2.t > S2.life) { drown(sh, c); return; }
  if (w[1] < top - 0.05) { w[1] = Math.min(top, w[1] + SWIM_UP * dt); c.fv = [0, 1, 0]; return; }
  w[1] = top + 0.06 * Math.sin(c.t * 2.4);
  var dst = S2.no.indexOf(sh) < 0 && boardPoint(sh, w) ? sh : null;   // 自己的船優先，上不去才往別艘（友船先、再敵船；照 SHIPS 的順序 ⇒ 一對一 ＝ 以前的敵艦）
  if (!dst) swimOthers(sh).some(function (o) { if (S2.no.indexOf(o) < 0 && boardPoint(o, w)) { dst = o; return true; } return false; });
  if (!dst) { c.fv = [0, 0, 0]; return; }
  var p = boardPoint(dst, w), dx = p[0] - w[0], dz = p[2] - w[2], d = Math.hypot(dx, dz);
  if (d < SWIM_REACH && Math.abs(dst.spd) < SWIM_GRAB) {                 // 船太快 ⇒ 抓不住，跟在旁邊游（船慢下來才爬得上去）
    if (dst === sh) { if (board(sh, c, true)) { sh.saved = (sh.saved || 0) + 1; note(sh, '一個落水的水手爬回船上了'); } else S2.no.push(sh); }
    else if (!S2.xfer) { S2.xfer = true; S2.to = dst; (sh.xfer = sh.xfer || []).push(c); }   // 別艘：這一步跑完再換名單（swimXfer）
    return;
  }
  var s = Math.min(d, SWIM_SP * dt); w[0] += dx / d * s; w[2] += dz / d * s; c.fv = [dx / d, 0, dz / d];
}
/** 溺水：算陣亡（原因「溺水」），之後沉下去 4 秒才不畫。 */
function drown(sh, c) {
  c.swim.dead = true; c.swim.t = c.swim.life; c.fv = [0, -1, 0];
  sh.dead++; sh.kills++; sh.causes['溺水'] = (sh.causes['溺水'] || 0) + 1; newsCrew(sh, c, true, '溺水');
}
/** 爬上船 sh：沿船舷往上爬到最上面那層甲板、跨進來站到走路格上那一點（42_hands.js stepHand 的爬法，船的格座標 ⇒ 跟著船走）。
 *  own（自己的船）⇒ 軍官、陸戰隊爬完回原職；其他人、還有被敵艦撈起的都當預備水手。走路格接不上（舷邊 3 m 內沒有站得住的點）⇒ 回 false、不爬。 */
function board(sh, c, own) {
  var NV = sh.nav, l = toLocal(sh, c.fw), lv = NV && sh.weatherDeck ? lvOf(NV.levels, sh.deckZ[sh.weatherDeck][0]) : -1;
  if (lv < 0) return false;
  var T = sh.T, N = NV.levels[lv].N, zr = NV.levels[lv].zr, s = l[1] >= T.cy ? 1 : -1, hb = T.hullHB[T.zw * T.hullTW + clamp(Math.round(l[0]), 0, T.hullTW - 1)] || 20;
  var ci = navSnap(N, [l[0], T.cy + s * Math.max(4, hb - 10), zr[0] + 3], 16);
  if (ci < 0) return false;
  var dest = navPos(N, ci), r = c.swim.role;
  if (c.art === undefined) c.art = r;                                   // 貼圖照原本的職位那一列（換成 HAND 之後 c.role 是 6 ＝ 船長那一列）；隊色照畫它的那艘
  c.backRole = own && (r === ROLE.OFFICER || r === ROLE.MARINE) ? r : undefined;
  c.role = ROLE.HAND; c.gun = null; c.st = 0; c.swim = null; c.hurtSwim = false; c.hp = Math.max(c.hp, CREW_HP * 0.5);   // 救上來的照常能動（傷的撐在一半）
  c.pos = [l[0], l[1], l[2]]; c.deck = NV.levels[lv].key;
  var sy = T.cy + s * (hb + 1);                                         // 先貼到船殼（水線那一層的外緣），再沿船殼往上爬、跨進來（⛔ 從游到的那一點直直往上 ⇒ 離船殼 1.8 m 的半空中爬）
  c.hand = { lv: lv, wait: rr(1, 3), legs: [], wp: null, k: 0, climb: { pts: [c.pos.slice(), [l[0], sy, l[2]], [l[0], sy, dest[2] + 3], dest], k: 0, lv: lv }, job: null, to: null };
  return true;
}
/** 那一艘的每一步跑完（stepCrew）：游到敵艦舷邊的人爬上敵艦、從這艘的名單移到敵艦的（爬不上去 ⇒ 留在水裡、不再往敵艦游）。 */
function swimXfer(sh) {
  var L = sh.xfer; sh.xfer = null;
  L.forEach(function (c) {
    var i = sh.crew.indexOf(c); if (i < 0 || c.st !== 5) return;
    var foe = c.swim.to || foeOf(sh), ally = foe && foe.team === sh.team;   // 游到的那一艘（友船 ⇒ 換到友船上，照樣當預備水手）
    c.swim.xfer = false;
    if (!foe || !board(foe, c, false)) { c.swim.no.push(foe); return; }
    sh.crew.splice(i, 1); foe.crew.push(c);
    sh.lostTo = (sh.lostTo || 0) + 1; foe.gained = (foe.gained || 0) + 1;
    if (ally) { note(sh, '一個落水的水手爬上了友艦'); note(foe, '撈起一個友艦的落水水手'); }
    else { note(sh, '一個落水的水手被敵艦撈走了'); note(foe, '撈起一個敵艦的落水水手（加入我方）'); }
  });
}
/** HUD 一段：現在在水裡的（還沒溺水的）。 */
function swimText(sh) {
  var n = sh.swims ? sh.crew.filter(function (c) { return c.st === 5 && !c.swim.dead; }).length : 0;
  return n ? '　<span style="color:#7fc8ff">落水 ' + n + '</span>' : '';
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/50_sim.js ──
// ───────────────────────── 電腦 ─────────────────────────
function ai(sh, dt) {
  var foe = foeOf(sh);                                              // 自己的目標（52_fleet.js；一對一 ＝ 另一艘）
  if (sh.sunk || sh.struck || sh.sinkingFinal || !foe) return;
  if (foe.sunk || foe.struck || foe.sinkingFinal) return;            // 對方降旗或在沉 ⇒ 停火
  captainThink(sh, foe);                                            // 砲長：該換瞄準模式就換（51_captain.js）
  sh.aiWait -= dt; if (sh.aiWait > 0) return;
  if (!anyBears(sh, foe.center)) { sh.aiWait = 0.5; return; }       // 哪一舷都對不到 ⇒ 等船轉過來
  var ready = 0, alive = 0, held = 0, FK = friendKeels(sh);         // 隔著友船的那幾門不算（52_fleet.js；沒有友船 ⇒ 空的）
  sh.guns.forEach(function (g) { if (g.alive && gunRate(g) > 0 && gunTarget(sh, g, foe.center)) { if (FK.length && friendInLine(FK, M4.pt(sh.M, g.muz[0], g.muz[1], g.muz[2]), foe.center)) { held++; return; } alive++; if (g.reload <= 0) ready++; } });
  if (!ready && held) { sh.ffHold = (sh.ffHold || 0) + held; sh.aiWait = 0.3; return; }   // 對得到的都隔著友船 ⇒ 忍住、等一下再看（不每一步重算）
  if (!ready || ready < Math.ceil(alive * 0.65)) return;
  var a = modeAim(foe, sh.aimMode || 'hull', true), t = a.t, ammo = a.ammo;   // 砲長選的模式裡亂挑一點（⛔ 以前固定 45% 船殼／27% 砲甲板／28% 桅，船殼瞄的是設計水線 ⇒ 敵艦浮高了還打在水面上）
  var err = Math.max(0.6, 4.5 - sh.salvo * 0.55) / S;
  setAim(sh, [t[0] + gauss() * err * 1.6, t[1], t[2] + gauss() * err * 0.5], foe);
  sh.aiSpread = 0.006;
  broadside(sh, ammo, true);
  sh.aiWait = rr(1.0, 3.5);
}

// ───────────────────────── 一步 ─────────────────────────
function step() {
  if (PF) PF.t = performance.now();                                 // 逐幀分段計時（?debug=1，00_core.js）
  SIMT += DT;
  pickFoes();                                                      // 每艘的目標（52_fleet.js）：這一步之內都用同一個
  stepWind(SIMT);                                                  // 風會變（08_weather.js）
  for (var i = 0; i < EVENTS.length; i++) {
    var e = EVENTS[i]; if (e.t > SIMT) continue;
    EVENTS.splice(i--, 1);
    var sh = SHIPS[e.sh], et = sh.sunk ? null : gunTarget(sh, e.g, add(aimPoint(sh), mul(shipAxis(sh), e.off)));   // 開火那一刻才挑點（兩艘都在動）
    if (et) fireGun(sh, e.g, et, e.ammo);
  }
  if (PF) pfLap('fire');
  SHIPS.forEach(function (sh) { sail(sh, DT); stepShip(sh, DT); if (PF) pfLap('ship'); stepCrew(sh, DT); if (PF) pfLap('crew'); });
  collide();
  SHIPS.forEach(function (sh) {                                    // 照 SHIPS 的順序（一對一：我艦先、敵艦後 ⇒ 跟以前同一個順序抽亂數）
    if (sh.i === PLAYER_I) { if (AUTOFIRE) ai(sh, DT); }            // 自動開砲：我艦也交給電腦瞄準開火
    else if (MODE !== 'sandbox') ai(sh, DT);                        // 沙盒的其他船不還手
  });
  if (PF) pfLap('ai');
  for (i = 0; i < BALLS.length; i++) { stepBall(BALLS[i], DT); if (!BALLS[i].alive) { if (CAM.follow === BALLS[i]) { CAM.hold = 1.2; } BALLS.splice(i--, 1); } }
  if (PF) pfLap('balls');
  SHIPS.forEach(function (sh) { integrity(sh); sh.impulse = [0, 0, 0]; });
  if (PF) pfLap('integrity');
  for (i = 0; i < PIECES.length; i++) if (!stepPiece(PIECES[i], DT)) { PIECES[i].rs.dispose(); PIECES.splice(i--, 1); }
  for (i = 0; i < FLY.length; i++) if (!stepFly(FLY[i], DT)) FLY.splice(i--, 1);
  if (PF) pfLap('pieces');
  if (SLOW_VIS) stepWater(DT, 'ship');                             // 殉爆慢動作中：只給人看的照畫面的時間走（73_slowmo.js），這裡只生船邊的水花
  else { stepDebris(DT); if (PF) pfLap('debris'); stepPts(DT); if (PF) pfLap('pts'); stepWater(DT); }
  if (PF) pfLap('water');                       // 船邊水花（13_water.js；只給人看、自己的亂數）
  if (PHYS) { var pt0 = performance.now(); SHIPS.forEach(function (sh) { if (sh.sink < 40) physStep(sh); }); PHYS_MS = PHYS_MS * 0.98 + (performance.now() - pt0) * 0.02; }   // 讀數只看、不回寫模擬
  if (PF) pfLap('phys');
  stepPowder();                                                    // 殉爆排程（23_powder.js）
  stepBlasts();                                                    // 還沒挖完的彈坑接著挖（23_powder.js）
  if (PF) pfLap('powder');
  if ((Math.round(SIMT / DT) % 30) === 0) { SHIPS.forEach(survey); SHIPS.forEach(newsFlush); }
  if (PF) pfLap('survey');
  if (!OVER || END_AT) checkEnd();                                 // 結束判定每一步看（結算畫面照模擬時間延後跳）
  if (PF) pfLap('end');
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/51_captain.js ──
// ───────────────────────── 砲長：瞄準模式與策略（Tim 2026-10-12） ─────────────────────────
// 瞄準模式：水線（敵艦「現在」的水線 ⇒ 浮高了就跟著往下）／砲甲板／帆具／甲板人員／彈藥庫（彈藥庫頂離水面 1 m 內才有意義），各配合適的彈種。
// 砲長（每艘一個，細節設定可選、預設隨機）：每隔幾秒照局勢替每個模式打分 ＝ 偏好 × 局勢 × 隨機 ±15%，最高的那個比現在的高兩成才換，換的時候上方廣播。
//   戰鬥中會換著打（Tim：不是固定用一種）：同一個模式打久了分數慢慢打折（45 秒折到一半）；現在這個模式打了沒用（局勢 ≈ 0：桅都倒了…）就馬上換。
//   局勢：水線 ＝ 0.6 ＋ 敵艦浮高（1.2 m 加滿 2.4）＋ 敵艦進水（4 m 加滿 0.4）—— Tim：敵艦浮高時改瞄水線；
//         砲甲板 ＝ 0.2 ＋ 0.8 × 敵艦還有人操作的砲比例；帆具 ＝ 還站著的桅比例 × 帆面積比例；甲板人員 ＝ 0.2 ＋ 0.8 × 還能動的人比例；
//         彈藥庫 ＝ 最淺那間的頂離水面 d：露出水面 3、1 m 內 3 × (1 − d)、更深 0（火藥拉滿不會爆 ⇒ 0）。
// 我艦手動時：Q 循環瞄準模式（點敵艦 ⇒ 回到自由）；瞄的是那個模式的中心點（不抽亂數 ⇒ HUD 每一格算也不影響戰局）。自動開砲 ⇒ 交給我艦的砲長。
var AIM_MODES = ['water', 'hull', 'rig', 'deck', 'mag'], AIM_CYCLE = ['free', 'water', 'hull', 'rig', 'deck', 'mag'];
var AIM_NAME = { free: '自由', water: '水線', hull: '砲甲板', rig: '帆具', deck: '甲板人員', mag: '彈藥庫' };
var CAPTAINS = {
  steady: { name: '穩健派', tip: '照局勢平均分配', think: 10, w: { water: 1.2, hull: 1.2, rig: 0.8, deck: 0.6, mag: 1.5 } },
  sink: { name: '擊沉派', tip: '專打水線，敵艦浮高就追著水線打', think: 8, w: { water: 2.2, hull: 0.7, rig: 0.4, deck: 0.4, mag: 2.0 } },
  mast: { name: '拆桅派', tip: '先拆桅讓對方跑不動，再打水線', think: 8, w: { water: 0.8, hull: 0.6, rig: 2.4, deck: 0.5, mag: 1.2 } },
  kill: { name: '殺傷派', tip: '打砲甲板與甲板上的人，讓對方開不了砲', think: 8, w: { water: 0.6, hull: 1.6, rig: 0.4, deck: 2.0, mag: 1.0 } },
  gamble: { name: '賭徒', tip: '彈藥庫一靠近水面就全押上去', think: 6, w: { water: 1.0, hull: 0.8, rig: 0.6, deck: 0.6, mag: 5.0 } }
};
var CAP_KEYS = Object.keys(CAPTAINS), AIM_P = 'free';   // AIM_P：我艦手動的瞄準模式（重開時保留）
/** 開局：每艘挑一個砲長（細節設定的；隨機 ⇒ 抽種子亂數）。 */
function pickCaptains() {
  SHIPS.forEach(function (sh) {
    var k = sh.i === PLAYER_I ? CAP_SET[0] : sh.team !== playerTeam() ? CAP_SET[1] : 'random'; if (!CAPTAINS[k]) k = CAP_KEYS[(rnd() * CAP_KEYS.length) | 0];   // 細節設定的兩格：我艦／敵船（友船隨機）
    sh.cap = k; sh.aimMode = null; sh.capT = -99; sh.pMode = sh.i === PLAYER_I ? AIM_P : 'free';
  });
}
/** 敵艦現在的水線（格座標的 z）：設計水線 ＋ 進水 − 浮高 − 浪。 */
function wlZ(foe) { return foe.T.zw + (foe.sink - foe.lift - foe.bob) / S; }
/** 最淺那間還在的彈藥庫：{ mag, d（頂離水面幾公尺，負 ＝ 露出水面）}；沒有 ⇒ null。 */
function magNear(foe) {
  var wl = wlZ(foe), best = null;
  (foe.mags || []).forEach(function (m) { if (m.gone) return; var d = (wl - m.box[5]) * S; if (!best || d < best.d) best = { mag: m, d: d }; });
  return best;
}
/** 每個模式的局勢分數（0 ＝ 打了沒用）。 */
function aimValue(foe, mode) {
  if (mode === 'water') return 0.6 + 2.4 * clamp(foe.lift / 1.2, 0, 1) + 0.4 * clamp(foe.sink / 4, 0, 1);
  if (mode === 'hull') return 0.2 + 0.8 * (foe.gunsManned || 0) / Math.max(1, foe.guns.length);
  if (mode === 'rig') return (foe.mastsUp || 0) / Math.max(1, foe.masts.length) * foe.sailFrac;   // 照那艘有幾根桅（夜隼號 2）
  if (mode === 'deck') return 0.2 + 0.8 * (foe.able || 0) / Math.max(1, foe.crew0);
  if (mode === 'mag') { if (powderNever()) return 0; var n = magNear(foe); return !n ? 0 : n.d <= 0 ? 3 : n.d < 1 ? 3 * (1 - n.d) : 0; }
  return 0;
}
/** 砲長想一想：該換模式就換、廣播一則。 */
function captainThink(sh, foe) {
  var C = CAPTAINS[sh.cap]; if (!C || SIMT - sh.capT < C.think) return;
  sh.capT = SIMT;
  var tired = sh.aimMode ? Math.max(0.5, 1 - (SIMT - sh.modeT) / 90) : 1, sc = {}, best = null, bs = -1;   // 打久了會膩：45 秒折到一半
  AIM_MODES.forEach(function (m) { var v = aimValue(foe, m), s = C.w[m] * v * rr(0.85, 1.15) * (m === sh.aimMode ? tired : 1); sc[m] = v > 0 ? s : 0; if (sc[m] > bs) { bs = sc[m]; best = m; } });
  var cur = sh.aimMode ? sc[sh.aimMode] : -1;
  if (best === sh.aimMode || (sh.aimMode && cur > 0.05 && bs < cur * 1.2)) return;
  var first = !sh.aimMode; sh.aimMode = best; sh.modeT = SIMT; sh.modes = (sh.modes || 0) + 1;
  var why = best === 'water' && foe.lift > 0.3 ? '敵艦浮高 ' + foe.lift.toFixed(1) + ' m' : best === 'mag' ? (function (n) { return n.d <= 0 ? '彈藥庫露出水面' : '彈藥庫離水面 ' + n.d.toFixed(1) + ' m'; })(magNear(foe)) : !first && tired < 0.75 ? '換個打法' : '';
  note(sh, '砲長（' + C.name + '）：' + (first ? '先瞄' : '改瞄') + AIM_NAME[best] + (why ? '（' + why + '）' : ''), best === 'mag');
}
/** 那個模式要瞄哪裡（敵艦的格座標）與用什麼彈；rand ⇒ 在範圍裡亂挑一點（電腦），否則中心點（我艦手動，不抽亂數）。 */
function modeAim(foe, mode, rand) {
  function R(a, b) { return rand ? rr(a, b) : (a + b) / 2; }
  function P(p) { return rand ? rnd() < p : p >= 0.5; }
  var wl = wlZ(foe), CY = foe.T.cy, WL_X0 = foe.T.wl0, WL_X1 = foe.T.wl1, xm = (WL_X0 + WL_X1) / 2;
  if (mode === 'mag') {
    var n = magNear(foe); if (n) return { t: [R(n.mag.box[0] + 4, n.mag.box[3] - 4), CY, wl + R(0.5, 4)], ammo: 0 };
    mode = 'water';
  }
  if (mode === 'water') return { t: [R(WL_X0 + 40, WL_X1 - 40), CY, wl + R(1, 9)], ammo: 0 };                 // 水面上 0.1–0.9 m（砲彈碰到水就沒了）
  if (mode === 'rig') {
    var masts = foe.masts.filter(function (m) { return m.up; });
    if (masts.length) { var m = rand ? masts[(rnd() * masts.length) | 0] : masts.reduce(function (a, b) { return Math.abs(b.x - xm) < Math.abs(a.x - xm) ? b : a; }); return { t: [m.x, CY, R(foe.T.geo.rigAim[0], foe.T.geo.rigAim[1])], ammo: P(0.7) ? 2 : 0 }; }
    mode = 'hull';
  }
  if (mode === 'deck') {
    var on = foe.crew.filter(function (c) { return c.st === 0 && (c.deck === foe.weatherDeck || c.role === ROLE.MARINE || c.role === ROLE.OFFICER || c.role === ROLE.HELM); });
    if (on.length) { var c = rand ? on[(rnd() * on.length) | 0] : on[0]; return { t: [rand ? c.pos[0] : xm, CY, c.pos[2] + 10], ammo: P(0.8) ? 1 : 0 }; }
    mode = 'hull';
  }
  return { t: [R(WL_X0 + 60, WL_X1 - 60), CY, R(foe.T.geo.deckAim[0], foe.T.geo.deckAim[1])], ammo: P(0.3) ? 1 : 0 };   // 砲甲板（高度照船型，05_hull.js GEO0）
}
/** 細節設定的砲長選單：選項 ＝ 隨機 ＋ 各砲長（說明當 title）。 */
function capOptions(sel, v) {
  sel.innerHTML = '<option value="random">隨機</option>' + CAP_KEYS.map(function (k) { return '<option value="' + k + '" title="' + CAPTAINS[k].tip + '">' + CAPTAINS[k].name + '（' + CAPTAINS[k].tip + '）</option>'; }).join('');
  sel.value = v;
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/52_fleet.js ──
// ───────────────────────── 艦隊（TASK-0537：多船的架構） ─────────────────────────
// 每艘有陣營（sh.team：'blue'／'red'）；「我的對手」不再是 SHIPS[1 − sh.i]，而是 foeOf(sh)：
//   每一步開始時挑一次（pickFoes）—— 玩家點過的那艘（還在、是敵船）優先，否則最近的、還沒沉的敵船；敵船全沉了 ⇒ 最近的那艘（照舊指著它，像以前一樣）。
//   ⇒ 一對一時永遠是另一艘 ⇒ 跟以前一位元都不差。只用船的位置（px、pz）、不抽亂數。
// 友軍跟敵軍只差在挑目標（Tim 2026-10-13）：同陣營不當目標；砲彈照舊打得到每一艘 ⇒ 誤擊照樣扣血、算傷亡（讀數 sh.ff：被友船打中幾發）。
// 瞄準點（sh.aim）是「那艘船」的格座標 ⇒ 一併記是哪艘（sh.aimOn，setAim）；換目標之前瞄的那一點不會被套到另一艘的座標上。
// 船數上限 MAX_SHIPS（00_core.js）；GPU 的格（陰影圖、船艙遮罩、透視）只給視野裡最近的 GPU_NEAR 艘（60_render.js gpuSlots），其他的靠全局陰影圖。
/** 誤擊的讀數：被友船打中幾發（sh.ff）、打中友船幾發（ffOut）。一顆彈只算一次（跟 hits 同一個 hitOnce）。 */
function ffHit(sh, b) { var o = SHIPS[b.owner]; if (o && o !== sh && o.team === sh.team) { sh.ff = (sh.ff || 0) + 1; o.ffOut = (o.ffOut || 0) + 1; } }
/** 落水的人上不了自己的船 ⇒ 往哪幾艘游（43_swim.js）：友船先、再敵船，各照 SHIPS 的順序（一對一 ＝ [敵艦]）。 */
function swimOthers(sh) { var o = SHIPS.filter(function (x) { return x !== sh; }); return o.filter(function (x) { return x.team === sh.team; }).concat(o.filter(function (x) { return x.team !== sh.team; })); }
function teamIdx(sh) { return sh.team === 'red' ? 1 : 0; }              // 貼圖的列、羅盤的顏色：藍 0、紅 1
function isFoe(a, b) { return !!a && !!b && a !== b && a.team !== b.team; }
function teamShips(team) { return SHIPS.filter(function (o) { return o.team === team; }); }
function pickFoes() {
  SHIPS.forEach(function (sh) {
    var c = SHIPS.filter(function (o) { return isFoe(sh, o); }); if (!c.length) { sh.foe = null; return; }
    if (sh.i === PLAYER_I && sh.aimOn && c.indexOf(sh.aimOn) >= 0 && !sh.aimOn.sunk) { sh.foe = sh.aimOn; return; }   // 玩家點過的那艘
    var live = c.filter(function (o) { return !o.sunk; }); if (live.length) c = live;
    var best = null, bd = 1e18;
    c.forEach(function (o) { var d = (o.px - sh.px) * (o.px - sh.px) + (o.pz - sh.pz) * (o.pz - sh.pz); if (d < bd) { bd = d; best = o; } });
    sh.foe = best;
  });
}
function foeOf(sh) { if (sh.foe === undefined) pickFoes(); return sh.foe; }
/** 瞄準點落在哪艘船（設瞄準點那一刻的那艘；沒有 ⇒ 現在的目標）。 */
function aimShip(sh) { return sh.aim && sh.aimOn ? sh.aimOn : foeOf(sh); }
function setAim(sh, aim, on) { sh.aim = aim; sh.aimOn = aim ? on || foeOf(sh) : null; }
/** 旗艦：那個陣營還沒沉的船裡，開戰時排水量（sh.mass0；還沒算 ⇒ 現算）最大的；全沉了 ⇒ 最大的那艘（Tim 2026-10-13：上方面板只顯示雙方旗艦）。
 *  ⛔ 照「現在」的排水量排 ⇒ 被打掉幾噸就換旗艦、面板一直跳。 */
function flagship(team) {
  var L = teamShips(team), live = L.filter(function (o) { return !o.sunk; }); if (live.length) L = live;
  var best = null, bm = -1;
  L.forEach(function (o) { var m = o.mass0 || shipT(o); if (m > bm) { bm = m; best = o; } });
  return best;
}
function teamTag(sh) { return teamIdx(sh) === 0 ? '（藍）' : '（紅）'; }
function playerTeam() { var me = SHIPS[PLAYER_I]; return me ? me.team : 'blue'; }
function foeTeam() { return playerTeam() === 'blue' ? 'red' : 'blue'; }
/** 那個陣營打完了沒：每艘都沉了或降旗。 */
function teamDown(team) { var L = teamShips(team); return L.length > 0 && L.every(function (o) { return o.sunk || o.struck; }); }
/** 開局的編隊（70_flow.js reset）：每一邊照編成排成縱隊（沿船長方向）、兩邊面對面 ±DIST/2；一邊一艘 ⇒ 跟以前同一個位置。
 *  spec：[{ team, hull }]，一對一 ＝ [我艦, 敵艦]；SHIPS 照這個順序建（i ＝ 序號；我艦是 0）。艘數超過 MAX_SHIPS ⇒ 截掉。 */
var FLEET_GAP = 85;                                                       // 同一邊兩艘之間隔多遠（m，沿船長方向；憲法號水線長 55 m ⇒ 頭尾隔 30 m）
var FLEET_DBG = null;                                                     // ?debug=1 的 __game.fleet([...])：直接給一串（蓋過主選單的編成）
/** 主選單的編成（FLEET_SET，05_hull.js）⇒ 一串：我艦、敵方第一艘、我方其他、敵方其他（一對一 ＝ [我艦, 敵艦]，跟以前同一個順序）。 */
function fleetSpec() {
  if (FLEET_DBG) return FLEET_DBG;
  var b = FLEET_SET[0], r = FLEET_SET[1], L = [{ team: 'blue', hull: b[0] }, { team: 'red', hull: r[0] }];
  b.slice(1).forEach(function (h) { L.push({ team: 'blue', hull: h }); });
  r.slice(1).forEach(function (h) { L.push({ team: 'red', hull: h }); });
  return L;
}
function spawnFleet(spec) {
  spec = spec.slice(0, MAX_SHIPS);
  var n = { blue: 0, red: 0 }, k = { blue: 0, red: 0 };
  spec.forEach(function (f) { n[f.team]++; });
  spec.forEach(function (f, i) {
    var blue = f.team === 'blue', j = k[f.team]++, off = (j - (n[f.team] - 1) / 2) * FLEET_GAP;
    SHIPS.push(makeShip(i, f.team, blue ? 0 : Math.PI, blue ? DIST / 2 : -DIST / 2, HULLT[f.hull], blue ? off : -off));   // 一邊一艘 ⇒ px 0，跟以前一樣
  });
}

// ───────────────────────── 艦隊電腦（TASK-0537 第二段） ─────────────────────────
// 只在同一邊有友船時才起作用（沒有友船 ⇒ 兩支都直接回「沒事」、不抽亂數）⇒ 一對一一位元都不差。
//   ① 讓船：照現在的相對速度 AV_T 秒內，友船的龍骨線會進到離我的不到 AV_NEAR（或已經不到 AV_HARD）⇒ 舵往遠離它的那一側打（蓋過追敵的航向）。
//      同向同速的縱隊（距離不變）不算 ⇒ 開局排成縱隊不會一開始就散開（⛔ 只看距離 ⇒ 縱隊頭尾隔 15 m，開局每一步都在讓）。
//   ② 不隔著友船開砲：電腦（含玩家開了自動開砲）排齊射時，砲口到瞄準點那條線離友船的龍骨線不到 FF_CLEAR 的那門不開（讀數 sh.ffHold：開局以來忍住幾門次）。
//      玩家自己按的齊射照開 —— 誤擊是玩法（Tim 2026-10-13：「有友軍傷害」）。
var FF_CLEAR = 9, AV_NEAR = 22, AV_HARD = 16, AV_T = 15, AV_TURN = 0.8;  // m、m、m、秒、rad（讓船時航向偏離自己船頭多少）；擦撞是 14 m（31_sailing.js collide）
function friendsOf(sh) { return SHIPS.filter(function (o) { return o !== sh && o.team === sh.team && !o.sunk && !o.sinkingFinal; }); }
/** 龍骨線（水線那一段的頭尾，世界座標）。 */
function keelLine(o) { var T = o.T; return [M4.pt(o.M, T.wl0, T.cy, T.zw), M4.pt(o.M, T.wl1, T.cy, T.zw)]; }
/** 兩條線段在水平面（x、z）上最近的距離與最近的兩點。 */
function segSeg(a, b, c, d) {
  function cr(p, q, r) { return (q[0] - p[0]) * (r[2] - p[2]) - (q[2] - p[2]) * (r[0] - p[0]); }
  function ptSeg(p, s0, s1) { var ux = s1[0] - s0[0], uz = s1[2] - s0[2], L = ux * ux + uz * uz, t = L > 0 ? clamp(((p[0] - s0[0]) * ux + (p[2] - s0[2]) * uz) / L, 0, 1) : 0, q = [s0[0] + ux * t, 0, s0[2] + uz * t]; return { d: Math.hypot(p[0] - q[0], p[2] - q[2]), q: q }; }
  if (cr(a, b, c) * cr(a, b, d) < 0 && cr(c, d, a) * cr(c, d, b) < 0) return { d: 0, p: a, q: c };   // 交叉
  var r1 = ptSeg(a, c, d), r2 = ptSeg(b, c, d), r3 = ptSeg(c, a, b), r4 = ptSeg(d, a, b), best = { d: r1.d, p: a, q: r1.q };
  if (r2.d < best.d) best = { d: r2.d, p: b, q: r2.q };
  if (r3.d < best.d) best = { d: r3.d, p: r3.q, q: c };
  if (r4.d < best.d) best = { d: r4.d, p: r4.q, q: d };
  return best;
}
/** 這一門從 from 打到 to，會不會先穿過友船（K：friendKeels 的結果，同一次齊射共用）。 */
function friendKeels(sh) { return friendsOf(sh).map(keelLine); }
function friendInLine(K, from, to) { for (var i = 0; i < K.length; i++) if (segSeg(from, to, K[i][0], K[i][1]).d < FF_CLEAR) return true; return false; }
/** 讓船：要讓 ⇒ 回傳該走的航向；不用 ⇒ null。只看最危險（最近）的那一艘友船。 */
function friendAvoid(sh) {
  var fr = friendsOf(sh); if (!fr.length) return null;
  var me = keelLine(sh), best = null;
  fr.forEach(function (o) {
    var r = segSeg(me[0], me[1], keelLine(o)[0], keelLine(o)[1]), n = sub(r.q, r.p); n[1] = 0; n = norm(n);
    var close = dot(sub(sh.vel, o.vel), n);                                // 往它靠近的速度（m/s）
    if (r.d < AV_HARD || (close > 0.05 && r.d - close * AV_T < AV_NEAR)) if (!best || r.d < best.d) best = { d: r.d, n: n };
  });
  if (!best) return null;
  var left = [-Math.sin(sh.yaw), 0, -Math.cos(sh.yaw)];                   // 左舷那一側（yaw 變大 ＝ 左轉，31_sailing.js fwd）
  var w = clamp(1 - (best.d - 14) / AV_NEAR, 0.4, 1);
  sh.avoidN = (sh.avoidN || 0) + 1;                                       // 讀數：開局以來讓了幾步
  return sh.yaw + (dot(best.n, left) > 0 ? -1 : 1) * AV_TURN * w;          // 友船在左 ⇒ 右轉
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/60_render.js ──
// ───────────────────────── 畫 ─────────────────────────
var CUBE = null, DEBVAO = null, DEBBUF = null, PTVAO = null, PTBUF = null, SKYVAO = null, SEAG = null;
function geometry() {
  // 方塊：24 頂點（每面 4 個，各帶法線）
  var F = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], V = [], I = [];
  F.forEach(function (n, fi) {
    var a = n[0] ? 0 : n[1] ? 1 : 2, u = (a + 1) % 3, w = (a + 2) % 3;
    [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(function (c) { var p = [0, 0, 0]; p[a] = n[a] * 0.5; p[u] = c[0] * 0.5; p[w] = c[1] * 0.5; V.push(p[0], p[1], p[2], n[0], n[1], n[2]); });
    var b = fi * 4, flip = (n[a] > 0) ? false : true;
    if (!flip) I.push(b, b + 1, b + 2, b, b + 2, b + 3); else I.push(b, b + 2, b + 1, b, b + 3, b + 2);
  });
  DEBVAO = gl.createVertexArray(); gl.bindVertexArray(DEBVAO);
  var vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(V), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 24, 0); gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 24, 12);
  var ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(I), gl.STATIC_DRAW);
  DEBBUF = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, DEBBUF); gl.bufferData(gl.ARRAY_BUFFER, DINST.byteLength, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 36, 0); gl.vertexAttribDivisor(2, 1);
  gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 4, gl.FLOAT, false, 36, 16); gl.vertexAttribDivisor(3, 1);
  gl.enableVertexAttribArray(4); gl.vertexAttribPointer(4, 1, gl.FLOAT, false, 36, 32); gl.vertexAttribDivisor(4, 1);
  gl.bindVertexArray(null);
  PTVAO = gl.createVertexArray(); gl.bindVertexArray(PTVAO); PTBUF = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, PTBUF); gl.bufferData(gl.ARRAY_BUFFER, PBUF.byteLength, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 36, 0); gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 1, gl.FLOAT, false, 36, 12);
  gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 36, 16); gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 1, gl.FLOAT, false, 36, 32); gl.bindVertexArray(null);
  SKYVAO = gl.createVertexArray(); gl.bindVertexArray(SKYVAO); var sb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, sb);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 8, 0); gl.bindVertexArray(null);
}
// 海面網格的細緻度（畫質）：seg 一圈幾格、min 最密的網格間距（m）、det 細漣漪幾道。網格間距往外照比例變粗（同心圓，跟透視一樣近密遠疏），到 4 km
var SEA_LV = [{ seg: 96, min: 1.2, det: 4 }, { seg: 160, min: 0.7, det: 8 }, { seg: 256, min: 0.4, det: 14 }];
/** 海面網格（第 lv 檔）：同心圓，頂點 (dx, dz, 那一圈的間距)，離中心 4 km；中心每格跟著鏡頭（render 給 uC）。 */
function seaGrid(lv) {
  var L = SEA_LV[lv], seg = L.seg, f = 2 * Math.PI / seg, R = [0], i, j;
  while (R[R.length - 1] < 4000) { var r0 = R[R.length - 1]; R.push(r0 + Math.max(L.min, r0 * f)); }
  var V = new Float32Array(R.length * seg * 3), I = new Uint32Array((R.length - 1) * seg * 6), q = 0;
  for (i = 0; i < R.length; i++) for (j = 0; j < seg; j++) { var k = (i * seg + j) * 3, a = j * f; V[k] = Math.cos(a) * R[i]; V[k + 1] = Math.sin(a) * R[i]; V[k + 2] = Math.max(L.min, R[i] * f); }
  for (i = 0; i < R.length - 1; i++) for (j = 0; j < seg; j++) { var a0 = i * seg + j, a1 = i * seg + (j + 1) % seg; I[q++] = a0; I[q++] = a0 + seg; I[q++] = a1; I[q++] = a1; I[q++] = a0 + seg; I[q++] = a1 + seg; }
  var g = SEAG || { vao: gl.createVertexArray(), vb: gl.createBuffer(), ib: gl.createBuffer() };
  gl.bindVertexArray(g.vao); gl.bindBuffer(gl.ARRAY_BUFFER, g.vb); gl.bufferData(gl.ARRAY_BUFFER, V, gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 12, 0);
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, g.ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, I, gl.STATIC_DRAW); gl.bindVertexArray(null);
  g.n = I.length; g.lv = lv; g.snap = L.min * 2; g.verts = V.length / 3; SEAG = g;
}
/** 船殼外形（原本的，不管被打掉多少）：每個 (x, z) 最外那一格離中線多遠（格）⇒ 海的著色器拿來判斷「在不在船艙裡」。
 *  這裡只算資料（T.hullHB、寬高）；上 GPU 是所有船型併成一個貼圖陣列（hullArr，畫的時候看到新的船型才重建）。 */
function hullTex(T, hb) {                              // hb ＝ 快取的那張（06_cache.js）
  T.hullTW = T.base.sx; T.hullTH = Math.min(256, T.base.sz);
  T.hullHB = hb || hullMask(T);                        // 存快取、對拍用（__game.hullCheck）
}
function hullMask(T) {
  var TW = T.base.sx, TH = Math.min(256, T.base.sz), CY = T.cy, hb = new Uint8Array(TW * TH);
  T.base.each(function (x, y, z) { if (z >= TH) return; var d = Math.min(255, Math.ceil(Math.abs(y + 0.5 - CY))); if (d > hb[z * TW + x]) hb[z * TW + x] = d; });
  return hb;
}
function resize() {
  var dpr = Math.min(window.devicePixelRatio || 1, 1.5), w = Math.max(1, cv.clientWidth * dpr | 0), h = Math.max(1, cv.clientHeight * dpr | 0);
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  var k = GFX_RES[GFX.res] || 1;                                       // 解析度（畫質）：場景照這個大小畫，最後縮放貼到畫布
  CAM.w = Math.max(1, Math.round(w * k)); CAM.h = Math.max(1, Math.round(h * k));
}
// ── 畫質管線（TASK-0522；設定在 07_gfx.js 的 GFX） ──
// 場景畫在自己的 framebuffer RT.A（反鋸齒開 ⇒ MSAA 4×），大小 ＝ 畫布 × 解析度；畫完解析到 RT.B、縮放貼到畫布。
// RT.B 也是折射的「海底下那一層」：畫完不透明的東西、畫海之前，A 的顏色與深度複製到 B（GFX.refr ＝ 2），海的著色器讀它。
// 陰影圖每艘船一張（SHM.maps[i]：正交投影罩住那艘船的外接球，從太陽那邊看的深度）：船殼、模型、帆、附近斷開的那一團畫進去；
//   收的那邊（體素、模型、帆、海）兩張都看、取暗的。陰影關 ⇒ 兩張 1×1 的假圖（取樣器的型別要對，⛔ 沒綁 ⇒ 畫不出來）。
// 反射：鏡頭對海面（y ＝ 0）鏡像，把船畫進 RT.R（低 1/4、高 1/2 解析度；水面以下丟掉），海照螢幕座標＋法線擾動讀。浪的起伏不進鏡像（擾動蓋過去）。
// ⛔ 這裡不碰模擬的狀態（反向對照見 07_gfx.js）。帆與繩的緩衝（buildRig／sailBuf）一格只做一次，在所有趟之前（prepRig）。
var RT = null, SHM = null, DUMMY = null, PASS = { vp: null, eye: null, clip: -1e9, sh: 1 }, LAST_BOLT = null;
var MIRROR = new Float32Array([1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]), FAR_M = new Float32Array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 1]);
function mkTex(ifmt, fmt, type, w, h, lin, cmp) {
  var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); gl.texImage2D(gl.TEXTURE_2D, 0, ifmt, w, h, 0, fmt, type, null);
  var f = lin ? gl.LINEAR : gl.NEAREST; gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, f); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, f);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  if (cmp) { gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_COMPARE_MODE, gl.COMPARE_REF_TO_TEXTURE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_COMPARE_FUNC, gl.LEQUAL); }
  return t;
}
function mkRB(fmt, w, h, s) { var r = gl.createRenderbuffer(); gl.bindRenderbuffer(gl.RENDERBUFFER, r); if (s) gl.renderbufferStorageMultisample(gl.RENDERBUFFER, s, fmt, w, h); else gl.renderbufferStorage(gl.RENDERBUFFER, fmt, w, h); return r; }
/** framebuffer：col／dep 是貼圖或 renderbuffer（null ＝ 沒有）。 */
function mkFB(col, dep) {
  var f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f);
  function at(pt, o) { if (!o) return; if (o instanceof WebGLTexture) gl.framebufferTexture2D(gl.FRAMEBUFFER, pt, gl.TEXTURE_2D, o, 0); else gl.framebufferRenderbuffer(gl.FRAMEBUFFER, pt, gl.RENDERBUFFER, o); }
  at(gl.COLOR_ATTACHMENT0, col); at(gl.DEPTH_ATTACHMENT, dep);
  if (!col) { gl.drawBuffers([gl.NONE]); gl.readBuffer(gl.NONE); }
  var ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  return { fb: f, col: col, dep: dep, ok: ok };
}
function freeFB(o) { if (!o) return; gl.deleteFramebuffer(o.fb); [o.col, o.dep].forEach(function (x) { if (x instanceof WebGLTexture) gl.deleteTexture(x); else if (x) gl.deleteRenderbuffer(x); }); }
/** 場景、解析、反射的 framebuffer：大小、反鋸齒、反射品質變了才重建。MSAA 建不起來 ⇒ 不反鋸齒（RT.s ＝ 0）。 */
function targets(w, h) {
  var s = GFX.aa ? Math.min(4, gl.getParameter(gl.MAX_SAMPLES) || 0) : 0, rq = GFX.refl;
  if (RT && RT.w === w && RT.h === h && RT.want === s && RT.rq === rq) return;
  if (RT) { freeFB(RT.A); freeFB(RT.B); freeFB(RT.R); }
  RT = { w: w, h: h, want: s, s: s, rq: rq };
  RT.A = mkFB(mkRB(gl.RGBA8, w, h, s), mkRB(gl.DEPTH_COMPONENT24, w, h, s));
  if (!RT.A.ok && s) { freeFB(RT.A); RT.s = 0; RT.A = mkFB(mkRB(gl.RGBA8, w, h, 0), mkRB(gl.DEPTH_COMPONENT24, w, h, 0)); }
  RT.B = mkFB(mkTex(gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, w, h, true), mkTex(gl.DEPTH_COMPONENT24, gl.DEPTH_COMPONENT, gl.UNSIGNED_INT, w, h, false));
  if (rq) { var d = rq === 2 ? 2 : 4, rw = Math.max(1, w / d | 0), rh = Math.max(1, h / d | 0); RT.R = mkFB(mkTex(gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, rw, rh, true), mkRB(gl.DEPTH_COMPONENT24, rw, rh, 0)); RT.R.w = rw; RT.R.h = rh; }
  else RT.R = null;
}
/** 陰影圖：深度貼圖陣列（SHM.tex，第 4 號），每一層一張、大小照畫質（關 ⇒ 1×1 的假圖）。off ＝ 收陰影時沿法線推出去的距離（約 1.5 個陰影圖格子）；offG ＝ 全局那一層的。
 *  SHM.maps[k] ＝ 第 k 層的 { F（畫進那一層的 framebuffer）, m（矩陣） }；SHM.mats ＝ 全部層的矩陣串起來（著色器的 uShM，GPU_NEAR＋1 個）。 */
function shadowMaps() {
  var n = [1, 1024, 2048][GFX.shadow] || 1;
  if (SHM && SHM.n === n) return;
  if (SHM) shadowFree();
  SHM = { n: n, off: 0, offG: 0, maps: [], tex: null, layers: 0, glob: false, mats: new Float32Array((GPU_NEAR + 1) * 16) };
}
function shadowFree() { SHM.maps.forEach(function (m) { gl.deleteFramebuffer(m.F.fb); }); if (SHM.tex) gl.deleteTexture(SHM.tex); SHM.maps = []; SHM.tex = null; SHM.layers = 0; }
/** 這一格用到幾格（著色器的 uNS）：至少 2（一對一跟以前一樣兩張）、最多 GPU_NEAR。 */
function nsGPU() { return Math.max(2, Math.min(SHIPS.length, GPU_NEAR)); }
/** 陰影圖陣列照用到的層數配（TASK-0537：沒用到的上限不佔記憶體）：前幾格 ＋ 有船排不進去 ⇒ 再一層全局（第 GPU_NEAR 層）。多了不收（換場又會用到）。 */
function shadowGrow() {
  var need = SHIPS.length > GPU_NEAR ? GPU_NEAR + 1 : nsGPU();
  if (SHM.layers >= need) return;
  shadowFree();
  var t = SHM.tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D_ARRAY, t);
  gl.texImage3D(gl.TEXTURE_2D_ARRAY, 0, gl.DEPTH_COMPONENT24, SHM.n, SHM.n, need, 0, gl.DEPTH_COMPONENT, gl.UNSIGNED_INT, null);
  [gl.TEXTURE_MIN_FILTER, gl.TEXTURE_MAG_FILTER].forEach(function (p) { gl.texParameteri(gl.TEXTURE_2D_ARRAY, p, gl.LINEAR); });
  [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T].forEach(function (p) { gl.texParameteri(gl.TEXTURE_2D_ARRAY, p, gl.CLAMP_TO_EDGE); });
  gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_COMPARE_MODE, gl.COMPARE_REF_TO_TEXTURE); gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_COMPARE_FUNC, gl.LEQUAL);
  gl.bindTexture(gl.TEXTURE_2D_ARRAY, null);
  for (var k = 0; k < need; k++) {
    var f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f);
    gl.framebufferTextureLayer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, t, 0, k); gl.drawBuffers([gl.NONE]); gl.readBuffer(gl.NONE);
    SHM.maps.push({ F: { fb: f, ok: gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE }, m: FAR_M });
  }
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  SHM.layers = need;
}
/** GPU 的格（陰影圖的層、船艙遮罩、透視）這一格給哪幾艘（Tim 2026-10-13：「優先選最近的 N 條船」「只選視野範圍內最近的」）：
 *  船數 ≤ GPU_NEAR ⇒ 全部、照 SHIPS 的順序（一對一跟以前一樣）；
 *  否則 ⇒ 外接球碰到鏡頭視錐的船裡，離鏡頭最近的 GPU_NEAR 艘（上一格已經在裡面的打九折 ⇒ 兩艘差不多遠時不會每一格換來換去、陰影閃）；
 *  排不進去的（看不到的、太遠的）⇒ 全局陰影圖（SLOTS.rest）、沒有船艙遮罩。 */
var SLOTS = [];
function gpuSlots() {
  if (SHIPS.length <= GPU_NEAR) { SLOTS = SHIPS.slice(); SLOTS.rest = []; return; }
  var vp = CAM.vp, pl = [];                                              // 視錐的六個面（列優先的矩陣：第 r 列 ＝ vp[r], vp[4+r], vp[8+r], vp[12+r]）
  [[3, 0, 1], [3, 0, -1], [3, 1, 1], [3, 1, -1], [3, 2, 1], [3, 2, -1]].forEach(function (q) {
    var a = [0, 1, 2, 3].map(function (c) { return vp[c * 4 + q[0]] + q[2] * vp[c * 4 + q[1]]; }), l = Math.hypot(a[0], a[1], a[2]) || 1;
    pl.push(a.map(function (v) { return v / l; }));
  });
  var prev = SLOTS, cand = SHIPS.map(function (s) {
    var B = s.T.base, R = s.T.shR || (s.T.shR = 0.5 * S * Math.hypot(B.sx, B.sy, B.sz)), c = M4.pt(s.M, B.sx / 2, B.sy / 2, B.sz / 2);
    var vis = s.sink <= 40 && pl.every(function (p) { return p[0] * c[0] + p[1] * c[1] + p[2] * c[2] + p[3] > -R; });
    return { s: s, vis: vis, d: Math.hypot(c[0] - CAM.eye[0], c[1] - CAM.eye[1], c[2] - CAM.eye[2]) * (prev.indexOf(s) >= 0 ? 0.9 : 1) };
  });
  var pick = cand.filter(function (o) { return o.vis; }).sort(function (a, b) { return a.d - b.d || a.s.i - b.s.i; }).slice(0, GPU_NEAR).map(function (o) { return o.s; });
  pick.sort(function (a, b) { return a.i - b.i; });
  SLOTS = pick; SLOTS.rest = SHIPS.filter(function (s) { return pick.indexOf(s) < 0; });
}
function ortho(r, n, f) { return new Float32Array([1 / r, 0, 0, 0, 0, 1 / r, 0, 0, 0, 0, -2 / (f - n), 0, 0, 0, -(f + n) / (f - n), 1]); }
/** 帆與繩的緩衝：一格做一次（之後陰影、反射、場景都用同一份）。 */
function prepRig() {
  SHIPS.concat(PIECES).forEach(function (ow) {
    var dirty = ow.rigDirty;
    if (dirty) buildRig(ow);
    if (ow.sink > 40) return;
    var tb = DEBUG ? performance.now() : 0;
    if (dirty || (PHYS && ow.crew)) sailBuf(ow);                     // 物理開著：船上的帆每一格重做；斷開的那一團是靜態的
    if (PHYS && ow.crew) looseBuf(ow);
    if (DEBUG) PROF.buf += performance.now() - tb;
  });
}
// 重網格化（TASK-0531）：打掉的格要重建那幾個區塊的網格（VoxelKit RegionSet：dirty 裡的區塊 → meshChunk → 那一區重新上傳）。
//   畫面迴圈每一格最多 RM_BUDGET 塊（殉爆、斷船一次上千塊 ⇒ 那一格卡 170 ms）；先做斷開的那幾團（新建的）、再做船
//   ⇒ 半截船先長出來、船身那邊才拿掉 ⇒ 中間那幾格只會兩份疊在一起（位置一樣、看不出來），不會開洞。
//   快轉（__game.run、?demo）一次做完（remesh(Infinity)）⇒ 縮圖不變。只動畫面：格子本身在模擬那一步就改好了。
//   ⛔ 不改 VoxelKit：RegionSet.dirty 是公開的 Set，這裡先把超出預算的拿出來、flush 完再放回去。
var RM_BUDGET = 96;
function rsAllDirty(rs) { var t = rs.grid.tab; for (var i = 0; i < t.length; i++) if (t[i] !== null) rs.dirty.add(i); }   // 新建的一團：整份排進去（＝ buildAll，只是分批）
function rsFlushSome(rs, n) {
  var k = rs.dirty.size; if (k <= n) { rs.flush(); return k; }
  var rest = [], j = 0;
  rs.dirty.forEach(function (i) { if (j++ >= n) rest.push(i); });
  rest.forEach(function (i) { rs.dirty.delete(i); }); rs.flush(); rest.forEach(function (i) { rs.dirty.add(i); });
  return n;
}
function remesh(budget) {
  var left = budget;
  PIECES.concat(SHIPS).forEach(function (o) { if (left > 0 && o.rs.dirty.size) left -= rsFlushSome(o.rs, left); });
}
function drawHulls(prog, near) {                                       // near(c)：只畫靠近 c 的（陰影圖用；沒給 ⇒ 全畫）
  SHIPS.forEach(function (sh) { if (sh.sink > 40 || (near && !near(sh))) return; cutSet(prog, sh); gl.uniformMatrix4fv(prog.u.uModel, false, sh.M); sh.rs.draw(); });   // cutSet：剖面與隱藏甲板（74_cutaway.js）
  cutSet(prog, null);
  PIECES.forEach(function (pc) { if (near && !near(pc)) return; gl.uniformMatrix4fv(prog.u.uModel, false, pc.M); pc.rs.draw(); });
}
function drawModels(prog, near) {
  SHIPS.forEach(function (sh) {
    if (sh.sink > 40 || (near && !near(sh))) return;
    cutSet(prog, sh);
    sh.models.forEach(function (m) {
      var me = sh.T.meshes[m.mesh]; if (!m.alive || !me) return;
      gl.uniformMatrix4fv(prog.u.uModel, false, M4.mul(sh.M, modelLocal(m)));
      if (prog.u.uGlow) gl.uniform1f(prog.u.uGlow, m.meta && m.meta.kind === 'lantern' ? lanternK(m) : 0);   // 取用點的火藥桶是後加的模型，沒有 meta
      gl.bindVertexArray(me.vao); gl.drawArrays(gl.TRIANGLES, 0, me.n);
    });
  });
  if (prog.u.uGlow) gl.uniform1f(prog.u.uGlow, 0);                     // 斷開的那一團、飛出去的模型：燈熄了
  cutSet(prog, null);
  PIECES.forEach(function (pc) { if (near && !near(pc)) return; (pc.mods || []).forEach(function (m) {      // 跟著斷開的那一團走的模型
    var me = pc.T.meshes[m.mesh]; if (!me) return;
    gl.uniformMatrix4fv(prog.u.uModel, false, M4.mul(pc.M, m.L));
    gl.bindVertexArray(me.vao); gl.drawArrays(gl.TRIANGLES, 0, me.n);
  }); });
  FLY.forEach(function (f) { var me = f.T.meshes[f.mesh]; if (!me || !f.M) return; gl.uniformMatrix4fv(prog.u.uModel, false, f.M); gl.bindVertexArray(me.vao); gl.drawArrays(gl.TRIANGLES, 0, me.n); });
}
/** 燈籠（餘燼號船尾三盞，meta kind=lantern）：亮度 0.8–1 慢慢晃，照模擬時間與燈的編號（⛔ 不抽 rnd()：只給人看）；打飛了就熄。 */
function lanternK(m) { var t = SIMT * 1.7 + m.k * 2.39; return 0.8 + 0.1 * Math.sin(t) + 0.1 * Math.sin(t * 2.71 + 1.3); }
function lanternHalo(push) {
  SHIPS.forEach(function (sh) {
    if (sh.sink > 40) return;
    sh.models.forEach(function (m) {
      if (!m.alive || !m.meta || m.meta.kind !== 'lantern') return;
      var k = lanternK(m), sz = Math.max(m.bb[3] - m.bb[0], m.bb[5] - m.bb[2]) * S;   // 燈籠多大（公尺）
      push(M4.pt(sh.M, m.c[0], m.c[1], m.c[2]), sz * (2.4 + 0.4 * k), [1, 0.6, 0.2], 0.18 + 0.2 * k * (1.6 - WX.lum));   // 天越暗越亮（暴風雨的 lum 比晴天低）
    });
  });
}
function drawSails(prog, near) {
  SHIPS.concat(PIECES).forEach(function (ow) {
    if (ow.sink > 40 || !ow.sb || !ow.sb.n || (near && !near(ow))) return;
    cutSet(prog, ow); gl.uniformMatrix4fv(prog.u.uModel, false, ow.M);
    gl.bindVertexArray(ow.sb.vao); gl.drawElements(gl.TRIANGLES, ow.sb.n, gl.UNSIGNED_INT, 0);
  });
}
/** 陰影圖：GPU 的每一格（gpuSlots）一層，罩住那艘的外接球（船型的格子外框對角線的一半）。那一格沒有船 ⇒ 矩陣把所有點丟到範圍外。
 *  有船排不進去（SLOTS.rest）⇒ 第 GPU_NEAR 層 ＝ 全局：一張罩住那幾艘全部的外接球（格子大、解析度低；近的那幾艘不畫進去 ⇒ 不會粗的疊在細的上面）。 */
function shadowPass() {
  gl.enable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE); gl.enable(gl.POLYGON_OFFSET_FILL); gl.polygonOffset(1.5, 3);
  gl.viewport(0, 0, SHM.n, SHM.n);
  function one(M, R, c, near) {
    var D = R + 30;
    M.m = M4.mul(ortho(R, D - R - 10, D + R + 10), M4.lookAt([c[0] + SUN[0] * D, c[1] + SUN[1] * D, c[2] + SUN[2] * D], c, [0, 1, 0]));
    gl.bindFramebuffer(gl.FRAMEBUFFER, M.F.fb); gl.clear(gl.DEPTH_BUFFER_BIT);
    PASS.vp = M.m;
    gl.useProgram(P.dvox.prog); setCommon(P.dvox); drawHulls(P.dvox, near);
    gl.useProgram(P.dtri.prog); setCommon(P.dtri); drawModels(P.dtri, near); drawSails(P.dtri, near);
  }
  function ball(sh) { var B = sh.T.base; return { R: sh.T.shR || (sh.T.shR = 0.5 * S * Math.hypot(B.sx, B.sy, B.sz)), c: M4.pt(sh.M, B.sx / 2, B.sy / 2, B.sz / 2) }; }
  for (var i = 0; i < nsGPU(); i++) (function (M, sh) {
    if (!sh || sh.sink > 40) { M.m = FAR_M; return; }
    var b = ball(sh), R = b.R, c = b.c;
    SHM.off = 1.5 * 2 * R / SHM.n;
    one(M, R, c, function (o) { if (o === sh) return true; if (o.crew) return false; var p = o.c || (o.M ? [o.M[12], o.M[13], o.M[14]] : c); return Math.hypot(p[0] - c[0], p[2] - c[2]) < R * 1.3; });
  })(SHM.maps[i], SLOTS[i]);
  var rest = (SLOTS.rest || []).filter(function (s) { return s.sink <= 40; });
  SHM.glob = rest.length > 0 && SHM.maps.length > GPU_NEAR;
  if (SHM.glob) {                                                          // 全局：罩住排不進去的那幾艘（xz 的外框中心、半徑 ＝ 最遠那艘的距離＋它的外接球）
    var bs = rest.map(ball), x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9, y = 0;
    bs.forEach(function (b) { x0 = Math.min(x0, b.c[0]); x1 = Math.max(x1, b.c[0]); z0 = Math.min(z0, b.c[2]); z1 = Math.max(z1, b.c[2]); y += b.c[1] / bs.length; });
    var C = [(x0 + x1) / 2, y, (z0 + z1) / 2], RG = 0;
    bs.forEach(function (b) { RG = Math.max(RG, Math.hypot(b.c[0] - C[0], b.c[1] - C[1], b.c[2] - C[2]) + b.R); });
    SHM.offG = 1.5 * 2 * RG / SHM.n;
    one(SHM.maps[GPU_NEAR], RG, C, function (o) { if (o.crew) return rest.indexOf(o) >= 0; var p = o.c || (o.M ? [o.M[12], o.M[13], o.M[14]] : C); return bs.some(function (b) { return Math.hypot(p[0] - b.c[0], p[2] - b.c[2]) < b.R * 1.3; }); });
  } else if (SHM.maps[GPU_NEAR]) SHM.maps[GPU_NEAR].m = FAR_M;
  PASS.vp = null; gl.disable(gl.POLYGON_OFFSET_FILL);
}
/** 著色器的 uShM（每一層的矩陣串起來；沒有那一層 ⇒ FAR_M）。 */
function shadowMats() { for (var k = 0; k <= GPU_NEAR; k++) SHM.mats.set(SHM.maps[k] ? SHM.maps[k].m : FAR_M, k * 16); }
/** 船艙遮罩的貼圖陣列（uHullA，第 1 號）：載好的每一型一層（T.hullLayer），寬高取最大的那一型；載了新的船型 ⇒ 重建。 */
var HULLA = { tex: null, key: '' };
function hullArr() {
  var Ts = Object.keys(HULLT).map(function (id) { return HULLT[id]; }).filter(function (T) { return T.hullHB; }), key = Ts.map(function (T) { return T.id; }).join(',');
  if (HULLA.tex && HULLA.key === key) return;
  if (HULLA.tex) gl.deleteTexture(HULLA.tex);
  var W = 1, H = 1; Ts.forEach(function (T) { W = Math.max(W, T.hullTW); H = Math.max(H, T.hullTH); });
  var t = HULLA.tex = gl.createTexture(); HULLA.key = key;
  gl.bindTexture(gl.TEXTURE_2D_ARRAY, t); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
  gl.texImage3D(gl.TEXTURE_2D_ARRAY, 0, gl.R8, W, H, Math.max(1, Ts.length), 0, gl.RED, gl.UNSIGNED_BYTE, null);
  Ts.forEach(function (T, k) { T.hullLayer = k; gl.texSubImage3D(gl.TEXTURE_2D_ARRAY, 0, 0, 0, k, T.hullTW, T.hullTH, 1, gl.RED, gl.UNSIGNED_BYTE, T.hullHB); });
  [gl.TEXTURE_MIN_FILTER, gl.TEXTURE_MAG_FILTER].forEach(function (p) { gl.texParameteri(gl.TEXTURE_2D_ARRAY, p, gl.NEAREST); });
  [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T].forEach(function (p) { gl.texParameteri(gl.TEXTURE_2D_ARRAY, p, gl.CLAMP_TO_EDGE); });
  gl.bindTexture(gl.TEXTURE_2D_ARRAY, null);
}
/** 反射：鏡像的鏡頭把船畫進 RT.R（水面以下丟掉）。低 ＝ 船身；高 ＝ 再加砲、模型與帆。 */
function reflPass() {
  var R = RT.R; gl.bindFramebuffer(gl.FRAMEBUFFER, R.fb); gl.viewport(0, 0, R.w, R.h);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  PASS.vp = M4.mul(CAM.vp, MIRROR); PASS.eye = [CAM.eye[0], -CAM.eye[1], CAM.eye[2]]; PASS.clip = 0; PASS.sh = 0;
  gl.enable(gl.DEPTH_TEST); gl.enable(gl.CULL_FACE);                   // 船的矩陣是鏡射（shipBaseMatrix）、反射的鏡頭又鏡射一次 ⇒ 兩次抵銷，繞序照常（CCW）
  gl.useProgram(P.vox.prog); setCommon(P.vox); drawHulls(P.vox);
  if (GFX.refl === 2) {
    gl.disable(gl.CULL_FACE); gl.useProgram(P.tri.prog); setCommon(P.tri); gl.uniform1f(P.tri.u.uLit, 1); drawModels(P.tri);
    gl.useProgram(P.sail.prog); setCommon(P.sail); drawSails(P.sail);
  }
  PASS.vp = null; PASS.eye = null; PASS.clip = -1e9; PASS.sh = 1;
}
/** 船艙遮罩的 uniform（海與白沫共用，01_gl.js HULL_GLSL）。開始沉（sinkingFinal）之前，船艙裡不畫海水（Tim 2026-10-12：船身下沉一點點，海面就從破洞、甲板開口看進去像淹了） */
var MASK_OFF = -1;                                                        // ?debug=1 的 __game.mask(k)：第 k 艘的遮罩關掉（量 4 艘時每一格遮罩都有作用：關掉那艘 ⇒ 它的船艙裡才看得到海）
var HU = { inv: new Float32Array(GPU_NEAR * 16), hide: new Float32Array(GPU_NEAR), k: new Float32Array(GPU_NEAR * 4), xb: new Float32Array(GPU_NEAR * 4) };
function hullUniforms(prog) {
  var u = prog.u;
  hullArr(); HU.hide.fill(0);
  for (var i = 0; i < GPU_NEAR; i++) {                                    // GPU 的每一格（gpuSlots）照那艘船型的那一層；排不進去的船 ⇒ 沒有遮罩
    var s = SLOTS[i], T = s && s.T;
    if (s) HU.inv.set(s.inv, i * 16);                                     // 透視（nearShip）也用
    if (!T || !T.hullHB || T.hullLayer === undefined) continue;
    HU.hide[i] = !s.sinkingFinal && !s.sunk && s.i !== MASK_OFF ? 1 : 0;
    HU.k[i * 4] = T.hullTW; HU.k[i * 4 + 1] = T.hullTH; HU.k[i * 4 + 2] = T.cy; HU.k[i * 4 + 3] = T.hullLayer;
  }
  gl.uniform1fv(u.uHide, HU.hide); gl.uniformMatrix4fv(u.uInv, false, HU.inv); gl.uniform4fv(u.uHullK, HU.k);
  gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D_ARRAY, HULLA.tex); gl.uniform1i(u.uHullA, 1);
  gl.activeTexture(gl.TEXTURE0);
}
function render() {
  resize(); var w = CAM.w, h = CAM.h;
  // 閃電（天氣，08_weather.js）：那一格的天空與環境光拉亮、0.3 秒內退掉；雷聲照距離延後（340 m/s）。只在畫面，畫完把天色還回去
  var bolt = wxBolt(SIMT), sky0 = SKY, hor0 = HORIZON;
  if (bolt && bolt.f > 0) { SKY = lerp3(SKY, [0.82, 0.86, 0.98], bolt.f * 0.7); HORIZON = lerp3(HORIZON, [0.76, 0.79, 0.88], bolt.f * 0.6); }
  if (bolt && bolt.n !== LAST_BOLT) { LAST_BOLT = bolt.n; if (RUNNING && !STILL) setTimeout(function () { sfx('thunder', null, 1 / (1 + bolt.d / 1500)); }, bolt.d / 340 * 1000); }
  targets(w, h); shadowMaps(); shadowGrow(); gpuSlots();             // gpuSlots：這一格 GPU 的格給哪幾艘（視野裡最近的 GPU_NEAR 艘）
  if (!DUMMY) { DUMMY = mkTex(gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, 1, 1, false); }
  prepRig();
  gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D_ARRAY, null); gl.activeTexture(gl.TEXTURE0);   // 畫陰影圖時不綁著它（⛔ 綁著 ⇒ 讀寫同一張）
  if (GFX.shadow && !cutOn()) shadowPass(); else { SHM.maps.forEach(function (m) { m.m = FAR_M; }); SHM.glob = false; }   // 剖面、隱藏甲板開著 ⇒ 不算陰影（拿掉的甲板不擋光；74_cutaway.js）
  shadowMats();
  gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D_ARRAY, SHM.tex);   // 陰影圖陣列：固定第 4 號（01_gl.js SHADOW_GLSL）
  gl.activeTexture(gl.TEXTURE0);
  if (RT.R) reflPass();
  gl.bindFramebuffer(gl.FRAMEBUFFER, RT.A.fb); gl.viewport(0, 0, w, h);
  gl.clearColor(HORIZON[0], HORIZON[1], HORIZON[2], 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.LEQUAL);
  // 天
  gl.depthMask(false); gl.useProgram(P.sky.prog); setCommon(P.sky); gl.uniformMatrix4fv(P.sky.u.uInv, false, CAM.inv);
  gl.bindVertexArray(SKYVAO); gl.drawArrays(gl.TRIANGLES, 0, 3); gl.depthMask(true);
  // 船與斷開的那幾團
  // 船的矩陣是鏡射（shipBaseMatrix：照雕刻引擎的手性）⇒ 船殼的正面變成順時針；帆的著色器看 gl_FrontFacing 翻法線，也要跟著
  gl.enable(gl.CULL_FACE); gl.frontFace(gl.CW); gl.useProgram(P.vox.prog); setCommon(P.vox); drawHulls(P.vox); gl.frontFace(gl.CCW);
  // 碎片
  var n = 0;
  for (var i = 0; i < D.n; i++) {
    var o = i * 3, p;
    if (D.st[i] === 2) { var sh = SHIPS[D.ship[i]]; p = M4.pt(sh.M, D.p[o], D.p[o + 1], D.p[o + 2]); } else p = [D.p[o], D.p[o + 1], D.p[o + 2]];
    var k = n * 9, fade = Math.min(1, D.life[i] / 1.5);
    DINST[k] = p[0]; DINST[k + 1] = p[1]; DINST[k + 2] = p[2]; DINST[k + 3] = D.size[i] * fade;
    DINST[k + 4] = D.q[i * 4]; DINST[k + 5] = D.q[i * 4 + 1]; DINST[k + 6] = D.q[i * 4 + 2]; DINST[k + 7] = D.q[i * 4 + 3]; DINST[k + 8] = D.col[i]; n++;
  }
  if (n) {
    gl.useProgram(P.deb.prog); setCommon(P.deb); gl.bindVertexArray(DEBVAO); gl.bindBuffer(gl.ARRAY_BUFFER, DEBBUF); gl.bufferSubData(gl.ARRAY_BUFFER, 0, DINST, 0, n * 9);
    gl.drawElementsInstanced(gl.TRIANGLES, 36, gl.UNSIGNED_SHORT, 0, n);
  }
  drawCrew();
  // 模型、繩與帆
  gl.disable(gl.CULL_FACE); gl.useProgram(P.tri.prog); setCommon(P.tri);
  gl.uniform1f(P.tri.u.uLit, 1); drawModels(P.tri);
  gl.uniform1f(P.tri.u.uLit, 0); gl.vertexAttrib3f(1, 0, 1, 0);
  SHIPS.concat(PIECES).forEach(function (ow) {
    if (ow.sink > 40) return;
    cutSet(P.tri, ow); gl.uniformMatrix4fv(P.tri.u.uModel, false, ow.M);
    if (ow.lines && ow.lines.n) { gl.bindVertexArray(ow.lines.vao); gl.drawArrays(gl.LINES, 0, ow.lines.n); }
    if (PHYS && ow.ll && ow.ll.n) { gl.bindVertexArray(ow.ll.vao); gl.drawArrays(gl.LINES, 0, ow.ll.n); }
  });
  gl.frontFace(gl.CW); gl.useProgram(P.sail.prog); setCommon(P.sail); drawSails(P.sail); gl.frontFace(gl.CCW);
  // 折射（高）：畫海之前的場景複製到 RT.B（顏色＋深度），海的著色器讀它
  if (GFX.refr === 2) {
    gl.bindFramebuffer(gl.READ_FRAMEBUFFER, RT.A.fb); gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, RT.B.fb);
    gl.blitFramebuffer(0, 0, w, h, 0, 0, w, h, gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT, gl.NEAREST);
    gl.bindFramebuffer(gl.FRAMEBUFFER, RT.A.fb);
  }
  // 海
  if (GFX.refr) { gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); }
  if (!SEAG || SEAG.lv !== GFX.sea) seaGrid(GFX.sea);
  gl.useProgram(P.water.prog); setCommon(P.water); gl.uniform1f(P.water.u.uDet, SEA_LV[GFX.sea].det);
  gl.uniform2f(P.water.u.uC, Math.round(CAM.eye[0] / SEAG.snap) * SEAG.snap, Math.round(CAM.eye[2] / SEAG.snap) * SEAG.snap);   // 中心照網格間距對齊 ⇒ 近處的頂點不在浪上滑動
  gl.uniform1f(P.water.u.uReflOn, RT.R ? 1 : 0); gl.uniform1f(P.water.u.uRefr, GFX.refr); gl.uniform2f(P.water.u.uView, w, h);
  gl.activeTexture(gl.TEXTURE6); gl.bindTexture(gl.TEXTURE_2D, RT.R ? RT.R.col : DUMMY); gl.uniform1i(P.water.u.uRefl, 6);
  gl.activeTexture(gl.TEXTURE7); gl.bindTexture(gl.TEXTURE_2D, RT.B.col); gl.uniform1i(P.water.u.uScene, 7);
  gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, RT.B.dep); gl.uniform1i(P.water.u.uSceneD, 3);
  hullUniforms(P.water);
  gl.uniform1f(P.water.u.uXr, FLX3 || CUTV.half ? 1 : 0);              // 停格的「🔍 透視」、剖面：船附近的海面不畫（72_floodui.js、74_cutaway.js；只拿掉甲板 ⇒ 船殼裡本來就不畫海，船邊照畫）
  for (var xi = 0; xi < GPU_NEAR; xi++) (function (i) {               // GPU 的格（gpuSlots）：排不進去的船沒有透視
    var s = SLOTS[i], b = s ? xrBox(s.T) : null, e = s && CUTV.half ? cutSide(s) * XR_CUT : 0;   // 剖面：往鏡頭那一側多拿掉 XR_CUT 格（⛔ 只拿船邊 6 m ⇒ 從側面看，鏡頭到船之間的海面把水線下整片擋住）
    HU.xb[i * 4] = b ? b[0] : 0; HU.xb[i * 4 + 1] = b ? b[1] + e / 2 : 0; HU.xb[i * 4 + 2] = b ? b[2] : -1e9; HU.xb[i * 4 + 3] = b ? b[3] + Math.abs(e) / 2 : -1e9;
  })(xi);
  gl.uniform4fv(P.water.u.uXb, HU.xb);
  gl.bindVertexArray(SEAG.vao); gl.drawElements(gl.TRIANGLES, SEAG.n, gl.UNSIGNED_INT, 0);
  gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  if (!FLX3 && !CUTV.half) wpDrawFoam(hullUniforms);                                              // 船邊水花的白沫（13_water.js）：貼著浪、不寫深度
  flDraw();                                                              // 艙內的水面（33_flood.js，粒子模式）
  // 粒子＋砲彈＋瞄準點
  var m = 0;
  function pushPt(p, s, c, a, ty) { if (m * 9 >= PBUF.length) return; var k = m * 9; PBUF[k] = p[0]; PBUF[k + 1] = p[1]; PBUF[k + 2] = p[2]; PBUF[k + 3] = s; PBUF[k + 4] = c[0]; PBUF[k + 5] = c[1]; PBUF[k + 6] = c[2]; PBUF[k + 7] = a; PBUF[k + 8] = ty === undefined ? -1 : ty; m++; }
  for (i = 0; i < PT.n; i++) { var f = PT.life[i] / PT.max[i], s = PT.s1[i] + (PT.s0[i] - PT.s1[i]) * f; pushPt([PT.p[i * 3], PT.p[i * 3 + 1], PT.p[i * 3 + 2]], s, [PT.c[i * 3], PT.c[i * 3 + 1], PT.c[i * 3 + 2]], PT.a[i] * Math.min(1, f * 3), PT.ty[i]); }
  wpPushSpray(pushPt);                                                   // 船邊水花的水滴（13_water.js）
  flPushJets(pushPt);                                                    // 從破口噴進來的水（33_flood.js）
  rdPushSplash(pushPt);                                                  // 雨滴打在海面與船上的水花（14_rain.js）
  lanternHalo(pushPt);                                                   // 燈籠的光暈
  BALLS.forEach(function (b) { pushPt(b.p, 0.32, [0.08, 0.08, 0.08], 1); });
  var me = SHIPS[PLAYER_I], mWorld = m;                                   // mWorld 之後的是瞄準圈：另一批畫、不做深度測試（被船身擋住也看得到）
  if (me && me.aim && !AUTOFIRE && !STILL) {
    // 圈：直立，水平軸跟著敵艦的船長方向（扣掉視線方向的分量）⇒ 從側面看跟著敵艦轉；快正對船頭／船尾時改用鏡頭的右方
    // ⛔ 世界固定的平面 ⇒ 敵艦一轉就側成一條線；⛔ 只用船身側面那個平面 ⇒ 從船頭船尾看一樣是一條線
    var fs = aimShip(me), c = M4.pt(fs.M, me.aim[0], me.aim[1], me.aim[2]), vd = norm(sub(CAM.look, CAM.eye)), ax = shipAxis(fs);
    var u = sub(ax, mul(vd, dot(ax, vd))), ul = len(u);
    u = ul > 0.35 ? mul(u, 1 / ul) : norm(cross(vd, [0, 1, 0]));
    for (i = 0; i < 16; i++) { var an = i / 16 * 6.2832 + SIMT; pushPt(add(c, add(mul(u, Math.cos(an) * 2.2), [0, Math.sin(an) * 2.2, 0])), 0.5, [1, 0.85, 0.3], 0.9); }
  }
  if (FLX3) flHoleMarks(pushPt);                                         // 停格的「🔍 透視」開著：破口畫成點、隔著船殼看得到（72_floodui.js）
  if (m) {
    gl.depthMask(false); gl.useProgram(P.pt.prog); setCommon(P.pt); gl.uniform1f(P.pt.u.uPx, CAM.h / (2 * Math.tan(0.45)));
    gl.uniform1f(P.pt.u.uUseFx, FX_TEX ? 1 : 0); if (FX_TEX) { gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, FX_TEX); gl.uniform1i(P.pt.u.uFx, 0); }
    gl.bindVertexArray(PTVAO); gl.bindBuffer(gl.ARRAY_BUFFER, PTBUF); gl.bufferSubData(gl.ARRAY_BUFFER, 0, PBUF, 0, m * 9);
    if (mWorld) gl.drawArrays(gl.POINTS, 0, mWorld);
    if (m > mWorld) { gl.disable(gl.DEPTH_TEST); gl.drawArrays(gl.POINTS, mWorld, m - mWorld); gl.enable(gl.DEPTH_TEST); }
    gl.depthMask(true);
  }
  rdDraw();                                                              // 3D 雨滴（14_rain.js；畫質的「雨滴（3D）」）：做深度測試、不寫深度
  // 雨（天氣 × 畫質的「雨」）：最上面一層，不做深度測試
  var rk = WX.rain * [0, 0.55, 1][GFX.rain || 0];
  if (rk > 0) {
    gl.enable(gl.BLEND); gl.disable(gl.DEPTH_TEST); gl.useProgram(P.rain.prog);
    gl.uniform1f(P.rain.u.uT, SIMT); gl.uniform1f(P.rain.u.uRain, rk); gl.uniform2f(P.rain.u.uView, w, h);
    gl.uniform1f(P.rain.u.uYaw, Math.atan2(CAM.look[2] - CAM.eye[2], CAM.look[0] - CAM.eye[0]));
    gl.bindVertexArray(SKYVAO); gl.drawArrays(gl.TRIANGLES, 0, 3); gl.enable(gl.DEPTH_TEST);
  }
  SKY = sky0; HORIZON = hor0;
  gl.disable(gl.BLEND); gl.bindVertexArray(null);
  // 收尾：RT.A（MSAA ⇒ 先解析到 RT.B）縮放貼到畫布
  var src = RT.A.fb;
  if (RT.s) { gl.bindFramebuffer(gl.READ_FRAMEBUFFER, RT.A.fb); gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, RT.B.fb); gl.blitFramebuffer(0, 0, w, h, 0, 0, w, h, gl.COLOR_BUFFER_BIT, gl.NEAREST); src = RT.B.fb; }
  gl.bindFramebuffer(gl.READ_FRAMEBUFFER, src); gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, null);
  gl.blitFramebuffer(0, 0, w, h, 0, 0, cv.width, cv.height, gl.COLOR_BUFFER_BIT, w === cv.width && h === cv.height ? gl.NEAREST : gl.LINEAR);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/61_hud.js ──
// ───────────────────────── HUD ─────────────────────────
// ───────────────────────── 廣播（畫面上方的訊息） ─────────────────────────
// 一行一則、最多 5 行，各自 4 秒後淡掉（⛔ 以前只有一行、新的蓋掉舊的 ⇒ 同一刻兩件事只看得到一件）。
// 砲被打飛：同一個半秒內的併成一行；傷亡：第一個人倒下起算 5 秒，報這 5 秒裡陣亡、受傷各幾個（不洗版；是 0 的那一項不報）。
var MSGS = [], MSG_MAX = 5, MSG_LIFE = 4;
/** imp：重要的（殉爆、斷成兩截、沉沒、降旗）⇒ 留 8 秒，滿了先擠掉不重要的。 */
function note(sh, text, imp) {
  if (DEMO >= 0 && !RUNNING) return;
  var who = sh.i === PLAYER_I ? '我艦' : '敵艦', el = document.createElement('div');
  el.innerHTML = '<span style="color:' + (sh.i === 0 ? 'var(--blue)' : 'var(--red)') + '">' + who + '</span>　' + text;
  $('msg').appendChild(el); MSGS.push({ el: el, t: imp ? 8 : MSG_LIFE, imp: !!imp });
  while (MSGS.length > MSG_MAX) { var j = MSGS.findIndex(function (m) { return !m.imp; }); MSGS.splice(j < 0 ? 0 : j, 1)[0].el.remove(); }
}
function stepMsgs(dt) {
  for (var i = 0; i < MSGS.length; i++) { var m = MSGS[i]; m.t -= dt; m.el.style.opacity = clamp(m.t / 0.6, 0, 1); if (m.t <= 0) { m.el.remove(); MSGS.splice(i--, 1); } }
}
function clearMsgs() { MSGS.forEach(function (m) { m.el.remove(); }); MSGS = []; }
/** 砲被打飛（blowModel 呼叫）：先記著，下一次 newsFlush 併成一行。 */
function newsGun(sh, m, drop) {
  var g = sh.guns.filter(function (x) { return x.model === m; })[0]; if (!g) return;
  var no = /(\d+)$/.exec(m.name), lab = sideName(g.side) + (g.type === 'chase' || g.type === 'carr' ? GUNS[g.type].short : GUNS[g.type].short + ' ') + (g.type === 'chase' ? '' : no ? +no[1] : '');
  sh.news.guns.push(lab + (drop ? '（掉下去）' : ''));
}
var NEWS_WIN = 5;                                  // 傷亡廣播的時間區間（秒；Tim：3 → 5）
/** 普通水手（砲手）以外的人倒下：船長、軍官、舵手 ⇒ 當下各報一則（船長 ＝ 重要）；陸戰隊、桅頂水手、送藥手 ⇒ 記著，併進 5 秒那一行（人多，一個一個報會洗版）。 */
function newsCrew(sh, c, dead, cause) {
  if (c.role === ROLE.GUN) return;
  var cap = c.art === ART_CAPTAIN, how = dead ? (cause === '落水' || cause === '溺水' ? cause : '陣亡') : '受傷倒下', why = cause && cause !== '落水' && cause !== '溺水' ? '（' + cause + '）' : '';
  if (cap) { note(sh, '<b style="color:var(--gold)">船長' + how + '！</b>' + why, true); return; }
  if (c.role === ROLE.OFFICER || c.role === ROLE.HELM) {
    var left = sh.crew.filter(function (o) { return o.role === c.role && able(o); }).length, nm = ROLE_NAME[c.role];
    note(sh, nm + how + why + (left ? '（還有 ' + left + ' 位）' : '　<b style="color:#ff9a7a">' + nm + '全倒' + (c.role === ROLE.OFFICER ? ' —— 沒人指揮，瞄準變散' : '') + '</b>'), !left);
    return;
  }
  var by = dead ? sh.news.kr : sh.news.wr; by[c.role] = (by[c.role] || 0) + 1;
}
function roleList(by) { var r = []; for (var k in by) r.push(ROLE_NAME[k] + ' ' + by[k]); return r.length ? '（' + r.join('、') + '）' : ''; }
/** 每半秒（survey 那一拍）：把記著的砲併成一行；傷亡滿 NEWS_WIN 秒報一次。 */
function newsFlush(sh) {
  var N = sh.news;
  if (N.guns.length) {
    var gl0 = N.guns.length, list = gl0 > 5 ? N.guns.slice(0, 4).join('、') + '…' : N.guns.join('、');   // 一次太多（殉爆）⇒ 只列前四門
    note(sh, (gl0 === 1 ? N.guns[0] + ' 被打飛' : gl0 + ' 門砲被打飛：' + list) + '（砲還在 ' + sh.gunsAlive + '／' + sh.guns.length + '）'); N.guns = [];
  }
  var dk = sh.kills - N.k, dw = sh.wounds - N.w;
  if (N.t < 0 && (dk > 0 || dw > 0)) N.t = SIMT;                       // 第一個人倒下 ⇒ 開始數
  if (N.t >= 0 && SIMT - N.t >= NEWS_WIN) {
    var parts = []; if (dk > 0) parts.push('陣亡 ' + dk + roleList(N.kr)); if (dw > 0) parts.push('受傷 ' + dw + roleList(N.wr));   // 是 0 的那一項不報；陸戰隊等另列
    N.kr = {}; N.wr = {};
    if (parts.length) note(sh, NEWS_WIN + ' 秒內 ' + parts.join('、'));   // 累計看兩邊面板（⛔ 也寫進來 ⇒ 一行太長、蓋到面板）
    N.k = sh.kills; N.w = sh.wounds; N.t = -1;
  }
}
/** 面板的一行：砲長與現在瞄哪裡（我艦手動 ⇒ 玩家的瞄準模式，砲長待命）。 */
function capText(sh) {
  var C = CAPTAINS[sh.cap], manual = sh.i === PLAYER_I && !AUTOFIRE;
  return '砲長 ' + (C ? C.name : '—') + '：' + (manual ? '待命（我在瞄：' + AIM_NAME[sh.pMode || 'free'] + '）' : sh.aimMode ? '瞄' + AIM_NAME[sh.aimMode] : '觀察中');
}
// 進水 %（HUD；TASK-0535，Tim 2026-10-13：原本 ＝ 下沉 ÷ 9 m ⇒ 26% 時已經注定要沉、50% 就淹過船體 ⇒ 改用艙內積水算：船重＋積水 ＝ 浮力 ⇒ 100%）。
//   浮力算到「開始沉」那條線（下沉 SINK_FINAL ＝ 4.2 m，32_hull.js；約略是甲板泡水）：W100 ＝ 船從現在的浮高再往下 4.2 m 要多吃的水（浮力表 T.hyd；
//   船被打輕、浮高了 ⇒ W100 跟著變大）。粒子模式 W ＝ 艙內的積水；公式模式沒有水量 ⇒ W ＝ 現在比原本多吃的水（下沉照浮力表換算）。
//   ⇒ 兩種模式都是開始沉那一刻 100%。只是顯示：航速照舊用下沉 ÷ 9 m（31_sailing.js，模擬）。
var SINK_FINAL = 4.2;
/** 浮高 L 公尺（負 ＝ 吃水深）時比設計水線的排水輕幾噸（32_hull.js liftFor 的反函數）。 */
function tonsAt(T, L) {
  var HYD = T.hyd, n = HYD.length - 1, z = T.zw - L / S;
  if (z <= 0) return HYD[0] * RHO_W; if (z >= n) return HYD[n] * RHO_W;
  var i = Math.floor(z); return (HYD[i] + (HYD[i + 1] - HYD[i]) * (z - i)) * RHO_W;
}
/** 進水 %（0–1）。 */
function floodPct(sh) {
  if (sh.sinkingFinal || sh.sunk) return 1;
  var T = sh.T; if (!T || !T.hyd) return clamp(sh.sink / SINK_FINAL, 0, 1);
  var base = T.disp - (sh.mass0 || shipT(sh)) + massLost(sh), L0 = liftFor(T, base), W100 = base - tonsAt(T, L0 - SINK_FINAL);
  var W = sh.fl && !sh.broken ? sh.fl.vol * RHO_W : base - tonsAt(T, L0 - sh.sink);
  return W100 > 0 ? clamp(W / W100, 0, 1) : 1;
}
function panel(sh, title) {
  var hull = sh.grid.count / sh.orig, fl = floodPct(sh);
  var m = sh.masts.map(function (x) { return x.name + (x.up ? '✓' : '✗'); }).join(' ');
  // 排水量（Tim 2026-10-13）＝ 開戰時整艘船的重量（格＋砲＋火藥桶＋壓艙物，sh.mass0）：浮著的船排開的水跟自己一樣重；預設壓艙物剛好在設計水線 ⇒ 也就是設計排水量。
  // 「現在」＝ 扣掉被打掉的（格、打飛的砲、炸掉的桶，massLost，跟減重上浮同一支）；艙內的積水不算（那是進水，看下一行）
  var m0 = sh.mass0 || shipT(sh), disp = Math.round(m0), now = Math.round(m0 - massLost(sh));   // 兩個都取到 1 噸（⛔ 開戰時的取到 10 噸 ⇒ 第一格「2,150・現在 2,154」，現在比開戰還重）
  return '<h3>' + title + '<span class="disp">排水量 ' + disp.toLocaleString() + ' 噸・現在 ' + now.toLocaleString() + ' 噸</span>' + (sh.fate && !sh.sunk ? '　<span style="color:var(--gold)">' + sh.fate + '</span>' : '') + '</h3>船體 ' + (hull * 100).toFixed(1) + '%（打掉 ' + sh.lost.toLocaleString() + ' 格）<div class="bar"><i style="width:' + (hull * 100).toFixed(1) + '%"></i></div>' +
    '進水 ' + (sh.sunk ? '沉沒' : (fl * 100).toFixed(0) + '%') + (sh.fl && !sh.broken ? '（艙內積水 ' + Math.round(sh.fl.vol * RHO_W).toLocaleString() + ' 噸・破口 ' + sh.fl.area.toFixed(1) + ' m²）' : '（水線下破洞 ' + (sh.inflow || 0).toLocaleString() + ' 格）') + (sh.lift > 0.05 ? '　浮高 ' + sh.lift.toFixed(1) + ' m' : sh.lift < -0.05 ? '　吃水深 ' + (-sh.lift).toFixed(1) + ' m' : '') + '<div class="bar water"><i style="width:' + (fl * 100).toFixed(0) + '%"></i></div>' +
    '航速 ' + (sh.spd * 1.944).toFixed(1) + ' 節（' + sh.pos + '）　' + SAILSETS[sh.sailSet] + ' ' + Math.round(sh.sailFrac * 100) + '%<br>' +
    ((SAIL === 'off' ? '停船' : sh.manual ? '手動操舵' : '自動操舵') + '　舵 ' + (sh.rudder > 0.05 ? '左 ' + Math.round(sh.rudder * 100) + '%' : sh.rudder < -0.05 ? '右 ' + Math.round(-sh.rudder * 100) + '%' : '正') + '<br>') +
    capText(sh) + '<br>' +
    '船員 ' + (sh.able || 0) + '/' + sh.crew0 + '（傷 ' + sh.wounded + '　亡 ' + sh.dead + '）' + handsText(sh) + swimText(sh) + '　' + supplyText(sh) + '<br>' +
    '砲 有人 ' + (sh.gunsManned || 0) + '／還在 ' + sh.gunsAlive + '／' + sh.guns.length + '　' + m + '<br>' + gunRow(sh, 'S') + '<br>' + gunRow(sh, 'P') + '<br>開火 ' + sh.fired + '　命中 ' + sh.hits;
}
/** 一舷的砲列（長砲｜carronade＋追擊砲；船頭在左）：形狀 ＝ 裝填（● 好　◌ 裝填中　○ 開不了　✕ 毀），
 *  顏色 ＝ 人手（綠 滿編、黃 人數不足但能開（裝填慢）、灰 少於最少人數、紅 毀）；▶ ＝ 這一舷有砲對得到目標（我艦看瞄準點、其他看敵艦中央）。
 *  面板兩舷都列 ⇒ 觀戰也看得到、沒在用的那一舷壞了幾門也看得到。 */
function gunRow(sh, side) {
  function cell(g) {
    var st = !g.alive ? 'dead' : g.wet ? 'wet' : g.manned < g.crewMin ? 'none' : g.manned < g.crewFull ? 'short' : 'full';
    var k = !g.alive ? 3 : g.wet ? 5 : gunRate(g) <= 0 ? 2 : g.needCart && !(g.box > 0) ? 4 : g.reload > 0 ? 1 : 0;   // 4 ＝ 等火藥與彈藥（藥箱空了）
    var hp = !g.alive ? 0 : Math.max(0, g.model.hp / g.model.hpMax), hurt = g.alive && hp < 0.999;   // 受損 ⇒ 底下一條血條（.hp::after，寬 ＝ 剩下的血量）
    var cls = 'g-' + st + (hurt ? ' hp' : ''), sty = hurt ? '--hp:' + Math.round(hp * 100) + '%;' : '';
    if (HUD_ART) return '<span class="ico ' + cls + '" style="' + sty + 'background-position:' + ((3 + (k === 4 ? 1 : k === 5 ? 2 : k)) * 100 / 7).toFixed(3) + '% 0"></span>';
    return '<span class="' + cls + '"' + (sty ? ' style="' + sty + '"' : '') + '>' + '●◌○✕△≈'[k] + '</span>';
  }
  var rows = sh.decks.map(function (D) { return sh.guns.filter(function (x) { return x.deck === D.key && x.side === side; }); });   // 每層砲甲板一段（由下往上）
  var foe = foeOf(sh), w = sh.i === PLAYER_I && !AUTOFIRE ? aimPoint(sh) : foe && foe.center;
  var on = w && anyBears(sh, w, side), lab = (on ? '<b style="color:var(--gold)">▶' : '<span style="color:var(--dim)">　') + sideName(side) + (on ? '</b> ' : '</span> ');
  return '<span class="gr">' + lab + rows.map(function (r) { return r.map(cell).join(''); }).join('｜') + '</span>';
}
/** 補給一行：送藥手還能動的／全部、等火藥的砲幾門、取用點還剩幾桶。 */
function supplyText(sh) {
  var pm = sh.crew.filter(function (c) { return c.role === ROLE.POWDER; }), ok = pm.filter(able).length;
  var wait = sh.guns.filter(function (g) { return g.alive && g.needCart && !(g.box > 0) && gunRate(g) > 0; }).length;
  return '送藥手 ' + ok + '/' + pm.length + (wait ? '　<span style="color:#ffb35a">等火藥 ' + wait + ' 門</span>' : '');
}
var HUDN = 0;
/** HUD 圖示表（art/hud.png，8 欄 × 2 列）：第一列 船員 傷 亡 裝填好 裝填中 沒人 毀 鏈；只換掉砲列的符號。 */
function hudArt() {
  var st = document.createElement('style');
  st.textContent = '.ico{display:inline-block;width:14px;height:14px;vertical-align:-2px;background-image:url(' + HUD_ART.src + ');background-size:800% 200%;}';
  document.head.appendChild(st);
}
// ───────────────────────── 左下：羅盤與船身 ─────────────────────────
// 羅盤跟著鏡頭轉（畫面上方 ＝ 鏡頭看的方向）；「北」＝ 世界 −z（只是參考方向，航向照它算：東 ＝ +x）。
// 圈上：我艦（中間，尖端 ＝ 船頭）、風（從哪吹來的箭頭）、敵艦方位（紅點）、兩舷的砲門射界（±26°，對得到敵艦的那一舷亮）。
var COMPASS = ['北', '北北東', '東北', '東北東', '東', '東南東', '東南', '南南東', '南', '南南西', '西南', '西南西', '西', '西北西', '西北', '北北西'];
function bearing(x, z) { return ((Math.atan2(x, -z) * 57.2958) % 360 + 360) % 360; }
function compassName(b) { return COMPASS[Math.round(b / 22.5) % 16]; }
function deg3(b) { return ('00' + Math.round(b) % 360).slice(-3) + '°'; }
/** 羅盤的射界（drawNav）：世界方位角（度，atan2(z, x)）的連續段 [起, 迄]。all ＝ 開得動的砲、on ＝ 這一刻對得到敵艦的。 */
var ARC_BIN = { all: new Uint8Array(360), on: new Uint8Array(360) };
function gunArcs(sh, foe) {
  var A = ARC_BIN.all, O = ARC_BIN.on, w = foe && foe.center; A.fill(0); O.fill(0);
  sh.guns.forEach(function (gn) {
    if (!gn.alive || gunRate(gn) <= 0) return;
    var ax = gunAxis(sh, gn), a = Math.round(Math.atan2(ax[2], ax[0]) * 57.2958), on = w && !!gunTarget(sh, gn, w);
    for (var d = -26; d <= 26; d++) { var k = ((a + d) % 360 + 360) % 360; A[k] = 1; if (on) O[k] = 1; }   // ±26° ＝ ±0.45 rad
  });
  function runs(B) {
    var out = [], s0 = -1, k, i;
    for (k = 0; k < 360 && B[k]; k++); if (k === 360) return [[0, 360]];   // 整圈都有
    for (i = 1; i <= 360; i++) { var j = (k + i) % 360; if (B[j] && s0 < 0) s0 = k + i; if (!B[j] && s0 >= 0) { out.push([s0, k + i - 1]); s0 = -1; } }   // 從空的那一格開始掃 ⇒ 跨 0° 的段不會斷成兩截
    return out;
  }
  return { all: runs(A), on: runs(O) };
}
var TURN_T = 10, TURN_COL = '#7ef0c8';                 // 羅盤外圈的轉向弧：預測幾秒後的船頭、顏色（跟射界的金、風的藍、敵艦的紅分開）
function drawNav(sh) {
  if (!CAM.look) return;
  var c2 = $('navc'), g = c2.getContext('2d'), dpr = Math.min(window.devicePixelRatio || 1, 2), W = 150;
  if (c2.width !== W * dpr || c2.height !== W * dpr) { c2.width = c2.height = W * dpr; }   // ⛔ 只比寬：canvas 預設 300×150，dpr 2（手機）時寬剛好是 300 ⇒ 高停在 150，羅盤被拉成兩倍高、下半截切掉
  g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, W);
  var f = norm([CAM.look[0] - CAM.eye[0], 0, CAM.look[2] - CAM.eye[2]]), rt = [-f[2], 0, f[0]], cx = W / 2, cy = W / 2, R = 56;
  function P(d, k) { return [cx + (d[0] * rt[0] + d[2] * rt[2]) * R * k, cy - (d[0] * f[0] + d[2] * f[2]) * R * k]; }
  function dirOf(b) { var a = b / 57.2958; return [Math.sin(a), 0, -Math.cos(a)]; }
  function line(a, b, col, w) { g.strokeStyle = col; g.lineWidth = w; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
  g.strokeStyle = 'rgba(255,255,255,.28)'; g.lineWidth = 1; g.beginPath(); g.arc(cx, cy, R, 0, 6.2832); g.stroke();
  for (var b = 0; b < 360; b += 30) line(P(dirOf(b), b % 90 ? 0.93 : 0.86), P(dirOf(b), 1), 'rgba(255,255,255,.35)', 1);
  g.font = '11px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = '#e8c26a';
  var pn = P(dirOf(0), 1.17); g.fillText('北', pn[0], pn[1]);
  var F = fwd(sh.yaw), foe = foeOf(sh);
  // 射界（Tim 2026-10-13：照真的能開的砲畫）：每一門還開得動的砲（沒毀、有人）自己的砲門射界（砲軸 ±0.45 rad，跟 bears 同一個數）的聯集 ⇒ 暗；
  //   這一刻對得到敵艦的那幾門（gunTarget，跟開砲同一支）再疊一層亮的。追擊砲（船頭、餘燼號的船尾）各自的方向都畫得出來；砲打掉、沒人操作 ⇒ 那一塊消失。
  //   以 1° 一格累計再畫連續的段（聯集、跨 ±180° 都不用另外處理）；從船的中心畫（羅盤的比例下砲口在船上的前後差可以不管）。
  var arc = gunArcs(sh, foe), p0 = P([0, 0, 0], 0);
  [[arc.all, 'rgba(232,194,106,.13)'], [arc.on, 'rgba(232,194,106,.45)']].forEach(function (L) {
    L[0].forEach(function (r) {
      g.fillStyle = L[1]; g.beginPath(); g.moveTo(p0[0], p0[1]);
      for (var d = r[0]; ; d = Math.min(d + 3, r[1])) { var t = d / 57.2958, q = P([Math.cos(t), 0, Math.sin(t)], 0.97); g.lineTo(q[0], q[1]); if (d >= r[1]) break; }   // 每 3° 一點，最後一點落在段尾
      g.closePath(); g.fill();
    });
  });
  // 風：從圈外吹進來的箭頭
  var Wd = norm(WIND), from = [-Wd[0], 0, -Wd[2]], a0 = P(from, 1.2), a1 = P(from, 0.62), hd = norm([a1[0] - a0[0], 0, a1[1] - a0[1]]);
  line(a0, a1, '#8fd3ff', 2.5);
  g.fillStyle = '#8fd3ff'; g.beginPath(); g.moveTo(a1[0] + hd[0] * 4, a1[1] + hd[2] * 4); g.lineTo(a1[0] - hd[0] * 6 - hd[2] * 5, a1[1] - hd[2] * 6 + hd[0] * 5); g.lineTo(a1[0] - hd[0] * 6 + hd[2] * 5, a1[1] - hd[2] * 6 - hd[0] * 5); g.fill();
  // 其他船的方位（TASK-0537：全部畫，敵紅、友藍、沉了灰；一對一 ＝ 以前那一個紅點）
  SHIPS.forEach(function (o) {
    if (o === sh || !o.center || !sh.center) return;
    var e = norm([o.center[0] - sh.center[0], 0, o.center[2] - sh.center[2]]), pe = P(e, 0.86);
    g.fillStyle = o.sunk ? '#666' : isFoe(sh, o) ? '#ff6f6f' : '#6f9bff'; g.beginPath(); g.arc(pe[0], pe[1], 4.5, 0, 6.2832); g.fill();
  });
  // 我艦：從上面俯瞰的船（05_hull.js navImg，載入時算一次；船頭朝上、右舷在右 ⇒ 只轉不翻），船長（含艏斜桅）＝ 半徑的 1.575 倍（中心到兩端約 0.79 R，還在圈裡）
  //   （⛔ 0.8 倍 ⇒ 船長寬比約 6:1，在 150 px 的圈裡細成一條線；Tim 2026-10-13：1.05 倍再放大 1.5 倍）；外面一圈我方的顏色。沒有圖 ⇒ 以前的三角形
  var tc = teamIdx(sh) === 0 ? '#6f9bff' : '#ff6f6f', NI = sh.T.navImg;
  if (NI) {
    var tip = P(F, 1), sc = R * 1.575 / NI.height;
    g.save(); g.translate(cx, cy); g.rotate(Math.atan2(tip[1] - cy, tip[0] - cx) + Math.PI / 2); g.scale(sc, sc);
    g.shadowColor = tc; g.shadowBlur = 5; g.imageSmoothingEnabled = true; g.drawImage(NI, -sh.T.navU, -sh.T.navV);
    g.restore();
  } else {
    var S2 = norm([F[2], 0, -F[0]]), tip0 = P(F, 0.42), l = P(add(mul(F, -0.32), mul(S2, 0.12)), 1), r2 = P(add(mul(F, -0.32), mul(S2, -0.12)), 1);
    g.fillStyle = tc; g.beginPath(); g.moveTo(tip0[0], tip0[1]); g.lineTo(l[0], l[1]); g.lineTo(r2[0], r2[1]); g.closePath(); g.fill();
  }
  // 轉向（Tim 2026-10-13：用圖示表現轉彎的方向與快慢，沿外圈畫）：從船頭的方向沿外圈畫到「照現在的轉向率，TURN_T 秒後船頭會在哪」，
  //   箭頭 ＝ 轉的方向，弧越長轉得越快（最多 120°）；幾乎直走（< 0.2°/秒）只畫船頭那一點。跟船頭在羅盤上用同一支 P(fwd(yaw)) ⇒ 弧的起點就是船頭指的方向。
  var yr = sh.yawRate || 0, span = clamp(yr * TURN_T, -2.094, 2.094), hp = P(F, 1.07);
  g.fillStyle = TURN_COL; g.beginPath(); g.arc(hp[0], hp[1], 2.5, 0, 6.2832); g.fill();
  if (Math.abs(yr) > 0.0035) {
    var nT = Math.max(2, Math.ceil(Math.abs(span) / 0.05)), pt = [];
    for (var iT = 0; iT <= nT; iT++) pt.push(P(fwd(sh.yaw + span * iT / nT), 1.07));
    g.strokeStyle = TURN_COL; g.lineWidth = 3; g.lineCap = 'round'; g.beginPath(); g.moveTo(pt[0][0], pt[0][1]);
    for (iT = 1; iT <= nT; iT++) g.lineTo(pt[iT][0], pt[iT][1]);
    g.stroke();
    var e1 = pt[nT], e0 = pt[nT - 1], tl = Math.hypot(e1[0] - e0[0], e1[1] - e0[1]) || 1, tx = (e1[0] - e0[0]) / tl, ty = (e1[1] - e0[1]) / tl;   // 箭頭：沿弧的切線
    g.beginPath(); g.moveTo(e1[0] + tx * 6, e1[1] + ty * 6); g.lineTo(e1[0] - ty * 4.5, e1[1] + tx * 4.5); g.lineTo(e1[0] + ty * 4.5, e1[1] - tx * 4.5); g.closePath(); g.fill();
  }
  // 文字
  var hb = bearing(F[0], F[2]), wb = bearing(from[0], from[2]), roll = (sh.rollA + (sh.rollW || 0)) * 57.2958, pitch = (sh.pitchA + (sh.pitchW || 0)) * 57.2958;
  var hull = sh.grid.count / sh.orig * 100, fl = floodPct(sh) * 100;
  $('navt').innerHTML =
    '航向 ' + deg3(hb) + '（' + compassName(hb) + '）　' + (sh.spd * 1.944).toFixed(1) + ' 節<br>' +
    '<span style="color:#8fd3ff">風 從 ' + deg3(wb) + '（' + compassName(wb) + '）' + windKnots().toFixed(0) + ' 節</span>　' + sh.pos + (sh.irons > 0.05 ? '　<b style="color:#ff9a7a">失速' + (sh.irons < 0.95 ? ' ' + Math.round(sh.irons * 100) + '%' : '') + '</b>' : '') + '<br>' +
    '船體 ' + hull.toFixed(1) + '%　進水 ' + (sh.sunk ? '沉沒' : fl.toFixed(0) + '%') + (sh.lift > 0.05 ? '　浮高 ' + sh.lift.toFixed(1) + ' m' : sh.lift < -0.05 ? '　吃水深 ' + (-sh.lift).toFixed(1) + ' m' : '') + '<br>' +
    '傾斜 ' + Math.abs(roll).toFixed(1) + '°' + (Math.abs(roll) < 0.2 ? '' : roll < 0 ? '（左低）' : '（右低）') + '　縱傾 ' + pitch.toFixed(1) + '°<br>' +
    SAILSETS[sh.sailSet] + ' ' + Math.round(sh.sailFrac * 100) + '%　舵 ' + (sh.rudder > 0.05 ? '左 ' + Math.round(sh.rudder * 100) + '%' : sh.rudder < -0.05 ? '右 ' + Math.round(-sh.rudder * 100) + '%' : '正') +
    (Math.abs(yr) > 0.0035 ? '　<span style="color:' + TURN_COL + '">' + (yr > 0 ? '左' : '右') + '轉 ' + (Math.abs(yr) * 57.2958).toFixed(1) + '°/秒</span>' : '');   // yawRate 正 ＝ 畫面上左轉（31_sailing.js fwd）
}
function hud(dt) {
  stepMsgs(dt);
  if (!SHIPS.length || (HUDN++ % 6)) return;
  var me = SHIPS[PLAYER_I], mf = flagship(playerTeam()) || me, ef = flagship(foeTeam());   // 上方兩個面板：雙方旗艦（52_fleet.js；一對一 ＝ 我艦、敵艦）
  $('me').innerHTML = panel(mf, (mf === me ? '我艦 ' : '我方旗艦 ') + mf.T.name + teamTag(mf));
  $('foe').innerHTML = ef ? panel(ef, (teamShips(ef.team).length > 1 ? '敵方旗艦 ' : '敵艦 ') + ef.T.name + teamTag(ef)) : '';
  // 下方：我艦的砲列（跟面板同一支）＋ 射界外警告；觀戰只顯示鏡頭
  var aw = aimPoint(me), bs = anyBears(me, aw, 'S') ? 'S' : anyBears(me, aw, 'P') ? 'P' : null;
  var warn = bs || AUTOFIRE ? '' : '　<b style="color:#ff9a7a">⚠ 射界外</b>';
  $('guns').innerHTML = gunRow(me, bs || me.side) + warn + '　' + CAM_NAMES[CAM.mode] + (PAUSED ? '　⏸ 停格' : '');
  [].forEach.call(document.querySelectorAll('#ammo span'), function (s) { s.className = +s.dataset.a === AMMO_I ? 'on' : ''; });
  var ak = $('aimk'); if (ak) ak.innerHTML = '<b>Q</b> 瞄準：' + (AUTOFIRE ? '砲長' : AIM_NAME[me.pMode || 'free']);
  var t = DEBUG ? '格：' + SHIPS.map(function (s) { return s.grid.count; }).join('／') + '　四邊形：' + SHIPS.map(function (s) { return s.rs.quads(); }).join('／') + '　碎片 ' + D.n + '　粒子 ' + PT.n + '　脫落 ' + PIECES.length + (PHYS ? '　物理 ' + PHYS_MS.toFixed(2) + ' ms/步、垂繩 ' + SHIPS.map(function (s) { return s.loose.length; }).join('／') : '') + '　' + FPS.toFixed(0) + ' fps' : '';
  $('tip').textContent = t;
  drawNav(me);
}
// 結算畫面照模擬時間延後跳（暫停時不會跳出來；殉爆的慢動作中跟著變慢）（Tim：先看完精彩畫面 —— 殉爆的火球、斷成兩截）：
//   輸的那艘已經沉了 ⇒ 再等 END_SINK 秒；已經開始沉（殉爆斷船、進水太多）⇒ 等它沉下去（sunk）再等 END_SINK 秒，最多等 END_MAX 秒（END_WAIT）；
//   降旗、全員倒下（沒在沉）⇒ END_OTHER 秒。Tim 2026-10-13：讓玩家欣賞完沉船 ⇒ 沉了 2.5 → 5 秒、開始沉的等它沉下去（以前一律 5.5 秒，斷船的那艘沉到一半就被結算蓋住）。
//   只管什麼時候亮出結算畫面：OVER、結算的文字照舊在分出勝負那一步定 ⇒ 戰局讀數不變。
var END_AT = 0, END_SINK = 5, END_OTHER = 5.5, END_MAX = 40, END_WAIT = null;
function checkEnd() {
  if (MODE === 'sandbox' || DEMO >= 0) return;
  if (OVER) {
    if (END_WAIT && (END_WAIT.sunk || SIMT >= END_AT)) { END_AT = Math.min(END_AT, SIMT + END_SINK); END_WAIT = null; }
    if (END_AT && !END_WAIT && SIMT >= END_AT) { END_AT = 0; $('end').className = 'on'; }
    return;
  }
  // 照陣營（TASK-0537）：敵方每艘都沉了或降旗 ⇒ 勝；我方每艘都是 ⇒ 敗。一對一 ⇒ 跟以前同一句、同一個判定順序。
  var me = SHIPS[PLAYER_I], mt = playerTeam(), ft = foeTeam(), mine = teamShips(mt), foes = teamShips(ft), txt = null, lose = null;
  function fate(sh) { return sh.sunk ? '沉沒' : sh.fate; }
  function who(L, one) { return L.length === 1 ? one + fate(L[0]) : one.replace('艦', '方') + ' ' + L.length + ' 艘全數' + (L.every(function (o) { return o.sunk; }) ? '沉沒' : '沉沒或降旗'); }
  if (foes.length && teamDown(ft)) { txt = '勝利！' + who(foes, '敵艦'); lose = foes; }
  else if (me.selfD) txt = '自爆！我艦引爆了彈藥庫';                      // 自爆（23_powder.js selfDestruct）：第一間炸的那一刻就結算（文字不等最後那間）
  else if (teamDown(mt)) { txt = '敗北……' + who(mine, '我艦'); lose = mine; }
  if (!txt) return;
  OVER = true;
  function sum(L, k) { return L.reduce(function (a, o) { return a + o[k]; }, 0); }
  $('endT').textContent = txt;
  $('endS').innerHTML = '打掉的格數：我' + (mine.length > 1 ? '方 ' : '艦 ') + sum(mine, 'lost').toLocaleString() + '　敵' + (foes.length > 1 ? '方 ' : '艦 ') + sum(foes, 'lost').toLocaleString() + '<br>開火／命中：' + me.fired + '／' + me.hits + '　經過 ' + SIMT.toFixed(0) + ' 秒' +
    '<br><span style="color:var(--dim)">' + strikeText() + '</span>';
  lose = lose || mine;                                              // 重開／回選單時 END_AT、END_WAIT 歸零（⛔ 不歸零 ⇒ 結束後幾秒內按重新開始，新的一局會跳出結算）
  var sinking = lose.filter(function (o) { return o.sinkingFinal && !o.sunk; })[0];   // 輸的那邊還有在沉的 ⇒ 等它沉下去
  if (sinking) { END_WAIT = sinking; END_AT = SIMT + END_MAX; }
  else if (lose.some(function (o) { return o.sunk; })) END_AT = SIMT + END_SINK;
  else END_AT = SIMT + END_OTHER;
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/69_prefs.js ──
// ───────────────────────── 設定存檔（localStorage；Tim 2026-10-13：直接開網頁時，設定存在玩家自己的瀏覽器，下次打開自動套用） ─────────────────────────
// 存：玩法（娛樂／寫實）、細節設定（血量、傷害、彈種倍率、火藥、補給、風壓、降旗、頂風失速、娛樂加成）、船隻設定（SHIP_CFG，照船型）、砲長、選了哪兩艘船、彈種、自動開砲、帆與繩的物理，
//   以及主選單的模式、距離、航行。不存整場戰局。
// 只存「跟預設不一樣」的那幾項：沒動過的照程式的預設走 ⇒ 之後改了預設值（例：火藥 450 → 675），沒動過的玩家也吃得到新的。
//   壓艙物的預設跟船走（T.ballast0）⇒ 存的時候記那艘船的 checksum，船重匯過就不套（PREF_BALLAST，04_state.js）。
// 網址參數優先：網址有的那一項照網址；網址帶了任何設定參數 ⇒ 只讀不寫（照連結開的那一場不蓋掉玩家自己的存檔）。
// ?demo（縮圖、對拍）⇒ 不讀也不寫：快轉出來的那一格不受存檔影響。?prefs=0 同（量預設用）。
// 讀寫都包 try/catch：畫廊彈窗的 iframe 只開 allow-scripts（不透明來源），一碰 localStorage 就丟錯 ⇒ 照預設跑。
// 格式帶版本號（v）；看不懂的版本、壞掉的 JSON ⇒ 整份不套；型別不對、界外的值 ⇒ 那一項不套（界外的夾回範圍）。
// 什麼時候存：每秒比一次（跟上次存的不一樣才寫）＋ 關頁、切到背景時。全部回到預設 ⇒ 刪掉那一筆。
var PREFS_KEY = 'ame_constitution_broadside.prefs', PREFS_VER = 1;
var PREF_Q = ['ship', 'blue', 'red', 'hard', 'flood', 'ballast', 'gunw', 'speed', 'agile', 'upwind', 'gunhp', 'sailhp', 'crewhp', 'powderhp', 'blast', 'blastv', 'dmg24', 'dmg32l', 'dmg32', 'dmg18',
  'box', 'carry', 'hands', 'drown', 'wind', 'ammo', 'strike', 'cap', 'phys', 'sail', 'play', 'stall', 'funspeed', 'funagile', 'funstall', 'funpowder', 'sea',
  'gfx', 'g_shadow', 'g_refl', 'g_refr', 'g_sea', 'g_res', 'g_aa', 'phx', 'p_rig', 'p_debris', 'p_fx', 'weather', 'g_rain', 'g_drops', 'g_dropspl', 'slowmo', 'slowcam'];          // 會蓋過存檔的網址參數（04_state.js、05_hull.js 讀的那些）
var DMG_Q = { long: 'dmg24', long32: 'dmg32l', carr: 'dmg32', chase: 'dmg18', long4: 'dmg4' };
var PREFS = { read: DEMO < 0 && Q.get('prefs') !== '0', write: false, state: '', last: '' };
PREFS.write = PREFS.read && !PREF_Q.some(function (k) { return Q.has(k); });
/** 現在的設定裡跟預設不一樣的那幾項（＋版本號）。 */
function prefsSnap() {
  var o = { v: PREFS_VER }, cfg = {};
  function put(k, v, d) { if (v !== d) o[k] = v; }
  if (FLEET_SET.some(function (L) { return L.length !== 1 || L[0] !== 'constitution'; })) o.fleet = FLEET_SET.map(function (L) { return L.slice(); });   // 艦隊編成（TASK-0537；舊存檔的 ship ＝ 一邊一艘，讀的時候照樣認）
  Object.keys(SHIP_CFG).forEach(function (id) {
    var c = SHIP_CFG[id], T = HULLT[id], d = {};
    SHIP_KEYS.forEach(function (k) { if (k !== 'ballast' && c[k] !== cfgBase(k, id)) d[k] = c[k]; });   // 跟那一型的預設比（HULL_CFG0）
    if (T && c.ballast !== undefined) { if (c.ballast !== T.ballast0) { d.ballast = c.ballast; d.chk = T.h.checksum; } }
    else if (PREF_BALLAST[id]) { d.ballast = PREF_BALLAST[id].v; d.chk = PREF_BALLAST[id].chk; }   // 這一場沒載那艘船 ⇒ 存檔裡的照留
    if (Object.keys(d).length) cfg[id] = d;
  });
  if (Object.keys(cfg).length) o.cfg = cfg;
  put('gunhp', GUN_HP, LIM.gunhp[2]); put('sailhp', SAIL_HP, LIM.sailhp[2]); put('crewhp', CREW_HP, LIM.crewhp[2]); put('powderhp', POWDER_HP, LIM.powderhp[2]);
  put('blast', BLAST_K, LIM.blast[2]); put('blastv', BLAST_V, LIM.blastv[2]); put('box', BOX_N, LIM.box[2]); put('carry', CARRY_N, LIM.carry[2]); put('hands', HANDS, LIM.hands[2]); put('drown', DROWN_T, LIM.drown[2]); put('wind', WIND_K, LIM.wind[2]);
  put('weather', WX_ID, 'clear'); put('sea', SEA_K, LIM.sea[2]); put('play', PLAY, 'fun'); put('stall', STALL_K, LIM.stall[2]); put('funspeed', FUN.speed, LIM.funspeed[2]); put('funagile', FUN.agile, LIM.funagile[2]); put('funstall', FUN.stall, LIM.funstall[2]); put('funpowder', FUN.powder, LIM.funpowder[2]);
  var dm = {}; Object.keys(DMG_Q).forEach(function (t) { if (DMG[t] !== LIM[DMG_Q[t]][2]) dm[t] = DMG[t]; });
  if (Object.keys(dm).length) o.dmg = dm;
  if (AMMO_K.some(function (r, i) { return r.some(function (v, j) { return v !== AMMO_K0[i][j]; }); })) o.ammoK = AMMO_K.map(function (r) { return r.slice(); });
  if (STRIKE.cas !== LIM.cas[2] || STRIKE.guns || STRIKE.masts || STRIKE.officers) o.strike = { cas: STRIKE.cas, guns: STRIKE.guns, masts: STRIKE.masts, officers: STRIKE.officers };
  if (CAP_SET.some(function (k) { return k !== 'random'; })) o.cap = CAP_SET.slice();
  var gd = GFX_PRESET[GFX_DEFAULT]; if (GFX_ITEMS.some(function (it) { return GFX[it.k] !== gd[it.k]; })) { o.gfx = {}; GFX_ITEMS.forEach(function (it) { o.gfx[it.k] = GFX[it.k]; }); }   // 畫質（07_gfx.js）：跟預設不一樣 ⇒ 整組存
  put('fps', GFX_FPS, false); put('slow', SLOW.on, true); put('slowcam', SLOW.cam, true);   // 殉爆的慢動作與特寫（73_slowmo.js）
  var xd = PHX_PRESET[PHX_DEFAULT]; if (PHX_ITEMS.some(function (it) { return PHX[it.k] !== xd[it.k]; })) { o.phx = {}; PHX_ITEMS.forEach(function (it) { o.phx[it.k] = PHX[it.k]; }); }   // 物理效果（09_phx.js）：跟預設不一樣 ⇒ 整組存
  put('ammo', AMMO_I, 0); put('mode', MODE, 'pve'); put('sail', SAIL, 'auto'); put('dist', DIST, 140);
  if (LAST_MODE === MODE) put('auto', AUTOFIRE, MODE === 'eve');     // 換了模式還沒開局 ⇒ 開局時會照模式重套（70_flow.js reset），這時的值不算數
  return o;
}
/** 存檔 ⇒ 變數。網址有的那一項不套；每一項各自驗（型別、範圍），不對的那一項照預設。 */
function prefsApply(p) {
  function num(v, lim, int) { if (typeof v !== 'number' || !isFinite(v)) return undefined; v = clamp(v, lim[0], lim[1]); return int ? Math.round(v) : v; }
  function set(qk, v, lim, int, f) { if (Q.has(qk)) return; var x = num(v, lim, int); if (x !== undefined) f(x); }
  if (!Q.has('ship') && !Q.has('blue') && !Q.has('red')) {               // 編成：網址給了任何一個 ⇒ 整組照網址
    if (Array.isArray(p.ship)) p.ship.forEach(function (w, i) { if (i < 2 && hullInfo(w)) FLEET_SET[i] = [w]; });   // 舊存檔（一邊一艘）
    if (Array.isArray(p.fleet)) p.fleet.forEach(function (L, i) { if (i < 2 && Array.isArray(L)) { L = L.filter(function (w) { return typeof w === 'string' && hullInfo(w); }); if (L.length) FLEET_SET[i] = L; } });
    fleetTrim(FLEET_SET);
  }
  if (p.cfg && typeof p.cfg === 'object') Object.keys(p.cfg).forEach(function (id) {
    var d = p.cfg[id]; if (!hullInfo(id) || !d || typeof d !== 'object') return;
    var c = shipCfg(id);
    SHIP_KEYS.forEach(function (k) { if (k !== 'ballast') set(k, d[k], LIM[k], false, function (x) { c[k] = x; }); });
    var b = num(d.ballast, LIM.ballast, true);
    if (b !== undefined && typeof d.chk === 'number') PREF_BALLAST[id] = { v: b, chk: d.chk };   // 船型載好、checksum 對得上才套（cfgDefault）
  });
  set('gunhp', p.gunhp, LIM.gunhp, true, function (x) { GUN_HP = x; });
  set('sailhp', p.sailhp, LIM.sailhp, true, function (x) { SAIL_HP = x; });
  set('crewhp', p.crewhp, LIM.crewhp, true, function (x) { CREW_HP = x; });
  set('powderhp', p.powderhp, LIM.powderhp, true, function (x) { POWDER_HP = x; });
  set('blast', p.blast, LIM.blast, false, function (x) { BLAST_K = x; });
  set('blastv', p.blastv, LIM.blastv, false, function (x) { BLAST_V = x; });
  set('box', p.box, LIM.box, true, function (x) { BOX_N = x; });
  set('carry', p.carry, LIM.carry, true, function (x) { CARRY_N = x; });
  set('hands', p.hands, LIM.hands, true, function (x) { HANDS = x; });
  set('drown', p.drown, LIM.drown, true, function (x) { DROWN_T = x; });
  set('wind', p.wind, LIM.wind, false, function (x) { WIND_K = x; });
  if (!Q.has('play') && (p.play === 'fun' || p.play === 'real')) PLAY = p.play;
  set('stall', p.stall, LIM.stall, false, function (x) { STALL_K = x; });
  set('sea', p.sea, LIM.sea, false, function (x) { SEA_K = x; });
  if (!Q.has('weather') && WEATHERS[p.weather]) { WX_ID = p.weather; WX = WEATHERS[WX_ID]; }   // 天色在 71_input.js 開頭 setWeather 套
  set('funspeed', p.funspeed, LIM.funspeed, false, function (x) { FUN.speed = x; });
  set('funagile', p.funagile, LIM.funagile, false, function (x) { FUN.agile = x; });
  set('funstall', p.funstall, LIM.funstall, false, function (x) { FUN.stall = x; });
  set('funpowder', p.funpowder, LIM.funpowder, false, function (x) { FUN.powder = x; });
  if (p.dmg && typeof p.dmg === 'object') Object.keys(DMG_Q).forEach(function (t) { set(DMG_Q[t], p.dmg[t], LIM[DMG_Q[t]], true, function (x) { DMG[t] = x; }); });
  if (!Q.has('ammo') && Array.isArray(p.ammoK)) p.ammoK.forEach(function (r, i) {
    if (i < 3 && Array.isArray(r)) r.forEach(function (v, j) { var x = num(v, AMMO_LIM, true); if (j < 3 && x !== undefined) AMMO_K[i][j] = x; });
  });
  if (!Q.has('strike') && p.strike && typeof p.strike === 'object') {
    var cas = num(p.strike.cas, LIM.cas); if (cas !== undefined) STRIKE.cas = cas;
    ['guns', 'masts', 'officers'].forEach(function (k) { if (typeof p.strike[k] === 'boolean') STRIKE[k] = p.strike[k]; });
  }
  if (!Q.has('cap') && Array.isArray(p.cap)) p.cap.forEach(function (w, i) { if (i < 2 && (w === 'random' || Object.prototype.hasOwnProperty.call(CAPTAINS, w))) CAP_SET[i] = w; });
  var a = num(p.ammo, [0, AMMO.length - 1], true); if (a !== undefined) AMMO_I = a;
  var qx = Q.has('phx') || Q.has('phys') || PHX_ITEMS.some(function (it) { return Q.has('p_' + it.k); });   // 網址指定了物理 ⇒ 存檔的那份不套
  if (!qx && p.phx && typeof p.phx === 'object') PHX_ITEMS.forEach(function (it) { var x = num(p.phx[it.k], [0, it.opt.length - 1], true); if (x !== undefined) PHX[it.k] = x; });
  else if (!qx && p.phys === false) PHX.rig = 0;                     // 舊格式（只存了帆與繩的開關）
  PHYS = PHX.rig > 0;
  if (p.gfx && typeof p.gfx === 'object' && !Q.has('gfx')) GFX_ITEMS.forEach(function (it) { var x = num(p.gfx[it.k], [0, it.opt.length - 1], true); if (x !== undefined && !Q.has('g_' + it.k)) GFX[it.k] = x; });
  if (typeof p.fps === 'boolean') GFX_FPS = p.fps;
  if (typeof p.slow === 'boolean' && !Q.has('slowmo')) SLOW.on = p.slow;
  if (typeof p.slowcam === 'boolean' && !Q.has('slowcam')) SLOW.cam = p.slowcam;
  if (!Q.has('sail') && (p.sail === 'auto' || p.sail === 'manual' || p.sail === 'off')) SAIL = p.sail;
  if (p.mode === 'pve' || p.mode === 'eve' || p.mode === 'sandbox') MODE = p.mode;
  if (typeof p.auto === 'boolean') { AUTOFIRE = p.auto; LAST_MODE = MODE; }   // 存了自動開砲 ⇒ 開局不再照模式套預設（70_flow.js reset）
  if ([].some.call(document.querySelectorAll('#dists button'), function (b) { return +b.dataset.d === p.dist; })) DIST = p.dist;
}
function prefsSave() {
  if (!PREFS.write) return;
  var o = prefsSnap(), s = JSON.stringify(o);
  if (s === PREFS.last) return;
  try {
    if (Object.keys(o).length > 1) window.localStorage.setItem(PREFS_KEY, s); else window.localStorage.removeItem(PREFS_KEY);   // 全部是預設 ⇒ 不留一筆
    PREFS.last = s;
  } catch (e) { PREFS.write = false; PREFS.state = '存不了（' + (e && e.name || e) + '）'; }
}
/** 細節設定的「重設預設值」：那一頁回到預設之後馬上存（只剩主選單的選擇；全部是預設 ⇒ 刪掉那一筆），也忘掉存檔裡別的船的壓艙物。 */
function prefsReset() { PREF_BALLAST = {}; PREFS.last = ''; prefsSave(); }
(function prefsLoad() {
  if (!PREFS.read) { PREFS.state = DEMO >= 0 ? '?demo ⇒ 不讀不存' : '?prefs=0 ⇒ 不讀不存'; return; }
  var s;
  try { s = window.localStorage.getItem(PREFS_KEY); } catch (e) { PREFS.read = PREFS.write = false; PREFS.state = '存不了（這個頁面不能用 localStorage）⇒ 照預設'; return; }
  if (s === null) PREFS.state = '沒有存檔（照預設）';
  else {
    var p = null; try { p = JSON.parse(s); } catch (e) { p = null; }
    if (!p || typeof p !== 'object' || p.v !== PREFS_VER) PREFS.state = '存檔看不懂（' + (p && typeof p === 'object' ? '版本 ' + p.v : '壞掉的 JSON') + '）⇒ 照預設';
    else { prefsApply(p); PREFS.state = '套用了本機存檔（' + (Object.keys(p).length - 1) + ' 項）'; }
  }
  if (!PREFS.write) PREFS.state += '；網址帶了設定參數 ⇒ 這一場不存';
  PREFS.last = JSON.stringify(prefsSnap());              // 套用後的樣子 ⇒ 玩家動了才寫（看不懂的存檔不會因為打開一次就被蓋掉）
  // 主選單按鈕的亮燈照套用後的值（航行與帆的物理由 71_input.js 照變數點）
  [].forEach.call(document.querySelectorAll('#modes button'), function (b) { b.className = b.dataset.m === MODE ? 'on' : ''; });
  [].forEach.call(document.querySelectorAll('#dists button'), function (b) { b.className = +b.dataset.d === DIST ? 'on' : ''; });
  $('autoF').classList.toggle('on', AUTOFIRE);
  if (!PREFS.write) return;
  setInterval(prefsSave, 1000);
  window.addEventListener('pagehide', prefsSave);
  document.addEventListener('visibilitychange', function () { if (document.hidden) prefsSave(); });
})();
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/70_flow.js ──
// ───────────────────────── 開局 ─────────────────────────
function reset() {
  END_AT = 0; END_WAIT = null;
  rs = SEED; rsD = SEED ^ RSD0; rsW = SEED ^ RSW0; rsF = SEED ^ RSF0; rsC = SEED ^ RSC0; SH_STAT.cut = SH_STAT.tris = 0; FLOOD_LV = PHX.flood; WP_STAT.spray = WP_STAT.foam = 0; WP_STAT.src = {}; DEB_ACC = PT_ACC = 0; SIMT = 0; stepWind(0);   // 開局的風 ＝ 原本的風（08_weather.js）              // 碎木、水花、進水粒子的亂數，少生的節拍跟著重設（12_effects.js、13_water.js、33_flood.js）；進水模式在這裡定（戰鬥中改了下一場生效）
  SHIPS.forEach(function (sh) { sh.rs.dispose(); });
  PIECES.forEach(function (pc) { pc.rs.dispose(); });
  SHIPS = []; PIECES = []; BALLS = []; EVENTS = []; FLY = []; BOOMS = []; SELFB = []; BLASTS = []; D.n = 0; PT.n = 0; WS.n = WF.n = 0; SIMT = 0; OVER = false; PAUSED = false;   // 彈種（AMMO_I）重開時保留（Tim 2026-10-12）
  clearMsgs();
  SLOW.active = false; SLOW.ts = 1; SLOW.t = 0; SLOW.camSave = null; SLOW.kicks = 0;   // 殉爆的慢動作與特寫（73_slowmo.js）：⛔ 不清 ⇒ 殉爆、自爆後馬上重開，新的一局接著慢、幾秒後鏡頭被拉回上一局的爆心
  PLAYER_I = 0;
  spawnFleet(fleetSpec());                                           // 編隊（52_fleet.js）：一對一 ＝ 以前那兩艘、同一個位置；船型要先載好（loadHull）
  pickFoes();
  KEYS.l = KEYS.r = false;
  if (MODE !== LAST_MODE) { setAutoFire(MODE === 'eve'); LAST_MODE = MODE; }   // 自動開砲：換了模式才套預設（觀戰開、其他關），同一個模式重開保留（Tim 2026-10-12）
  SHIPS.forEach(function (sh) { stepShip(sh, 0); survey(sh); });
  pickCaptains();                                                    // 砲長（51_captain.js）
  CAM.mode = 0; CAM.follow = null; CAM.trMe = CAM.trYaw = null; CAM.dist = DIST * 1.05 + 40; CAM.tgt = [0, 8, 0]; CAM.yaw = 2.2; CAM.pitch = 0.22; CAM.snap = true;
  if (!CAMQ) { CAM.mode = 4; CAM.aoff = 0.35; CAM.dist = 78; CAM.pitch = 0.2; }   // 預設：我艦→敵艦（?cam= 給了 ⇒ 那個固定機位）
  if (CAMQ === 'close') { CAM.dist = 85; CAM.tgt = [10, 9, -DIST / 2 + 12]; CAM.yaw = 1.95; CAM.pitch = 0.16; }
  if (CAMQ === 'blue') { CAM.dist = 88; CAM.tgt = [4, 12, DIST / 2 - 10]; CAM.yaw = -1.8; CAM.pitch = 0.15; }
  if (CAMQ === 'deck') { CAM.mode = 4; CAM.aoff = +(Q.get('aoff') || 0.3); CAM.dist = +(Q.get('dist') || 56); CAM.pitch = +(Q.get('pitch') || 0.3); }   // 縮圖：跟著我艦、近一點高一點 ⇒ 看得到甲板上的人
  if (CAMQ === 'high') { CAM.dist = DIST + 120; CAM.yaw = 2.5; CAM.pitch = 0.62; }
}

function start() {
  initAudio(); if (AC && AC.state === 'suspended') AC.resume();
  $('cover').style.display = 'none'; $('end').className = '';
  if (document.activeElement && document.activeElement.blur) document.activeElement.blur();   // 不然空白鍵會再按一次「開戰」
  reset(); RUNNING = true;
  note(SHIPS[PLAYER_I], AUTOFIRE ? '自動開砲中（G 關掉就自己打）' : '點敵艦設瞄準點，空白鍵齊射（G 自動開砲）');
  if (WX.aim) note(SHIPS[PLAYER_I], '暴風雨：浪大、風強 —— 船晃得越兇砲越散，舵也難使');
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/71_input.js ──
// ───────────────────────── 輸入 ─────────────────────────
var drag = null, PTRS = new Map(), PINCH = null;          // PTRS：按著的指頭（觸控）；兩指（PINCH）⇒ 張合 ＝ 縮放、一起拖 ＝ 平移（同右鍵拖曳；Tim 2026-10-13），不轉鏡頭也不瞄準
function pinchD() { var a = Array.from(PTRS.values()); return Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y) || 1; }
function pinchM() { var a = Array.from(PTRS.values()); return { x: (a[0].x + a[1].x) / 2, y: (a[0].y + a[1].y) / 2 }; }
/** 平移（右鍵拖曳、兩指拖曳）：換成自由鏡頭，從現在看的那一點開始移。dx／dy ＝ 螢幕像素。 */
function panBy(dx, dy) {
  if (CAM.mode === 1) CAM.mode = 0;
  if (CAM.mode > 1) { CAM.tgt = CAM.look.slice(); CAM.mode = 0; }      // 從跟著船的鏡頭換成自由鏡頭
  var fw = norm([CAM.look[0] - CAM.eye[0], 0, CAM.look[2] - CAM.eye[2]]), rt = [-fw[2], 0, fw[0]], k = CAM.dist * 0.0018;
  CAM.tgt = add(CAM.tgt, add(mul(rt, -dx * k), mul(fw, dy * k)));
}
cv.addEventListener('contextmenu', function (e) { e.preventDefault(); });
document.addEventListener('contextmenu', function (e) { if (!/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) e.preventDefault(); });   // 面板、按鈕、說明上長按也不跳選單（輸入框照常）
cv.addEventListener('pointerdown', function (e) {
  cv.setPointerCapture(e.pointerId); PTRS.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (PTRS.size === 2) { var m0 = pinchM(); PINCH = { d: pinchD(), dist: CAM.dist, x0: m0.x, y0: m0.y, mx: m0.x, my: m0.y, moved: false }; drag = null; return; }
  if (PTRS.size > 2) return;
  drag = { x: e.clientX, y: e.clientY, b: e.button, moved: false };
});
cv.addEventListener('pointermove', function (e) {
  if (PTRS.has(e.pointerId)) PTRS.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (PINCH && PTRS.size === 2) {
    CAM.dist = clamp(PINCH.dist * PINCH.d / pinchD(), 12, 900);
    var m = pinchM();                                                  // 兩指中點移了 8 px 以上才開始平移（⛔ 不設門檻 ⇒ 只是張合時手指晃一下畫面也跟著跑）
    if (!PINCH.moved && Math.hypot(m.x - PINCH.x0, m.y - PINCH.y0) < 8) return;
    PINCH.moved = true; panBy(m.x - PINCH.mx, m.y - PINCH.my); PINCH.mx = m.x; PINCH.my = m.y;
    return;
  }
  if (!drag) return;
  var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if (!drag.moved && Math.hypot(dx, dy) < 5) return;
  drag.moved = true; drag.x = e.clientX; drag.y = e.clientY;
  if (drag.b === 2) panBy(dx, dy);
  else { if (CAM.mode === 1) CAM.mode = 0; if (CAM.mode === 4) CAM.aoff += dx * 0.006; else CAM.yaw += dx * 0.006; CAM.pitch = clamp(CAM.pitch + dy * 0.005, 0.02, 1.45); }
});
function ptrEnd(e) { PTRS.delete(e.pointerId); if (PTRS.size < 2) PINCH = null; }
cv.addEventListener('pointerup', function (e) {
  if (drag && !drag.moved && drag.b === 0 && RUNNING && !PINCH) pick(e.clientX, e.clientY);
  drag = null; ptrEnd(e);
});
cv.addEventListener('pointercancel', function (e) { drag = null; ptrEnd(e); });
cv.addEventListener('wheel', function (e) { e.preventDefault(); CAM.dist = clamp(CAM.dist * Math.pow(1.0015, e.deltaY), 12, 900); }, { passive: false });
function pick(cx, cy) {
  var r = cv.getBoundingClientRect(), nx = (cx - r.left) / r.width * 2 - 1, ny = 1 - (cy - r.top) / r.height * 2;
  var a = M4.pt(CAM.inv, nx, ny, -1), bq = CAM.inv, w0 = bq[3] * nx + bq[7] * ny + bq[11] * -1 + bq[15], w1 = bq[3] * nx + bq[7] * ny + bq[11] + bq[15];
  var p0 = mul(M4.pt(CAM.inv, nx, ny, -1), 1 / w0), p1 = mul(M4.pt(CAM.inv, nx, ny, 1), 1 / w1), d = norm(sub(p1, p0));
  var me = SHIPS[PLAYER_I], hit = null, on = null;                   // 每艘敵船都射一次，取最近的那一個（t：沿射線多遠；每艘的公尺／格一樣）
  SHIPS.forEach(function (foe) {
    if (!isFoe(me, foe)) return;
    var oL = toLocal(foe, p0), dL = M4.dir(foe.inv, d[0], d[1], d[2]), h = VK.raycast(foe.grid, oL, dL, 3000);
    if (h && (!hit || h.t < hit.t)) { hit = h; on = foe; }
  });
  if (hit) { setAim(me, [hit.x + 0.5, hit.y + 0.5, hit.z + 0.5], on); me.pMode = AIM_P = 'free'; sfx('crack', null, 0.08); }   // 點了哪艘 ⇒ 那艘變成我的目標（52_fleet.js pickFoes）   // 點了 ⇒ 瞄準模式回到自由
}
window.addEventListener('keydown', function (e) {
  if (!RUNNING) return;
  var k = e.key.toLowerCase(); if (e.code === 'Space') k = ' ';
  if (k === 'escape') { e.preventDefault(); if (HELP.open) helpClose(); else if (FLX) floodClose(); else if (FLX3) xrayToggle(); else gsetToggle(); return; }   // 遊戲內的設定面板
  if (k === ' ' || k === 'tab' || k === 'a' || k === 'd' || k === 'w' || k === 's' || k.indexOf('arrow') === 0) e.preventDefault();
  doKey(k, e.repeat);
});
/** 一個鍵的動作（鍵盤與畫面上的按鈕共用 ⇒ 手機也能玩）。打舵（A／D）是「按住」：這裡只按下，放開走 keyUp。 */
function doKey(k, repeat) {
  if (!RUNNING) return;
  var me = SHIPS[PLAYER_I];
  if (k === ' ') { if (!PAUSED && !me.sunk) broadside(me, AMMO_I); }   // 降旗了 ⇒ broadside／fireOne 自己擋
  else if (k === 'f') { if (!PAUSED) fireOne(me, AMMO_I); }
  else if (k === '1' || k === '2' || k === '3') AMMO_I = +k - 1;
  else if (k === 'q') { me.pMode = AIM_P = AIM_CYCLE[(AIM_CYCLE.indexOf(me.pMode || 'free') + 1) % AIM_CYCLE.length]; note(me, '瞄準：' + AIM_NAME[me.pMode] + (me.pMode === 'free' ? '（點敵艦設瞄準點）' : '')); }   // 瞄準模式（51_captain.js）
  else if (k === 'c') { CAM.mode = CAM_ORDER[(CAM_ORDER.indexOf(CAM.mode) + 1) % CAM_ORDER.length]; CAM.follow = null; if (CAM.mode === 2 || CAM.mode === 3) { CAM.dist = 75; } else if (CAM.mode === 0) CAM.dist = DIST + 40; else if (CAM.mode === 4) { CAM.dist = 78; CAM.aoff = 0.35; } }
  else if (k === 'p') { PAUSED = !PAUSED; frzShow(); }                               // 停格（72_floodui.js：停格時上方一條、進水細節頁）
  else if (k === 'i') { if (PAUSED) floodToggle(); }                 // 停格時：進水圖表／透視（72_floodui.js）
  else if (k === 'x') xrayToggle();
  else if (k === 'z') cutToggle();                                    // 停格時：剖面、隱藏甲板（74_cutaway.js）
  else if (k === 'l') deckCycle();
  else if (k === 'm') { muted = !muted; gsetShow(); }
  else if (k === 'h' || k === '?') helpToggle();
  else if (k === 'r') { gsetClose(); helpClose(); RUNNING = false; END_AT = 0; END_WAIT = null; $('cover').style.display = ''; $('end').className = ''; }
  else if (k === 'tab') {                                           // 航行：自動 → 手動 → 停船 → 自動（觀戰沒有手動）
    var order = ['auto', 'manual', 'off'];
    setSailMode(order[(order.indexOf(SAIL) + 1) % order.length]);
  }
  else if (k === 'a' || k === 'd' || k === 'arrowleft' || k === 'arrowright') {   // 打舵：自動或停船中一碰就換手動
    if (SAIL !== 'manual') setSailMode('manual'); KEYS[k === 'a' || k === 'arrowleft' ? 'l' : 'r'] = true;
  }
  else if (k === 'v') setCamTrack(!CAM.track);
  else if (k === 'g') setAutoFire(!AUTOFIRE);
  else if (k === 'b') setPhys(!PHYS);
  else if (k === 'n') { gsetClose(); helpClose(); start(); }                                        // 重新開始：同樣的模式、距離、滑桿，不用打完
  else if (k === 'w' || k === 's' || k === 'arrowup' || k === 'arrowdown') {     // 帆裝
    if (!repeat) setSails(me, me.sailSet + (k === 'w' || k === 'arrowup' ? 1 : -1));
  }
}
function keyUp(k) { if (k === 'a' || k === 'arrowleft') KEYS.l = false; if (k === 'd' || k === 'arrowright') KEYS.r = false; }
window.addEventListener('keyup', function (e) { keyUp(e.key.toLowerCase()); });
window.addEventListener('blur', function () { KEYS.l = KEYS.r = false; });
// 畫面上的按鍵提示（下方控制列 .kb、說明裡的 kbd[data-k]）：點 ＝ 按那個鍵；data-hold 的（打舵）按住才算
[].forEach.call(document.querySelectorAll('[data-k]'), function (b) {
  var k = b.dataset.k;
  if (b.dataset.hold) {
    b.addEventListener('pointerdown', function (e) { e.preventDefault(); b.classList.add('down'); doKey(k, false); try { b.setPointerCapture(e.pointerId); } catch (x) { } });   // 手指滑出按鈕也算按著，放開才鬆舵
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(function (ev) { b.addEventListener(ev, function () { b.classList.remove('down'); keyUp(k); }); });
  } else b.addEventListener('click', function (e) { e.preventDefault(); doKey(k, false); });
});
/** 航行模式（選單與遊戲中同一個）：auto 兩艘自動、manual 我艦手動、off 兩艘停船。 */
var SAIL_NAMES = { auto: '自動航行', manual: '手動操舵（A／D 打舵）', off: '停船' };
function setSailMode(m) {
  SAIL = m; KEYS.l = KEYS.r = false;
  [].forEach.call(document.querySelectorAll('[data-s]'), function (x) { x.classList.toggle('on', x.dataset.s === SAIL); });
  if (RUNNING && SHIPS.length) note(SHIPS[PLAYER_I], SAIL_NAMES[m] + '（Tab 切換）');
}
/** 自由鏡頭跟不跟著兩艘的中點走（預設跟；鏡頭「看敵艦／看我艦」本來就跟著那一艘）。 */
function setCamTrack(on) {
  CAM.track = on; CAM.trMe = CAM.trYaw = null;
  $('camT').classList.toggle('on', on);
  if (RUNNING && SHIPS.length) note(SHIPS[PLAYER_I], on ? '鏡頭跟著船' : '鏡頭固定（V 切換）');
}
/** 自動開砲（我艦）：觀戰預設開、其他模式預設關（reset 時照模式設）。 */
function setAutoFire(on) {
  AUTOFIRE = on; $('autoF').classList.toggle('on', on);
  if (RUNNING && SHIPS.length) note(SHIPS[PLAYER_I], on ? '自動開砲' : '自己開砲（點敵艦瞄準、空白鍵齊射）');
}
[].forEach.call(document.querySelectorAll('#hudctl [data-s]'), function (b) { b.onclick = function () { setSailMode(b.dataset.s); }; });
$('autoF').onclick = function () { setAutoFire(!AUTOFIRE); };
$('camT').onclick = function () { setCamTrack(!CAM.track); };
$('physT').onclick = function () { setPhys(!PHYS); };
$('restartB').onclick = function () { if (RUNNING) { gsetClose(); helpClose(); start(); } };
$('boomB').onclick = function () { if (selfDestruct()) { gsetClose(); helpClose(); PAUSED = false; } };   // 自爆：關掉設定、解除停格，看煙花（23_powder.js）
// 遊戲內的設定面板（⚙ 設定、Esc）：打開 ⇒ 暫停（關掉回到打開之前的暫停狀態）；畫質、物理效果的檔位跟主選單是同一份（07_gfx.js／09_phx.js）
var GSET = { open: false, paused: false };
function gsetOpen() { if (!RUNNING || GSET.open) return; helpClose(); GSET.open = true; GSET.paused = PAUSED; PAUSED = true; $('gset').classList.add('on'); $('gsetBg').classList.add('on'); gsetShow(); }
function gsetClose() { if (!GSET.open) return; GSET.open = false; PAUSED = GSET.paused; $('gset').classList.remove('on'); $('gsetBg').classList.remove('on'); }
function gsetToggle() { if (GSET.open) gsetClose(); else gsetOpen(); }
function gsetShow() {
  var gl = gfxLevel(), xl = phxLevel();
  [].forEach.call(document.querySelectorAll('#gset [data-gg]'), function (b) { b.classList.toggle('on', b.dataset.gg === gl); });
  [].forEach.call(document.querySelectorAll('#gset [data-gx]'), function (b) { b.classList.toggle('on', b.dataset.gx === xl); });
  $('gsGfx').textContent = gl === 'custom' ? '（自訂）' : ''; $('gsPhx').textContent = xl === 'custom' ? '（自訂）' : '';
  $('muteT').classList.toggle('on', muted); $('fpsT').classList.toggle('on', GFX_FPS);
  $('slowT').classList.toggle('on', SLOW.on); $('slowCamT').classList.toggle('on', SLOW.cam); $('boomB').classList.toggle('dis', !canSelfDestruct());
  $('fullT').classList.toggle('on', fsOn()); $('fullT').classList.toggle('dis', !fsCan()); $('gsFull').textContent = fsCan() ? '' : '（這裡不給全螢幕：iPhone 的 Safari 只給影片）';
}
$('setB').onclick = gsetToggle;
// 說明（設定裡的「H 說明」、H、?）：打開 ⇒ 暫停（關掉回到打開之前的暫停狀態，跟設定一樣）；外面蓋一層 #helpBg，點外面、✕、H、Esc 都關（Tim 2026-10-13：手機上不好關說明）
var HELP = { open: false, paused: false };
function helpOpen() { if (!RUNNING || HELP.open) return; gsetClose(); HELP.open = true; HELP.paused = PAUSED; PAUSED = true; $('help').classList.add('on'); $('helpBg').classList.add('on'); }
function helpClose() { if (!HELP.open) return; HELP.open = false; PAUSED = HELP.paused; $('help').classList.remove('on'); $('helpBg').classList.remove('on'); }
function helpToggle() { if (HELP.open) helpClose(); else helpOpen(); }
$('helpBg').onclick = helpClose; $('helpX').onclick = helpClose; $('helpB').onclick = helpOpen;
$('gsetBg').onclick = gsetClose;                                    // 面板外點一下 ⇒ 關（不會順便瞄準、開砲：底下的東西被這一層蓋住）
$('gsGo').onclick = gsetClose;
$('menuB').onclick = function () { doKey('r'); };
$('muteT').onclick = function () { muted = !muted; gsetShow(); };
$('fpsT').onclick = function () { GFX_FPS = !GFX_FPS; gfxShow(); };
// 全螢幕（設定面板的「F11 全螢幕」；Tim 2026-10-13：主要給手機用）：整頁（documentElement）進出全螢幕；畫布大小每一格照量（60_render.js resize）⇒ 不用另外處理。
//   畫廊彈窗的 iframe（sandbox＋allow="fullscreen"，ArtGallery/index.html）進得去（量過：fullscreenEnabled、點了 fs ＝ true、按鈕亮）。
//   不給全螢幕的地方（iPhone 的 Safari 只給影片、沒開 fullscreen 權限的 iframe）⇒ 按鈕變灰、寫原因。Esc 是瀏覽器自己退出全螢幕的鍵（頁面收不到那一下）。
//   「F11」只是提示電腦上按 F11 也能全螢幕（Tim：只是提示）—— 那是瀏覽器自己的全螢幕，頁面不攔（⛔ 攔了要猜瀏覽器的全螢幕開了沒：拿視窗跟螢幕比大小，縮放與無頭 Chrome 都會猜錯）。
//   不存檔：進全螢幕一定要使用者點一下才行，開局自動進不去。
function fsOn() { return !!(document.fullscreenElement || document.webkitFullscreenElement); }
function fsCan() { return !!(document.fullscreenEnabled || document.webkitFullscreenEnabled); }
function fsToggle() {
  if (!fsCan()) return;
  var d = document, e = d.documentElement;
  try {
    var r = fsOn() ? (d.exitFullscreen || d.webkitExitFullscreen).call(d) : (e.requestFullscreen || e.webkitRequestFullscreen).call(e, { navigationUI: 'hide' });
    if (r && r.catch) r.catch(function () { gsetShow(); });                          // 被拒（沒有點擊、權限）⇒ 按鈕照實際狀態
  } catch (err) { gsetShow(); }
}
$('fullT').onclick = fsToggle;
['fullscreenchange', 'webkitfullscreenchange'].forEach(function (ev) { document.addEventListener(ev, gsetShow); });   // 進出（含 Esc 退出）⇒ 按鈕跟著亮滅
[].forEach.call(document.querySelectorAll('#gset [data-gg]'), function (b) { b.onclick = function () { gfxSet(b.dataset.gg); gfxShow(); }; });
[].forEach.call(document.querySelectorAll('#gset [data-gx]'), function (b) { b.onclick = function () { phxSet(b.dataset.gx); phxSync(); }; });
$('endA').onclick = start;
[].forEach.call(document.querySelectorAll('#ammo span'), function (s) { s.onclick = function () { AMMO_I = +s.dataset.a; }; });
[].forEach.call(document.querySelectorAll('#modes button'), function (b) { b.onclick = function () { MODE = b.dataset.m; [].forEach.call(document.querySelectorAll('#modes button'), function (x) { x.className = x === b ? 'on' : ''; }); }; });
/** 選單：滑桿的上下限從 LIM 來；數值只在使用者動了那一條時才從滑桿讀回（⛔ 一開頭就讀回 ⇒ 網址給的 0.33 被 step 吃成 0.35）。
 *  船殼、砲、帆、火藥桶、航行、降旗的滑桿在「細節設定」那一頁（從主選單進）；主選單只留一行摘要（#detV）。 */
/** 模型（砲、火藥桶）的總重（噸）：照匯出的模型清單＋取用點的 12 桶（細節設定的例子用；開戰時每艘照自己的模型算）。 */
function modelMassT(T, gunw) { if (!T) return 0; var t = 12 * KEG_T; (T.rig.models || []).forEach(function (m) { t += modelT({ kind: modelKind(m) }, gunw); }); return t; }
var CFG_ID = myHull();                             // 細節設定的「船隻設定」正在編輯哪一型
var SLIDERS_SHOW = null;                               // 載入完（HYD 算好）再顯示一次 ⇒ 減重上浮的例子有數字
function sliders() {
  var lf = $('ballast'), f = $('flood'), h = $('hard'), c = $('cas'), sp = $('speed'), ag = $('agile'), uw = $('upwind'), gh = $('gunhp'), gw = $('gunw'), sl = $('sailhp'), ph = $('powderhp'), bl = $('blast'), bv = $('blastv'), ch = $('crewhp');
  var dm = { long: $('dmg24'), long32: $('dmg32l'), carr: $('dmg32'), chase: $('dmg18'), long4: $('dmg4') }, DLIM = { long: LIM.dmg24, long32: LIM.dmg32l, carr: LIM.dmg32, chase: LIM.dmg18, long4: LIM.dmg4 }, bx = $('box'), cy = $('carry'), wk = $('wind'), hd = $('hands'), dr = $('drown');
  var st = $('stall'), fs = $('funspeed'), fa = $('funagile'), fl = $('funstall'), fp = $('funpowder'), se = $('sea');   // 頂風失速、娛樂加成、浪
  [[se, 'sea'], [st, 'stall'], [fs, 'funspeed'], [fa, 'funagile'], [fl, 'funstall'], [fp, 'funpowder']].forEach(function (e) { e[0].min = LIM[e[1]][0]; e[0].max = LIM[e[1]][1]; });
  hd.min = LIM.hands[0]; hd.max = LIM.hands[1]; dr.min = LIM.drown[0]; dr.max = LIM.drown[1];
  bx.min = LIM.box[0]; bx.max = LIM.box[1]; cy.min = LIM.carry[0]; cy.max = LIM.carry[1]; wk.min = LIM.wind[0]; wk.max = LIM.wind[1];
  // 硬度跨 40 倍 ⇒ 對數刻度：滑桿 0..1 ↔ 硬度 LIM 下限 × (上限／下限)^v
  var hk = Math.log(LIM.hard[1] / LIM.hard[0]);
  lf.min = LIM.ballast[0]; lf.max = LIM.ballast[1]; gw.min = LIM.gunw[0]; gw.max = LIM.gunw[1];
  f.min = LIM.flood[0]; f.max = LIM.flood[1]; h.min = 0; h.max = 1; h.step = 0.005; c.min = LIM.cas[0] * 100; c.max = LIM.cas[1] * 100;
  sp.min = LIM.speed[0]; sp.max = LIM.speed[1]; ag.min = LIM.agile[0]; ag.max = LIM.agile[1]; uw.min = LIM.upwind[0]; uw.max = LIM.upwind[1];
  gh.min = LIM.gunhp[0]; gh.max = LIM.gunhp[1]; sl.min = LIM.sailhp[0]; sl.max = LIM.sailhp[1]; ph.min = LIM.powderhp[0]; ph.max = LIM.powderhp[1];
  bl.min = LIM.blast[0]; bl.max = LIM.blast[1]; bv.min = LIM.blastv[0] * 100; bv.max = LIM.blastv[1] * 100; ch.min = LIM.crewhp[0]; ch.max = LIM.crewhp[1];
  for (var t in dm) { dm[t].min = DLIM[t][0]; dm[t].max = DLIM[t][1]; }
  function am(r, k) { return $('am-' + r + '-' + k); }
  function C() { return shipCfg(CFG_ID); }             // 正在編輯的那一型（船隻設定）
  function put() {                                     // 變數 ⇒ 滑桿位置（開頭、重設預設值、換編輯的船時）
    var k = C(); $('cfgShip').value = CFG_ID;
    lf.value = k.ballast !== undefined ? k.ballast : LIM.ballast[2]; f.value = k.flood; h.value = Math.log(k.hard / LIM.hard[0]) / hk; c.value = STRIKE.cas * 100; sp.value = k.speed; ag.value = k.agile; uw.value = k.upwind;
    gh.value = GUN_HP; gw.value = k.gunw; sl.value = SAIL_HP; ph.value = POWDER_HP; bl.value = BLAST_K; bv.value = Math.round(BLAST_V * 100); ch.value = CREW_HP;
    for (var t in dm) dm[t].value = DMG[t];
    bx.value = BOX_N; cy.value = CARRY_N; wk.value = WIND_K; hd.value = HANDS; dr.value = DROWN_T;
    se.value = SEA_K; st.value = STALL_K; fs.value = FUN.speed; fa.value = FUN.agile; fl.value = FUN.stall; fp.value = FUN.powder;
    for (var r = 0; r < 3; r++) for (var k = 0; k < 3; k++) am(r, k).value = AMMO_K[r][k];
    ['guns', 'masts', 'officers'].forEach(function (k) { $('st-' + k).checked = STRIKE[k]; });
    [0, 1].forEach(function (i) { $('cap' + i).value = CAP_SET[i]; });
  }
  function show() {
    var K = C(), SPEEDK = K.speed, AGILK = K.agile, FLOOD = K.flood, HARDK = K.hard, GUNW_K = K.gunw, BALLAST_T = K.ballast !== undefined ? K.ballast : LIM.ballast[2];   // 正在編輯的那一型
    var fun = PLAY === 'fun' ? '（娛樂：' : '（', SPE = SPEEDK * playK('speed'), AGE = AGILK * playK('agile');   // 娛樂 ⇒ 括號裡寫乘過加成的實際值
    $('speedV').textContent = SPEEDK.toFixed(2) + '×' + fun + '最快約 ' + (VMAX * SPE * 1.944).toFixed(0) + ' 節）';
    $('agileV').textContent = AGILK.toFixed(2) + '×' + fun + '滿帆側風約 ' + ((0.012 + 0.016 * VMAX * 0.92) * AGE * 57.3).toFixed(1) + '°/秒）';
    var UPK = K.upwind; $('upwindV').textContent = UPK.toFixed(2) + '×（' + (UPK === 1 ? '照舊：' : '') + '風從船頭 ' + (90 - (90 - NOGO_DEG) * UPK).toFixed(0) + '° 開始失速、' + (90 - (90 - NOGO_FULL) * UPK).toFixed(0) + '° 全失速（手動操舵）；近迎風轉向最多 ×' + UPK.toFixed(2) + '）';
    var SK = STALL_K * playK('stall'), WA = WAVES.reduce(function (a, w) { return a + w.a; }, 0) * SEA_K;   // WA：幾道浪疊在一起最高的那一下（振幅）
    $('seaV').textContent = SEA_K <= 0 ? '0（平靜）' : SEA_K.toFixed(2) + '×（浪高最多約 ' + (WA * 2).toFixed(1) + ' m，主浪週期 ' + (2 * Math.PI / WAVES[0].w).toFixed(1) + ' 秒）';
    $('stallV').textContent = Math.round(STALL_K * 100) + '%' + (PLAY === 'fun' ? '（娛樂：實際 ' + Math.round(SK * 100) + '%）' : '') + (SK <= 0 ? '（不會失速）' : SK >= 0.95 ? '（寫實）' : '');
    $('funspeedV').textContent = FUN.speed.toFixed(2) + '×'; $('funagileV').textContent = FUN.agile.toFixed(2) + '×'; $('funstallV').textContent = FUN.stall.toFixed(2) + '×';
    $('funpowderV').textContent = FUN.powder.toFixed(2) + '×' + (powderNever() ? '（火藥拉滿：不會爆）' : '（火藥血量 ' + POWDER_HP + ' ⇒ ' + Math.round(POWDER_HP * FUN.powder) + '）');
    $('floodV').textContent = FLOOD === 0 ? '0×（不會沉）' : FLOOD.toFixed(2) + '×' + (FLOOD < 0.5 ? '（慢）' : FLOOD < 1.2 ? '' : '（快）');
    var HT = HULLT[CFG_ID], m0 = (HT ? HT.base.count * VOX_T : 0) + modelMassT(HT, GUNW_K) + BALLAST_T, l0 = liftFor(HT, HT ? HT.disp - m0 : 0), lx = liftFor(HT, HT ? HT.disp - m0 + 70 : 0);   // 照我艦的船型   // 開戰時浮在哪；例子：再打掉 10 萬格（70 噸）
    var gm = 0, kinds = {}; if (HT) (HT.rig.models || []).forEach(function (m) { var k = modelKind(m); if (GUNS[k]) { gm += GUNS[k].mass * GUNW_K; kinds[k] = 1; } });
    $('gunwV').textContent = GUNW_K.toFixed(2) + '×（' + Object.keys(GUNS).filter(function (k) { return !HT || kinds[k]; }).map(function (k) { return GUNS[k].name + ' ' + (GUNS[k].mass * GUNW_K).toFixed(1) + ' 噸'; }).join('、') + (gm ? '；全部 ' + Math.round(gm) + ' 噸' : '') + '）';
    $('ballastV').textContent = BALLAST_T + ' 噸' + (l0 === null ? '' : '（' + HT.name + ' ' + Math.round(m0).toLocaleString() + ' 噸 ⇒ ' + (Math.abs(l0) < 0.05 ? '剛好在設計水線' : l0 > 0 ? '浮高 ' + l0.toFixed(1) + ' m' : '吃水深 ' + (-l0).toFixed(1) + ' m') + '；打掉 10 萬格再浮 ' + (lx - l0).toFixed(2) + ' m）');
    $('hardV').textContent = HARDK.toFixed(1) + '×' + (HARDK < 1 ? '（容易打穿）' : HARDK > 10 ? '（幾乎打不穿）' : HARDK > 3 ? '（很難打穿）' : '');
    function shots(hp, dmg) { return dmg > 0 ? Math.ceil(hp / dmg - 1e-9) : '∞'; }
    $('gunhpV').textContent = GUN_HP + '（24 磅實心 ' + shots(GUN_HP, DMG.long * ammoK(0, VS_GUN)) + ' 發、舵輪 ' + Math.round(GUN_HP * 0.6) + '）';
    $('sailhpV').textContent = SAIL_HP + '（24 磅鏈彈 ' + shots(SAIL_HP, DMG.long * ammoK(2, VS_SAIL)) + ' 發）';
    $('crewhpV').textContent = CREW_HP + (CREW_HP === LIM.crewhp[2] ? '' : CREW_HP > LIM.crewhp[2] ? '（耐打）' : '（脆）');
    $('powderhpV').textContent = powderNever() ? '拉滿（不會爆）' : POWDER_HP + (PLAY === 'fun' ? '（娛樂：實際 ' + powderHP() + '）' : '') + (powderHP() >= 600 ? '（很難殉爆，' : powderHP() >= 250 ? '（偶爾殉爆，' : '（很容易殉爆，') + '藥包 ' + Math.round(powderHP() * CART_K) + '）';   // 照實際的（娛樂乘過加成）；300 量過六艘一艘殉爆 ⇒ 偶爾
    $('blastV').textContent = BLAST_K.toFixed(2) + '×（前彈藥庫半徑約 ' + (MAG_R * Math.pow(BLAST_K, 1 / 3) * (S || 0.1)).toFixed(1) + ' m）';
    var r0 = MAG_R * Math.pow(BLAST_K * (1 - BLAST_V), 1 / 3) * (S || 0.1), r1 = MAG_R * Math.pow(BLAST_K * (1 + BLAST_V), 1 / 3) * (S || 0.1);
    $('blastvV').textContent = BLAST_V <= 0 ? '0（每次一樣）' : '±' + Math.round(BLAST_V * 100) + '%（前彈藥庫半徑 ' + r0.toFixed(1) + '～' + r1.toFixed(1) + ' m）';
    $('boxV').textContent = BOX_N + ' 份（開戰時裝滿）';
    $('drownV').textContent = DROWN_T ? '約 ' + DROWN_T + ' 秒（浮上水面、往自己的船游，爬回來當預備水手；受傷的減半）' : '0（關：落水當場算陣亡、淹到的跟著船沉）';
    $('handsV').textContent = HANDS ? '每艘 ' + HANDS + ' 人（在住艙甲板待命，缺人手時補位）' : '0（沒有：倒下的位子不補）';
    $('windV').textContent = WIND_K.toFixed(2) + '×（帆上的風約 ' + (WIND_SAIL * WIND_K).toFixed(0) + ' m/s，陣風 ±' + Math.round(GUST[0] * 100) + '%）';
    $('carryV').textContent = CARRY_N + ' 份' + (CARRY_N > BOX_N ? '（比藥箱多 ⇒ 一趟送好幾門）' : '');
    $('dmg24V').textContent = DMG.long; $('dmg32lV').textContent = DMG.long32; $('dmg32V').textContent = DMG.carr; $('dmg18V').textContent = DMG.chase; $('dmg4V').textContent = DMG.long4;
    $('casV').textContent = STRIKE.cas >= 1 ? '100%（全員倒下才停）' : Math.round(STRIKE.cas * 100) + '%';
    $('strikeV').textContent = strikeText();
    var amDef = AMMO_K.every(function (r, i) { return r.every(function (v, j) { return v === AMMO_K0[i][j]; }); });
    $('detV').textContent = '玩法 ' + (PLAY === 'fun' ? '娛樂（航速 ×' + FUN.speed.toFixed(2) + '、靈活 ×' + FUN.agile.toFixed(2) + '、頂風失速 ' + Math.round(SK * 100) + '%）' : '寫實（頂風失速 ' + Math.round(SK * 100) + '%）') + '・天氣 ' + WX.name + '・浪 ' + (SEA_K > 0 ? SEA_K.toFixed(2) + '×' : '平靜') + '・' + fleetHulls().map(function (id) { var c = shipCfg(id), hi = hullInfo(id); return (hi ? hi.name : id) + '：硬度 ' + c.hard.toFixed(1) + '×・進水 ' + c.flood.toFixed(2) + '×・壓艙物 ' + (c.ballast !== undefined ? c.ballast + ' 噸' : '（載入後）') + '・砲重 ' + c.gunw.toFixed(2) + '×・航速 ' + c.speed.toFixed(2) + '×・靈活 ' + c.agile.toFixed(2) + '×・逆風 ' + c.upwind.toFixed(2) + '×'; }).join('；') + '・血量 砲 ' + GUN_HP + '／帆 ' + SAIL_HP + '／船員 ' + CREW_HP +
      '・傷害 ' + DMG.long + '／' + DMG.long32 + '／' + DMG.carr + '／' + DMG.chase + '／' + DMG.long4 + (amDef ? '' : '・彈種倍率已改') + '・藥箱 ' + BOX_N + '、一次搬 ' + CARRY_N + '・預備水手 ' + HANDS + '・溺水 ' + (DROWN_T ? DROWN_T + ' 秒' : '關') +
      '・火藥桶 ' + (powderNever() ? '不會爆' : '血量 ' + powderHP() + '、殉爆 ' + BLAST_K.toFixed(2) + '×' + (BLAST_V > 0 ? ' ±' + Math.round(BLAST_V * 100) + '%' : '')) + '・砲長 ' + CAP_SET.map(function (k) { return CAPTAINS[k] ? CAPTAINS[k].name : '隨機'; }).join('／') + '・' + strikeText();
  }
  lf.oninput = function () { C().ballast = Math.round(+lf.value); show(); };
  f.oninput = function () { C().flood = +f.value; show(); };
  sp.oninput = function () { C().speed = +sp.value; show(); };
  ag.oninput = function () { C().agile = +ag.value; show(); };
  uw.oninput = function () { C().upwind = +uw.value; show(); };
  h.oninput = function () { C().hard = Math.round(LIM.hard[0] * Math.exp(h.value * hk) * 10) / 10; show(); };
  c.oninput = function () { STRIKE.cas = c.value / 100; show(); };
  gh.oninput = function () { GUN_HP = Math.round(+gh.value); show(); };
  gw.oninput = function () { C().gunw = +gw.value; show(); };
  sl.oninput = function () { SAIL_HP = Math.round(+sl.value); show(); };
  ph.oninput = function () { POWDER_HP = Math.round(+ph.value); show(); };
  bl.oninput = function () { BLAST_K = +bl.value; show(); };
  bv.oninput = function () { BLAST_V = Math.round(+bv.value) / 100; show(); };
  ch.oninput = function () { CREW_HP = Math.round(+ch.value); show(); };
  bx.oninput = function () { BOX_N = Math.round(+bx.value); show(); };
  cy.oninput = function () { CARRY_N = Math.round(+cy.value); show(); };
  hd.oninput = function () { HANDS = Math.round(+hd.value); show(); };
  dr.oninput = function () { DROWN_T = Math.round(+dr.value); show(); };
  st.oninput = function () { STALL_K = +st.value; show(); };
  se.oninput = function () { SEA_K = +se.value; show(); };
  fs.oninput = function () { FUN.speed = +fs.value; show(); }; fa.oninput = function () { FUN.agile = +fa.value; show(); }; fl.oninput = function () { FUN.stall = +fl.value; show(); }; fp.oninput = function () { FUN.powder = +fp.value; show(); };
  wk.oninput = function () { WIND_K = +wk.value; show(); };          // 物理是每一步讀 ⇒ 遊戲中也能調（只管畫面）
  Object.keys(dm).forEach(function (t) { dm[t].oninput = function () { DMG[t] = Math.round(+dm[t].value); show(); }; });
  for (var r = 0; r < 3; r++) for (var k = 0; k < 3; k++) (function (r, k) {
    var el = am(r, k);
    el.oninput = function () { var v = parseFloat(el.value); if (isFinite(v)) { AMMO_K[r][k] = clamp(Math.round(v), AMMO_LIM[0], AMMO_LIM[1]); show(); } };
    el.onchange = function () { el.value = AMMO_K[r][k]; };          // 打了界外或空白 ⇒ 回到夾過的值
  })(r, k);
  ['guns', 'masts', 'officers'].forEach(function (k) { var b = $('st-' + k); b.onchange = function () { STRIKE[k] = b.checked; show(); }; });
  [0, 1].forEach(function (i) { var s = $('cap' + i); capOptions(s, CAP_SET[i]); s.onchange = function () { CAP_SET[i] = s.value; show(); }; });   // 砲長
  var cs = $('cfgShip'); hullOptions(cs, CFG_ID);                // 船隻設定：編輯哪一型（選到還沒載的船 ⇒ 先載，壓艙物的預設要船型才算得出來）
  cs.onchange = function () { CFG_ID = cs.value; loadHull(CFG_ID).then(function () { put(); show(); }); put(); show(); };
  fleetUI();                                                     // 主選單：艦隊編成
  // 細節設定那一頁：主選單 ⇄ 細節設定（同一個 #cover 裡兩張卡片，一次顯示一張）
  function page(w) { $('detail').style.display = w === 'det' ? '' : 'none'; $('gfxp').style.display = w === 'gfx' ? '' : 'none'; $('phxp').style.display = w === 'phx' ? '' : 'none'; document.querySelector('#cover .card:not(#detail):not(#gfxp):not(#phxp)').style.display = w ? 'none' : ''; $('cover').scrollTop = 0; }   // w：'' 主選單、'det' 細節設定、'gfx' 畫質設定、'phx' 物理設定
  [].forEach.call(document.querySelectorAll('#plays button'), function (b) { b.onclick = function () { setPlay(b.dataset.p); show(); }; });   // 主選單：玩法
  $('detB').onclick = function () { page('det'); };
  $('detX').onclick = function () { page(''); };
  $('gfxB').onclick = function () { page('gfx'); };
  $('gfxX').onclick = function () { page(''); };
  $('phxB').onclick = function () { page('phx'); };
  $('phxX').onclick = function () { page(''); };
  gfxUI(); phxUI();
  $('detR').onclick = function () {                    // 重設預設值：LIM 的第三格、降旗全不勾
    SHIP_CFG = {}; Object.keys(HULLT).forEach(function (id) { var c = shipCfg(id); SHIP_KEYS.forEach(function (k) { c[k] = k === 'ballast' ? HULLT[id].ballast0 : cfgBase(k, id); }); });   // 每一型回到它的預設（壓艙物 ＝ 剛好在設計水線；航速、靈活照 HULL_CFG0）
    GUN_HP = LIM.gunhp[2]; SAIL_HP = LIM.sailhp[2]; POWDER_HP = LIM.powderhp[2]; BLAST_K = LIM.blast[2]; BLAST_V = LIM.blastv[2]; CREW_HP = LIM.crewhp[2];
    DMG.long = LIM.dmg24[2]; DMG.long32 = LIM.dmg32l[2]; DMG.carr = LIM.dmg32[2]; DMG.chase = LIM.dmg18[2]; DMG.long4 = LIM.dmg4[2]; BOX_N = LIM.box[2]; CARRY_N = LIM.carry[2]; WIND_K = LIM.wind[2]; HANDS = LIM.hands[2]; DROWN_T = LIM.drown[2];
    AMMO_K = AMMO_K0.map(function (r) { return r.slice(); });
    SEA_K = LIM.sea[2]; STALL_K = LIM.stall[2]; FUN.speed = LIM.funspeed[2]; FUN.agile = LIM.funagile[2]; FUN.stall = LIM.funstall[2]; FUN.powder = LIM.funpowder[2];
    STRIKE.cas = LIM.cas[2]; STRIKE.guns = STRIKE.masts = STRIKE.officers = false; CAP_SET = ['random', 'random'];
    put(); show(); prefsReset();                         // 存檔跟著清（69_prefs.js：只剩主選單的選擇）
  };
  window.addEventListener('keydown', function (e) { if (!RUNNING && e.key === 'Escape' && ($('detail').style.display !== 'none' || $('gfxp').style.display !== 'none' || $('phxp').style.display !== 'none')) page(''); });
  put(); show(); SLIDERS_SHOW = function () { put(); show(); };
}
/** 畫質（07_gfx.js）：主選單的低／中／高、畫質設定頁每一項的按鈕、顯示 FPS。改了立刻生效（render 每一格讀 GFX）。 */
function gfxUI() {
  var box = $('gfxItems');
  box.innerHTML = GFX_ITEMS.map(function (it) {
    return '<div class="row"><label>' + it.name + '</label>' + it.opt.map(function (o, v) { return '<button data-k="' + it.k + '" data-v="' + v + '">' + o + '</button>'; }).join('') + '</div>';
  }).join('');
  [].forEach.call(box.querySelectorAll('button'), function (b) { b.onclick = function () { GFX[b.dataset.k] = +b.dataset.v; gfxShow(); }; });
  [].forEach.call(document.querySelectorAll('#gfxs button[data-g], #gfxPre button'), function (b) { b.onclick = function () { gfxSet(b.dataset.g); gfxShow(); }; });
  var f = $('gfxFps'); f.checked = GFX_FPS; f.onchange = function () { GFX_FPS = f.checked; gfxShow(); };
  gfxShow();
}
function gfxShow() {
  var lv = gfxLevel();
  [].forEach.call(document.querySelectorAll('#gfxs button[data-g], #gfxPre button'), function (b) { b.className = b.dataset.g === lv ? 'on' : ''; });
  var gb = $('gfxB'); gb.textContent = lv === 'custom' ? '自訂（畫質設定…）' : '畫質設定…'; gb.className = lv === 'custom' ? 'on' : '';
  [].forEach.call(document.querySelectorAll('#gfxItems button'), function (b) { b.className = GFX[b.dataset.k] === +b.dataset.v ? 'on' : ''; });
  $('gfxLv').textContent = '現在：' + GFX_NAME[lv]; $('gfxFps').checked = GFX_FPS; $('fps').className = GFX_FPS ? 'hud on' : 'hud';
  if (typeof gsetShow === 'function') gsetShow();
}
/** 物理效果（09_phx.js）：主選單的全開／高／中／低、物理設定頁每一項的按鈕。帆與繩換到「關」或從「關」換出來 ⇒ setPhys（跟 B 鍵同一支）。 */
function phxUI() {
  var box = $('phxItems');
  box.innerHTML = PHX_ITEMS.map(function (it) {
    return '<div class="row"><label>' + it.name + '</label>' + it.opt.map(function (o, v) { return '<button data-k="' + it.k + '" data-v="' + v + '">' + o + '</button>'; }).join('') + '</div>';
  }).join('');
  [].forEach.call(box.querySelectorAll('button'), function (b) { b.onclick = function () { PHX[b.dataset.k] = +b.dataset.v; phxSync(); }; });
  [].forEach.call(document.querySelectorAll('#phxs button[data-x], #phxPre button'), function (b) { b.onclick = function () { phxSet(b.dataset.x); phxSync(); }; });
  phxShow();
}
function phxSync() { if ((PHX.rig > 0) !== PHYS) setPhys(PHX.rig > 0); phxShow(); }
function phxShow() {
  var lv = phxLevel();
  [].forEach.call(document.querySelectorAll('#phxs button[data-x], #phxPre button'), function (b) { b.className = b.dataset.x === lv ? 'on' : ''; });
  var pb = $('phxB'); pb.textContent = lv === 'custom' ? '自訂（物理設定…）' : '物理設定…'; pb.className = lv === 'custom' ? 'on' : '';
  [].forEach.call(document.querySelectorAll('#phxItems button'), function (b) { b.className = PHX[b.dataset.k] === +b.dataset.v ? 'on' : ''; });
  $('phxLv').textContent = '現在：' + PHX_NAME[lv];
  if (typeof gsetShow === 'function') gsetShow();
}
/** 玩法：娛樂／寫實（04_state.js 的 PLAY）＋主選單按鈕的亮燈。航行每一步都讀（playK）；按鈕在主選單，沒開戰時才按得到。 */
function setPlay(p) { PLAY = p === 'real' ? 'real' : 'fun'; [].forEach.call(document.querySelectorAll('#plays button'), function (x) { x.className = x.dataset.p === PLAY ? 'on' : ''; }); }
/** 選單列船：HULL_LIST 的每一艘。 */
function hullOptions(sel, v) { sel.innerHTML = HULL_LIST.map(function (h) { return '<option value="' + h.id + '">' + h.name + '</option>'; }).join(''); sel.value = v; }
/** 主選單的艦隊編成（TASK-0537）：我方、敵方各一列，每艘一個選單；第二艘起有 ×（拿掉）；＋ 加一艘（照那一邊最後一艘的船型），合計到 MAX_SHIPS 就停用。
 *  我方第一艘 ＝ 我艦。改了就重建這兩列。 */
function fleetUI() {
  var full = FLEET_SET[0].length + FLEET_SET[1].length >= MAX_SHIPS;
  [0, 1].forEach(function (s) {
    var box = $('fleet' + s), L = FLEET_SET[s];
    box.innerHTML = L.map(function (id, j) {
      var lab = s === 0 ? (j ? '友艦 ' + j : '我艦') : '敵艦 ' + (j + 1);
      return '<span class="fs"><select data-s="' + s + '" data-j="' + j + '" aria-label="' + lab + '的船" title="' + lab + '"></select>' + (j ? '<button class="fx" data-s="' + s + '" data-j="' + j + '" aria-label="拿掉' + lab + '">×</button>' : '') + '</span>';
    }).join('') + '<button class="fa" data-s="' + s + '" aria-label="' + (s ? '加一艘敵艦' : '加一艘友艦') + '"' + (full ? ' disabled' : '') + '>＋</button>';
    [].forEach.call(box.querySelectorAll('select'), function (el) { hullOptions(el, L[+el.dataset.j]); el.onchange = function () { pickShip(s, +el.dataset.j, el.value); }; });
    [].forEach.call(box.querySelectorAll('button.fx'), function (b) { b.onclick = function () { L.splice(+b.dataset.j, 1); fleetUI(); pickShip(); }; });
    box.querySelector('button.fa').onclick = function () { if (FLEET_SET[0].length + FLEET_SET[1].length < MAX_SHIPS) { L.push(L[L.length - 1]); fleetUI(); pickShip(); } };
  });
  $('fleetN').textContent = FLEET_SET[0].length + ' 對 ' + FLEET_SET[1].length + (full ? '（上限 ' + MAX_SHIPS + ' 艘）' : '');
}
/** 主選單換船（s 那一邊第 j 艘換成 id；不給 ⇒ 只是艘數變了）：還沒載的先載（開戰鈕暫時停用），載好就把背景的船換掉；細節設定跟著編輯我艦那一型。 */
function pickShip(s, j, id) {
  if (id) { FLEET_SET[s][j] = id; if (s === 0 && j === 0) CFG_ID = id; }
  var need = fleetHulls().filter(function (h) { return !HULLT[h]; });
  var go = $('go'); go.disabled = true; go.textContent = need.length ? '載入' + hullInfo(need[0]).name + '…' : '編隊中…';
  Promise.all(fleetHulls().map(loadHull)).then(function () {
    if (fleetHulls().some(function (h) { return !HULLT[h]; })) return;     // 又換了一艘、還在載
    go.disabled = false; go.textContent = '開戰';
    if (!RUNNING) reset();                                                  // 選單後面的兩艘換成選到的船
    if (SLIDERS_SHOW) SLIDERS_SHOW();
  }).catch(function (e) { go.textContent = '載不了：' + (e && e.message || e); console.error(e); });
}
sliders(); setPlay(PLAY); setWeather(WX_ID);
[].forEach.call(document.querySelectorAll('#wxs button'), function (b) { b.onclick = function () { setWeather(b.dataset.w); if (SLIDERS_SHOW) SLIDERS_SHOW(); }; });   // 主選單：天氣（08_weather.js）
[].forEach.call(document.querySelectorAll('#dists button'), function (b) { b.onclick = function () { DIST = +b.dataset.d; [].forEach.call(document.querySelectorAll('#dists button'), function (x) { x.className = x === b ? 'on' : ''; }); }; });
[].forEach.call(document.querySelectorAll('#sails button'), function (b) { b.onclick = function () { setSailMode(b.dataset.s); }; });
setSailMode(SAIL); setCamTrack(true); $('physT').classList.toggle('on', PHYS);
$('go').onclick = start;
$('endC').onclick = function () { $('end').className = ''; };
$('endR').onclick = function () { RUNNING = false; $('end').className = ''; $('cover').style.display = ''; };
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/72_floodui.js ──
// ───────────────────────── 停格與進水細節頁（Tim 2026-10-13） ─────────────────────────
// P ＝「停格」（以前叫暫停；停住模擬、照樣能轉鏡頭）：上方出現一條「⏸ 停格中　進水：📊 圖表（I）🔍 透視（X）　▶ 繼續（P）」。設定、說明打開時不出現（它們自己會暫停）。
// 進水細節分兩個開關（Tim 2026-10-13：不然圖表會擋住 3D）——只在停格時打得開，繼續就都收起：
//   📊 圖表（FLX，I）：數字與剖面的面板，右上 ✕ 也能關；🔍 透視（FLX3，X）：3D 裡的艙內水面與破口隔著船殼看得到，
//   而且船附近的海面與白沫不畫（Tim 2026-10-13：會影響觀察）⇒ 看得到水線下的船殼與破口。
//   兩艘各一段：數字（積水、破口（水下幾個）、進出水、抽水、下沉、傾斜、水的重心、粒子與水格）＋ 側視、俯視的剖面（艙內的水、破口、外面的水面、設計水線）。
//   透視：艙內的水面不做深度測試（33_flood.js flDraw）、破口畫成點（水下紅；水上橙、小而淡 —— 暴風雨打爛的船水上的洞上百個，⛔ 一樣大 ⇒ 糊成一片，flHoleMarks）。
// 公式模式沒有艙內的水 ⇒ 只寫公式的讀數。⛔ 只讀模擬、不改（停格中沒有在走）。
var FLX = false, FLX3 = false;
/** 每一格（90_main.js frame）：停格條顯示與否；繼續了 ⇒ 進水細節頁收起。 */
function frzShow() {
  var on = RUNNING && PAUSED && !GSET.open && !HELP.open;
  $('frz').classList.toggle('on', on); $('msg').style.visibility = on ? 'hidden' : '';   // 停格條跟上方廣播同一個位置（⛔ 不藏 ⇒ 廣播的字透過半透明的條）
  if (!on) { if (FLX) floodClose(); FLX3 = false; CUTV.half = false; CUTV.deck = 0; }   // 剖面、隱藏甲板也跟著收（74_cutaway.js）
  $('frzFlood').classList.toggle('on', FLX); $('frzX').classList.toggle('on', FLX3);
  $('frzCut').classList.toggle('on', CUTV.half); $('frzDeck').classList.toggle('on', CUTV.deck > 0); $('frzDeck').textContent = deckLabel();
}
/** 船型 T 在格座標的 [中心 x, 中線 y, 半長, 半寬]（設計水線那一層；透視時拿掉附近海面用，01_gl.js nearShip）。 */
function xrBox(T) {
  if (!T.xrB) { var hb = 0; for (var x = T.wl0; x <= T.wl1; x++) hb = Math.max(hb, T.hullHB[T.zw * T.hullTW + x] || 0); T.xrB = [(T.wl0 + T.wl1) / 2, T.cy, (T.wl1 - T.wl0) / 2, hb]; }
  return T.xrB;
}
function xrayToggle() { if (!RUNNING || !PAUSED) return; FLX3 = !FLX3; frzShow(); }   // 按了就更新按鈕（⛔ 只靠每一格的 frzShow ⇒ 分頁在背景時按鈕不動）
function floodOpen() { if (!RUNNING || !PAUSED) return; FLX = true; $('floodp').classList.add('on'); floodPanel(); frzShow(); }
function floodClose() { FLX = false; $('floodp').classList.remove('on'); $('frzFlood').classList.remove('on'); }
function floodToggle() { if (FLX) floodClose(); else floodOpen(); }
$('frzFlood').onclick = floodToggle; $('frzX').onclick = xrayToggle;
$('frzGo').onclick = function () { PAUSED = false; frzShow(); };
$('floodX').onclick = floodClose;
function deg(a) { return (a * 57.2958).toFixed(1) + '°'; }
/** 填進水細節頁：兩艘各一段，畫完剖面。 */
function floodPanel() {
  var box = $('floodBody');
  box.innerHTML = SHIPS.map(function (sh, k) {
    var fl = sh.fl, who = (k === PLAYER_I ? '我艦' : '敵艦') + ' ' + sh.T.name, lines;
    var tilt = '橫傾 ' + deg(sh.rollA) + (sh.rollA > 0.002 ? '（往' + sideName('S') + '）' : sh.rollA < -0.002 ? '（往' + sideName('P') + '）' : '') + '・縱傾 ' + deg(sh.pitchA) + (sh.pitchA < -0.002 ? '（船頭低）' : sh.pitchA > 0.002 ? '（船尾低）' : '');
    if (!fl || sh.broken) {
      lines = '<div>' + (sh.broken ? '斷成兩截 ⇒ 照公式（一定沉）' : '公式模式（物理效果「進水」選粒子才看得到艙內的水）') + '</div>' +
        '<div>水線下打掉 ' + (sh.inflow || 0).toLocaleString() + ' 格・下沉 ' + sh.sink.toFixed(2) + ' m・' + tilt + '</div>';
      return '<div class="fpS"><div class="fpH">' + who + '</div>' + lines + '</div>';
    }
    var under = 0, uA = 0;
    fl.holes.forEach(function (h) { if (!(fl.hA[h] > 0)) return; var P = M4.pt(sh.M, fl.hX[h], fl.hY[h], fl.hZ[h]); if (P[1] < seaH(P[0], P[2], SIMT)) { under++; uA += fl.hA[h]; } });
    lines = '<div>艙內積水 <b>' + Math.round(fl.vol * RHO_W).toLocaleString() + ' 噸</b>（' + fl.vol.toFixed(1) + ' m³）・破口 ' + fl.open + ' 處 ' + fl.area.toFixed(2) + ' m²，水下 ' + under + ' 處 ' + uA.toFixed(2) + ' m²</div>' +
      '<div>進水 ' + fl.inQ.toFixed(2) + ' m³/s・往外流 ' + fl.outQ.toFixed(2) + ' m³/s・累計 進 ' + fl.inTot.toFixed(0) + '／出 ' + fl.outTot.toFixed(0) + '／抽掉 ' + fl.pumped.toFixed(0) + ' m³</div>' +
      '<div>下沉 ' + sh.sink.toFixed(2) + ' m（照水該 ' + fl.sinkT.toFixed(2) + '；4.2 m 開始沉）・' + tilt + '</div>' +
      '<div>水的重心：' + (Math.abs(fl.comY) < 0.05 ? '在中線' : '偏' + sideName(fl.comY > 0 ? 'S' : 'P') + ' ' + Math.abs(fl.comY).toFixed(1) + ' m') + '・' + (fl.comX >= 0 ? '偏船頭 ' : '偏船尾 ') + Math.abs(fl.comX).toFixed(1) + ' m・噴進來的水 ' + fl.J.n + ' 顆・水格 ' + fl.actN + ' 格（邊長 ' + (fl.F.c * S).toFixed(1) + ' m）</div>' +
      '<div class="fpL">側視（船頭在右）</div><canvas class="fpC" id="fpS' + k + '"></canvas><div class="fpL">俯視（船頭在右、' + sideName('P') + '在上）</div><canvas class="fpC" id="fpT' + k + '"></canvas>';
    return '<div class="fpS"><div class="fpH">' + who + '</div>' + lines + '</div>';
  }).join('');
  // 剖面等下一格再畫：⛔ 剛換掉 innerHTML 就量 clientWidth ⇒ 第一次打開量到 24 px（量過），剖面縮成一小塊
  requestAnimationFrame(function () { if (FLX) SHIPS.forEach(function (sh, k) { if (sh.fl && !sh.broken && $('fpS' + k)) { fpDraw($('fpS' + k), sh, 0); fpDraw($('fpT' + k), sh, 1); } }); });
}
window.addEventListener('resize', function () { if (FLX) floodPanel(); });
/** 剖面：view 0 側視（x × z，沿船寬加總）、1 俯視（x × y，沿高度加總）。灰 ＝ 艙內空間、藍 ＝ 水（越滿越深）、紅點 ＝ 水下的破口、橙點 ＝ 水上的、青線 ＝ 外面的水面、虛線 ＝ 設計水線。 */
function fpDraw(cv, sh, view) {
  var fl = sh.fl, F = fl.F, c = F.c, NX = F.NX, NY = F.NY, NZ = F.NZ, NXY = NX * NY, Vc = Math.pow(c * S, 3), A = fl.A, cap = fl.cap;
  var NV = view ? NY : NZ, dpr = Math.min(window.devicePixelRatio || 1, 2), w = cv.clientWidth || 600, h = Math.max(40, Math.round(w * NV / NX));
  cv.style.height = h + 'px'; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
  var g = cv.getContext('2d'), cw = cv.width / NX, ch = cv.height / NV, a, b, k;
  g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(0, 0, cv.width, cv.height);
  var capS = new Float32Array(NX * NV), watS = new Float32Array(NX * NV);
  for (k = 0; k < F.N; k++) {
    if (!(cap[k] > 0.02)) continue;
    var ix = k % NX, iy = ((k / NX) | 0) % NY, iz = (k / NXY) | 0, j = (view ? iy : iz) * NX + ix;
    capS[j] += cap[k] * Vc; watS[j] += A[k];
  }
  for (b = 0; b < NV; b++) for (a = 0; a < NX; a++) {
    var q = b * NX + a; if (!(capS[q] > 0)) continue;
    var y0 = view ? b * ch : (NV - 1 - b) * ch;                          // 側視：z 往上；俯視（從上往下看、船頭在右）：格 +y（右舷）在下
    g.fillStyle = 'rgba(150,150,140,0.45)'; g.fillRect(a * cw, y0, cw + 0.5, ch + 0.5);
    if (watS[q] > 1e-4) { var f = Math.min(1, watS[q] / capS[q]); g.fillStyle = 'rgba(40,140,230,' + (0.35 + 0.65 * f).toFixed(2) + ')'; g.fillRect(a * cw, y0, cw + 0.5, ch + 0.5); }
  }
  var M = sh.M, px = function (x) { return (x - F.X0) / c * cw; }, pv = function (v) { return view ? (v - F.Y0) / c * ch : cv.height - v / c * ch; };
  if (!view) {
    g.setLineDash([4 * dpr, 4 * dpr]); g.strokeStyle = 'rgba(255,255,255,0.5)'; g.lineWidth = dpr; g.beginPath(); g.moveTo(0, pv(sh.T.zw)); g.lineTo(cv.width, pv(sh.T.zw)); g.stroke(); g.setLineDash([]);
    g.strokeStyle = 'rgba(80,230,255,0.9)'; g.lineWidth = 1.5 * dpr; g.beginPath();
    for (a = 0; a <= NX; a++) {                                            // 外面的水面（中線上）：那一點的世界水面換回船上的高度
      var x = F.X0 + a * c, W0 = M4.pt(M, x, sh.T.cy, sh.T.zw), hs = seaH(W0[0], W0[2], SIMT), z = (hs - (M[1] * x + M[5] * sh.T.cy + M[13])) / M[9];
      if (a) g.lineTo(px(x), pv(z)); else g.moveTo(px(x), pv(z));
    }
    g.stroke();
  }
  fl.holes.forEach(function (hh) {
    if (!(fl.hA[hh] > 0)) return;
    var P = M4.pt(M, fl.hX[hh], fl.hY[hh], fl.hZ[hh]), wet = P[1] < seaH(P[0], P[2], SIMT), r = Math.max(1.5 * dpr, Math.sqrt(fl.hA[hh]) / 2 / (c * S) * cw * 1.3);   // 照洞的實際大小（⛔ 固定像素 ⇒ 手機上的剖面整排紅點糊成一條）
    g.fillStyle = wet ? 'rgba(255,60,50,0.95)' : 'rgba(255,170,40,0.85)'; g.beginPath(); g.arc(px(fl.hX[hh]), pv(view ? fl.hY[hh] : fl.hZ[hh]), r, 0, 6.2832); g.fill();
  });
}
/** 透視開著：破口在 3D 裡畫成點（不做深度測試 ⇒ 隔著船殼看得到；60_render.js 瞄準圈那一批）。水下的紅、照洞的大小；水上的橙、小而淡。 */
function flHoleMarks(pushPt) {
  SHIPS.forEach(function (sh) {
    var fl = sh.fl; if (!fl || sh.broken || sh.sinkingFinal || sh.sunk) return;
    fl.holes.forEach(function (h) {
      if (!(fl.hA[h] > 0)) return;
      var P = M4.pt(sh.M, fl.hX[h], fl.hY[h], fl.hZ[h]), wet = P[1] < seaH(P[0], P[2], SIMT);
      if (wet) pushPt(P, 0.25 + Math.sqrt(fl.hA[h]) * 0.8, [1, 0.25, 0.2], 0.95); else pushPt(P, 0.12 + Math.sqrt(fl.hA[h]) * 0.25, [1, 0.65, 0.15], 0.45);
    });
  });
}
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/73_slowmo.js ──
// ───────────────────────── 殉爆的慢動作與特寫（TASK-0531） ─────────────────────────
// Tim 2026-10-13：卡頓先優化掉（開戰第一輪對砲：21_gunnery.js stepBall）；減速只留給殉爆，可以開關；慢多少是動態的（大的殉爆慢很多）。
// 慢動作：模擬照舊一步 1/60 秒（DT），只是每一格畫面累積的時間 ×SLOW.ts（90_main.js frame）⇒ 模擬時間對真實時間變慢。
//   ⇒ 開或關同一個種子走出同一局（只差在哪一格畫面走那一步）；?demo、__game.run 不經過 frame ⇒ 不受影響。
//   倍率：殉爆那一刻掉到 tsMin（照爆炸半徑：前彈藥庫 9.5 m ⇒ 0.1×、後彈藥庫 5.5 m ⇒ 約 0.26×），停 hold 秒（真實時間，大的停久一點：前 5 秒、後 3.7 秒），再 SLOW_EASE 秒平滑回到 1×。
//   Tim 2026-10-13：慢動作時間可以延長 ⇒ 停 1–2.5 → 2–5 秒、回到 1× 2.5 → 3.5 秒。
//   兩間接連炸 ⇒ 取比較慢的那個、從頭算。
//   慢動作中，只給人看的（碎木、煙與水花、船邊水花：12_effects.js、13_water.js）改成每一格畫面照「畫面的 dt × 倍率」走（SLOW_VIS；step() 那邊跳過）
//   ⇒ 火球、碎片照樣平順（⛔ 留在 step() ⇒ 0.1× 時十格才動一下）。它們不回寫模擬 ⇒ 戰局不變。
// 特寫：殉爆那一刻鏡頭切到爆心的側面（自由鏡頭、不跟船），慢動作回到 1× 再過 SLOW_CAM_TAIL 秒，回到原本的鏡頭；中間按了換鏡頭（C）⇒ 不再切回去。
// 設定：遊戲內設定面板的「殉爆慢動作」「殉爆特寫」（跟著存檔；網址 ?slowmo=0、?slowcam=0）。狀態 SLOW 在 04_state.js（存檔在 69_prefs.js 載入時就讀）。
var SLOW_EASE = 3.5, SLOW_CAM_TAIL = 0.8;
/** 殉爆（23_powder.js magBoom）：w ＝ 爆心（世界）、R ＝ 爆炸半徑（格）。快轉（?demo）不切。 */
function slowKick(sh, w, R) {
  if (DEMO >= 0 || !RUNNING) return;
  var k = clamp(R / MAG_R, 0, 1.3);
  SLOW.kicks++;
  if (SLOW.on) {
    var m = clamp(0.1 + (1 - k) * 0.37, 0.1, 0.5), h = 2 + 3 * Math.min(k, 1);
    if (!SLOW.active || m < SLOW.ts) { SLOW.min = m; SLOW.hold = h; SLOW.t = 0; SLOW.active = true; SLOW.ts = m; }
  }
  if (SLOW.cam) {
    if (!SLOW.camSave) SLOW.camSave = { mode: CAM.mode, tgt: CAM.tgt.slice(), dist: CAM.dist, yaw: CAM.yaw, pitch: CAM.pitch, track: CAM.track };
    var F = M4.dir(sh.M, 1, 0, 0), side = norm([-F[2], 0, F[0]]), e = CAM.eye;          // 船的正橫；站在鏡頭本來那一側
    if ((e[0] - w[0]) * side[0] + (e[2] - w[2]) * side[2] < 0) side = mul(side, -1);
    var yw = Math.atan2(side[2], side[0]) + 0.35;                                         // 偏一點船頭的方向 ⇒ 看得到斷開的兩截
    CAM.mode = 0; CAM.track = false; CAM.tgt = [w[0], w[1] + R * S * 0.4, w[2]]; CAM.dist = clamp(R * S * 5.2, 28, 70); CAM.yaw = yw; CAM.pitch = 0.2; CAM.snap = true;
    SLOW.camT = SLOW.hold + SLOW_EASE + SLOW_CAM_TAIL; SLOW.camMode = 0;
  }
}
/** 每一格畫面（90_main.js frame，停格時不走）：照真實時間算現在的倍率；特寫時間到了把鏡頭還回去。回：倍率。 */
function slowTick(dt) {
  if (SLOW.active) {
    SLOW.t += dt;
    var u = (SLOW.t - SLOW.hold) / SLOW_EASE;
    if (u >= 1 || !SLOW.on) { SLOW.active = false; SLOW.ts = 1; }
    else SLOW.ts = u <= 0 ? SLOW.min : SLOW.min + (1 - SLOW.min) * u * u * (3 - 2 * u);
  }
  if (SLOW.camSave) {
    SLOW.camT -= dt;
    if (CAM.mode !== SLOW.camMode) SLOW.camSave = null;                                   // 中間換過鏡頭 ⇒ 照玩家的
    else if (SLOW.camT <= 0 || !SLOW.cam) {
      var s = SLOW.camSave; SLOW.camSave = null;
      CAM.mode = s.mode; CAM.tgt = s.tgt; CAM.dist = s.dist; CAM.yaw = s.yaw; CAM.pitch = s.pitch; CAM.track = s.track;
    }
  }
  return SLOW.ts;
}
/** 慢動作中，只給人看的效果照畫面的時間走（step() 那邊跳過）。 */
function slowVisStep(dt) { stepDebris(dt); stepPts(dt); stepWater(dt, 'fly'); }
/** 慢動作的提示（畫面上方中間）：倍率 < 0.98 才顯示。 */
function slowShow() {
  var el = $('slowB'); if (!el) return;
  var on = RUNNING && SLOW.active && SLOW.ts < 0.98;
  el.classList.toggle('on', on); if (on) el.textContent = '慢動作 ×' + SLOW.ts.toFixed(2);
}
$('slowT').onclick = function () { SLOW.on = !SLOW.on; if (!SLOW.on) { SLOW.active = false; SLOW.ts = 1; } gsetShow(); };
$('slowCamT').onclick = function () { SLOW.cam = !SLOW.cam; gsetShow(); };
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/74_cutaway.js ──
// ───────────────────────── 剖面與隱藏甲板（停格的選項；Tim 2026-10-13） ─────────────────────────
// 停格條多兩個：✂ 剖面（Z）＝ 船剖成兩半、拿掉靠鏡頭那一半（鏡頭繞過中線就換邊）；☰ 甲板（L）＝ 由上往下一層一層拿掉，
//   拿到只剩船底再按 ⇒ 全部回來（Loop）。兩個可以一起開。繼續（P）⇒ 都收起（跟透視一樣）。
// 甲板的切高照舷弧逐欄（x）量（deckCut）：船中段兩旁（中線 ±6、±14 格）站得住的高度出現得夠多 ⇒ 一層，再往船頭船尾一欄一欄跟著走（高低差 4 格內）；
//   拿掉第 k 層 ＝ 那層的地板與底下的樑以上都不畫。最下面那層（船底）不拿。
// 開著時：陰影關掉（拿掉的甲板不該再擋光：剖面圖要看得清楚）；剖面另外不畫船附近的海面與白沫（跟透視一樣，再往鏡頭那一側多拿 XR_CUT ⇒ 從側面看得到水線下）。
//   只拿掉甲板 ⇒ 海照畫（船殼裡的海本來就有遮罩；⛔ 也拿 ⇒ 船邊一圈白色的長方形）。
// 只動畫面：船殼、模型、繩、帆照格座標在著色器裡丟掉（01_gl.js CUT_GLSL）；人：站的那一點在拿掉的那一邊就不畫；碎片、粒子、斷開的那幾團不剖。
var CUTV = { half: false, deck: 0 }, CUT_NAMES = ['住艙甲板', '底艙甲板'], XR_CUT = 300;   // XR_CUT：剖面時海面往鏡頭那一側多拿掉幾格（30 m；60_render.js）
function cutOn() { return CUTV.half || CUTV.deck > 0; }
/** 船型的甲板切高（記在 T 上）：{ W, n（拿得掉的層數）, names, rows（第 k 層的切高，逐欄）, tex（R32F，寬 W、高 n） }。 */
function deckCut(sh) {
  var T = sh.T; if (T.cutD) return T.cutD;
  var g = T.base, CY = T.cy, W = g.sx, x, z;
  var zMax = sh.decks.length ? sh.decks[sh.decks.length - 1].zr[1] + 3 : Math.min(g.sz - 12, T.zw + 80);
  var FL = [];                                                            // 每一欄站得住的高度（腳下實心、頭上 1 m 空）
  for (x = 0; x < W; x++) {
    var zs = [];
    if (x >= T.hx0 && x <= T.hx1) [-14, -6, 6, 14].forEach(function (dy) {
      var y = CY + dy;
      for (var z = 2; z <= zMax; z++) { if (!g.get(x, y, z - 1) || g.get(x, y, z)) continue; var h = 1; while (h < 10 && !g.get(x, y, z + h)) h++; if (h === 10 && zs.indexOf(z) < 0) zs.push(z); }
    });
    FL.push(zs);
  }
  var xm = Math.round((T.wl0 + T.wl1) / 2), cnt = {}, ns = 0;               // 船中段 ±30 欄：每個高度出現幾欄
  for (x = xm - 30; x <= xm + 30; x++) { ns++; FL[x].forEach(function (z) { cnt[z] = (cnt[z] || 0) + 1; }); }
  var seeds = [];                                                         // 相差 4 格內併成一層（取出現最多的那個高度），出現在兩成五的欄以上才算
  Object.keys(cnt).map(Number).sort(function (a, b) { return b - a; }).forEach(function (z) {
    var s = seeds[seeds.length - 1];
    if (s && s.z1 - z <= 4) { s.n += cnt[z]; s.z1 = z; if (cnt[z] > s.best) { s.best = cnt[z]; s.z = z; } } else seeds.push({ z: z, z1: z, n: cnt[z], best: cnt[z] });
  });
  seeds = seeds.filter(function (s) { return s.n >= ns * 0.25; });
  var prof = seeds.map(function (s) {                                     // 往船頭、船尾一欄一欄跟著走（找不到 ⇒ 照上一欄的高度延伸）
    var Z = new Float32Array(W).fill(s.z);
    [1, -1].forEach(function (dir) {
      var cur = s.z;
      for (var x = xm; x >= 0 && x < W; x += dir) {
        var best = null; FL[x].forEach(function (z) { if (Math.abs(z - cur) <= 4 && (best === null || Math.abs(z - cur) < Math.abs(best - cur))) best = z; });
        if (best !== null) cur = best;
        Z[x] = cur;
      }
    });
    return Z;
  });
  var n = Math.max(0, prof.length - 1), rows = [], names = [], low = sh.decks.length ? sh.decks[0].zr[0] : 1e9, below = 0;
  for (var k = 0; k < n; k++) {
    var Z = prof[k], runs = [];                                           // 地板＋底下的樑有多厚：船中段兩旁往下數連續的實心格，取九成的那個（最多 6 格；不切到下一層頭頂 1.2 m）
    for (x = T.hx0; x <= T.hx1; x += 2) [-20, -10, 10, 20].forEach(function (dy) { var y = CY + dy, r = 0; while (r < 8 && g.get(x, y, Z[x] - 1 - r)) r++; if (r) runs.push(r); });
    runs.sort(function (a, b) { return a - b; });
    var dep = Math.min(6, runs.length ? runs[Math.floor(runs.length * 0.9)] : 1), R = new Float32Array(W);
    for (x = 0; x < W; x++) R[x] = Math.max(prof[k + 1][x] + 12, Z[x] - dep);
    rows.push(R);
    var zc = Z[xm], D = sh.decks.filter(function (D) { return zc >= D.zr[0] && zc <= D.zr[1]; })[0];
    names.push(D ? D.name : zc < low ? CUT_NAMES[Math.min(below++, CUT_NAMES.length - 1)] : '第 ' + (k + 1) + ' 層');
  }
  var tex = gl.createTexture(), data = new Float32Array(W * Math.max(1, n));
  rows.forEach(function (R, k) { data.set(R, k * W); });
  gl.activeTexture(gl.TEXTURE8); gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.R32F, W, Math.max(1, n), 0, gl.RED, gl.FLOAT, data);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.activeTexture(gl.TEXTURE0);
  return T.cutD = { W: W, n: n, names: names, rows: rows, tex: tex, floors: prof.map(function (Z) { return Z[xm]; }) };
}
/** 剖哪一邊：鏡頭在中線的哪一邊就拿掉那一邊（+1 ＝ 格 +y）。 */
function cutSide(sh) { return toLocal(sh, CAM.eye)[1] >= sh.T.cy ? 1 : -1; }
/** 畫一艘船（或斷開的那幾團）之前：設好剖面的 uniform。不是兩艘船本身、或沒開 ⇒ 關。 */
function cutSet(prog, ow) {
  var u = prog.u; if (!u.uCut) return;
  if (!cutOn() || SHIPS.indexOf(ow) < 0) { gl.uniform4f(u.uCut, 0, 0, -1, 0); return; }
  var D = deckCut(ow);
  gl.uniform4f(u.uCut, ow.T.cy, CUTV.half ? cutSide(ow) : 0, CUTV.deck > 0 && D.n ? Math.min(CUTV.deck, D.n) - 1 : -1, 1);
  if (u.uCutW) gl.uniform2f(u.uCutW, D.W, Math.max(1, D.n));
  if (u.uCutInv) gl.uniformMatrix4fv(u.uCutInv, false, ow.inv);
  gl.activeTexture(gl.TEXTURE8); gl.bindTexture(gl.TEXTURE_2D, D.tex); gl.uniform1i(u.uCutT, 8); gl.activeTexture(gl.TEXTURE0);
}
/** 這個人在拿掉的那一邊？（drawCrew；墜落中的不管） */
function cutHides(sh, c) {
  if (!cutOn() || c.st === 4 || c.st === 5) return false;
  var p = c.pos;
  if (CUTV.half && cutSide(sh) * (p[1] - sh.T.cy) > 0) return true;
  if (CUTV.deck > 0) { var D = deckCut(sh); if (D.n && p[2] >= D.rows[Math.min(CUTV.deck, D.n) - 1][clamp(Math.floor(p[0]), 0, D.W - 1)]) return true; }
  return false;
}
function cutToggle() { if (!RUNNING || !PAUSED) return; CUTV.half = !CUTV.half; frzShow(); }
/** 甲板：全部 → 拿掉最上面一層 → … → 只剩船底 → 全部（照我艦的層數）。 */
function deckCycle() {
  if (!RUNNING || !PAUSED || !SHIPS[PLAYER_I]) return;
  var n = deckCut(SHIPS[PLAYER_I]).n; CUTV.deck = n ? (CUTV.deck + 1) % (n + 1) : 0; frzShow();
}
/** 停格條上「甲板」那顆的字。 */
function deckLabel() {
  var sh = SHIPS[PLAYER_I]; if (!CUTV.deck || !sh) return '☰ 甲板（L）';
  var D = deckCut(sh), k = Math.min(CUTV.deck, D.n);
  return '☰ ' + (k >= D.n ? '只剩船底' : '拿掉到' + D.names[k - 1]) + '（L）';
}
$('frzCut').onclick = cutToggle; $('frzDeck').onclick = deckCycle;
// ── D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/90_main.js ──
// ───────────────────────── 主迴圈 ─────────────────────────
var last = 0, acc = 0, FPS = 60, fpsT = 0;
function frame(ts, noRaf) {                                         // noRaf：__game.live 同步呼叫（不再排下一格，⛔ 排了 ⇒ 兩條畫面迴圈、模擬走兩倍快）
  var f0 = PF ? performance.now() : 0;                                // 逐幀分段計時（?debug=1）
  var dt = last ? Math.min(0.1, (ts - last) / 1000) : DT; last = ts;
  FPS = FPS * 0.95 + (1 / Math.max(dt, 1e-3)) * 0.05;
  if (RUNNING && !PAUSED) {
    var sk = slowTick(dt); SLOW_VIS = sk < 1;                         // 殉爆的慢動作（73_slowmo.js）：模擬一步照舊 DT，只是每格累積的時間 × 倍率
    acc += dt * sk; var n = 0;
    while (acc >= DT && n < 4) { step(); acc -= DT; n++; }
    if (n === 4) acc = 0;
    if (SLOW_VIS) { if (PF) PF.t = performance.now(); slowVisStep(dt * sk); if (PF) pfLap('slowvis'); }
    SLOW_VIS = false;                                                 // 快轉（__game.run）不經過這裡 ⇒ 照常在 step() 走
  }
  if (PF) PF.t = performance.now();
  camFollow(dt);                                                      // 追砲彈（03_camera.js）
  if (!PAUSED && !STILL) stepRain(dt);                                // 3D 雨滴（14_rain.js）：照畫面的時間走；停格、縮圖不動
  if (PF) pfLap('rain');
  remesh(RM_BUDGET);                                                  // 重網格化，每格有預算（60_render.js）
  if (PF) pfLap('flush');
  camUpdate(dt); render(); if (PF) pfLap('render'); hud(dt); frzShow(); slowShow();                        // 停格條（72_floodui.js）
  if (PF) { pfLap('hud'); pfEnd(f0, RUNNING && !PAUSED ? n : 0); }
  if (GFX_FPS && (fpsT -= dt) <= 0) { fpsT = 0.5; $('fps').textContent = 'FPS ' + Math.round(FPS) + '　畫質 ' + GFX_NAME[gfxLevel()] + '　' + CAM.w + '×' + CAM.h + (RT && RT.s ? '　MSAA ' + RT.s + '×' : ''); }   // 畫質設定頁的「顯示 FPS」
  if (!noRaf) requestAnimationFrame(frame);
}

// ───────────────────────── 載入 ─────────────────────────
if (DEBUG) window.__game = {
  start: function (mode, dist) { MODE = mode || 'pve'; DIST = dist || DIST; start(); },
  fleet: function (spec, mode) {   // 多船（TASK-0537）：spec ＝ [{ team: 'blue'|'red', hull: 'constitution'|… }]，第一艘是我艦；船型要先載好（loadHull）；null ⇒ 回到兩艘
    FLEET_DBG = spec; MODE = mode || 'eve'; start();
    return SHIPS.map(function (s) { return { i: s.i, team: s.team, hull: s.T.id, px: s.px, pz: s.pz, foe: s.foe ? s.foe.i : null }; });
  },
  loadHull: function (id) { return loadHull(id).then(function (T) { return T.id; }); },
  foes: function () { return SHIPS.map(function (s) { return { i: s.i, team: s.team, foe: s.foe ? s.foe.i : null, aimOn: s.aimOn ? s.aimOn.i : null, ff: s.ff || 0, ffOut: s.ffOut || 0, ffHold: s.ffHold || 0, avoid: s.avoidN || 0, hits: s.hits, sunk: s.sunk, struck: s.struck, x: +s.px.toFixed(1), z: +s.pz.toFixed(1) }; }); },
  mask: function (k) { MASK_OFF = k === undefined ? -1 : k; render(); return MASK_OFF; },   // 船艙遮罩（60_render.js）：關掉第 k 艘的、畫一格
  gpu: function () { render(); return { near: GPU_NEAR, max: MAX_SHIPS, slots: SLOTS.map(function (s) { return s.i; }), rest: (SLOTS.rest || []).map(function (s) { return s.i; }), glob: SHM.glob, layers: SHM.layers, shadowN: SHM.n, offG: +SHM.offG.toFixed(3), hullLayers: HULLA.key, err: gl.getError() }; },   // GPU 的格（60_render.js gpuSlots）
  cut: function (o) { if (o) for (var k in o) CUTV[k] = o[k]; render(); return CUTV; },     // 剖面與隱藏甲板（74_cutaway.js）：{ half, deck }
  menuFleet: function (F) { if (F) { FLEET_SET = fleetTrim(F.map(function (L) { return L.slice(); })); fleetUI(); pickShip(); } return { set: FLEET_SET, spec: fleetSpec(), html: [$('fleet0').innerHTML.length, $('fleet1').innerHTML.length] }; },
  run: function (sec) { var n = Math.round(sec / DT); for (var i = 0; i < n; i++) { step(); if (i % 30 === 29) remesh(Infinity); } remesh(Infinity); camUpdate(1); render(); hud(1); PF.cur = {}; return this.stats(); },   // PF.cur：快轉的不算進下一格畫面
  fire: function (ammo, aim) { var me = SHIPS[PLAYER_I]; if (aim) setAim(me, aim); return broadside(me, ammo || 0); },
  one: function (ammo, aim) { var me = SHIPS[PLAYER_I]; if (aim) setAim(me, aim); fireOne(me, ammo || 0); return BALLS.length; },
  ships: function () { return SHIPS; }, balls: function () { return BALLS; }, pieces: function () { return PIECES; },
  camera: function () { return { mode: CAM.mode, follow: CAM.follow ? { age: +CAM.follow.age.toFixed(2), owner: CAM.follow.owner, alive: CAM.follow.alive } : null, pick: CAM.pick || null, track: CAM.track, yaw: CAM.yaw, dist: CAM.dist, tgt: CAM.tgt.slice(), eye: CAM.eye.slice() }; },
  strike: function (o) { for (var k in o) STRIKE[k] = o[k]; return { rules: STRIKE, text: strikeText() }; },
  /** 量降旗用：第 i 艘還能動的人照順序倒下，直到死傷比例到 frac（role 給了只倒那個職位）；下一次 survey 才判降旗。 */
  casualty: function (i, frac, role) {
    var sh = SHIPS[i], need = Math.ceil(sh.crew0 * frac) - (sh.crew0 - sh.crew.filter(able).length);
    sh.crew.forEach(function (c) { if (need > 0 && able(c) && (role === undefined || c.role === role)) { killCrew(sh, c, '量測'); need--; } });
    return sh.crew.filter(able).length;
  },
  /** 畫質（07_gfx.js）：給 level（low／mid／high）或 { shadow: 2, … } 就換；回傳現在的設定與管線的讀數。 */
  gfx: function (o) { if (typeof o === 'string') gfxSet(o); else if (o) for (var k in o) GFX[k] = o[k]; if (o && typeof gfxShow === 'function' && $('gfxB')) gfxShow(); return { level: gfxLevel(), gfx: JSON.parse(JSON.stringify(GFX)), w: CAM.w, h: CAM.h, msaa: RT ? RT.s : null, shadow: SHM ? SHM.n : null, refl: RT && RT.R ? [RT.R.w, RT.R.h] : null, sea: SEAG ? { lv: SEAG.lv, verts: SEAG.verts, tris: SEAG.n / 3 } : null }; },
  /** 天氣（08_weather.js）：給 id（clear／storm）就換；回傳現在的天氣。 */
  weather: function (id) { if (id) setWeather(id); return { id: WX_ID, wx: WX, wind: WIND.slice(), from: +bearing(-WIND[0], -WIND[2]).toFixed(1), spd: +WIND_SPD.toFixed(3), knots: +windKnots().toFixed(1) }; },
  /** 浪（08_sea.js）：(x, z) 的水面高度（t 不給 ＝ 現在）；sea() ＝ 浪的設定。 */
  sea: function (x, z, t) { return x === undefined ? { k: SEA_K, waves: WAVES } : seaH(x, z, t === undefined ? SIMT : t); },
  camFollow: function (dt) { camFollow(dt); return CAM.follow; },
  predict: function (b) { return ballPredict(b); },
  cam: function (o) { for (var k in o) CAM[k] = o[k]; CAM.snap = true; camUpdate(1); render(); },
  phys: function (on) { if (on !== undefined) setPhys(!!on); return PHYS; },
  /** 進水（33_flood.js，粒子模式）：第 i 艘的水量、破口、進出水、抽水、粒子、重心、該下沉多少；公式模式 ⇒ null。 */
  flood: function (i, o) {
    if (o && 'hide' in o) FL_HIDE = !!o.hide;
    if (o && o.gm > 0) FL_GM = o.gm;                                   // 調穩心高（量傾斜用）
    var sh = SHIPS[i || 0], fl = sh.fl; if (!fl) return null;
    var cells = 0; for (var t = 0; t < fl.actN; t++) if (fl.A[fl.act[t]] > 0) cells++;
    return { lv: FLOOD_LV, c: fl.F.c, grid: [fl.F.NX, fl.F.NY, fl.F.NZ], m3: +fl.vol.toFixed(3), t: +(fl.vol * RHO_W).toFixed(2), cells: cells, jets: fl.J.n, holes: fl.open, area: +fl.area.toFixed(3),
      inQ: +fl.inQ.toFixed(3), outQ: +fl.outQ.toFixed(3), inTot: +fl.inTot.toFixed(2), outTot: +fl.outTot.toFixed(2), pumped: +fl.pumped.toFixed(2), lost: +(fl.lost || 0).toFixed(3),
      comX: +fl.comX.toFixed(2), comY: +fl.comY.toFixed(2), sinkT: +fl.sinkT.toFixed(3), sink: +sh.sink.toFixed(3), roll: +sh.rollA.toFixed(4), pitch: +sh.pitchA.toFixed(4), dirty: fl.dirty.length + fl.hdirty.length };
  },
  /** 量進水用：第 i 艘在格 (x, z) 那一舷（side 0 ＝ 格 +y、1 ＝ −y）的船殼打一個半徑 r 格的洞（從最外那一格往艙內打穿）。回打掉幾格。 */
  hole: function (i, x, z, side, r) {
    var sh = SHIPS[i || 0], B = sh.T.base, y0 = -1, y, s = side ? 1 : -1, n = 0; r = r || 4;
    if (side) { for (y = 0; y < sh.T.cy; y++) if (B.get(x, y, z)) { y0 = y; break; } } else { for (y = B.sy - 1; y > sh.T.cy; y--) if (B.get(x, y, z)) { y0 = y; break; } }
    if (y0 < 0) return null;
    for (var dz = -r; dz <= r; dz++) for (var dx = -r; dx <= r; dx++) {
      if (dx * dx + dz * dz > r * r) continue;
      for (var t = 0; t < 16; t++) { var yy = y0 + s * t; if (t > 2 && !B.get(x + dx, yy, z + dz)) break; if (removeVoxel(sh, x + dx, yy, z + dz, false)) n++; }
    }
    sh.rs.flush(); return { removed: n, skin: y0 };
  },
  /** 船邊水花（13_water.js）：現在的檔、水滴與白沫各幾顆、開局以來生了幾顆。{ hide: true } ⇒ 照算、不畫（量繪製成本）。 */
  /** 逐幀分段計時（TASK-0531）：最慢的 top 格（預設 8）各段幾 ms、這一格走了幾步模擬；{ clear: true } ⇒ 清掉重記；{ sum: true } ⇒ 再附上全部格的各段總和與平均。 */
  /** 照真的畫面迴圈跑 sec 秒模擬（同步呼叫 frame()，dt ＝ 實際經過的時間 ⇒ 追趕迴圈補幾步跟真的玩一樣；預覽分頁在背景時 rAF 停也量得到）。finish ⇒ 每格 gl.finish()（把 GPU 的時間也算進去）。 */
  live: function (sec, finish) {
    var end = SIMT + sec, n = 0, t0 = performance.now(); last = 0;
    while (SIMT < end && n < sec * 400) { frame(performance.now(), true); if (finish) gl.finish(); n++; }
    return { frames: n, ms: Math.round(performance.now() - t0), simt: +SIMT.toFixed(2), fps: +(n / ((performance.now() - t0) / 1000)).toFixed(1) };
  },
  frames: function (o) {
    o = o || {}; if (o.clear) { PF.ring = []; PF.cur = {}; return 'cleared'; }
    var R = PF.ring, f2 = function (x) { return +x.toFixed(1); }, fmt = function (c) { var r = { simt: f2(c.simt), total: f2(c.total), steps: c.steps }; Object.keys(c).filter(function (k) { return ['simt', 'total', 'steps'].indexOf(k) < 0 && c[k] >= 0.5; }).sort(function (a, b) { return c[b] - c[a]; }).forEach(function (k) { r[k] = f2(c[k]); }); return r; };
    var top = R.slice().sort(function (a, b) { return b.total - a.total; }).slice(0, o.top || 8).map(fmt), out = { frames: R.length, top: top };
    if (o.sum) { var s = {}; R.forEach(function (c) { for (var k in c) if (k !== 'simt' && k !== 'steps') s[k] = (s[k] || 0) + c[k]; }); for (var k in s) s[k] = f2(s[k] / Math.max(1, R.length)); out.avg = s; }
    return out;
  },
  /** 殉爆的慢動作與特寫（73_slowmo.js）：給 { on, cam } 就改設定；回現在的倍率、狀態、殉爆幾次。 */
  slow: function (o) { if (o) { if ('on' in o) SLOW.on = !!o.on; if ('cam' in o) SLOW.cam = !!o.cam; gsetShow(); } return { on: SLOW.on, cam: SLOW.cam, active: SLOW.active, ts: +SLOW.ts.toFixed(3), min: SLOW.min, hold: SLOW.hold, t: +SLOW.t.toFixed(2), kicks: SLOW.kicks, camHeld: !!SLOW.camSave }; },
  /** 3D 雨滴（14_rain.js）：現在幾滴、上一格畫了幾條、水花幾個、開了以來落海與打到船幾次。{ bench: n } ⇒ 量 n 格（走一格＋填緩衝畫一次）各花幾 ms。 */
  rain: function (o) {
    var b = null; if (o && o.bench) { var t0 = performance.now(), i; for (i = 0; i < o.bench; i++) stepRain(1 / 60); var t1 = performance.now(); for (i = 0; i < o.bench; i++) rdDraw(); gl.finish(); b = { step: +((t1 - t0) / o.bench).toFixed(3), draw: +((performance.now() - t1) / o.bench).toFixed(3) }; }
    return { bench: b, lv: GFX.drops, n: RD.n, drawn: RD.drawn, splash: RS.n, hit: { sea: RD_STAT.hitSea, ship: RD_STAT.hitShip }, v: RD.v.map(function (x) { return +x.toFixed(2); }), top: +RD.top.toFixed(1) }; },
  water: function (o) { if (o && 'hide' in o) WP_HIDE = !!o.hide; return { lv: PHX.water, spray: WS.n, foam: WF.n, emitted: { spray: WP_STAT.spray, foam: WP_STAT.foam }, src: WP_STAT.src }; },
  /** 物理效果（09_phx.js）：給 level（full／high／mid／low）或 { rig: 1, … } 就換；回傳現在的設定。 */
  phx: function (o) { if (typeof o === 'string') phxSet(o); else if (o) for (var k in o) PHX[k] = o[k]; if (o) { if ((PHX.rig > 0) !== PHYS) setPhys(PHX.rig > 0); if ($('phxB')) phxShow(); } return { level: phxLevel(), phx: JSON.parse(JSON.stringify(PHX)), phys: PHYS, rig: rigLv(), debris: DEB_KS[PHX.debris], fx: FX_KS[PHX.fx] }; },
  /** 帆桁追風的讀數：相對風吹去的方向、每根帆桁現在離正橫幾度（作品的角度＋追風轉的）。 */
  yards: function (i) { var sh = SHIPS[i || 0]; return { psi: sh.psi === undefined ? null : +(sh.psi * 57.3).toFixed(1), side: sh.braceSide || 0, ropes: sh.yRopes.length,
    yards: sh.yards.map(function (m) { return { name: m.name, kind: m.yk, deg: +((m.r0 + m.rot) * 57.3).toFixed(1), rot: +(m.rot * 57.3).toFixed(1), alive: m.alive }; }) }; },
  /** 量殉爆用：第 i 艘的第 k 間彈藥庫（0 後、1 前）。how：'keg' 點一桶（連鎖照血量走）、'mag' 整間直接殉爆。 */
  ignite: function (i, k, how) {
    var sh = SHIPS[i], mag = sh.mags[k]; if (!mag) return null;
    if (how === 'mag') magBoom(sh, mag); else { var m = mag.kegs.filter(function (x) { return x.alive; })[0]; if (m) ignite(sh, m, 0); }
    return this.powder(i);
  },
  /** 砲長的讀數：每艘的砲長、現在的模式、換過幾次、各模式的局勢分數。 */
  captain: function () { return SHIPS.map(function (sh) { var foe = foeOf(sh), v = {}; AIM_MODES.forEach(function (m) { v[m] = +aimValue(foe, m).toFixed(2); }); return { cap: sh.cap, mode: sh.aimMode, switches: sh.modes || 0, pMode: sh.pMode, value: v }; }); },
  /** 手持物的讀數：上一格畫了幾件、每艘現在誰拿著什麼。 */
  items: function () { return { drawn: ITEMS_N, ships: SHIPS.map(function (sh) { var r = {}; sh.crew.forEach(function (c) { var it = heldItem(sh, c, crewFrame(sh, c)); if (it) r[it.id] = (r[it.id] || 0) + 1; }); return r; }) }; },
  powder: function (i) { var sh = SHIPS[i]; return { never: powderNever(), hp: powderHP(), blast: BLAST_K, broken: !!sh.broken, cartBooms: sh.cartN || 0, keel: sh.keel || null, fate: sh.fate,
    mags: sh.mags.map(function (g) { return { name: g.name, lb: g.lb, kegs: g.kegs.length, alive: g.kegs.filter(function (m) { return m.alive; }).length, boomed: g.boomed, gone: g.gone, R: g.R ? +(g.R * S).toFixed(2) : 0, removed: g.removed || 0, broke: !!g.broke }; }),
    pieces: PIECES.map(function (p) { return { n: p.n, hull: !!p.hull, mods: (p.mods || []).length, y: +p.c[1].toFixed(2) }; }),
    stations: sh.stations.map(function (st) { return { name: st.name, at: st.at, kegs: st.kegs.filter(function (m) { return m.alive; }).length }; }) }; },
  /** 預備水手的讀數（42_hands.js）：走得到的甲板（走路格幾點、分成幾片）、梯子（兩頭在哪一層、爬過幾次）、人在哪一層、在做什麼、派了幾次、補上幾個。 */
  hands: function (i) {
    var sh = SHIPS[i || 0], H = sh.nav; if (!H) return null;
    var hs = sh.crew.filter(function (c) { return c.role === ROLE.HAND; }), st = {}, on = {};
    hs.forEach(function (c) { var k = c.st ? 'down' : c.hand.climb ? 'climb' : c.hand.job ? 'job-' + c.hand.job.kind : c.hand.wp || c.hand.legs.length ? 'walk' : 'wait'; st[k] = (st[k] || 0) + 1; if (!c.st) { var n = H.levels[c.hand.lv].key; on[n] = (on[n] || 0) + 1; } });
    return { n: hs.length, states: st, on: on, called: H.called, joined: H.joined, ms: +H.ms.toFixed(1), home: H.levels[H.home].key, reach: H.reach.map(function (j) { return H.levels[j].key; }), gun0: H.gun0, pm0: H.pm0, helm0: H.helm0,
      levels: H.levels.map(function (L) { return { key: L.key, name: L.name, zr: L.zr, cells: L.N.cells.length, parts: L.N.parts }; }),
      ladders: H.ladders.map(function (L) { return { name: L.name, from: H.levels[L.lo].key, to: H.levels[L.hi].key, x: Math.round(L.x), used: L.n }; }) };
  },
  /** 落水求生的讀數（43_swim.js）：現在在水裡幾個（浮上來中／在游／在踩水／溺水沉下去中）、累計落水、救上來、溺水、被敵艦撈走／撈起敵艦的、名單上幾個人。 */
  swim: function (i) {
    var sh = SHIPS[i || 0], st = {};
    sh.crew.forEach(function (c) { if (c.st !== 5) return; var k = c.swim.dead ? 'sinking' : c.fv[1] > 0 ? 'rising' : c.fv[0] || c.fv[2] ? 'swimming' : 'treading'; st[k] = (st[k] || 0) + 1; });
    return { now: st, total: sh.swims || 0, saved: sh.saved || 0, drowned: sh.causes['溺水'] || 0, lostTo: sh.lostTo || 0, gained: sh.gained || 0, crew: sh.crew.length, drownT: DROWN_T };
  },
  /** 量落水用：第 i 艘最上面那層甲板上還能動的人，挑最靠舷邊的 n 個推下海（往舷外 3 m/s）。 */
  overboard: function (i, n) {
    var sh = SHIPS[i || 0], cy = sh.T.cy, out = sh.crew.filter(function (c) { return c.st === 0 && c.pos[2] >= sh.deckZ[sh.weatherDeck][0]; })
      .sort(function (a, b) { return Math.abs(b.pos[1] - cy) - Math.abs(a.pos[1] - cy); }).slice(0, n || 1);
    out.forEach(function (c) { var s = c.pos[1] >= cy ? 1 : -1; fall(sh, c, add(mul(norm(M4.dir(sh.M, 0, s, 0)), 3), [0, 2, 0])); });
    return out.length;
  },
  /** 補給的讀數：送藥手各自在做什麼、每門砲的藥箱。 */
  supply: function (i) { var sh = SHIPS[i]; var pm = sh.crew.filter(function (c) { return c.role === ROLE.POWDER; });
    return { monkeys: pm.length, able: pm.filter(able).length, states: pm.reduce(function (a, c) { var s = c.st ? 'down' : c.pm.st; a[s] = (a[s] || 0) + 1; return a; }, {}),
      boxes: sh.guns.map(function (g) { return g.alive ? g.box : '✕'; }).join(''), waiting: sh.guns.filter(function (g) { return g.alive && g.needCart && !(g.box > 0); }).length, noDrop: sh.guns.filter(function (g) { return !g.drop; }).length }; },
  prof: function (reset) { var r = { cloth: +PROF.cloth.toFixed(1), rope: +PROF.rope.toFixed(1), shred: +PROF.shred.toFixed(1), buf: +PROF.buf.toFixed(1), perStep: +PHYS_MS.toFixed(3) }; if (reset) PROF = { cloth: 0, rope: 0, shred: 0, buf: 0 }; return r; },
  /** 帆與繩的讀數：每面帆最鼓的那一點離雕刻作品形狀多遠（格）、還綁著幾個點、垂下來的繩幾條。 */
  cloth: function (i) {
    var sh = SHIPS[i || 0];
    return { templates: sh.T.cloth.map(function (T) { return { name: T.name, n: T.n, sim: T.sim.n, grid: T.grid, simEdges: T.sim.ea.length, simPins: Array.prototype.filter.call(T.sim.hk, function (x) { return x; }).length, pins: T.pins, clews: T.clews, sides: T.sides }; }),
      sails: sh.cl.map(function (c, k) {
        var d = 0, P0 = c.T.sim.p0; if (c.p) for (var j = 0; j < c.T.sim.n * 3; j += 3) d = Math.max(d, Math.hypot(c.p[j] - P0[j], c.p[j + 1] - P0[j + 1], c.p[j + 2] - P0[j + 2]));
        return { name: c.T.name, live: !!c.p && !c.hidden && !c.gone, loose: !!c.loose, torn: !!c.torn, pins: c.npin, maxMove: +d.toFixed(2) };
      }),
      loose: sh.loose.length, loosePinned: sh.loose.filter(function (o) { return o.pin[0] || o.pin[o.n - 1]; }).length, loosePts: sh.loose.reduce(function (a, o) { return a + o.n; }, 0),
      shreds: (sh.shreds || []).length, shredWet: (sh.shreds || []).filter(function (f) { return f.wet; }).length, shredPts: (sh.shreds || []).reduce(function (a, f) { return a + f.n; }, 0), shredCut: SH_STAT.cut, shredTris: SH_STAT.tris };   // 布片（34_shreds.js）：現在幾片、落水幾片、開局以來切了幾片
  },
  stats: function () { return { t: +SIMT.toFixed(2), ships: SHIPS.map(function (s) { return { lost: s.lost, count: s.grid.count, quads: s.rs.quads(), sink: +s.sink.toFixed(3), lift: +s.lift.toFixed(3), massLost: +massLost(s).toFixed(1), mass0: Math.round(s.mass0 || 0), roll: +s.rollA.toFixed(3), inflow: s.inflow, water: s.fl ? +(s.fl.vol * RHO_W).toFixed(1) : undefined, guns: s.gunsAlive, masts: s.masts.map(function (m) { return m.name + (m.up ? '✓' : '✗'); }).join(' '), fired: s.fired, hits: s.hits, ropesDead: s.ropes.filter(function (r) { return r.dead; }).length, sailsDead: s.sails.filter(function (x) { return x.dead; }).length,
    crew: s.crew0, able: s.able, wounded: s.wounded, dead: s.dead, causes: s.causes, manned: s.gunsManned, struck: s.struck, fate: s.fate,
    knots: +(s.spd * 1.944).toFixed(2), yaw: +s.yaw.toFixed(3), x: +s.px.toFixed(1), z: +s.pz.toFixed(1), sail: +s.sailFrac.toFixed(3), point: s.pos,
    side: s.side, manual: s.manual, rudder: +s.rudder.toFixed(2), sailSet: SAILSETS[s.sailSet] }; }), over: OVER, end: OVER ? $('endT').textContent : '', pieces: PIECES.map(function (p) { return p.n; }), debris: D.n, pts: PT.n, balls: BALLS.length, masts: SHIPS.length ? SHIPS[0].T.masts : [] }; }
};
/** 讀數的一段：這艘船是讀快取還是現場解析（06_cache.js）。 */
function cacheText(st) { return !st ? '' : st.hit ? '（讀快取 ' + (st.readMs / 1000).toFixed(2) + ' 秒）' : '（現場解析；' + st.why + '）'; }
if (DEBUG) {
  /** 快取對拍：船型 id 讀回的那幾份 ＝ 現在這份程式現場算的？逐位元組比（船體網格每個區塊、模型網格的頂點與佔用格、海面遮罩、浮力表、布模板）。 */
  window.__game.hullCheck = function (id) {
    var T = HULLT[id || myHull()]; if (!T) return null;
    function same(a, b) {
      if (a === b) return true;
      if (ArrayBuffer.isView(a) && ArrayBuffer.isView(b)) { if (a.length !== b.length || a.constructor !== b.constructor) return false; for (var i = 0; i < a.length; i++) if (a[i] !== b[i] && !(a[i] !== a[i] && b[i] !== b[i])) return false; return true; }
      if (!a || !b || typeof a !== 'object' || typeof b !== 'object' || Array.isArray(a) !== Array.isArray(b)) return a !== a && b !== b;
      var ka = Object.keys(a), kb = Object.keys(b); if (ka.length !== kb.length) return false;
      return ka.every(function (k) { return same(a[k], b[k]); });
    }
    var g = T.base, r = { id: T.id, cached: T.cached, chunks: 0, chunkDiff: 0, quads: T.pristine.quads() };
    for (var cz = 0; cz < g.nz; cz++) for (var cy = 0; cy < g.ny; cy++) for (var cx = 0; cx < g.nx; cx++) {
      var i = g.ci(cx, cy, cz); if (g.tab[i] === null) continue;
      var m = VK.meshChunk(g, cx, cy, cz), c = T.pristine.meshes.get(i); r.chunks++;
      if (!(m ? c && same(m, c) : !c)) r.chunkDiff++;
    }
    r.hullMask = same(hullMask(T), T.hullHB);
    var H = { base: g, zw: T.zw }; hydrostatics(H); r.hyd = same(H.hyd, T.hyd) && H.disp === T.disp;
    r.models = (T.rig.meshes || []).map(function (m, k) {
      var tri = meshTris(m), got = new Float32Array(tri.length); gl.bindBuffer(gl.ARRAY_BUFFER, T.meshes[k].vbo); gl.getBufferSubData(gl.ARRAY_BUFFER, 0, got);
      return same(tri, got) && same(meshOcc(m), T.meshes[k].occ);
    }).filter(function (ok) { return !ok; }).length + ' 份不同／' + (T.rig.meshes || []).length;
    r.rbox = same(T.rig.ropes.map(function (rp) { return ropeBox(rp.pts); }), T.rbox);
    r.cloth = T.rig.sails.map(function (s, k) { return same(clothTemplate(T, s), T.cloth[k]); }).filter(function (ok) { return !ok; }).length + ' 面不同／' + T.rig.sails.length;
    return r;
  };
}
var t0 = performance.now();
function say(s) { $('load').textContent = s; }
say('解碼船體…');
programs(); geometry(); wpGL(); flGL(); rdGL(); bbSetup(); QIDX = new VK.QuadIndex(gl);
hullSay = function (s) { var go = $('go'); if (go.disabled) go.textContent = '解析' + s; };   // 解析中：開戰鈕寫進度（設定照樣能調）
requestAnimationFrame(frame);                                       // 解析中也畫（天、海；船載好才有）
yieldUI().then(function () {                                        // 先讓主選單畫出來，再開始解析
  return Promise.all(fleetHulls().map(loadHull));                   // 只載編成裡的船（預設兩艘都是憲法號 ⇒ 一份）
}).then(function () {
  var T = HULLT[myHull()], h = T.h, chk = T.chk;
  if (SLIDERS_SHOW) SLIDERS_SHOW();
  var line = '1:1 ' + T.name + ' ' + chk.voxels.toLocaleString() + ' 格 checksum ' + chk.checksum.toString(16) + (chk.ok ? '（＝ 封裝檔 header，逐格相同 ✓）' : '（✗ 跟封裝檔對不上：' + h.voxels + '／' + h.checksum.toString(16) + '）') +
    '\n合併後 ' + T.pristine.quads().toLocaleString() + ' 個四邊形、繩 ' + T.rig.ropes.length + '、帆 ' + T.rig.sails.length + '、桅 ' + T.masts.length +
    '\n解碼 ' + (T.decodeMs / 1000).toFixed(2) + ' 秒、網格化 ' + (T.meshMs / 1000).toFixed(2) + ' 秒' + cacheText(hullInfo(T.id).cache) +
    '\n設定：' + PREFS.state;
  say(line); window.__vxk = { verify: chk, quads: T.pristine.quads(), masts: T.masts.length, decodeMs: +T.decodeMs.toFixed(1), meshMs: +T.meshMs.toFixed(1), ms: T.ms,
    cache: hullInfo(T.id).cache, prefs: PREFS.state };
  loadArt().then(function (why) { line += '\n素材：' + why; say(line); window.__vxk.art = why; if (HUD_ART) hudArt(); });
  if (!chk.ok) { fail('船體資料跟封裝檔對不上，停下來（不畫半艘船）。\n' + line); return; }
  $('go').disabled = false; $('go').textContent = '開戰';
  if (DEMO >= 0) {                                             // 快轉：電腦對電腦、固定步長
    MODE = 'eve'; reset(); RUNNING = true;
    var steps = Math.round(DEMO / DT), phys = PHYS, from = Math.max(0, steps - 360);     // 帆與繩只畫最後那一格 ⇒ 物理只在最後 6 秒跑（不影響戰局）
    if (phys && from > 0) setPhys(false);
    // ?dump=1：每半秒記每艘的最大橫傾、開始沉／沉沒／降旗的時間，跑完寫進頁面（#dump；無頭 Chrome --dump-dom 讀，量進水模式用）
    var rec = Q.get('dump') === '1' ? SHIPS.map(function () { return { maxList: 0, maxPre: 0, maxSinkPre: 0, final: null, sunk: null, struck: null }; }) : null;
    for (var i = 0; i < steps; i++) {
      if (phys && i === from && from > 0) setPhys(true); step(); if (i % 30 === 29) remesh(Infinity);
      if (rec && i % 30 === 29) SHIPS.forEach(function (sh, k) { var r = rec[k]; r.maxList = Math.max(r.maxList, Math.abs(sh.rollA)); if (!sh.sinkingFinal) { r.maxPre = Math.max(r.maxPre, Math.abs(sh.rollA)); r.maxSinkPre = Math.max(r.maxSinkPre, sh.sink); r.maxPctPre = Math.max(r.maxPctPre || 0, floodPct(sh)); } if (sh.sinkingFinal && r.final === null) r.final = +SIMT.toFixed(1); if (sh.sunk && r.sunk === null) r.sunk = +SIMT.toFixed(1); if (sh.struck && r.struck === null) r.struck = +SIMT.toFixed(1); });
    }
    remesh(Infinity); RUNNING = false; $('cover').style.display = 'none';
    if (rec) { var pre = document.createElement('pre'); pre.id = 'dump'; document.body.appendChild(pre);
      pre.textContent = JSON.stringify({ seed: SEED, t: +SIMT.toFixed(1), flood: FLOOD_LV, ships: SHIPS.map(function (sh, k) { var r = rec[k];
        return { maxListDeg: +(r.maxList * 57.3).toFixed(1), maxPreDeg: +(r.maxPre * 57.3).toFixed(1), maxSinkPre: +r.maxSinkPre.toFixed(2), maxPctPre: Math.round((r.maxPctPre || 0) * 100), final: r.final, sunk: r.sunk, struck: r.struck, fate: sh.fate, lost: sh.lost, hits: sh.hits, dead: sh.dead, cart: sh.cartN || 0, magGone: sh.mags.filter(function (m) { return m.gone; }).length, mastsDown: sh.masts.filter(function (m) { return !m.up; }).length, sink: +sh.sink.toFixed(2), water: sh.fl ? Math.round(sh.fl.vol * RHO_W) : null, area: sh.fl ? +sh.fl.area.toFixed(1) : null, inflow: sh.inflow }; }) }); }
    window.__vxk.demo = { t: SIMT, lost: SHIPS.map(function (s) { return s.lost; }), pieces: PIECES.length, debris: D.n };
  } else {
    // 選單後面先擺好兩艘船當背景
    reset();
  }
}).catch(function (e) { fail('載入失敗：' + (e && e.message || e)); console.error(e); });
// ── D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m/design/game_fixture/probe.js ──

var fixtureProbe = setInterval(function () {
  if (!window.__vxk || !window.__vxk.demo) return;
  clearInterval(fixtureProbe);
  var out = {gameVerify: window.__vxk.verify, glError:gl.getError(), simt:SIMT,
    ships:SHIPS.map(function(s){return {name:s.T.name,voxels:s.T.base.count, waterline:s.T.zw,
      mass:s.mass0, designDisplacement:s.T.disp, lift:s.lift, sink:s.sink,
      masts:s.masts.length, sails:s.sails.length, models:s.models.length,
      crew:s.crew.length, helms:s.crew.filter(function(c){return c.role===ROLE.HELM;}).length,
      mags:s.mags.map(function(m){return {name:m.name,lb:m.lb,kegs:m.kegs.length};}),
      ladders:s.nav?s.nav.ladders.length:0, ladderNames:s.nav?s.nav.ladders.map(function(l){return l.name;}):[],
      guns:s.guns.map(function(g){return {name:g.name,type:g.type,spots:g.spots.length,min:g.crewMin,alive:g.alive};}),
      modelsWithNoFoot:s.models.filter(function(m){return m.foot<0;}).map(function(m){return m.path;})};})};
  var pre=document.createElement('pre');pre.id='tidegrave-fixture-report';pre.textContent=JSON.stringify(out);document.body.appendChild(pre);
}, 50);
})();
