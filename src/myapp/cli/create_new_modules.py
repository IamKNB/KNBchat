from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _validate_identifier(kind: str, value: str) -> str:
    if not NAME_RE.fullmatch(value):
        raise ValueError(
            f"{kind} must be snake_case (lowercase letters, digits, underscore) "
            f"and start with a letter: {value!r}"
        )
    return value


def _paths() -> tuple[Path, Path, Path]:
    myapp_dir = Path(__file__).resolve().parents[1]
    modules_dir = myapp_dir / "modules"
    router_path = myapp_dir / "router.py"
    return myapp_dir, modules_dir, router_path


def _ensure_modules_dir(modules_dir: Path) -> None:
    if not modules_dir.exists():
        raise FileNotFoundError(f"modules directory not found: {modules_dir}")
    if not modules_dir.is_dir():
        raise NotADirectoryError(f"modules path is not a directory: {modules_dir}")


def _ensure_dir(path: Path, *, dry_run: bool) -> None:
    if path.exists():
        if not path.is_dir():
            raise NotADirectoryError(f"expected directory at {path}")
        return
    if dry_run:
        print(f"[dry-run] create dir {path}")
        return
    path.mkdir(parents=True, exist_ok=True)


def _write_file(path: Path, content: str, *, force: bool, dry_run: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"file exists: {path}")
    if dry_run:
        print(f"[dry-run] write file {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _router_py(module_name: str) -> str:
    return (
        "from fastapi import APIRouter\n\n"
        "from .routes import router as routes_router\n\n"
        f"router = APIRouter(prefix=\"/{module_name}\", tags=[\"{module_name}\"])\n"
        "router.include_router(routes_router)\n"
    )


def _routes_init_py(route_name: str) -> str:
    return (
        "from fastapi import APIRouter\n\n"
        f"from . import {route_name}\n\n"
        "router = APIRouter()\n"
        f"router.include_router({route_name}.router)\n\n"
        "__all__ = [\"router\"]\n"
    )


def _route_py() -> str:
    return "from fastapi import APIRouter\n\nrouter = APIRouter()\n"


def _module_init_py() -> str:
    return "from . import api\n"


def _api_init_py() -> str:
    return "from .router import router\n\n__all__ = [\"router\"]\n"


def _scaffold_module(
    module_name: str,
    route_name: str,
    *,
    force: bool,
    dry_run: bool,
) -> Path:
    _, modules_dir, _ = _paths()
    _ensure_modules_dir(modules_dir)

    module_dir = modules_dir / module_name
    if module_dir.exists() and not force:
        raise FileExistsError(
            f"module directory already exists (use --force to overwrite): {module_dir}"
        )

    dirs = [
        module_dir,
        module_dir / "api",
        module_dir / "api" / "routes",
        module_dir / "schemas",
        module_dir / "services",
        module_dir / "domain",
        module_dir / "persistence",
        module_dir / "persistence" / "models",
        module_dir / "persistence" / "repositories",
    ]
    for d in dirs:
        _ensure_dir(d, dry_run=dry_run)

    files: dict[Path, str] = {
        module_dir / "__init__.py": _module_init_py(),
        module_dir / "api" / "__init__.py": _api_init_py(),
        module_dir / "api" / "router.py": _router_py(module_name),
        module_dir / "api" / "routes" / "__init__.py": _routes_init_py(route_name),
        module_dir / "api" / "routes" / f"{route_name}.py": _route_py(),
        module_dir / "schemas" / "__init__.py": "",
        module_dir / "services" / "__init__.py": "",
        module_dir / "domain" / "__init__.py": "",
        module_dir / "persistence" / "__init__.py": "",
        module_dir / "persistence" / "models" / "__init__.py": "",
        module_dir / "persistence" / "repositories" / "__init__.py": "",
    }
    for path, content in files.items():
        _write_file(path, content, force=force, dry_run=dry_run)

    return module_dir


def _update_main_router(module_name: str, *, dry_run: bool) -> bool:
    _, _, router_path = _paths()
    if not router_path.exists():
        raise FileNotFoundError(f"router.py not found: {router_path}")

    import_line = (
        f"from myapp.modules.{module_name}.api import router as {module_name}_router"
    )
    include_line = f"router.include_router({module_name}_router)"

    text = router_path.read_text(encoding="utf-8")
    if import_line in text and include_line in text:
        return False

    lines = text.splitlines()

    if import_line not in text:
        last_module_import = None
        last_import = None
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("from myapp.modules."):
                last_module_import = idx
            if stripped.startswith("from ") or stripped.startswith("import "):
                last_import = idx
        insert_at = (
            last_module_import + 1
            if last_module_import is not None
            else (last_import + 1 if last_import is not None else 0)
        )
        lines.insert(insert_at, import_line)

    if include_line not in lines:
        last_include = None
        router_init = None
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "router = APIRouter()":
                router_init = idx
            if stripped.startswith("router.include_router("):
                last_include = idx
        if last_include is not None:
            insert_at = last_include + 1
        elif router_init is not None:
            insert_at = router_init + 1
        else:
            raise ValueError("Could not find 'router = APIRouter()' in router.py")
        lines.insert(insert_at, include_line)

    new_text = "\n".join(lines) + "\n"
    if dry_run:
        print(f"[dry-run] update {router_path}")
        return True

    router_path.write_text(new_text, encoding="utf-8")
    return True


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a new module scaffold under src/myapp/modules."
    )
    parser.add_argument("name", help="module name (snake_case)")
    parser.add_argument(
        "--route",
        default="main",
        help="initial route file name under api/routes (default: main)",
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="also update src/myapp/router.py to include the module router",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing files if the module already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print planned changes without writing files",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        module_name = _validate_identifier("module name", args.name)
        route_name = _validate_identifier("route name", args.route)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        module_dir = _scaffold_module(
            module_name, route_name, force=args.force, dry_run=args.dry_run
        )
    except (FileExistsError, FileNotFoundError, NotADirectoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.register:
        try:
            updated = _update_main_router(module_name, dry_run=args.dry_run)
        except (FileNotFoundError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if updated:
            print(f"router updated: {module_name}")
        else:
            print("router already up to date")

    print(f"module created: {module_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
