"""Remove saved cell outputs from notebooks before they enter Git."""

import json
import os
import subprocess
import sys
from pathlib import Path


def clean(content):
    notebook = json.loads(content)
    changed = False
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            if cell.get("outputs"):
                cell["outputs"] = []
                changed = True
            if cell.get("execution_count") is not None:
                cell["execution_count"] = None
                changed = True
    if not changed:
        return content
    return (json.dumps(notebook, ensure_ascii=False, indent=2) + "\n").encode()


def clean_files():
    for path in Path("notebooks").rglob("*.ipynb"):
        content = path.read_bytes()
        cleaned = clean(content)
        if cleaned != content:
            path.write_bytes(cleaned)
            print(f"Salidas eliminadas: {path}")


def git(*args, input=None):
    return subprocess.check_output(["git", *args], input=input)


def clean_index():
    entries = git("ls-files", "--stage", "-z", "--", "notebooks").split(b"\0")
    for entry in filter(None, entries):
        info, name = entry.split(b"\t", 1)
        mode, object_id, stage = info.decode().split()
        if stage != "0" or not name.endswith(b".ipynb"):
            continue
        content = git("cat-file", "blob", object_id)
        cleaned = clean(content)
        if cleaned != content:
            new_id = git("hash-object", "-w", "--stdin", input=cleaned).decode().strip()
            git("update-index", "--cacheinfo", mode, new_id, os.fsdecode(name))
            print(f"Salidas eliminadas del índice: {os.fsdecode(name)}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--all", "--staged"]:
        clean_files()
        clean_index()
    elif sys.argv[1:] == ["--all"]:
        clean_files()
    elif len(sys.argv) == 1:
        sys.stdout.buffer.write(clean(sys.stdin.buffer.read()))
    else:
        raise SystemExit("Uso: strip_notebook_outputs.py [--all [--staged]]")
