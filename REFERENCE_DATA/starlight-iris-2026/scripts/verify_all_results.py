#!/usr/bin/env python3
"""Processed-table consistency validator (not a provenance authenticator)."""
from __future__ import annotations
import sys, hashlib, csv
from pathlib import Path
import numpy as np
import pandas as pd
from numpy.polynomial.polynomial import polyfit

ROOT = Path(__file__).resolve().parents[1]
ok = True
notes = []

def check(label, cond, detail=""):
    global ok
    if not cond:
        ok = False
    print(f"[{'PASS' if cond else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))

def not_checked(label, reason):
    print(f"[NOT CHECKED] {label} — {reason}")
    notes.append(label)

def main():
    grid = pd.read_csv(ROOT/"simulation/primary_grid.csv")
    conf = pd.read_csv(ROOT/"simulation/confirmation.csv")
    mf = pd.read_csv(ROOT/"simulation/model_forms.csv")

    check("66 grid rows", len(grid)==66)
    check("grid unique condition_id", grid.condition_id.is_unique)
    check("n_plus+n_minus <= n_pairs (grid)", bool(((grid.n_plus+grid.n_minus)<=grid.n_pairs).all()))
    check("grid has no both_succeed/both_fail", "both_succeed" not in grid.columns and "both_fail" not in grid.columns)
    check("conf has no both_succeed/both_fail", "both_succeed" not in conf.columns and "both_fail" not in conf.columns)
    vc = grid.certificate_label.value_counts()
    check("labels 8A/29D/29U", int(vc.get("A",0))==8 and int(vc.get("D",0))==29 and int(vc.get("unresolved",0))==29)
    check("no Clock/Compass sim cols", "controller" not in grid.columns)

    # model forms
    check("15 model-form rows", len(mf)==15)
    non = mf[mf.is_base_repeat==0]
    check("12 non-base", len(non)==12)
    check("non-base n_pairs=4000", set(non.n_pairs)=={4000})
    check("missions_additional == 2*n_pairs", bool((non.missions_executed_additional==2*non.n_pairs).all()))
    calc = (mf.n_plus-mf.n_minus)/mf.n_pairs*100
    check("model-form deltas match counts", float((calc-mf.delta_pp).abs().max())<1e-6)
    # base rows match grid discordances
    for _, row in mf[mf.is_base_repeat==1].iterrows():
        g = float(row.gain_g)
        match = grid[(np.isclose(grid.gain_g,g)) & (np.isclose(grid.stress_s,0.03)) & (np.isclose(grid.timestep_s,0.04))]
        if len(match)==1:
            m = match.iloc[0]
            check(f"base g={g} matches grid n+/n-",
                  int(m.n_plus)==int(row.n_plus) and int(m.n_minus)==int(row.n_minus))
        else:
            check(f"base g={g} found in grid", False, f"matches={len(match)}")
    not_checked("model-form CI family derivation", "interval endpoints depend on multiplicity procedure not recomputed here")

    # confirmation
    w = conf.loc[conf.setting_id.str.contains("1.200_s030")].iloc[0]
    check("confirm 1.200 witness", int(w.n_plus)==90 and int(w.n_minus)==6 and abs(float(w.delta_pp)-1.05)<1e-9)
    w = conf.loc[conf.setting_id.str.contains("1.260_s030")].iloc[0]
    check("confirm 1.260 witness", int(w.n_plus)==59 and int(w.n_minus)==293 and abs(float(w.delta_pp)+2.925)<1e-9)
    w = conf.loc[conf.setting_id.str.contains("1.245")].iloc[0]
    check("confirm 1.245 87/31", int(w.n_plus)==87 and int(w.n_minus)==31)
    w = conf.loc[conf.setting_id.str.contains("1.255")].iloc[0]
    check("confirm 1.255 67/93", int(w.n_plus)==67 and int(w.n_minus)==93)
    check("conf missions=2*n_pairs", bool((conf.missions_executed==2*conf.n_pairs).all()))
    check("conf n_plus+n_minus <= n_pairs", bool(((conf.n_plus+conf.n_minus)<=conf.n_pairs).all()))

    total = int(grid.missions_executed.sum())+int(conf.missions_executed.sum())+int(mf.missions_executed_additional.sum())
    check("752000 missions", total==752000, str(total))

    attr = pd.read_csv(ROOT/"simulation/attribution.csv")
    check("attribution gain~0.7313", abs(float(attr.loc[attr.factor=="gain_g","variance_share"].iloc[0])-0.7313)<1e-4)
    check("attribution sum~1", abs(float(attr.variance_share.sum())-1)<1e-3)

    # WP1
    wp1 = pd.read_csv(ROOT/"physical/wp1/emergency_stop_trips.csv")
    check("WP1 10/10 initial", int(wp1.loc[wp1.cohort=="initial_gate","motor_cut_confirmed"].sum())==10)
    check("WP1 23/24 confirmed", int(wp1.motor_cut_confirmed.sum())==23 and len(wp1)==24)
    check("WP1 ES_12 failed", int(wp1.loc[wp1.trip_id=="ES_12","motor_cut_confirmed"].iloc[0])==0)
    check("WP1 mean latency ~14.2 on successes", abs(float(wp1.cut_latency_ms.dropna().mean())-14.2)<0.5)
    check("WP1 failed trip has null latency", pd.isna(wp1.loc[wp1.trip_id=="ES_12","cut_latency_ms"].iloc[0]))

    # WP3 quantiles
    cam = pd.read_csv(ROOT/"physical/wp3/dock_camera_accuracy.csv")
    p95h = float(np.percentile(cam.heading_error_deg, 95))
    p95p = float(np.percentile(cam.position_error_mm, 95))
    check("WP3 position p95~2.48", abs(p95p-2.48)<0.01, f"{p95p:.3f}")
    check("WP3 heading p95~1.286", abs(p95h-1.286)<0.01, f"{p95h:.3f}")
    check("WP3 heading FAIL vs 1.0", p95h > 1.0)

    # WP4
    cc = pd.read_csv(ROOT/"physical/wp4/clock_compass_pairs.csv")
    def mean(sess, cond, ctrl):
        return float(cc[(cc.session==sess)&(cc.condition==cond)&(cc.controller==ctrl)].heading_shift_deg.mean())
    def n(sess, cond, ctrl):
        return int(((cc.session==sess)&(cc.condition==cond)&(cc.controller==ctrl)).sum())
    check("WP4 dial n=22", n("dial_pilot","mismatch","Clock")==22)
    check("WP4 dial Clock 6.80", abs(mean("dial_pilot","mismatch","Clock")-6.80)<1e-6)
    check("WP4 dial Compass 1.10", abs(mean("dial_pilot","mismatch","Compass")-1.10)<1e-6)
    check("WP4 link mis Clock 6.42", abs(mean("linkage_consolidated","mismatch","Clock")-6.42)<1e-6)
    check("WP4 link mis Compass 0.48", abs(mean("linkage_consolidated","mismatch","Compass")-0.48)<1e-6)
    check("WP4 link mat n=10", n("linkage_consolidated","matched","Clock")==10)
    check("WP4 link mat Clock 6.64", abs(mean("linkage_consolidated","matched","Clock")-6.64)<1e-6)
    not_checked("WP4 vs poster pilot labels", "poster may still show 6.75/1.14; CSV-authoritative values are 6.80/1.10")

    st = pd.read_csv(ROOT/"physical/wp2/steering_calibration.csv")
    slope = float(polyfit(st.servo_command-75, st.protractor_angle_deg, 1)[1])
    check("steering~1.238", abs(slope-1.238)<5e-4, f"{slope:.6f}")
    lat = pd.read_csv(ROOT/"physical/wp2/latency_events.csv")
    check("latency 3 misses @33ms", int((lat.latency_ms>33).sum())==3)

    # The named-strategy benchmark is excluded from this public release.
    check("decision-cost caselevel intentionally absent", not (ROOT/"decision_cost/caselevel.csv").exists())
    check("decision-cost aggregated intentionally absent", not (ROOT/"decision_cost/aggregated.csv").exists())
    not_checked("seven-baseline decision-cost evaluation", "excluded due to unresolved policy definitions")

    ext = pd.read_csv(ROOT/"physical/d1/extended_shared_failure_pairs.csv")
    check("D1ext 204 rows", len(ext)==204)
    check("D1ext 160 both_fail", int((ext.outcome=="both_fail").sum())==160)
    check("D1ext unique pair_id", ext.pair_id.is_unique)
    check("D1ext exclusive outcomes", bool(((ext.clock_fail+ext.compass_fail)>=1).all()))

    # cartpole metadata-only
    check("cartpole_summary exists", (ROOT/"simulation/cartpole_summary.csv").exists())
    check("old cartpole.csv absent", not (ROOT/"simulation/cartpole.csv").exists())

    # dictionary sanity
    dd = (ROOT/"DATA_DICTIONARY.md").read_text()
    check("dictionary has no clock_failures", "clock_failures" not in dd)
    check("dictionary notes 1.286 heading", "1.286" in dd)
    check("dictionary notes ES_12 / 23/24", "23/24" in dd or "ES_12" in (ROOT/"README.md").read_text())

    # changelog must not claim mismatch inflates Clock
    cl = (ROOT/"CHANGELOG_DATA.md").read_text().lower()
    check("changelog has no 'mismatch inflates'", "mismatch inflates" not in cl)

    # Verify final release files against both independent checksum formats.
    manifest_dir = ROOT / "evidence/manifests"
    csv_path = manifest_dir / "SHA256_manifest.csv"
    sums_path = manifest_dir / "SHA256SUMS.txt"
    check("SHA256_manifest present", csv_path.is_file())
    check("SHA256SUMS present", sums_path.is_file())
    if csv_path.is_file() and sums_path.is_file():
        with csv_path.open(newline="", encoding="utf-8") as f:
            records = list(csv.DictReader(f))
        csv_hashes = {}
        verified = True
        for rec in records:
            relative = rec["path"]
            target = (ROOT / relative).resolve()
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                verified = False
                continue
            blob = target.read_bytes()
            digest = hashlib.sha256(blob).hexdigest()
            if digest != rec["sha256"] or len(blob) != int(rec["bytes"]):
                verified = False
            csv_hashes[relative] = rec["sha256"]
        check("SHA256_manifest content verification", verified and len(records) > 0,
              f"{len(records)} entries")
        sums = {}
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split("  ", 1)
            if len(parts) != 2:
                verified = False
                continue
            digest, relative = parts
            sums[relative] = digest
        check("SHA256SUMS agree with CSV manifest", verified and sums == csv_hashes)
        files = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
        excluded = {"evidence/manifests/SHA256_manifest.csv", "evidence/manifests/SHA256SUMS.txt"}
        check("manifest covers all release files", files - excluded == set(csv_hashes))
    not_checked("raw instrument authenticity", "original logs/videos not in public release")
    not_checked("simulator regeneration", "generator/seeds not in public release")

    print("----")
    if ok:
        print("ALL SUPPORTED INTERNAL CHECKS PASS")
        if notes:
            print(f"({len(notes)} item(s) marked NOT CHECKED)")
        return 0
    print("SOME CHECKS FAILED")
    return 1

if __name__ == "__main__":
    sys.exit(main())
