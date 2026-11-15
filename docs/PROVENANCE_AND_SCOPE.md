# Provenance, verification and scope

## Four independently supplied ZIP archives

1. **GitHub-safe processed research data**: canonical source of the 27 files in `REFERENCE_DATA/starlight-iris-2026/`, copied byte-for-byte. Includes 18 CSVs (17 study tables plus one raw-evidence index), verification script and internal SHA-256 manifest. Physical session window stated in the archive: 1–9 November 2026.
2. **Reconstructed Python tools**: new read-only data analysis, tests and mocked future-acquisition interfaces in `starlight/`, `tests/`, `TOOLS/`, `CONTRACTS/`, and `configs/`. These are **not recovered original November 2026 execution code**.
3. **WRO team archive**: original historical robot software and selected hardware documentation/photographs copied into `legacy/competition_2026/` without editing source files.
4. **APOC_FE archive**: original historical competition source code in `legacy/competition_2026/apoc/`.

The separately supplied 27-page manuscript dated 12 November 2026 is copied into `paper/` byte-for-byte.

## Verification levels

- **Byte integrity:** the published processed reference files are unchanged relative to the original input archive; the source archive already includes checksums, and the final package includes its own release-wide checksum inventory.
- **Internal consistency:** source validator and replay tests check CSV schemas, arithmetic, expected outputs and code behavior. They cannot prove the original observations are authentic.
- **Independent recreation:** the original simulator/seed bank, full raw instrumentation and complete video lineage are **not** supplied. A replay of processed sufficient statistics is not independent reproduction of 752,000 simulator executions.
- **Claims requiring reconciliation:** historical decision-cost benchmarking, exact original policy definitions, a few archived interval endpoints and unresolved raw-video crosswalks remain outside what this public release establishes.

## Strict labels

- **A / D** refer exclusively to simulated architecture bundles.
- **Clock / Compass** refer to physical docking controllers.
- **S1 / S2 / S3** refer to colour sorter recipes.
- The physical steering slope of approximately 1.238 is not automatically the same parameter as simulated gain `g`.
- Simulation intervals cover the specified *finite model family*, not real-world vehicle reliability.

See `docs/CLAIMS_AND_LIMITATIONS.md` and `reports/RECONSTRUCTION_VS_ORIGINAL.md`.
