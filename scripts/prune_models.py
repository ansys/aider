#!/usr/bin/env python3
"""
Prune unused model files under `models/` that are not referenced
by any Python file matching specified glob patterns.

By default, we look for `.py` files in:
  - aider/api/*.py
  - aider/api/apis/**/*.py
  - aider/api/impl/**/*.py

Hence, those files serve as the "entry points" to check which models are used.

Usage:
  python prune_unused_models.py [--root-globs <pattern1> <pattern2> ...] [--dry-run True|False]

Examples:
  # Dry run with the default patterns
  python prune_unused_models.py

  # Actually remove unreferenced files, scanning default patterns:
  python prune_unused_models.py --dry-run=False

  # Supply your own globs
  python prune_unused_models.py --root-globs 'myapp/*.py' 'myapp/subfolder/**/*.py'

Requirements:
  pip install networkx
"""

import argparse
import ast
import glob
import os
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

import networkx as nx


def expand_globs_to_py_files(patterns: List[str]) -> List[Path]:
    """
    Given a list of glob patterns (e.g. ["aider/api/*.py", "aider/api/apis/**/*.py"]),
    return a list of unique `.py` files that match them.
    """
    all_files = []
    for pattern in patterns:
        for match in glob.glob(pattern, recursive=True):
            p = Path(match)
            if p.is_file() and p.suffix == ".py":
                all_files.append(p.resolve())
    return list(set(all_files))


def parse_python_imports(file_path: Path) -> List[Tuple[str, str]]:
    """
    Parse a Python file's imports via AST and return a list of (import_type, import_name).
    Example returns might look like:
      [
        ("import", "aider.api.models.foo"),
        ("from",   "aider.api.models.bar"),
        ...
      ]
    """
    imports = []
    try:
        with file_path.open("r", encoding="utf-8") as f:
            root = ast.parse(f.read(), filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return imports

    for node in ast.walk(root):
        # Handle "import X" statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                # e.g. import aider.api.models.foo
                imports.append(("import", alias.name))

        # Handle "from X import Y" statements
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # e.g. from aider.api.models.foo import Bar
                full_name = node.module
                imports.append(("from", full_name))

    return imports


def module_name_from_path(py_file: Path) -> str:
    """
    Convert a file path like:  /path/to/aider/api/models/foo_bar.py
    into a canonical 'models.foo_bar' string (assuming we only care about subpaths under `models`).

    If you have deeper subdirs under models/ (e.g. models/subdir/foo.py),
    we'll build `models.subdir.foo`.
    """
    parts = list(py_file.parts)
    try:
        models_index = parts.index("models")
    except ValueError:
        # Not in models dir
        return ""

    # Build the dotted module from everything after "models", dropping the '.py'
    post_models = parts[models_index + 1 :]
    if not post_models:
        # means it was literally the file `models/__init__.py`
        return "models"

    # remove .py from last element
    last = post_models[-1]
    last = last.replace(".py", "")
    post_models[-1] = last

    return "models." + ".".join(post_models)


def build_dependency_graph(entry_files: List[Path], model_files: List[Path]) -> nx.DiGraph:
    """
    Build a directed graph where each node is a `models.something` module.
    A -> B means "A imports B" or "A references B".
    """
    graph = nx.DiGraph()

    # Step 1: Initialize nodes for every file in `models/`.
    for mf in model_files:
        mod_name = module_name_from_path(mf)
        if mod_name:
            graph.add_node(mod_name)

    # Step 2: For each "entry" file (matching user glob but not in models),
    #         parse references to models.*
    #         Mark them as externally referenced if found.
    for ef in entry_files:
        imports = parse_python_imports(ef)
        for imp_type, imp_name in imports:
            if "models" not in imp_name:
                continue
            # We look for "models" in the import path. Extract the portion after 'models.'
            subpath = re.split(r"\bmodels\.?", imp_name, maxsplit=1)
            if len(subpath) < 2:
                continue
            remainder = subpath[1].lstrip(".")
            if remainder:
                full_mod = "models." + remainder
            else:
                # e.g. `from models import something`
                full_mod = "models"

            # If it matches a known node, mark it used externally
            if full_mod in graph.nodes:
                graph.nodes[full_mod].setdefault("external_refs", set()).add(str(ef))

    # Step 3: Parse references within `models/` themselves.
    #         For each models/X, if it imports models/Y, add an edge X -> Y.
    for mf in model_files:
        from_mod = module_name_from_path(mf)
        if not from_mod:
            continue
        imports = parse_python_imports(mf)
        for imp_type, imp_name in imports:
            if "models" not in imp_name:
                continue
            subpath = re.split(r"\bmodels\.?", imp_name, maxsplit=1)
            if len(subpath) < 2:
                continue
            remainder = subpath[1].lstrip(".")
            if remainder:
                full_mod = "models." + remainder
            else:
                full_mod = "models"

            if full_mod in graph.nodes:
                graph.add_edge(from_mod, full_mod)

    return graph


def get_reachable_nodes(graph: nx.DiGraph) -> Set[str]:
    """
    From all nodes that have the 'external_refs' attribute (meaning used by external files),
    do a DFS and find all nodes reachable from them. Return that set.
    """
    reachable = set()
    externally_used = [n for n, data in graph.nodes(data=True) if "external_refs" in data]

    for node in externally_used:
        # get all nodes reachable from 'node'
        sub_reachable = nx.algorithms.traversal.depth_first_search.dfs_tree(
            graph, source=node
        ).nodes()
        reachable.update(sub_reachable)

    return reachable


def main():
    parser = argparse.ArgumentParser(
        description="Designed to prune unused model files under `aider/api/models/`."
    )
    parser.add_argument(
        "--entry-files",
        nargs="+",
        type=Path,
        help=(
            "Glob patterns for .py files serving as 'entry points'"
            " which must fulfill their imports. Supports globs."
            " Example: aider/api/*.py aider/api/apis/**/*.py aider/api/impl/**/*.py"
        ),
    )
    parser.add_argument(
        "--prune-files",
        nargs="+",
        type=Path,
        help="The files we are potentially deleting. Supports globs. Example: aider/models/*.py",
    )
    parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        default=True,
        help="Unless you use this argument, it will only print the files that would be removed.",
    )
    args = parser.parse_args()

    # Check that these are all python files
    for file in args.prune_files:
        assert file.is_file(), f"{file} does not exist"
        assert str(file).endswith(".py"), f"{file} is not a python file"

    # 3. Build the dependency graph
    graph = build_dependency_graph(args.entry_files, args.prune_files)

    # 4. Figure out which models are reachable from external references
    reachable = get_reachable_nodes(graph)

    # 5. Identify all model modules that are not reachable
    all_model_nodes = set(graph.nodes)
    unused = all_model_nodes - reachable

    # 6. Map node name -> file path
    node_to_path = {}
    for mf in args.prune_files:
        mod_name = module_name_from_path(mf)
        if mod_name:
            node_to_path[mod_name] = mf

    # 7. Prepare a list of files to remove
    to_remove = []
    for node in unused:
        if node in node_to_path:
            to_remove.append(node_to_path[node])

    if not to_remove:
        print("No unused model files found.")
        sys.exit(0)

    print("The following model files appear unused:")
    for f in to_remove:
        print(f"  {f}")

    if args.dry_run:
        print("\n(DRY RUN) No files were removed. Run again with --no-dry-run to remove.")
    else:
        for f in to_remove:
            try:
                os.remove(f)
                print(f"Removed {f}")
            except OSError as e:
                print(f"Error removing {f}: {e}")
        print("\nUnused model files removed.")


if __name__ == "__main__":
    main()
