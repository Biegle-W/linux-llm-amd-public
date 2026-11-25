"""Summarize benchmark runs as Markdown and JSON."""

import argparse
import json
from pathlib import Path

from fast_amd.build_manifest import write_json


def cell(value):
    if value is None:
        return "—"
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    def line(values):
        return "| " + " | ".join(map(cell, values)) + " |"

    return [line(headers), line(["---"] * len(headers)), *(line(row) for row in rows)]


def report(out, runs):
    models = []
    for name, run_dir in runs:
        with (run_dir / "fast-result.json").open(encoding="utf-8") as source:
            result = json.load(source)
        fields = (
            "model", "group", "load_seconds", "item_seconds", "single_correct", "episodes_passed",
            "episodes15_passed", "score", "score15", "covered_score", "coverage", "complete",
            "score_meaningful", "timeouts", "status", "pools",
        )
        models.append({
            "name": name, "item_minutes": round(result["item_seconds"] / 60, 3),
            **{field: result[field] for field in fields if field in result},
        })

    lines = ["# Fast AMD results", ""]
    lines.extend(table(
        ("Run", "Model", "Group", "Load (s)", "Items (min)", "Single", "Core", "All episodes",
         "Score", "Score (15)", "Covered score", "Coverage", "Meaningful", "Timeouts", "Status"),
        (
            (
                model["name"], model["model"], model["group"], model["load_seconds"],
                model["item_minutes"], f"{model['single_correct']}/40",
                f"{model['episodes_passed']}/9",
                f"{model['episodes15_passed']}/15" if model["group"] == "large" else None,
                model["score"], model.get("score15"), model.get("covered_score"),
                model["coverage"], "Yes" if model["score_meaningful"] else "No",
                model["timeouts"], model["status"],
            )
            for model in models
        ),
    ))
    lines.extend(["", "## Per-pool results", ""])
    lines.extend(table(
        ("Run", "Pool", "Correct", "Scored", "Total", "Timeouts"),
        (
            (model["name"], pool, data["correct"], data["scored"], data["total"], data["timeouts"])
            for model in models for pool, data in model["pools"].items()
        ),
    ))
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(out / "report.json", {"models": models})


def run_spec(value):
    name, separator, directory = value.partition("=")
    if not name or not separator or not directory:
        raise argparse.ArgumentTypeError("expected NAME=RUN_DIR")
    return name, Path(directory)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("runs", nargs="+", type=run_spec)
    args = parser.parse_args(argv)
    report(args.out, args.runs)


if __name__ == "__main__":
    main()
