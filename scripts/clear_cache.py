"""Clear local runtime/test caches for the project."""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

CACHE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def main() -> None:
    removed = []
    for path in ROOT.rglob("*"):
        if path.is_dir() and path.name in CACHE_DIR_NAMES:
            shutil.rmtree(path, ignore_errors=True)
            removed.append(path)

    if removed:
        print("Removed cache directories:")
        for item in removed:
            print(f"- {item.relative_to(ROOT)}")
    else:
        print("No cache directories found.")


if __name__ == "__main__":
    main()
