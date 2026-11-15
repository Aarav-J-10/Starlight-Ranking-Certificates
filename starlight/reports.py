import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
from uuid import uuid4

from . import __version__
from .analysis import DATASETS, grouped
from .schema import Schema, require, units


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def snapshot(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def verify_manifests(project: Path, root: Path) -> dict:
    checks = {}
    paths = (project / "MANIFEST_SHA256.csv", root / "evidence/manifests/SHA256_manifest.csv")
    for manifest in paths:
        base = project if manifest.parent == project else root
        records = list(csv.DictReader(manifest.open(encoding="utf-8", newline="")))
        for record in records:
            target = (base / record["path"]).resolve()
            require(target.is_relative_to(base.resolve()), "Manifest path escapes source")
            blob = target.read_bytes()
            require(hashlib.sha256(blob).hexdigest() == record["sha256"] and len(blob) == int(record["bytes"]), f"Hash mismatch: {target}")
        checks[manifest.name] = len(records)
    listed = {r["path"]: r["sha256"] for r in records}
    sums = dict(line.split("  ", 1)[::-1] for line in (root / "evidence/manifests/SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if line.strip())
    require(sums == listed, "Release manifests disagree")
    actual = set(snapshot(root)) - {"evidence/manifests/SHA256_manifest.csv", "evidence/manifests/SHA256SUMS.txt"}
    require(actual == set(listed), "Release manifest coverage mismatch")
    return checks


def manifest(kind: str, hashes: dict, config: dict | None = None) -> dict:
    config = config or {}
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    dependencies = {}
    for package in ("scipy", "numpy", "pandas", "matplotlib", "pytest", "opencv-contrib-python"):
        try:
            dependencies[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            pass
    return {"label": kind, "implementation": "reconstructed_implementation", "software_build": __version__, "git_commit": commit,
            "implementation_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob("*.py"))},
            "git_note": "No commit available" if commit is None else "Source may include uncommitted changes; source hashes identify delivered files",
            "created_at": datetime.now(timezone.utc).isoformat(), "timezone": "UTC", "operator": config.get("operator"),
            "apparatus_revision": config.get("apparatus_revision"), "calibration_file": config.get("calibration_file"),
            "sensors": config.get("sensors", []), "pins": config.get("pins", {}), "video_pointers": config.get("video_pointers", []),
            "log_pointers": config.get("log_pointers", []), "recording_program_version": __version__, "paired_session_ids": config.get("paired_session_ids", []),
            "consent_flags": config.get("consent_flags", {}), "source_sha256": hashes, "dependencies": dependencies}


def new_output(base: Path, name: str, root: Path) -> Path:
    protected = root.parent if root.parent.name == "REFERENCE_DATA" else root
    require(not base.resolve().is_relative_to(protected.resolve()), "Output cannot be inside REFERENCE_DATA")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = base / name / f"{stamp}-{uuid4().hex[:6]}"
    target.mkdir(parents=True, exist_ok=False)
    return target


def plot(name: str, tables: dict, summary: dict, target: Path) -> None:
    target.mkdir()
    if name in {"cartpole", "evidence"}:
        (target / "README.txt").write_text("Metadata only; no performance figure can be reconstructed.\n", encoding="utf-8")
        return
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        (target / "SKIPPED.txt").write_text('Figures need: python -m pip install -e ".[science]"\n', encoding="utf-8")
        return
    rows = tables[DATASETS[name][0]]
    fig, ax = plt.subplots(figsize=(9, 4.8), layout="constrained")
    extra = None
    if name == "model-forms":
        plt.close(fig)
        fig, (ax, extra) = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True, layout="constrained")
    if name in {"primary-grid", "confirmation", "model-forms"}:
        if name == "primary-grid":
            for key, group in grouped(rows, "stress_s", "timestep_s").items():
                ax.scatter([r["gain_g"] for r in group], [r["delta_pp"] for r in group], label=f"s={key[0]}, dt={key[1]}", s=18)
        else:
            groups = grouped(rows, "model_form") if name == "model-forms" else {("common s=.030, dt=.040",): [r for r in rows if r["stress_s"] == .03 and r["timestep_s"] == .04]}
            for key, group in groups.items():
                chart = extra if key[0] == "clearance" else ax
                y = [r["delta_pp"] for r in group]
                chart.errorbar([r["gain_g"] for r in group], y, yerr=[[r["delta_pp"] - r["ci_low_pp"] for r in group], [r["ci_high_pp"] - r["delta_pp"] for r in group]], fmt="o", linestyle="none", label=key[0])
        ax.axhline(0, color="gray", linewidth=.8)
        ax.set(xlabel="Simulated gain g", ylabel="D minus A failure risk (pp)")
        ax.legend(fontsize=7)
        if name == "model-forms":
            ax.set_title("Model specifications (base included)")
            extra.set(title="Clearance: changed failure criterion", xlabel="Simulated gain g")
            extra.axhline(0, color="gray", linewidth=.8)
            extra.legend(fontsize=7)
    elif name == "wp4":
        for i, (key, group) in enumerate(grouped(rows, "session", "condition").items()):
            for pair in grouped(group, "pair_id").values():
                values = {r["controller"]: r["heading_shift_deg"] for r in pair}
                ax.plot([2 * i, 2 * i + .7], [values["Clock"], values["Compass"]], "o-", alpha=.35, markersize=3)
        labels = list(grouped(rows, "session", "condition"))
        ax.set_xticks([2 * i + .35 for i in range(len(labels))], ["\n".join(k) + "\nClock / Compass" for k in labels], fontsize=8)
        ax.set_ylabel("Recorded heading-shift magnitude (degrees)")
    elif name == "wp7":
        for i, (phase, group) in enumerate(grouped(rows, "phase").items()):
            values = [r["measured_gain_response"] for r in group]
            ax.scatter([i + (j - 5.5) * .012 for j in range(len(values))], values, s=14)
            from statistics import mean, stdev
            ax.errorbar(i, mean(values), yerr=stdev(values), fmt="ko", capsize=6)
        ax.set_xticks(range(3), [k[0] for k in grouped(rows, "phase")])
        ax.set_ylabel("Steering response (dimensionless); magnified axis, mean +/- SD")
    elif name == "wp6":
        ax.set_axis_off()
        for i, r in enumerate(rows):
            x, y = i % 5, 1 - i // 5
            ax.add_patch(plt.Rectangle((x, y), .95, .9, color="#b6dccb" if r["agreement"] else "#f2b9aa"))
            ax.text(x + .475, y + .45, f'{r["unit_id"]}\n{r["decision"]}\nref: {r["reference_outcome"]}', ha="center", va="center", fontsize=7)
        ax.set(xlim=(-.1, 5), ylim=(-.1, 2))
    elif name == "wp8":
        keys = ["S1_fixed", "S2_calibrated", "S3_recheck"]
        ax.bar(keys, [100 * summary[k]["accuracy"] for k in keys])
        ax.set(ylabel="Correct / pooled items (%)", ylim=(0, 100))
    elif name == "wp5":
        ax.bar([r["session"] for r in rows], [r["clock_success"] for r in rows], width=.4, label="Clock")
        ax.plot([r["session"] for r in rows], [r["compass_success"] for r in rows], "o", label="Compass")
        ax.set(ylabel="Successes / 12 paired scenarios", ylim=(0, 12))
        ax.legend()
    elif name == "d1":
        categories = ("both_succeed", "both_fail", "clock_only", "compass_only")
        ax.bar(categories, [summary["detailed"][c] for c in categories], label="Detailed 60")
        ax.plot(categories, [summary["extended"][c] for c in categories], "o", label="Extended 204; separate study")
        ax.set_ylabel("Pairs; separate denominators")
        ax.legend()
    elif name == "attribution":
        ax.barh([r["factor"] for r in rows], [r["variance_share"] for r in rows])
        ax.set_xlabel("Reported finite-grid variance share; descriptive")
    elif name == "wp2-steering":
        for key, group in grouped(rows, "sweep_direction").items():
            ax.scatter([r["servo_command"] - 75 for r in group], [r["protractor_angle_deg"] for r in group], s=14, label=key[0])
        ax.set(xlabel="Command minus 75 (command units)", ylabel="Protractor angle (degrees)")
        ax.legend()
    else:
        column = {"wp1": "cut_latency_ms", "wp2-latency": "latency_ms", "wp3": "heading_error_deg"}[name]
        ax.plot([i + 1 for i, r in enumerate(rows) if r[column] is not None], [r[column] for r in rows if r[column] is not None], ".")
        ax.set(xlabel="Archived observation index", ylabel=f"{column} ({units(column)})")
        if name == "wp3":
            ax.axhline(1, color="red", label="1 degree heading gate")
            ax.legend()
    if not ax.get_title():
        ax.set_title(name + " | processed replay")
    fig.savefig(target / "summary.svg")
    fig.savefig(target / "summary.png", dpi=120)
    plt.close(fig)
    if name in {"confirmation", "wp3", "wp7"}:
        fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
        if name == "confirmation":
            companions = [r for r in rows if r["stress_s"] != .03 or r["timestep_s"] != .04]
            ax.errorbar(range(len(companions)), [r["delta_pp"] for r in companions], yerr=[[r["delta_pp"] - r["ci_low_pp"] for r in companions], [r["ci_high_pp"] - r["delta_pp"] for r in companions]], fmt="o")
            ax.set_xticks(range(len(companions)), [f'g={r["gain_g"]}, s={r["stress_s"]}, dt={r["timestep_s"]}' for r in companions], fontsize=8)
            ax.set(title="Companion confirmation settings; stored intervals", ylabel="D minus A failure risk (pp)")
        elif name == "wp3":
            ax.plot([r["position_error_mm"] for r in rows], ".")
            ax.axhline(2.5, color="red", label="2.5 mm gate")
            ax.set(title="Camera position error", xlabel="Archived observation index", ylabel="Position error (mm)")
            ax.legend()
        else:
            from statistics import mean, stdev
            for i, (phase, group) in enumerate(grouped(rows, "phase").items()):
                values = [r["servo_current_A"] for r in group]
                ax.scatter([i + (j - 5.5) * .012 for j in range(len(values))], values, s=14)
                ax.errorbar(i, mean(values), yerr=stdev(values), fmt="ko", capsize=6)
            ax.set_xticks(range(3), [k[0] for k in grouped(rows, "phase")])
            ax.set(title="Servo current by phase; mean +/- SD", ylabel="Current (A); magnified axis")
        fig.savefig(target / "supplement.svg")
        fig.savefig(target / "supplement.png", dpi=120)
        plt.close(fig)


def write_replay(schema: Schema, tables: dict, summaries: dict, names: list[str], output: Path, checks: list[dict], hashes: dict) -> None:
    dump(output / "expected_comparison.json", checks)
    audits = []
    for name in names:
        directory = output / name
        directory.mkdir()
        summary = dict(summaries[name], label="processed_replay", experiment=name,
                       timestamp_provenance="Archived naive timestamps; release describes Asia/Kolkata (IST). No timezone was recorded in individual CSV timestamps.",
                       source_files=list(DATASETS[name]), units={c: units(c) for k in DATASETS[name] for c in schema.spec[k]["columns"] if c in tables[k][0] and isinstance(tables[k][0][c], (int, float))},
                       missing={k: {c: sum(r[c] is None for r in tables[k]) for c in schema.spec[k]["columns"] if any(r[c] is None for r in tables[k])} for k in DATASETS[name]})
        dump(directory / "summary.json", summary)
        text = f"# {name}\n\nProcessed replay of immutable archived CSVs.\n\n" + summary.get("notes", "D1 studies are separate; overlap unknown.") + "\n\n```json\n" + json.dumps(summary, indent=2, default=str) + "\n```\n"
        (directory / "summary.md").write_text(text, encoding="utf-8")
        dump(directory / "run_manifest.json", manifest("processed_replay", {k: hashes[k] for k in DATASETS[name]}))
        for key in DATASETS[name]:
            target = directory / "csv" / key
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as file:
                file.write((schema.root / key).read_bytes())
        plot(name, tables, summary, directory / "figures")
        audits.extend(dict(experiment=name, **r) for r in summary.get("interval_audit", []))
    dump(output / "interval_discrepancies.json", audits)
    lines = ["# Interval audit", "", "New explicit Bonferroni marginal CP calculation; historical tail allocation is not version-locked.", "", "| Dataset / ID | Stored pp | Recomputed pp | Differs beyond .00051 pp |", "|---|---|---|---|"]
    for r in audits:
        bounds = r["recomputed_pp"]
        rendered = "unavailable; install science extra" if bounds is None else f"[{bounds[0]:.6f}, {bounds[1]:.6f}]"
        lines.append(f'| {r["experiment"]} / {r["id"]} | {r["stored_pp"]} | {rendered} | {r["discrepancy"]} |')
    (output / "INTERVAL_DISCREPANCIES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    dump(output / "run_manifest.json", manifest("processed_replay", hashes))
