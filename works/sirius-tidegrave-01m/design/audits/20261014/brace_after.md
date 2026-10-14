# Brace after final anchor repair — PASS

After snapshot SHA256 `5e92885eb98c095b41f21d80e0f69e287206e55be7815fe27c6a4e8abc42f8d1`. Independent body count 1,036,066; checksum `bdd5856b`.

`main-topgallant.brace-S` now ends at `(335.5,170.5,136.5)`, radius 0.2. Exact capsule/unit-box test of the complete exported curve reports **zero interior collisions**. One collision remains at occupied endpoint cell `(335,170,136)`, the intended top-of-post attachment. The previous four post-interior collisions are gone.

Before evidence remains in `final_audit.json` / `FINAL.md` (snapshot `9f079ab5…`). After evidence is `brace_after.json`.

Limited delta checks: all eleven other previously checked rope curves, endpoint names, and radii match exactly; body voxel count/checksum and flag bounding box match. Parent confirms only this named anchor changed. Previous flag/support/ornament static conclusions therefore remain applicable within that reported change scope. Full body connectivity/air and full flag triangle tests were not rerun for this single-anchor change. Dynamic model sweep, mesh-to-mesh interference and gameplay human routes remain outside this verifier's proved scope.
