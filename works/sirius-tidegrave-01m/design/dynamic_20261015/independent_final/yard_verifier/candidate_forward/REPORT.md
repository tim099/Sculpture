# Forward feet with original .04 lowest ratio: FAIL at lowest ratline

Six proposed feet are all original body solid cells: P [290.5,70.5,128.5], [310.5,70.5,128.5], [330.5,69.5,128.5]; S [290.5,170.5,128.5], [310.5,170.5,128.5], [330.5,171.5,128.5]. All connect to original P/S hounds [205.5,116.5/124.5,260.5].

All 48 proposed lines clear all ten yards across complete continuous absolute square [-.7,.7] and gaff/boom [-1.4,1.4] ranges. 4,304 intervals, 3,380 disjoint leaves, 0 unresolved. The two lowest ratlines at ratio .04 each contact 7 body rail voxels. The other 40 ratlines clear body. See sibling candidate_forward065 for the verified correction of only these two ratios to .065.

All 38 shroud/body contacts occur within 1.596245 voxels of a shroud endpoint, with exact cube coordinates, segment parameter, distance and witness in report.json. These contacts are not erased from the data. check.py conservatively tags only contacts <=1.0 voxel as attachment candidates; the P/S0 additional hounds corners remain explicitly outside that tag. See the corrected candidate report for detail.

Run check.py to reproduce. It reads ../input via its parent directory and writes only this candidate folder. The independent exact segment/AABB and Lipschitz rotating-cuboid method is documented in ../candidate/REPORT.md.
