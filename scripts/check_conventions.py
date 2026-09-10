#!/usr/bin/env python3
"""Check mechanically verifiable project conventions and print diagnostics."""
from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Diagnostic:
    rule_id: str
    file: str
    line: int
    message: str


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = dotted(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return ""


def literal_int(node: ast.AST | None) -> int | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, int) else None


def check_file(path: Path, root: Path) -> list[Diagnostic]:
    rel = path.relative_to(root).as_posix()
    tree = ast.parse(path.read_text(), filename=rel)
    out: list[Diagnostic] = []

    def add(rule: str, node: ast.AST, message: str) -> None:
        out.append(Diagnostic(rule, rel, getattr(node, "lineno", 1), message))

    is_api = rel.startswith("app/api/")
    is_service = rel.startswith("app/service/")
    is_repo = rel.startswith("app/repository/")
    is_task_routes = rel == "app/api/v1/tasks.py"
    is_api_test = rel.startswith("tests/test_api/") or rel.startswith("tests/test_")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = dotted(node.func)
            leaf = name.rsplit(".", 1)[-1]
            if (is_api or is_service) and not name.startswith("router.") and leaf in {"select", "update", "delete", "execute", "add", "flush"}:
                add("C1", node, f"SQL/ORM operation {leaf} belongs in repository")
            if (is_api or is_repo) and leaf in {"commit", "rollback"}:
                add("C2", node, f"transaction operation {leaf} belongs in service")

        if is_repo and isinstance(node, (ast.Import, ast.ImportFrom)):
            module = node.module if isinstance(node, ast.ImportFrom) else ""
            names = [a.name for a in node.names]
            if module == "fastapi" or "fastapi" in names or "HTTPException" in names:
                add("C3", node, "repository must not depend on FastAPI")

        if is_task_routes and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or dotted(dec.func).split(".")[-1] not in {"get", "post", "put", "patch", "delete"}:
                    continue
                kws = {kw.arg: kw.value for kw in dec.keywords if kw.arg}
                if literal_int(kws.get("status_code")) != 204 and "response_model" not in kws:
                    add("C4", dec, "JSON task route needs an explicit response_model")
                defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d]
                deps = {dotted(d.args[0]) for d in defaults if isinstance(d, ast.Call) and dotted(d.func).endswith("Depends") and d.args}
                for required in ("get_db", "get_current_user"):
                    if not any(dep.endswith(required) for dep in deps):
                        add("C5", node, f"task route must use Depends({required})")

        if is_service and isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and dotted(node.exc.func).endswith("HTTPException"):
            kws = {kw.arg: kw.value for kw in node.exc.keywords if kw.arg}
            if literal_int(kws.get("status_code")) == 404:
                detail = kws.get("detail")
                valid = isinstance(detail, ast.JoinedStr) and "Task " in ast.unparse(detail) and "not found" in ast.unparse(detail)
                if not valid:
                    add("C6", node, "task 404 detail must be f\"Task {task_id} not found\"")

        if is_api_test and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_") and "_should_" not in node.name:
            add("C7", node, "API test name must contain _should_")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    paths = [*root.glob("app/**/*.py"), *root.glob("tests/**/*.py")]
    diagnostics = sorted((d for p in paths for d in check_file(p, root)), key=lambda d: (d.file, d.line, d.rule_id))
    if args.json:
        print(json.dumps({"total": len(diagnostics), "diagnostics": [asdict(d) for d in diagnostics]}, indent=2))
    else:
        for d in diagnostics:
            print(f"{d.file}:{d.line}: {d.rule_id} {d.message}")
        print(f"Total violations: {len(diagnostics)}")
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
