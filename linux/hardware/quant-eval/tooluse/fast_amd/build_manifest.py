"""Build and verify the frozen selection from the local BFCL snapshot."""

import argparse
import hashlib
import json
from pathlib import Path

from fast_amd.bfcl.backend import CLASS_FILES
from fast_amd.tooling import tool_schema, validate_tool_names

PACKAGE = Path(__file__).resolve().parent
SOURCE = PACKAGE.parent / "bfcl-src"
MANIFEST = PACKAGE / "manifest.json"
SEED = 20261122
POOLS = {
    "parallel": ("parallel", 15),
    "irrelevance": ("irrelevance", 15),
    "simple": ("simple_python", 10),
    "mt_base": ("multi_turn_base", 5),
    "mt_miss_param": ("multi_turn_miss_param", 5),
    "mt_miss_func": ("multi_turn_miss_func", 5),
}


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def index_rows(data, name):
    rows = {}
    for line in data.splitlines():
        if line.strip():
            row = json.loads(line)
            key = row[name]
            if key in rows:
                raise ValueError(f"Duplicate {name}: {key}")
            rows[key] = row
    return rows


def build(src):
    files = {}

    def read(relative):
        data = (src / relative).read_bytes()
        files[relative] = sha(data)
        return data

    commit = read("COMMIT").decode().strip()
    backend = "eval_checker/multi_turn_eval"
    for relative in (
        f"{backend}/multi_turn_checker.py", f"{backend}/multi_turn_utils.py",
        "constants/default_prompts.py", "model_handler/base_handler.py", "model_handler/utils.py",
    ):
        read(relative)
    docs = {}
    for name, module in CLASS_FILES.items():
        read(f"{backend}/func_source_code/{module}.py")
        docs[name] = list(index_rows(read(f"data/multi_turn_func_doc/{module}.json"), "name").values())

    selected = {}
    data = {}
    ids = set()
    for pool, (filename, count) in POOLS.items():
        filename = f"BFCL_v4_{filename}.json"
        questions = index_rows(read(f"data/{filename}"), "id")
        answers = (
            {} if pool == "irrelevance"
            else index_rows(read(f"data/possible_answer/{filename}"), "id")
        )
        multi = pool.startswith("mt_")
        eligible = []
        for item_id, row in questions.items():
            if item_id in ids:
                raise ValueError(f"Duplicate id: {item_id}")
            ids.add(item_id)
            if multi:
                if not set(row["involved_classes"]) <= CLASS_FILES.keys():
                    continue
            else:
                if len(row["question"]) != 1 or (pool != "irrelevance" and item_id not in answers):
                    continue
                try:
                    functions = row["function"]
                    validate_tool_names(functions)
                    # Keep the frozen eligibility rule separate from wire conversion.
                    tool_schema(functions)
                except (KeyError, TypeError, AttributeError, ValueError):
                    continue
            eligible.append(item_id)
        eligible.sort(key=lambda item_id: (sha(f"{SEED}|{pool}|{item_id}".encode()), item_id))
        if len(eligible) < count:
            raise ValueError(f"Too few eligible items in {pool}")
        selected[pool] = []
        for index, item_id in enumerate(eligible[:count]):
            row, answer = questions[item_id], answers.get(item_id)
            if multi and answer is None:
                raise ValueError(f"Missing answer for {item_id}")
            data[item_id] = row, answer
            selected[pool].append({
                "id": item_id, "pool": pool, "part": "multi" if multi else "single",
                "core": not multi or index < 3,
                "sha256": sha(canonical([row, answer])),
            })

    items = [item for pool in ("parallel", "irrelevance", "simple") for item in selected[pool]]
    for triplet in zip(*(selected[pool] for pool in ("mt_base", "mt_miss_param", "mt_miss_func"))):
        items.extend(triplet)
    groups = {
        "small": [item["id"] for item in items if item["core"]],
        "large": [item["id"] for item in items],
    }
    manifest = {
        "seed": SEED, "source_commit": commit, "source_sha256": files,
        "counts": {pool: len(items) for pool, items in selected.items()},
        "items": items, "groups": groups,
    }
    manifest["manifest_hash"] = sha(canonical(manifest))
    return manifest, data, docs


def verify(src, path):
    frozen = json.loads(path.read_bytes())
    expected, data, docs = build(src)
    if frozen != expected:
        raise ValueError("Manifest or BFCL source hash mismatch")
    return frozen, data, docs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=MANIFEST)
    args = parser.parse_args(argv)
    manifest, _, _ = build(args.src)
    write_json(args.out, manifest)


if __name__ == "__main__":
    main()
