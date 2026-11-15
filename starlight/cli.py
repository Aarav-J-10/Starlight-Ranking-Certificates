import argparse
import json
from pathlib import Path
import sys

from .acquisition import dry_run, live_hardware
from .analysis import DATASETS, compute, expected_comparison
from .decision import PolicyConfig, decide
from .reports import dump, manifest, new_output, snapshot, verify_manifests, write_replay
from .schema import Schema, require


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Starlight processed-data replay and safe future-run interfaces")
    parser.add_argument("command", nargs="?", default="replay", help="replay, validate, acquire, decision, or experiment name")
    parser.add_argument("experiment", nargs="?", default=None)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--mode", choices=("replay", "validate", "acquire"))
    modes.add_argument("--replay", dest="mode", action="store_const", const="replay")
    modes.add_argument("--validate", dest="mode", action="store_const", const="validate")
    modes.add_argument("--acquire", dest="mode", action="store_const", const="acquire")
    parser.add_argument("--reference-root", type=Path, default=Path("REFERENCE_DATA/starlight-iris-2026"))
    parser.add_argument("--contracts", type=Path)
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    parser.add_argument("--config", type=Path, help="JSON configuration")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--enable-hardware", action="store_true")
    parser.add_argument("--arm", action="store_true")
    parser.add_argument("--fresh", action="store_true", help="Validate fresh CSVs without historical counts/results")
    args = parser.parse_args(argv)
    try:
        config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
        if args.command == "decision":
            require(bool(config), "insufficient_configuration: --config policy JSON required")
            result = decide(config["difference_pp"], config["reliability_a"], config["reliability_d"], PolicyConfig(**config["policy"]))
            print(json.dumps(result, indent=2))
            return 0
        mode = args.mode or (args.command if args.command in ("replay", "validate", "acquire") else "replay")
        name = args.experiment or ("all" if args.command in ("replay", "validate", "acquire") else args.command)
        require(name in DATASETS or name == "all", f"Unknown experiment {name}; choices: all, {', '.join(DATASETS)}")
        names = list(DATASETS) if name == "all" else [name]
        schema = Schema(args.reference_root, args.contracts)
        before = snapshot(schema.root)
        if mode == "acquire":
            require(name not in {"all", "primary-grid", "confirmation", "model-forms", "attribution", "cartpole", "evidence"}, "Choose one physical experiment; no historical simulation generator is available")
            if not args.dry_run:
                require(args.enable_hardware and args.arm and config, "Live acquisition needs --enable-hardware --arm --config and verified commissioning")
                live_hardware(config, args.enable_hardware, args.arm)
            output = new_output(args.out, name, schema.root)
            result = dry_run(output, name, args.seed)
            dump(output / "summary.json", result)
            dump(output / "run_manifest.json", manifest("TEST_ONLY", before, config))
            require(snapshot(schema.root) == before, "Reference files changed")
            print(f"TEST_ONLY dry run: {output}")
            return 0
        require(not args.enable_hardware and not args.arm, "Hardware flags are only valid in acquire mode")
        if args.fresh:
            require(mode == "validate", "--fresh is for validation only; archived replay remains separate")
            for target in names:
                for key in DATASETS[target]:
                    schema.read(key, archived=False)
            print("PASS: fresh schemas; historical targets not applied")
            return 0
        integrity = verify_manifests(schema.contracts.parent, schema.root)
        tables, summaries = compute(schema, args.seed)
        checks = expected_comparison(schema, summaries, tables)
        require(all(c["pass"] for c in checks), "Expected-result mismatch: " + str([c for c in checks if not c["pass"]]))
        output = new_output(args.out, name if mode == "replay" else "validation", schema.root)
        if mode == "replay":
            write_replay(schema, tables, summaries, names, output, checks, before)
        else:
            dump(output / "expected_comparison.json", checks)
            dump(output / "run_manifest.json", manifest("validation", before))
        require(snapshot(schema.root) == before, "Reference files changed")
        dump(output / "integrity.json", {"unchanged": True, "files": len(before), "input_manifests": integrity})
        print(f"PASS: 18 CSV schemas, {len(checks)} expected metrics, {len(before)} unchanged reference files")
        print(f"Output: {output}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
