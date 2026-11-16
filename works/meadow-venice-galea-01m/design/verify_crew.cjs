const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const d = __dirname;
const src = fs.readFileSync(process.argv[2], "utf8");
const assemblyVoxels = fs.readFileSync(process.argv[3], "utf8");
const engineCode = src.slice(src.indexOf("function standZ("), src.indexOf("function crewBlockOf(")) +
    src.slice(src.indexOf("function oarCrew("), src.indexOf("function stokerCrew("));
const oarCrew = new Function("ROLE", "oarRowers", engineCode + "\nreturn oarCrew")({OAR: 10, GUN: 0}, m => m.meta.rowers);
const occupancy = new Set();
for (const line of assemblyVoxels.split(/\r?\n/)) {
    const parts = line.trim().split(",");
    if (parts.length === 4 && /^\d+$/.test(parts[0])) occupancy.add(parts.slice(0, 3).join(","));
}
const g = {get: (x, y, z) => occupancy.has([x, y, z].join(","))};
const rows = JSON.parse(fs.readFileSync(path.join(d, "oar_layout.json"), "utf8"));
const models = rows.map(r => ({kind: "oar", meta: {rowers: 4},
    pts: {pivot: r.pivot, seat: r.seat, blade: r.blade}}));
const sh = {models, T: {cy: 160.5}};
const crew = [];
oarCrew(sh, g, {}, crew, (role, at) => crew.push({role, at}));
assert.equal(sh.oarWant, 196);
assert.equal(crew.length, 196);
let direct = 0;
for (let i = 0; i < rows.length; i++) {
    for (let j = 0; j < 4; j++) {
        const [x, y] = rows[i].seat;
        const expected = [x, y - rows[i].side * 6 * j, 23];
        if (crew[i * 4 + j].at.every((v, k) => v === expected[k])) direct++;
    }
}
assert.equal(direct, 196);
const summary = {oars: models.length, want: sh.oarWant, stood: crew.length, direct, static_voxels: occupancy.size};
fs.writeFileSync(path.join(d, "verify_crew.json"), JSON.stringify(summary, null, 2) + "\n");
console.log(summary);
