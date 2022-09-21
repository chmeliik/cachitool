from pathlib import Path
from typing import Any, Literal

import pydantic

from cachitool import util
from cachitool.models.unique import UniqueItem, make_unique


class PkgSpec(UniqueItem, extra="forbid"):
    type: str
    path: Path

    @pydantic.validator("path")
    def make_absolute(cls, path: Path) -> Path:
        return path.resolve()

    def unique_by(self) -> tuple[str, Path]:
        return self.type, self.path


class GoPkgSpec(PkgSpec):
    type: Literal["gomod"]


class PipPkgSpec(PkgSpec):
    type: Literal["pip"]
    requirements_files: list[Path] | None = None
    requirements_build_files: list[Path] | None = None

    @pydantic.validator("requirements_files", "requirements_build_files")
    def normalize_reqfile_paths(cls, v: list[str | Path] | None) -> list[Path] | None:
        if v is None:
            return None
        return [util.normpath(p) for p in v]


def make_package_spec(data: dict[str, Any]) -> PkgSpec:
    pkg_type = data.get("type")
    match pkg_type:
        case "gomod":
            return GoPkgSpec(**data)
        case "pip":
            return PipPkgSpec(**data)
        case _:
            raise ValueError(f"unknown package type: {pkg_type}")
