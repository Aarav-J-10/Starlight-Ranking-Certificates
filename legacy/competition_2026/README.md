# Historical Starlight competition code (2026)

These files were supplied as snapshots of the team's WRO Future Engineers and APOC development sources. They are **historical controller implementations**, not the missing original Starlight research experiment acquisition, simulator generator, or hardware-validation scripts. Their presence is evidence of engineering development, not a claim that they produced the November 2026 research CSVs.

- `wro/*.py`: originals from the supplied **World-Robot-Olympiad---Team-Sentio--main** ZIP; not edited.
- `apoc/*.py`: originals from the supplied **APOC_FE** ZIP; includes an empty `open_22.py` as delivered.
- `vehicle_photos/`: physical prototype views; do not assume every photograph shows the same late-stage sensor or linkage revision.
- `circuit_diagram.png`, `models/*.stl`, `historical_hardware/`, `failure_log_original.md`, `WRO_2026_original_README.md`: historical materials, preserved without altering their technical claims.
- Historical public robot demonstration provided in the WRO archive: https://youtu.be/L8zsNdFoFtE

**Safety:** Do not execute historic GPIO/motor/servo code on connected hardware without independently checking current wiring, motor polarity, power rails, emergency stop and tested limits. The reconstructed analysis at the repository root is read-only by default; it does not drive the robot.

The original WRO snapshot did not include a reuse license. Redistribution/permission for contributors, photos and software must be checked before making this repository public; see `docs/RIGHTS_AND_PUBLICATION.md`.
