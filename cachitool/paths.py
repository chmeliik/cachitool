from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import PosixPath


PathT = type(Path())


# class SafePath(PosixPath):  # uncomment this (and remove line below) to pass type check
class SafePath(PathT):
    def __new__(cls, *args: Any, **kwargs: dict[str, Any]) -> SafePath:
        path = super().__new__(cls, *args, **kwargs)
        return path.resolve()

    def get_subpath(self, relpath: str | Path) -> SafePath:
        path = (self / relpath).resolve()
        if not path.is_relative_to(self):
            raise ValueError(f"{relpath} (or the file it points to) is outside {path}!")
        return path

    def mkdirs(self) -> SafePath:
        self.mkdir(parents=True, exist_ok=True)
        return self


def subpath(relpath: str | Path) -> property:
    def get_this_subpath(safepath: SafePath) -> SafePath:
        return safepath.get_subpath(relpath)

    return property(get_this_subpath)


class OutputDir(SafePath):
    gomod_deps = subpath("deps/gomod")
    pip_deps = subpath("deps/pip")
    pip_local_index = subpath("piprepo")
    config_files = subpath("config-files")
    env_file = subpath("env.json")
    content_manifest = subpath("content-manifest.json")
